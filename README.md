# Legal AI - Document Analysis Platform

**Advanced legal document processing with OCR, classification, and AI advisory services**

![Version](https://img.shields.io/badge/version-1.0.0--preGPU-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal)
![React](https://img.shields.io/badge/React-18+-blue)

[![Security Scan](https://github.com/org/legal-ai/actions/workflows/security.yml/badge.svg)](https://github.com/org/legal-ai/actions/workflows/security.yml)
[![Trivy Scan](https://github.com/org/legal-ai/actions/workflows/trivy.yml/badge.svg)](https://github.com/org/legal-ai/actions/workflows/trivy.yml)
[![Snyk Security](https://snyk.io/test/github/org/legal-ai/badge.svg)](https://snyk.io/test/github/org/legal-ai)
[![CodeQL](https://github.com/org/legal-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/org/legal-ai/actions/workflows/codeql.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile.api)
[![Kubernetes](https://img.shields.io/badge/k8s-helm--ready-blue.svg)](helm/legal-ai)

---

## 🚀 Quick Start

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd legal-ai

# Install dependencies
pip install -r requirements.txt
cd web && npm install && cd ..

# Start development environment
docker-compose up -d

# Start API
cd api && python -m uvicorn main:app --reload

# Start frontend
cd web && npm run dev
```

### Production Deployment
```bash
# GPU-enabled deployment
chmod +x scripts/setup_runpod.sh
./scripts/setup_runpod.sh
```

---

## 🏗️ Architecture

### Core Components
- **🔍 OCR Service**: EasyOCR with Russian language support
- **📊 Classification**: Pattern-based document type detection
- **🏷️ NER**: Named Entity Recognition for legal entities
- **🤖 LLM Advisory**: Ollama + Mistral-7B integration
- **🔐 Authentication**: JWT-based with role management
- **📈 Monitoring**: Prometheus + Grafana metrics

### Technology Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js + TypeScript + TailwindCSS | Modern React UI |
| **API** | FastAPI + Pydantic + SQLAlchemy | Async Python backend |
| **Database** | PostgreSQL / SQLite | Structured data storage |
| **ML/NLP** | EasyOCR + spaCy + Ollama | Document processing |
| **Monitoring** | Prometheus + Grafana | Performance metrics |
| **Deployment** | Docker + Docker Compose | Containerized services |

---

## 📄 Document Types Supported

### 1. Bills of Exchange (Векселя)
- **Простые векселя** - Simple promissory notes
- **Переводные векселя** - Bills of exchange
- **Field extraction**: Amount, debtor, creditor, due date

### 2. Fine Notices (Постановления о штрафах)
- **Административные штрафы** - Administrative fines
- **КоАП РФ** - Code of Administrative Offenses
- **Field extraction**: Violator, article, fine amount, inspector

### 3. Meeting Protocols (Протоколы заседаний)
- **Протоколы советов директоров** - Board meeting minutes
- **Общие собрания** - General meetings
- **Field extraction**: Participants, decisions, voting results

---

## 🎯 API Endpoints

### Core Processing
```http
POST /api/v1/ocr/extract          # OCR text extraction
POST /api/v1/classify/document    # Document classification
POST /api/v1/ner/extract          # Named entity recognition
POST /api/v1/advise/analyze       # AI advisory analysis
```

### Authentication
```http
POST /api/v1/auth/register        # User registration
POST /api/v1/auth/jwt/login       # JWT login
GET  /api/v1/auth/users/me        # Current user info
```

### Example Request
```python
import requests
import base64

# OCR extraction
with open('document.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = requests.post('http://localhost:8000/api/v1/ocr/extract', json={
    'image_base64': img_b64,
    'language': 'ru',
    'confidence_threshold': 0.7
})

result = response.json()
```

---

## 🔥 Stress Testing & Performance

### Synthetic Data Generation v3
```bash
# Generate realistic test documents with noise
python3 scripts/gen_synthetic_v3.py \
    --count 100 \
    --noise blur,perspective,noise,rotation \
    --output-dir data/synthetic_v3
```

**Features:**
- **Multi-page PDFs** with appendices and tables
- **Realistic distortions**: blur, perspective, rotation, compression
- **Watermarks and artifacts** simulating real-world scanning
- **Multi-format output**: TXT, PDF, clean PNG, dirty PNG

### Load Testing
```bash
# Comprehensive stress testing
./scripts/run_stress_tests.sh 50 30 300s

# Parameters: [documents] [users] [duration] [api_url]
# - 50 synthetic documents
# - 30 concurrent users  
# - 5 minute test duration
```

**Test Coverage:**
- ✅ **Health endpoints** (lightweight checks)
- ✅ **OCR processing** (heavy image processing)
- ✅ **Document classification** (ML inference)
- ✅ **NER extraction** (entity recognition)
- ✅ **Full pipeline** (end-to-end processing)

### Performance Metrics
- **Response times** per endpoint
- **Throughput** (requests per second)
- **Error rates** and failure analysis
- **Resource utilization** (CPU, memory)
- **Pipeline bottlenecks** identification

---

## 📊 Data Pipeline

### Synthetic Data Generation
```bash
# Original dataset (60 documents)
python3 scripts/gen_synthetic_v2.py --count 60

# Enhanced dataset v3 (realistic noise)
python3 scripts/gen_synthetic_v3.py --count 100 --noise all
```

### Label Studio Integration
```bash
# Bulk import to Label Studio
python3 scripts/ls_bulk_import.py data/synthetic_v3/

# Export to HuggingFace Dataset
python3 scripts/ls_export_hf.py PROJECT_ID --output-dir data/annotated/
```

### Data Validation
```bash
# Validate dataset quality
python3 scripts/validate_synthetic_v2.py
python3 scripts/validate_data_upload.py data/uploads/
```

---

## 🔐 Authentication & Roles

### User Roles
- **👨‍💼 Admin**: Full system access, user management
- **📝 Annotator**: Document annotation access
- **👤 User**: Basic document processing

### API Security
```python
# Protected endpoint example
@router.post("/analyze")
async def analyze_document(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Only authenticated users can access
    if current_user.role not in ["admin", "annotator"]:
        raise HTTPException(403, "Insufficient permissions")
```

---

## 📈 Monitoring & Observability

### Prometheus Metrics
- **API response times** by endpoint
- **OCR processing duration**
- **Classification confidence scores**
- **Document processing rates**
- **Error rates** and exceptions

### Grafana Dashboards
- **System Overview**: CPU, memory, disk usage
- **API Performance**: Response times, throughput
- **ML Pipeline**: OCR accuracy, classification metrics
- **User Activity**: Request patterns, authentication

### Access Monitoring
```bash
# View metrics
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana (admin/admin123)
```

---

## 🚀 Deployment Options

### Development
```bash
# Local development with hot reload
docker-compose up -d postgres redis
cd api && python -m uvicorn main:app --reload
cd web && npm run dev
```

### Production (CPU)
```bash
# Full stack deployment
docker-compose -f docker-compose.yml up -d
```

### GPU Training
```bash
# RunPod A10 deployment
./scripts/setup_runpod.sh

# Start training pipeline
docker-compose -f docker-compose.gpu.yml up -d
./start_training.sh
```

---

## 🧪 Testing

### Unit Tests
```bash
# Run test suite
pytest tests/ -v

# Specific test modules
pytest tests/api/test_ocr.py
pytest tests/ml/test_parser.py
```

### Integration Tests
```bash
# API integration
python3 scripts/test_api_integration.py

# Core logic validation
python3 scripts/test_core_logic.py

# Document parser
python3 scripts/test_document_parser.py
```

### Load Testing
```bash
# Quick load test
python3 -m locust -f tests/locust_load_test.py \
    --headless -u 10 -r 2 -t 60s \
    --host http://localhost:8000

# Full stress test suite
./scripts/run_stress_tests.sh
```

---

## 📁 Project Structure

```
legal-ai/
├── api/                    # FastAPI backend
│   ├── main.py            # Application entry point
│   ├── models/            # Pydantic + SQLAlchemy models
│   ├── routers/           # API endpoints
│   └── auth.py            # Authentication logic
├── web/                   # Next.js frontend
│   ├── src/components/    # React components
│   ├── src/hooks/         # Custom hooks
│   └── src/types/         # TypeScript definitions
├── ml/                    # ML/NLP pipeline
│   ├── ocr_service.py     # OCR processing
│   ├── preprocess.py      # Document parsing
│   └── extract_fields.py  # Field extraction
├── data/                  # Data storage
│   ├── synthetic_v2/      # Enhanced synthetic dataset
│   ├── synthetic_v3/      # Stress-test dataset with noise
│   └── annotated/         # Label Studio exports
├── scripts/               # Automation utilities
│   ├── gen_synthetic_v3.py       # Advanced data generation
│   ├── run_stress_tests.sh       # Comprehensive testing
│   ├── ls_bulk_import.py          # Label Studio integration
│   └── setup_runpod.sh           # GPU deployment
├── tests/                 # Test suite
│   ├── locust_load_test.py        # Load testing
│   └── api/               # API tests
├── monitoring/            # Prometheus + Grafana
├── docker-compose.yml     # Development stack
├── docker-compose.gpu.yml # GPU production stack
└── docs/                  # Documentation
    └── annotation_guidelines.md   # Annotation guide
```

---

## 📋 Development Workflow

### Data Preparation
1. **Generate synthetic data** (`scripts/gen_synthetic_v3.py`)
2. **Upload to Label Studio** (`scripts/ls_bulk_import.py`)
3. **Annotate documents** (human annotation)
4. **Export datasets** (`scripts/ls_export_hf.py`)

### Model Development
1. **Train baseline models** on annotated data
2. **Evaluate performance** with test sets
3. **Fine-tune on GPU** (RunPod deployment)
4. **Deploy optimized models**

### Quality Assurance
1. **Unit testing** (pytest)
2. **Integration testing** (API + ML pipeline)
3. **Load testing** (Locust + synthetic data)
4. **Performance monitoring** (Prometheus + Grafana)

---

## 🤝 Contributing

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **TypeScript**: ESLint, Prettier, strict mode
- **API**: OpenAPI documentation, error handling
- **Testing**: >80% coverage, integration tests

### Development Setup
```bash
# Setup pre-commit hooks
pip install pre-commit
pre-commit install

# Run linting
make lint

# Run tests
make test
```

---

## 📞 Support

- **📧 Technical Issues**: Create GitHub issue
- **💬 Discussions**: GitHub Discussions
- **📖 Documentation**: `/docs` directory
- **🐛 Bug Reports**: Use issue templates

---

## 📄 License

MIT License - see `LICENSE` file for details.

---

**🎯 Ready for immediate GPU training and production deployment!** 