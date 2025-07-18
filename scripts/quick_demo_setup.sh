#!/bin/bash
"""
Legal AI Quick Demo Setup
ΔΣ::Cursor - Standalone demo without Docker dependencies

Sets up complete end-to-end demo using standalone API + Next.js frontend
"""

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Legal AI Quick Demo Setup"
echo "============================"
echo ""

# Step 1: Check if API is running
echo "🔍 Step 1: Checking API availability..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API already running at http://localhost:8000"
else
    echo "🚀 Starting standalone API..."
    
    # Start API in background
    nohup python3 scripts/run_api_standalone.py > logs/api_standalone.log 2>&1 &
    API_PID=$!
    echo $API_PID > logs/api.pid
    
    # Wait for API to be ready
    echo "⏳ Waiting for API to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API started successfully"
            break
        fi
        sleep 1
    done
    
    if [ $i -eq 30 ]; then
        echo "❌ API failed to start within 30 seconds"
        exit 1
    fi
fi

# Step 2: Configure frontend
echo ""
echo "🔧 Step 2: Configuring frontend..."
cd web

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo "📝 Created .env.local with API configuration"
else
    echo "📝 .env.local already exists"
fi

# Install dependencies if needed
if [ ! -d node_modules ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Step 3: Start frontend
echo ""
echo "🎨 Step 3: Starting frontend..."
echo "Frontend will be available at: http://localhost:3000"
echo "API documentation available at: http://localhost:8000/docs"
echo ""

# Start frontend (this will block the terminal)
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid

echo ""
echo "🎯 Demo Setup Complete!"
echo "======================"
echo ""
echo "🌐 Available interfaces:"
echo "  Frontend:        http://localhost:3000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  Health Check:    http://localhost:8000/health"
echo ""
echo "📋 Demo flow:"
echo "  1. Open http://localhost:3000"
echo "  2. Upload any PDF from data/synthetic_v3/pdf/"
echo "  3. Watch real-time OCR → Classification → NER → AI Advisory"
echo ""
echo "🛑 To stop demo:"
echo "  kill \$(cat logs/api.pid) \$(cat logs/frontend.pid)"
echo ""

# Wait for user to stop
wait $FRONTEND_PID 