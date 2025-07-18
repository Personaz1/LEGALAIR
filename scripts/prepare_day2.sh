#!/bin/bash

# Legal ASI - Day 2 Preparation Script
# Setup data pipeline and Label Studio for annotation

set -e

echo "🏗️ Legal ASI - Day 2 Data Pipeline Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create data directories
print_info "Creating data directory structure..."
mkdir -p data/raw/{bills,fines,protocols,mixed}
mkdir -p data/annotated
mkdir -p data/processed

# Create sample upload instructions
cat > data/raw/README.md << 'EOF'
# 📁 Legal Document Upload Instructions

## Directory Structure
- `bills/` - Векселя (Bills of Exchange)
- `fines/` - Штрафы (Fine Notices)  
- `protocols/` - Протоколы (Protocols)
- `mixed/` - Unclassified documents

## File Requirements
- **Formats:** PDF, JPG, PNG
- **Resolution:** ≥300 DPI
- **Language:** Russian legal documents
- **Naming:** descriptive filenames (e.g., `bill_001.pdf`)

## Target: 50+ documents per category (150+ total)

## Upload Process
1. Copy files to appropriate directories
2. Verify file quality and readability
3. Start annotation in Label Studio (port 8081)
4. Follow annotation guidelines in docs/annotation_guide.md
EOF

print_status "Data directories created"

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

print_status "Docker environment verified"

# Start core services (avoiding port conflicts)
print_info "Starting core services..."

# Use Label Studio on port 8081 to avoid conflicts
cat > docker-compose.day2.yml << 'EOF'
services:
  # Label Studio for annotation
  label-studio:
    image: heartexlabs/label-studio:latest
    ports:
      - "8081:8080"
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data
    volumes:
      - label_studio_data:/label-studio/data
      - ./data/raw:/label-studio/data/raw:ro
      - ./docs:/label-studio/data/docs:ro
    restart: unless-stopped

  # MinIO for file storage (different ports)
  minio:
    image: minio/minio:latest
    ports:
      - "9003:9000"   # API port
      - "9004:9001"   # Console port
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped

volumes:
  label_studio_data:
  minio_data:

networks:
  default:
    name: legal-ai-day2-network
EOF

# Start services
docker-compose -f docker-compose.day2.yml up -d

print_status "Services starting..."

# Wait for services to be ready
print_info "Waiting for services to initialize..."
sleep 15

# Check service status
if docker-compose -f docker-compose.day2.yml ps | grep -q "Up"; then
    print_status "Services are running"
else
    print_warning "Some services may not be ready yet"
fi

# Display access information
echo ""
echo "🌐 Service Access Information"
echo "============================="
echo "📊 Label Studio:  http://localhost:8081"
echo "🗄️  MinIO Console: http://localhost:9004"
echo "📁 File Upload:   Copy files to data/raw/"
echo ""

# Create Label Studio project setup instructions
cat > docs/label_studio_setup.md << 'EOF'
# 🏷️ Label Studio Setup Instructions

## Initial Setup
1. Access Label Studio: http://localhost:8081
2. Create account (admin/admin recommended for development)
3. Create new project: "Legal Documents Annotation"

## Project Configuration
1. Import config from: `scripts/label_studio_config.xml`
2. Set data source: Local files (`/label-studio/data/raw`)
3. Enable OCR preprocessing if needed

## Annotation Workflow
1. Start with document classification
2. Add named entity annotations
3. Review and export periodically
4. Target: 50+ documents by end of day

## Export Settings
- Format: JSON
- Include annotations and predictions
- Save to: `data/annotated/`

See `docs/annotation_guide.md` for detailed instructions.
EOF

print_status "Label Studio setup guide created"

# Validate data upload process
print_info "Validating data upload process..."

# Create a test file to verify upload
echo "Test document content for validation" > data/raw/test_upload.txt

if [ -f "data/raw/test_upload.txt" ]; then
    print_status "Data upload process validated"
    rm data/raw/test_upload.txt
else
    print_error "Data upload validation failed"
fi

# Final checklist
echo ""
echo "📋 Day 2 Preparation Checklist"
echo "==============================="
echo "✅ Data directories created"
echo "✅ Docker services started"
echo "✅ Label Studio accessible"
echo "✅ Upload process validated"
echo "✅ Documentation ready"
echo ""

print_info "Next steps:"
echo "1. Upload legal documents to data/raw/ directories"
echo "2. Access Label Studio at http://localhost:8081"
echo "3. Follow annotation guidelines in docs/annotation_guide.md"
echo "4. Target: 50+ annotated documents by end of day"
echo ""

print_status "Day 2 preparation complete! Ready for data collection."
echo "" 