#!/bin/bash
set -e

# Legal AI - RunPod GPU Setup Script
# Автоматическая настройка окружения для GPU обучения

echo "🚀 Legal AI - RunPod GPU Setup"
echo "==============================================="

# Check if running on GPU instance
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ No NVIDIA GPU detected. This script requires a GPU instance."
    exit 1
fi

echo "✅ GPU detected:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits

# Update system packages
echo "📦 Updating system packages..."
apt-get update -qq
apt-get install -y git curl wget vim htop tree jq

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    systemctl start docker
    systemctl enable docker
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install NVIDIA Container Toolkit
if ! command -v nvidia-container-runtime &> /dev/null; then
    echo "🎯 Installing NVIDIA Container Toolkit..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
    
    apt-get update -qq
    apt-get install -y nvidia-container-toolkit
    systemctl restart docker
fi

# Set working directory
WORK_DIR="/workspace/legal-ai"
echo "📁 Setting up workspace at $WORK_DIR"

# Clone repository if not exists
if [ ! -d "$WORK_DIR" ]; then
    echo "📥 Cloning Legal AI repository..."
    git clone https://github.com/your-org/legal-ai.git $WORK_DIR
    cd $WORK_DIR
else
    echo "📂 Using existing repository at $WORK_DIR"
    cd $WORK_DIR
    git pull origin main
fi

# Set up environment variables
echo "🔐 Setting up environment variables..."
cat > .env << EOF
# GPU Environment Configuration
SECRET_KEY=legal-ai-gpu-$(openssl rand -hex 16)
DATABASE_URL=postgresql+asyncpg://legal_ai:legal_ai_pass@postgres:5432/legal_ai_db
OLLAMA_URL=http://ollama:11434

# GPU Settings
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Model Configuration
MODEL_CACHE_DIR=/workspace/models
HUGGINGFACE_HUB_CACHE=/workspace/hf_cache
TRANSFORMERS_CACHE=/workspace/transformers_cache

# RunPod specific
RUNPOD_POD_ID=${RUNPOD_POD_ID:-unknown}
RUNPOD_PUBLIC_IP=${RUNPOD_PUBLIC_IP:-localhost}

# Label Studio
LABEL_STUDIO_USERNAME=admin
LABEL_STUDIO_PASSWORD=admin123
EOF

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p data/{raw,annotated,processed}
mkdir -p ml/checkpoints
mkdir -p models hf_cache transformers_cache

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.gpu.yml build

# Download and setup Ollama models
echo "🤖 Setting up Ollama models..."
docker-compose -f docker-compose.gpu.yml up -d ollama
sleep 10

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version > /dev/null; then
        echo "✅ Ollama is ready"
        break
    fi
    echo "⏳ Waiting... ($i/30)"
    sleep 2
done

# Pull required models
echo "📥 Pulling Mistral-7B model..."
docker exec legal-ai-ollama ollama pull mistral:7b

echo "📥 Pulling additional models..."
docker exec legal-ai-ollama ollama pull llama2:7b
docker exec legal-ai-ollama ollama pull codellama:7b

# Install Python dependencies for training
echo "🐍 Installing Python training dependencies..."
cat > requirements.gpu.txt << EOF
# GPU Training Dependencies
torch>=2.0.0
transformers>=4.30.0
datasets>=2.14.0
accelerate>=0.20.0
peft>=0.4.0
bitsandbytes>=0.39.0
scipy>=1.11.0
scikit-learn>=1.3.0
wandb>=0.15.0
tensorboard>=2.13.0

# Model specific
spacy[cuda]>=3.6.0
sentence-transformers>=2.2.0
optimum>=1.9.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0
pillow>=10.0.0
opencv-python>=4.8.0

# Monitoring
prometheus-client>=0.17.0
psutil>=5.9.0
EOF

pip install -r requirements.gpu.txt

# Download spaCy Russian model
python -m spacy download ru_core_news_lg

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.gpu.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

# Health checks
echo "🏥 Running health checks..."

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is running"
else
    echo "❌ API health check failed"
fi

# Check Web UI
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Web UI is running"
else
    echo "❌ Web UI health check failed"
fi

# Check Label Studio
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Label Studio is running"
else
    echo "❌ Label Studio health check failed"
fi

# Check Grafana
if curl -s http://localhost:3001 > /dev/null; then
    echo "✅ Grafana is running"
else
    echo "❌ Grafana health check failed"
fi

# Display service URLs
echo ""
echo "🌐 Service URLs (replace localhost with your RunPod IP):"
echo "==============================================="
echo "🖥️  Main Web UI:      http://localhost:3000"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "📊 Label Studio:      http://localhost:8080 (admin/admin123)"
echo "📈 Grafana:          http://localhost:3001 (admin/admin123)"
echo "🔍 Prometheus:       http://localhost:9090"
echo "🤖 Ollama:           http://localhost:11434"
echo ""

# Display GPU information
echo "🎯 GPU Information:"
echo "==============================================="
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits

# Display system resources
echo ""
echo "💻 System Resources:"
echo "==============================================="
echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $4 " available"}')"

# Create training script shortcut
echo "📚 Creating training shortcuts..."
cat > start_training.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Legal AI Training Pipeline"
echo "======================================"

# Check if data is available
if [ ! -d "data/annotated" ] || [ -z "$(ls -A data/annotated)" ]; then
    echo "❌ No annotated data found in data/annotated/"
    echo "Please run annotation workflow first"
    exit 1
fi

# Start training container with GPU access
docker-compose -f docker-compose.gpu.yml exec api python -m ml.train_baseline \
    --data-dir /app/data/annotated \
    --model-output /app/ml/checkpoints \
    --epochs 10 \
    --batch-size 16 \
    --learning-rate 2e-5

echo "✅ Training completed!"
EOF

chmod +x start_training.sh

# Display final instructions
echo ""
echo "✅ Setup completed successfully!"
echo "==============================================="
echo ""
echo "🔥 Next steps:"
echo "1. Upload real document scans to data/raw/"
echo "2. Run: python scripts/ls_bulk_import.py data/synthetic_v2/"
echo "3. Annotate documents in Label Studio"
echo "4. Export annotations: python scripts/ls_export_hf.py PROJECT_ID"
echo "5. Start training: ./start_training.sh"
echo ""
echo "📊 Monitor progress:"
echo "- Training metrics: http://localhost:3001"
echo "- System resources: htop or nvidia-smi"
echo "- Container logs: docker-compose -f docker-compose.gpu.yml logs -f"
echo ""
echo "🎯 Ready for GPU training!"

# Start resource monitoring in background
nohup watch -n 5 nvidia-smi > /tmp/gpu_monitor.log 2>&1 &
echo "GPU monitoring started (logs: /tmp/gpu_monitor.log)" 