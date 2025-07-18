#!/bin/bash
set -e

# Legal AI Stress Testing Suite
# Combines synthetic data generation v3 with comprehensive load testing

echo "🔥 Legal AI Stress Testing Suite"
echo "======================================="

# Configuration
SYNTHETIC_COUNT=${1:-40}
LOAD_USERS=${2:-20}
LOAD_DURATION=${3:-120s}
API_URL=${4:-http://localhost:8000}

echo "📊 Test Configuration:"
echo "  - Synthetic documents: $SYNTHETIC_COUNT"
echo "  - Concurrent users: $LOAD_USERS"
echo "  - Test duration: $LOAD_DURATION"
echo "  - API URL: $API_URL"
echo ""

# Step 1: Generate synthetic data v3
echo "🎭 Step 1: Generating Synthetic Dataset v3"
echo "-------------------------------------------"
echo "Generating $SYNTHETIC_COUNT documents with realistic noise..."

python3 scripts/gen_synthetic_v3.py \
    --count $SYNTHETIC_COUNT \
    --output-dir data/synthetic_v3 \
    --noise blur,perspective,noise,rotation,jpeg_compression \
    --doc-types bill_of_exchange,fine_notice,protocol

if [ $? -eq 0 ]; then
    echo "✅ Synthetic data generation completed"
else
    echo "❌ Synthetic data generation failed"
    exit 1
fi

echo ""

# Step 2: Check API availability
echo "🔗 Step 2: API Health Check"
echo "----------------------------"

# Wait for API to be ready
echo "Checking API availability..."
for i in {1..30}; do
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo "✅ API is ready at $API_URL"
        break
    else
        echo "⏳ Waiting for API... ($i/30)"
        sleep 2
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ API not available at $API_URL"
        echo "Please start the API first: cd api && python -m uvicorn main:app --reload"
        exit 1
    fi
done

echo ""

# Step 3: Single document test
echo "🧪 Step 3: Single Document Pipeline Test"
echo "----------------------------------------"

# Test with a synthetic v3 document
if [ -f "data/synthetic_v3/dirty_png/doc_000.png" ]; then
    echo "Testing OCR with synthetic v3 document..."
    
    # Convert image to base64 for testing
    python3 -c "
import base64
import json
import requests

# Read and encode image
with open('data/synthetic_v3/dirty_png/doc_000.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Test OCR
payload = {
    'image_base64': img_b64,
    'language': 'ru',
    'confidence_threshold': 0.7
}

try:
    response = requests.post('$API_URL/api/v1/ocr/extract', json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print('✅ OCR test successful')
            text = result.get('text', '')
            print(f'   Extracted {len(text)} characters')
            
            # Test classification
            classify_payload = {
                'text': text,
                'include_sections': True,
                'include_fields': True
            }
            
            classify_response = requests.post('$API_URL/api/v1/classify/document', json=classify_payload, timeout=15)
            if classify_response.status_code == 200:
                classify_result = classify_response.json()
                if classify_result.get('success'):
                    print(f'✅ Classification test successful: {classify_result.get(\"document_type\")}')
                else:
                    print('⚠️  Classification failed')
            else:
                print(f'⚠️  Classification failed: {classify_response.status_code}')
        else:
            print('❌ OCR test failed: no text extracted')
    else:
        print(f'❌ OCR test failed: {response.status_code}')
except Exception as e:
    print(f'❌ Single document test failed: {e}')
    "
else
    echo "⚠️  No synthetic v3 documents found, skipping single test"
fi

echo ""

# Step 4: Load testing with Locust
echo "🚀 Step 4: Load Testing with Locust"
echo "------------------------------------"

# Check if locust is available
if ! command -v locust &> /dev/null; then
    echo "⚠️  Locust not found in PATH, trying python -m locust"
    LOCUST_CMD="python3 -m locust"
else
    LOCUST_CMD="locust"
fi

echo "Starting load test with $LOAD_USERS concurrent users for $LOAD_DURATION..."
echo "Test scenarios:"
echo "  - Health checks (lightweight)"
echo "  - OCR processing (heavy)"
echo "  - Document classification"
echo "  - NER extraction"
echo "  - Full pipeline processing"

# Run Locust headless
$LOCUST_CMD -f tests/locust_load_test.py \
    --headless \
    --users $LOAD_USERS \
    --spawn-rate 2 \
    --run-time $LOAD_DURATION \
    --host $API_URL \
    --html reports/load_test_report.html \
    --csv reports/load_test

if [ $? -eq 0 ]; then
    echo "✅ Load testing completed"
else
    echo "❌ Load testing failed"
    exit 1
fi

echo ""

# Step 5: Generate performance report
echo "📊 Step 5: Performance Analysis"
echo "------------------------------"

# Create reports directory
mkdir -p reports

# Collect system metrics during test
echo "System Information:" > reports/system_metrics.txt
echo "==================" >> reports/system_metrics.txt
echo "Date: $(date)" >> reports/system_metrics.txt
echo "OS: $(uname -a)" >> reports/system_metrics.txt
echo "CPU cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu)" >> reports/system_metrics.txt
echo "Memory: $(free -h 2>/dev/null || echo 'N/A on macOS')" >> reports/system_metrics.txt
echo "" >> reports/system_metrics.txt

# Python environment info
echo "Python Environment:" >> reports/system_metrics.txt
echo "===================" >> reports/system_metrics.txt
python3 --version >> reports/system_metrics.txt
echo "Package versions:" >> reports/system_metrics.txt
pip list | grep -E "(fastapi|uvicorn|pillow|numpy|opencv)" >> reports/system_metrics.txt 2>/dev/null || echo "Package info not available" >> reports/system_metrics.txt

# Analyze synthetic data v3 quality
if [ -f "data/synthetic_v3/metadata_v3.json" ]; then
    echo "Synthetic Data v3 Analysis:" >> reports/system_metrics.txt
    echo "=============================" >> reports/system_metrics.txt
    python3 -c "
import json
with open('data/synthetic_v3/metadata_v3.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)

print(f'Generated documents: {metadata[\"document_count\"]}')
print(f'Generation time: {metadata[\"generation_time_seconds\"]:.2f}s')
print(f'Document types: {metadata[\"document_types\"]}')
print(f'Noise types: {metadata[\"noise_types\"]}')

# Calculate statistics
docs = metadata.get('documents', [])
if docs:
    char_counts = [doc['char_count'] for doc in docs]
    avg_chars = sum(char_counts) / len(char_counts)
    print(f'Average document length: {avg_chars:.0f} characters')
    
    type_dist = {}
    for doc in docs:
        doc_type = doc['document_type']
        type_dist[doc_type] = type_dist.get(doc_type, 0) + 1
    
    print('Document type distribution:')
    for doc_type, count in type_dist.items():
        print(f'  {doc_type}: {count}')
    " >> reports/system_metrics.txt
fi

# Display summary
echo ""
echo "✅ Stress Testing Complete!"
echo "=========================="
echo ""
echo "📁 Generated Files:"
echo "  - Synthetic Dataset v3: data/synthetic_v3/"
echo "  - Load Test Report: reports/load_test_report.html"
echo "  - CSV Data: reports/load_test_*.csv"
echo "  - System Metrics: reports/system_metrics.txt"
echo ""
echo "📊 Quick Results:"
if [ -f "reports/load_test_stats.csv" ]; then
    echo "Load Test Statistics:"
    head -n 5 reports/load_test_stats.csv
    echo ""
fi

echo "🔍 Analysis Commands:"
echo "  - View HTML report: open reports/load_test_report.html"
echo "  - Check system metrics: cat reports/system_metrics.txt"
echo "  - View CSV data: cat reports/load_test_stats.csv"

echo ""
echo "💡 Next Steps:"
echo "  1. Review performance bottlenecks in HTML report"
echo "  2. Adjust API optimization based on metrics"
echo "  3. Scale up testing if performance is satisfactory"
echo "  4. Deploy to GPU environment when ready"

echo ""
echo "🎯 Stress testing completed successfully!" 