# Legal ASI Development Makefile
# Version: 0.1.0-preGPU

.PHONY: help build up down logs clean test lint format init-data

# Default target
help:
	@echo "Legal ASI Development Commands"
	@echo "================================"
	@echo "build          Build all Docker images"
	@echo "up             Start all services"
	@echo "down           Stop all services"
	@echo "logs           Show service logs"
	@echo "clean          Clean up containers and volumes"
	@echo "test           Run test suite"
	@echo "lint           Run linting and formatting checks"
	@echo "format         Format code automatically"
	@echo "init-data      Initialize with sample data"
	@echo "shell          Open API container shell"
	@echo "db-shell       Open database shell"
	@echo "status         Show service status"

# Docker operations
build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting Legal ASI services..."
	docker-compose up -d
	@echo "Services started. Check status with 'make status'"
	@echo "API: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "Label Studio: http://localhost:8080"
	@echo "MinIO Console: http://localhost:9001"

down:
	@echo "Stopping services..."
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development tools
test:
	@echo "Running test suite..."
	docker-compose exec api pytest tests/ -v --tb=short

lint:
	@echo "Running linting checks..."
	docker-compose exec api flake8 api/ ml/ --max-line-length=88
	docker-compose exec api black --check api/ ml/
	docker-compose exec api isort --check-only api/ ml/

format:
	@echo "Formatting code..."
	docker-compose exec api black api/ ml/
	docker-compose exec api isort api/ ml/

# Data operations
init-data:
	@echo "Initializing sample data..."
	@mkdir -p data/raw data/annotated data/processed
	@echo "Sample data directories created"
	@echo "Upload sample documents to data/raw/ for testing"

# Shell access
shell:
	docker-compose exec api bash

db-shell:
	docker-compose exec db psql -U legal_user -d legal_ai

# Monitoring
status:
	@echo "Service Status:"
	@echo "==============="
	@docker-compose ps
	@echo
	@echo "Health Checks:"
	@echo "=============="
	@curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API not responding"
	@curl -s http://localhost:8000/api/v1/ocr/health | jq . 2>/dev/null || echo "OCR service not responding"

# GPU version (for future use)
up-gpu:
	@echo "Starting GPU-enabled services..."
	docker-compose -f docker-compose.gpu.yml up -d

# Backup operations
backup-db:
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U legal_user legal_ai > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T db psql -U legal_user legal_ai < $$backup_file

# Model operations
download-models:
	@echo "Downloading ML models..."
	docker-compose exec api python -m spacy download ru_core_news_sm

# Day-specific targets for sprint tracking
day1:
	@echo "Day 1 Tasks:"
	@echo "- [✓] Repository structure"
	@echo "- [✓] Docker compose setup"
	@echo "- [ ] Label Studio running"
	@echo "- [ ] API health checks"

day2:
	@echo "Day 2 Tasks:"
	@echo "- [ ] Upload 50+ scans"
	@echo "- [ ] Configure Label Studio"
	@echo "- [ ] Start annotations"

day3:
	@echo "Day 3 Tasks:"
	@echo "- [ ] OCR service implementation"
	@echo "- [ ] API tests"

day4:
	@echo "Day 4 Tasks:"
	@echo "- [ ] ruBERT integration"
	@echo "- [ ] Classification API"

day5:
	@echo "Day 5 Tasks:"
	@echo "- [ ] Frontend implementation"
	@echo "- [ ] E2E testing"

# Quick development reset
reset:
	@echo "Resetting development environment..."
	make down
	make clean
	make build
	make up
	@echo "Environment reset complete!" 

# Crawler targets
.PHONY: crawl crawl-setup crawl-test crawl-build crawl-deploy

crawl: ## Run document crawler
	@echo "🕷️ Running Legal AI Document Crawler"
	@if [ -z "$(source)" ]; then \
		echo "Usage: make crawl source=<spider> [limit=<num>] [since=<date>]"; \
		echo "Available spiders: pravo, kad, gibdd, github, all"; \
		exit 1; \
	fi
	@mkdir -p data/crawl logs
	python scripts/crawl_docs.py $(source) \
		--limit $(or $(limit),10) \
		$(if $(since),--since $(since)) \
		--output-dir data/crawl \
		--log-level INFO

