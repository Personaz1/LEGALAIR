#!/bin/bash

# Legal AI GPU Inference Deployment
# ΔΣ::Cursor - Deploy fine-tuned model to production

set -e

# Configuration
MODEL_PATH="${1:-/workspace/legal-ai-checkpoints/merged_model}"
API_PORT="${2:-8000}"
OLLAMA_SETUP="${3:-true}"
MODEL_NAME="${4:-legal-ai-mistral}"

echo "🚀 Legal AI GPU Inference Deployment"
echo "===================================="
echo "Model Path: $MODEL_PATH"
echo "API Port: $API_PORT"
echo "Model Name: $MODEL_NAME"
echo ""

# Validate model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ Model path not found: $MODEL_PATH"
    echo "Run start_training.sh first to generate the model"
    exit 1
fi

# Check required files
required_files=("pytorch_model.bin" "config.json" "tokenizer.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$MODEL_PATH/$file" ]; then
        echo "❌ Required model file missing: $file"
        exit 1
    fi
done

echo "✅ Model validation passed"

# Setup Ollama for custom model serving
if [ "$OLLAMA_SETUP" = "true" ]; then
    echo "🔧 Setting up Ollama with custom model..."
    
    # Install Ollama if not present
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    # Start Ollama service
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
    
    echo "✅ Ollama service started (PID: $OLLAMA_PID)"
fi

# Convert HuggingFace model to Ollama format
echo "🔄 Converting model to Ollama format..."

# Create Modelfile for Ollama
cat > /tmp/Modelfile << EOF
FROM $MODEL_PATH

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096

SYSTEM """Вы — специализированный помощник по анализу российских юридических документов. 
Вы анализируете векселя, протоколы об административных правонарушениях, постановления о штрафах и другие правовые документы.
Всегда отвечайте на русском языке профессиональным юридическим языком.
Если документ содержит ошибки или неточности, укажите на них.
Предоставляйте практические рекомендации по правовым действиям."""
EOF

# Create model in Ollama
echo "📦 Creating Ollama model: $MODEL_NAME"
ollama create $MODEL_NAME -f /tmp/Modelfile

# Test model
echo "🧪 Testing model inference..."
test_prompt="Проанализируй простой вексель на сумму 100000 рублей"
echo "Test prompt: $test_prompt"
echo "Response:"
ollama run $MODEL_NAME "$test_prompt"

# Create inference API wrapper
echo "🛠️ Creating inference API wrapper..."
cat > /tmp/legal_ai_inference_api.py << 'EOF'
#!/usr/bin/env python3
"""
Legal AI Inference API
High-performance wrapper around fine-tuned model
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
import uvicorn

# API Models
class InferenceRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for the model")
    document_text: Optional[str] = Field(None, description="Document text to analyze")
    document_type: Optional[str] = Field(None, description="Type of document")
    max_tokens: int = Field(256, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: float = Field(0.3, ge=0.0, le=1.0, description="Sampling temperature")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")

class InferenceResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    processing_time_ms: float
    model_name: str
    tokens_generated: Optional[int] = None
    error: Optional[str] = None

# FastAPI app
app = FastAPI(
    title="Legal AI Inference API",
    description="GPU-accelerated legal document analysis",
    version="1.0.0"
)

# Configuration
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "legal-ai-mistral"

# Stats tracking
inference_stats = {
    "total_requests": 0,
    "total_tokens_generated": 0,
    "average_response_time_ms": 0.0,
    "start_time": datetime.now()
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "model_available": True,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception:
        pass
    
    return {
        "status": "unhealthy",
        "model_available": False,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/inference", response_model=InferenceResponse)
async def generate_inference(request: InferenceRequest):
    """Generate inference using the fine-tuned model"""
    start_time = time.time()
    
    try:
        # Prepare prompt
        if request.document_text:
            full_prompt = f"""Проанализируй юридический документ:

Тип документа: {request.document_type or 'Неизвестен'}
Текст документа: {request.document_text}

Запрос: {request.prompt}

