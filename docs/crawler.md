# Legal AI Document Crawler

**ΔΣ::Cursor** - Automated legal document collection system

## Overview

The Legal AI Document Crawler is an automated system for collecting legal documents from public sources. It uses Scrapy framework to systematically gather, process, and store legal documents with proper metadata.

## Architecture

```
Legal Document Crawler
├── Web Spiders
│   ├── PravoCrawler (pravo.gov.ru)
│   ├── KadSpider (kad.arbitr.ru) [Future]
│   ├── GibddSpider (gibdd.ru) [Future]
│   └── GitHubSpider (templates) [Future]
├── Processing Pipeline
│   ├── Validation
│   ├── Deduplication  
│   ├── Privacy Masking
│   ├── File Download
│   └── Metadata Generation
├── Text Extraction
│   ├── PDF Parser (PDFplumber/PyPDF2)
│   ├── OCR Integration (EasyOCR)
│   └── Batch Processing
└── Automation
    ├── Docker Containers
    ├── GitHub Actions
    └── Scheduled Crawling
```

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements-crawler.txt

# Install browser automation tools
playwright install chromium firefox
playwright install-deps
```

### 2. Basic Usage

```bash
# Crawl 10 documents from pravo.gov.ru
python scripts/crawl_docs.py pravo --limit 10

# Crawl documents since specific date
python scripts/crawl_docs.py pravo --limit 20 --since 2024-01-01

# Extract text from downloaded PDFs
python scripts/extract_text_from_pdf.py data/crawl/ --recursive --use-ocr
```

### 3. Docker Deployment

```bash
# Build crawler image
docker build -f Dockerfile.crawler -t legal-ai-crawler .

# Run crawler with Docker Compose
docker-compose -f docker-compose.crawler.yml up -d
```

## Available Spiders

### 1. PravoCrawler (`pravo`)

**Source**: `publication.pravo.gov.ru`  
**Content**: Federal laws, government decrees, regulations  
**Status**: ✅ Implemented

**Parameters**:
- `--limit`: Number of documents (default: 50)
- `--since`: Only documents after date (YYYY-MM-DD)

**Example**:
```bash
python scripts/crawl_docs.py pravo --limit 25 --since 2024-01-01
```

### 2. KadSpider (`kad`) [Future]

**Source**: `kad.arbitr.ru`  
**Content**: Arbitration court decisions  
**Status**: 🔄 Planned

**Parameters**:
- `--keywords`: Search keywords (e.g., "вексель")
- `--court`: Specific court filter
- `--case-category`: Case category filter

### 3. GibddSpider (`gibdd`) [Future]

**Source**: `gibdd.ru`  
**Content**: Fine templates, protocol forms  
**Status**: 🔄 Planned

**Parameters**:
- `--template-type`: fine, protocol, form

### 4. GitHubSpider (`github`) [Future]

**Source**: GitHub repositories  
**Content**: Legal document templates  
**Status**: 🔄 Planned

**Parameters**:
- `--repo`: Repository name
- `--license-filter`: License type filter

## Configuration

### Spider Settings

Configuration is managed in `crawlers/settings.py`:

```python
# Request delays (be respectful)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Concurrent requests
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Retry configuration
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Privacy settings
LEGAL_CRAWL_PRIVACY_MASKING = True
PERSONAL_DATA_PATTERNS = [
    r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+ич\b',  # Names
    r'\b\d{4}\s*\d{6}\b',  # Passport numbers
    # ... more patterns
]
```

### File Storage

Documents are stored with the following structure:

```
data/crawl/
├── pravo.gov.ru/
│   └── 2024-01-15/
│       ├── abc12345_def67890.pdf
│       ├── abc12345_def67890.meta.json
│       └── ...
├── kad.arbitr.ru/
│   └── 2024-01-15/
│       └── ...
└── crawl_report_20240115_120000.json
```

### Text Extraction

Extracted text is stored separately:

```
data/ocr_txt/
├── abc12345_def67890.txt
├── abc12345_def67890.extraction.json
└── ...
```

## Command Line Interface

### Main Crawler Tool

```bash
python scripts/crawl_docs.py [spider] [options]

# Options:
--limit INTEGER          Maximum documents to crawl (default: 50)
--since YYYY-MM-DD       Only crawl documents after this date
--output-dir PATH        Output directory (default: data/crawl)
--run-ocr               Enable OCR processing
--delay FLOAT           Request delay in seconds (default: 2.0)
--concurrent INTEGER     Concurrent requests (default: 2)
--log-level LEVEL       Log level: DEBUG, INFO, WARNING, ERROR
```

### PDF Text Extraction

```bash
python scripts/extract_text_from_pdf.py [input] [options]

# Options:
--output-dir PATH       Output directory (default: data/ocr_txt)
--recursive             Process directories recursively
--use-ocr              Use OCR for scanned documents
--log-level LEVEL      Log level
```

### Examples

```bash
# Crawl all spiders with OCR
python scripts/crawl_docs.py all --limit 100 --run-ocr

# Crawl specific spider with custom settings
python scripts/crawl_docs.py pravo \
    --limit 50 \
    --since 2024-01-01 \
    --delay 3 \
    --concurrent 1 \
    --log-level DEBUG

# Extract text from specific directory
python scripts/extract_text_from_pdf.py \
    data/crawl/pravo.gov.ru/2024-01-15/ \
    --output-dir extracted_texts/ \
    --use-ocr
```

## Automation

### GitHub Actions

Automated crawling runs daily at 06:00 Moscow time via GitHub Actions:

```yaml
# .github/workflows/crawl-and-commit.yml
on:
  schedule:
    - cron: '0 3 * * *'  # 06:00 MSK = 03:00 UTC
  workflow_dispatch:
