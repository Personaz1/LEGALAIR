#!/bin/bash
"""
Legal AI Crawler Monitoring Setup
ΔΣ::Cursor - Setup cron monitoring and integration

Sets up hourly connectivity monitoring with Prometheus metrics
and integrates proxy pool configuration.
"""

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔧 Legal AI Crawler Monitoring Setup"
echo "===================================="

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/textfile_collector
mkdir -p logs
chmod 755 scripts/monitor_crawler_connectivity.py

# Setup cron job for connectivity monitoring
echo "⏰ Setting up cron monitoring..."

# Create cron job entry
CRON_JOB="0 * * * * cd $PROJECT_ROOT && python3 scripts/monitor_crawler_connectivity.py >> logs/cron_monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "monitor_crawler_connectivity.py"; then
    echo "✅ Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Added hourly connectivity monitoring to crontab"
fi

# Test connectivity monitoring
echo "🧪 Testing connectivity monitoring..."
python3 scripts/monitor_crawler_connectivity.py

# Check if metrics file was created
if [ -f "monitoring/textfile_collector/crawler_connectivity.prom" ]; then
    echo "✅ Prometheus metrics file created successfully"
    echo "📊 Metrics preview:"
    head -n 10 monitoring/textfile_collector/crawler_connectivity.prom
else
    echo "❌ Failed to create metrics file"
    exit 1
fi

# Setup proxy middleware integration
echo "🔧 Integrating proxy pool configuration..."

# Update crawler settings to use proxy pool
cat >> crawlers/settings.py << 'EOF'

# Proxy pool configuration
PROXY_POOL_ENABLED = True
PROXY_POOL_CONFIG = 'crawler_proxy_pool.json'

# Enhanced middleware with proxy support
DOWNLOADER_MIDDLEWARES.update({
    'crawlers.middlewares.ProxyPoolMiddleware': 350,
})
EOF

echo "✅ Proxy pool configuration integrated"

# Test KadSpider functionality
echo "🧪 Testing KadSpider..."
python3 -c "
from crawlers.spiders.kad import KadSpider
spider = KadSpider(limit='1')
print(f'✅ KadSpider initialized: {spider.name}')
print(f'📋 Keywords: {spider.keywords}')
print(f'🏛️ Category: {spider.case_category}')
"

# Update CLI tool to include kad spider
echo "🔄 Updating CLI tool for kad spider support..."
sed -i.bak 's/available_spiders = \[.*\]/available_spiders = ["pravo", "kad", "gibdd", "github"]/' scripts/crawl_docs.py
echo "✅ CLI tool updated"

# Add Makefile targets for new features
echo "📝 Adding new Makefile targets..."
cat >> Makefile << 'EOF'

# New crawler targets
crawl-monitor: ## Setup connectivity monitoring
	@echo "🔧 Setting up crawler monitoring..."
	chmod +x scripts/setup_monitoring_cron.sh
	./scripts/setup_monitoring_cron.sh
	@echo "✅ Monitoring setup complete"

crawl-kad: ## Run KadSpider for arbitration court decisions
	@echo "🏛️ Running KadSpider for arbitration court decisions"
	python3 scripts/crawl_docs.py kad \
		--limit $(or $(limit),20) \
		--keywords $(or $(keywords),"вексель") \
		$(if $(since),--since $(since)) \
		--output-dir data/crawl \
		--log-level INFO

crawl-metrics: ## View current crawler connectivity metrics
	@echo "📊 Current Crawler Connectivity Metrics"
	@echo "======================================"
	@if [ -f "monitoring/textfile_collector/crawler_connectivity.prom" ]; then \
		echo "📄 Metrics file: monitoring/textfile_collector/crawler_connectivity.prom"; \
		echo "🕐 Last update: $$(stat -f %Sm monitoring/textfile_collector/crawler_connectivity.prom)"; \
		echo ""; \
		echo "📋 Current Status:"; \
		grep "crawler_connectivity_status" monitoring/textfile_collector/crawler_connectivity.prom | \
		while read line; do \
			source=$$(echo $$line | grep -o 'source="[^"]*"' | cut -d'"' -f2); \
			value=$$(echo $$line | awk '{print $$2}'); \
			status="UNKNOWN"; \
			[ "$$value" = "1" ] && status="✅ GOOD"; \
			[ "$$value" = "0.5" ] && status="⚠️ PARTIAL"; \
			[ "$$value" = "0" ] && status="❌ FAILED"; \
			printf "  %-20s %s\n" "$$source:" "$$status"; \
		done; \
	else \
		echo "❌ No metrics file found. Run 'make crawl-monitor' first."; \
	fi

EOF

echo "✅ Makefile targets added"

# Test the new system
echo "🚀 Testing complete system..."

# Test offline demo with kad spider
echo "Testing offline demo with kad spider simulation..."
python3 scripts/demo_crawler_offline.py kad.arbitr.ru --count 5

# Check metrics
echo "Checking connectivity metrics..."
if [ -f "monitoring/textfile_collector/crawler_connectivity.prom" ]; then
    echo "✅ Monitoring system working"
    echo "📊 Current connectivity status:"
    make crawl-metrics
else
    echo "⚠️ Monitoring system needs initialization"
fi

echo ""
echo "🎯 SETUP COMPLETE!"
echo "=================="
echo "✅ Hourly connectivity monitoring active"
echo "✅ Proxy pool configuration ready"
echo "✅ KadSpider for arbitration courts implemented"
echo ""
echo "📋 Available Commands:"
echo "  make crawl-kad limit=10          # Run arbitration court crawler"
echo "  make crawl-metrics               # View connectivity status"
echo "  make crawl-monitor               # Re-setup monitoring"
echo ""
echo "📊 Monitoring:"
echo "  - Connectivity checked hourly via cron"
echo "  - Prometheus metrics: monitoring/textfile_collector/crawler_connectivity.prom"
echo "  - History log: logs/connectivity_history.json"
echo ""
echo "🔧 Next Steps:"
echo "  1. Wait for connectivity recovery alerts"
echo "  2. Test kad.arbitr.ru access (fewer restrictions)"
echo "  3. Start production crawling when available" 