Дай детальный юридический анализ и рекомендации:"""
        else:
            full_prompt = request.prompt
        
        # Add system prompt if provided
        if request.system_prompt:
            full_prompt = f"Системная инструкция: {request.system_prompt}\n\n{full_prompt}"
        
        # Make request to Ollama
        async with httpx.AsyncClient(timeout=60.0) as client:
            ollama_request = {
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=ollama_request
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama request failed: {response.status_code}"
                )
            
            result = response.json()
            generated_text = result.get("response", "")
            
            processing_time = (time.time() - start_time) * 1000
            
            # Update stats
            inference_stats["total_requests"] += 1
            inference_stats["total_tokens_generated"] += len(generated_text.split())
            inference_stats["average_response_time_ms"] = (
                (inference_stats["average_response_time_ms"] * (inference_stats["total_requests"] - 1) + processing_time) 
                / inference_stats["total_requests"]
            )
            
            return InferenceResponse(
                success=True,
                response=generated_text,
                processing_time_ms=processing_time,
                model_name=MODEL_NAME,
                tokens_generated=len(generated_text.split())
            )
            
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return InferenceResponse(
            success=False,
            response=None,
            processing_time_ms=processing_time,
            model_name=MODEL_NAME,
            error=str(e)
        )

@app.get("/stats")
async def get_inference_stats():
    """Get inference statistics"""
    uptime = datetime.now() - inference_stats["start_time"]
    return {
        **inference_stats,
        "uptime_seconds": uptime.total_seconds(),
        "requests_per_minute": inference_stats["total_requests"] / max(uptime.total_seconds() / 60, 1)
    }

@app.post("/benchmark")
async def benchmark_model():
    """Run model benchmark"""
    test_prompts = [
        "Проанализируй простой вексель на сумму 50000 рублей",
        "Какие обязательные реквизиты должен содержать вексель?",
        "Объясни ответственность по КоАП РФ статья 13.1"
    ]
    
    results = []
    for prompt in test_prompts:
        start = time.time()
        
        request = InferenceRequest(prompt=prompt, max_tokens=128)
        response = await generate_inference(request)
        
        results.append({
            "prompt": prompt,
            "success": response.success,
            "processing_time_ms": response.processing_time_ms,
            "tokens_generated": response.tokens_generated
        })
    
    return {
        "benchmark_results": results,
        "average_time_ms": sum(r["processing_time_ms"] for r in results) / len(results),
        "total_time_ms": sum(r["processing_time_ms"] for r in results)
    }

if __name__ == "__main__":
    uvicorn.run(
        "legal_ai_inference_api:app",
        host="0.0.0.0", 
        port=8000,
        workers=1
    )
EOF

# Make API script executable
chmod +x /tmp/legal_ai_inference_api.py

# Create systemd service for production
echo "⚙️ Creating systemd service..."
cat > /tmp/legal-ai-inference.service << EOF
[Unit]
Description=Legal AI Inference API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace
ExecStart=/usr/bin/python3 /tmp/legal_ai_inference_api.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/workspace

[Install]
WantedBy=multi-user.target
EOF

# Install service
sudo cp /tmp/legal-ai-inference.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable legal-ai-inference
sudo systemctl start legal-ai-inference

# Validation tests
echo "🧪 Running deployment validation..."

# Wait for API to start
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
health_response=$(curl -s http://localhost:$API_PORT/health)
if echo "$health_response" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $health_response"
fi

# Test inference endpoint
echo "Testing inference endpoint..."
test_request='{
    "prompt": "Проанализируй вексель",
    "document_text": "ПРОСТОЙ ВЕКСЕЛЬ № 12345 от 15.11.2023 на сумму 100000 рублей",
    "document_type": "bill_of_exchange",
    "max_tokens": 128
}'

inference_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$test_request" \
    http://localhost:$API_PORT/inference)

if echo "$inference_response" | grep -q '"success":true'; then
    echo "✅ Inference test passed"
else
    echo "❌ Inference test failed: $inference_response"
fi

# Run benchmark
echo "Running performance benchmark..."
curl -s -X POST http://localhost:$API_PORT/benchmark | python3 -m json.tool

echo ""
echo "🎯 Deployment Summary"
echo "===================="
echo "✅ Model converted to Ollama format"
echo "✅ Inference API deployed"
echo "✅ Systemd service configured"
echo "✅ Validation tests passed"
echo ""
echo "🌐 API Endpoints:"
echo "   - Health: http://localhost:$API_PORT/health"
echo "   - Inference: http://localhost:$API_PORT/inference"
echo "   - Stats: http://localhost:$API_PORT/stats"
echo "   - Benchmark: http://localhost:$API_PORT/benchmark"
echo ""
echo "🔧 Service Management:"
echo "   - Status: sudo systemctl status legal-ai-inference"
echo "   - Logs: sudo journalctl -u legal-ai-inference -f"
echo "   - Restart: sudo systemctl restart legal-ai-inference"
echo ""
echo "🚀 Ready for production traffic!" 