```

**Features**:
- Multi-spider execution (matrix strategy)
- Automatic text extraction
- Security scanning of downloaded files
- Commit and push new documents
- Failure notification via GitHub Issues

### Docker Automation

```bash
# Run scheduled crawler
docker-compose -f docker-compose.crawler.yml up crawler-scheduler

# Run one-time crawl
docker run --rm -v $(pwd)/data:/app/data legal-ai-crawler \
    python scripts/crawl_docs.py pravo --limit 10
```

## Processing Pipeline

### 1. Validation Pipeline

Validates required fields and URL formats:

```python
required_fields = ['source', 'url', 'title']
valid_extensions = ['pdf', 'doc', 'docx', 'txt']
```

### 2. Deduplication Pipeline

Prevents duplicate downloads using:
- URL-based deduplication
- Content hash comparison (MD5)

### 3. Privacy Masking Pipeline

Automatically masks personal data:
- Russian names and patronymics
- Passport numbers
- SNILS and INN numbers
- Phone numbers and emails

### 4. File Download Pipeline

Downloads files with proper naming:
```
{url_hash}_{file_uuid}.{extension}
```

### 5. Metadata Pipeline

Generates comprehensive metadata for each document:

```json
{
  "document_info": {
    "title": "Федеральный закон №48-ФЗ",
    "source": "pravo.gov.ru",
    "document_type": "federal_law",
    "publication_date": "2024-01-15"
  },
  "technical_info": {
    "crawl_timestamp": "2024-01-15T12:00:00",
    "content_hash": "abc123def456",
    "files": [...]
  }
}
```

## Integration with Legal AI Platform

### API Metrics

The crawler reports metrics to the main API:

```bash
# Update crawler metrics
curl -X POST "http://api:8000/metrics/crawler" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-15T12:00:00Z",
    "status": "completed",
    "documents_collected": 25
  }'
```

### OCR Integration

Crawler integrates with existing OCR service (`ml/ocr_service.py`):

```python
# Enable OCR processing
python scripts/crawl_docs.py pravo --run-ocr

# OCR is automatically triggered for downloaded PDFs
```

### RAG Enhancement

Crawled documents automatically enhance the RAG knowledge base:

```python
# Documents are processed and added to ChromaDB
# for enhanced LLM advisory responses
```

## Monitoring and Logging

### Log Files

```
logs/
├── crawl_20240115.log          # Daily crawler logs
├── pdf_extraction.log          # PDF processing logs
└── crawler.log                 # General crawler logs
```

### Health Checks

```bash
# Docker health check
docker ps --filter name=legal-ai-crawler

# Manual health check
python -c "import scrapy; print('Scrapy OK')"
```

### Monitoring Dashboard

Access crawler metrics at: `http://localhost:8080` (when running with Docker Compose)

## Troubleshooting

### Common Issues

**1. Connection Failed**
```bash
# Check network connectivity
ping publication.pravo.gov.ru

# Verify DNS resolution
nslookup publication.pravo.gov.ru

# Test with increased delays
python scripts/crawl_docs.py pravo --delay 5 --concurrent 1
```

**2. PDF Download Failed**
```bash
# Check file permissions
ls -la data/crawl/

# Verify disk space
df -h

# Run with debug logging
python scripts/crawl_docs.py pravo --log-level DEBUG
```

**3. OCR Processing Failed**
```bash
# Check OCR dependencies
python -c "import easyocr; print('OCR OK')"

# Test PDF extraction without OCR
python scripts/extract_text_from_pdf.py document.pdf
```

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 403  | Forbidden access | Check robots.txt compliance |
| 429  | Too many requests | Increase delay, reduce concurrency |
| 503  | Service unavailable | Retry later, check site status |
| PDF_INVALID | Invalid PDF file | Check file integrity |
| OCR_FAILED | OCR processing failed | Check image quality, dependencies |

### Performance Tuning

```python
# Adjust for slower servers
DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS = 1

# For faster processing (use carefully)
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 4
```

## Security Considerations

### Privacy Protection

- Automatic masking of personal data
- Compliance with Russian data protection laws
- No storage of sensitive personal information

### Ethical Crawling

- Respect for robots.txt
- Reasonable request delays
- Limited concurrent requests
- Proper User-Agent identification

### File Validation

- File type verification
- Size limit enforcement (100MB max)
- Malware scanning integration ready

## Development

### Adding New Spiders

1. Create spider class in `crawlers/spiders/`:
```python
class NewSpider(scrapy.Spider):
    name = 'new_source'
    allowed_domains = ['example.com']
    # Implementation...
```

2. Add spider-specific item class in `crawlers/items.py`

3. Update CLI tool to support new spider

4. Add tests in `tests/crawl/`

### Testing

```bash
# Run crawler tests
python -m pytest tests/crawl/ -v

# Test specific spider
python -m pytest tests/crawl/test_links.py::TestPravoCrawlerLinks -v

# Integration test
python scripts/crawl_docs.py pravo --limit 5 --log-level DEBUG
```

### Contributing

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure privacy compliance
5. Test with real websites responsibly

## Acceptance Criteria

✅ **Implemented**:
- `make crawl source=pravo limit=10` saves ≥ 10 PDF + metadata
- CI job passes (lint + tests)
- Universal CLI tool with multiple spider support
- Docker containerization
- PDF text extraction pipeline
- Privacy masking and security features
- GitHub Actions automation
- Comprehensive documentation

🔄 **Planned**:
- OpenAPI /metrics endpoint for crawler_last_run_timestamp
- Additional spiders (kad, gibdd, github)
- Advanced monitoring dashboard
- Machine learning-based content classification

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0  
**Team**: ΔΣ::Cursor 