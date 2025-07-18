#!/bin/bash
"""
Legal ASI - Ollama Setup Script
Installs and configures Ollama with Mistral-7B for advisory service
"""

set -e

echo "🚀 Legal ASI - Setting up Ollama with Mistral-7B"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on macOS or Linux
OS=$(uname -s)
echo -e "${BLUE}🔍 Detected OS: $OS${NC}"

# Install Ollama based on OS
install_ollama() {
    echo -e "${YELLOW}📦 Installing Ollama...${NC}"
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        if ! command -v ollama &> /dev/null; then
            echo "Installing Ollama for macOS..."
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            echo "✅ Ollama already installed"
        fi
    elif [[ "$OS" == "Linux" ]]; then
        # Linux
        if ! command -v ollama &> /dev/null; then
            echo "Installing Ollama for Linux..."
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            echo "✅ Ollama already installed"
        fi
    else
        echo -e "${RED}❌ Unsupported OS: $OS${NC}"
        exit 1
    fi
}

# Start Ollama service
start_ollama() {
    echo -e "${YELLOW}🔄 Starting Ollama service...${NC}"
    
    # Check if Ollama is already running
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama is already running"
        return 0
    fi
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS - start as background process
        nohup ollama serve > ollama.log 2>&1 &
        echo "Started Ollama on macOS (background process)"
    elif [[ "$OS" == "Linux" ]]; then
        # Linux - try systemd first, fallback to background process
        if systemctl --user start ollama 2>/dev/null; then
            echo "Started Ollama via systemd"
        else
            nohup ollama serve > ollama.log 2>&1 &
            echo "Started Ollama as background process"
        fi
    fi
    
    # Wait for service to start
    echo "Waiting for Ollama to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            echo "✅ Ollama service is running"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ Failed to start Ollama service${NC}"
    exit 1
}

# Pull Mistral model
pull_mistral() {
    echo -e "${YELLOW}📥 Pulling Mistral-7B model...${NC}"
    echo "This may take several minutes depending on your internet connection..."
    
    if ollama list | grep -q "mistral:7b"; then
        echo "✅ Mistral-7B already available"
        return 0
    fi
    
    echo "Downloading Mistral-7B (approximately 4.1GB)..."
    if ollama pull mistral:7b; then
        echo "✅ Mistral-7B model downloaded successfully"
    else
        echo -e "${RED}❌ Failed to download Mistral-7B model${NC}"
        exit 1
    fi
}

# Test the setup
test_setup() {
    echo -e "${YELLOW}🧪 Testing Ollama setup...${NC}"
    
    # Test API availability
    if ! curl -s http://localhost:11434/api/version > /dev/null; then
        echo -e "${RED}❌ Ollama API not accessible${NC}"
        exit 1
    fi
    
    # Test model availability
    if ! ollama list | grep -q "mistral:7b"; then
        echo -e "${RED}❌ Mistral-7B model not found${NC}"
        exit 1
    fi
    
    # Test inference
    echo "Testing model inference..."
    test_response=$(ollama run mistral:7b "Ответь кратко: что такое вексель?" 2>/dev/null || echo "error")
    
    if [[ "$test_response" == "error" ]] || [[ -z "$test_response" ]]; then
        echo -e "${YELLOW}⚠️  Model inference test failed, but model is available${NC}"
    else
        echo "✅ Model inference test successful"
        echo "Sample response: ${test_response:0:100}..."
    fi
}

# Display usage information
show_usage() {
    echo -e "${BLUE}📖 Ollama Usage Information${NC}"
    echo "=================================="
    echo
    echo "🔧 Management Commands:"
    echo "  ollama list                    # List downloaded models"
    echo "  ollama run mistral:7b         # Interactive chat with Mistral"
    echo "  ollama stop mistral:7b        # Stop model (free memory)"
    echo "  ollama rm mistral:7b          # Remove model"
    echo
    echo "🌐 API Endpoints:"
    echo "  http://localhost:11434/api/version    # Service status"
    echo "  http://localhost:11434/api/tags       # List models"
    echo "  http://localhost:11434/api/chat       # Chat completion"
    echo
    echo "🔄 Service Management:"
    if [[ "$OS" == "Darwin" ]]; then
        echo "  pkill ollama                  # Stop Ollama service"
        echo "  ollama serve                  # Start Ollama service"
    elif [[ "$OS" == "Linux" ]]; then
        echo "  systemctl --user stop ollama  # Stop Ollama service"
        echo "  systemctl --user start ollama # Start Ollama service"
    fi
    echo
    echo "💡 Tips:"
    echo "  - Mistral-7B uses ~4GB RAM when loaded"
    echo "  - Model auto-unloads after 5 minutes of inactivity"
    echo "  - Use OLLAMA_HOST to change binding address"
    echo "  - Use OLLAMA_MODELS to change model storage location"
}

# Main execution
main() {
    case "${1:-install}" in
        "install")
            install_ollama
            start_ollama
            pull_mistral
            test_setup
            show_usage
            echo
            echo -e "${GREEN}🎉 Ollama setup complete!${NC}"
            echo -e "${GREEN}✅ Mistral-7B ready for Legal ASI advisory service${NC}"
            ;;
        "start")
            start_ollama
            ;;
        "test") 
            test_setup
            ;;
        "stop")
            echo -e "${YELLOW}🛑 Stopping Ollama...${NC}"
            if [[ "$OS" == "Darwin" ]]; then
                pkill ollama || echo "Ollama not running"
            elif [[ "$OS" == "Linux" ]]; then
                systemctl --user stop ollama || pkill ollama || echo "Ollama not running"
            fi
            echo "✅ Ollama stopped"
            ;;
        "status")
            echo -e "${BLUE}📊 Ollama Status${NC}"
            echo "=================="
            if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
                echo "✅ Service: Running"
                echo "📋 Models:"
                ollama list
            else
                echo "❌ Service: Not running"
            fi
            ;;
        "help"|"-h"|"--help")
            echo "Legal ASI - Ollama Setup Script"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  install    Install Ollama and Mistral-7B (default)"
            echo "  start      Start Ollama service"
            echo "  stop       Stop Ollama service"
            echo "  test       Test current setup"
            echo "  status     Show service and model status"
            echo "  help       Show this help message"
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Check for required tools
check_requirements() {
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl is required but not installed${NC}"
        exit 1
    fi
}

# Script entry point
check_requirements
main "$@" 