crawl-setup: ## Install crawler dependencies
	@echo "🔧 Setting up crawler environment"
	pip install -r requirements-crawler.txt
	playwright install chromium firefox
	playwright install-deps
	@echo "✅ Crawler setup complete"

crawl-test: ## Run crawler tests
	@echo "🧪 Testing crawler functionality"
	python -m pytest tests/crawl/ -v --tb=short
	@echo "✅ Crawler tests complete"

crawl-build: ## Build crawler Docker image
	@echo "🐳 Building crawler Docker image"
	docker build -f Dockerfile.crawler -t legal-ai-crawler .
	@echo "✅ Crawler image built: legal-ai-crawler"

crawl-deploy: crawl-build ## Deploy crawler with Docker Compose
	@echo "🚀 Deploying crawler services"
	docker-compose -f docker-compose.crawler.yml up -d
	@echo "✅ Crawler deployed: http://localhost:8080"

crawl-extract: ## Extract text from crawled PDFs
	@echo "📄 Extracting text from PDFs"
	@if [ ! -d "data/crawl" ]; then \
		echo "❌ No crawled data found. Run 'make crawl' first"; \
		exit 1; \
	fi
	python scripts/extract_text_from_pdf.py data/crawl \
		--output-dir data/ocr_txt \
		--recursive \
		--log-level INFO
	@echo "✅ Text extraction complete"

crawl-status: ## Check crawler status and statistics
	@echo "📊 Legal AI Crawler Status"
	@echo "=================================="
	@if [ -d "data/crawl" ]; then \
		echo "📄 PDF files: $$(find data/crawl -name '*.pdf' | wc -l)"; \
		echo "📋 Metadata files: $$(find data/crawl -name '*.meta.json' | wc -l)"; \
		echo "💾 Total size: $$(du -sh data/crawl 2>/dev/null | cut -f1 || echo '0B')"; \
	else \
		echo "📁 No crawled data found"; \
	fi
	@if [ -d "data/ocr_txt" ]; then \
		echo "📝 Extracted texts: $$(find data/ocr_txt -name '*.txt' | wc -l)"; \
	else \
		echo "📝 No extracted texts found"; \
	fi
	@echo "=================================="
	@if docker ps --filter name=legal-ai-crawler --format "table {{.Names}}\t{{.Status}}" | grep -q crawler; then \
		echo "🐳 Docker Status:"; \
		docker ps --filter name=legal-ai-crawler --format "table {{.Names}}\t{{.Status}}"; \
	else \
		echo "🐳 Docker: Not running"; \
	fi

crawl-logs: ## View crawler logs
	@echo "📋 Recent crawler logs:"
	@if [ -f "logs/crawler.log" ]; then \
		tail -n 50 logs/crawler.log; \
	elif [ -f "logs/crawl_$$(date +%Y%m%d).log" ]; then \
		tail -n 50 logs/crawl_$$(date +%Y%m%d).log; \
	else \
		echo "No crawler logs found"; \
	fi

crawl-clean: ## Clean crawler data and logs
	@echo "🧹 Cleaning crawler data"
	@read -p "Delete all crawled data and logs? [y/N] " confirm && [ "$$confirm" = "y" ]
	rm -rf data/crawl/*
	rm -rf data/ocr_txt/*
	rm -rf logs/crawl_*.log
	rm -rf logs/pdf_extraction.log
	@echo "✅ Crawler data cleaned"

# Update help target to include crawler commands
help: ## Show this help
	@echo "Legal AI Platform Commands"
	@echo "=========================="
	@echo "Core Platform:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -v crawl
	@echo ""
	@echo "Document Crawler:"
	@awk 'BEGIN {FS = ":.*?## "} /^crawl.*:.*?## / {printf "\033[33m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make crawl source=pravo limit=10"
	@echo "  make crawl source=all limit=50 since=2024-01-01"
	@echo "  make crawl-extract"
	@echo "  make crawl-status" 