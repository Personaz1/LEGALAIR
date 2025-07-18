# Scrapy settings for legal document crawlers
# ΔΣ::Cursor - Legal AI Platform

BOT_NAME = 'legal_crawlers'

SPIDER_MODULES = ['crawlers.spiders']
NEWSPIDER_MODULE = 'crawlers.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure a delay for requests (be respectful)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Reduce concurrent requests to be respectful to servers
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Disable cookies unless needed
COOKIES_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru,en',
    'User-Agent': 'Legal-AI-Crawler/1.0 (+https://legal-ai.com/bot)',
}

# Configure pipelines
ITEM_PIPELINES = {
    'crawlers.pipelines.ValidationPipeline': 100,
    'crawlers.pipelines.DuplicatesPipeline': 200,
    'crawlers.pipelines.PrivacyMaskingPipeline': 300,
    'crawlers.pipelines.FileDownloadPipeline': 400,
    'crawlers.pipelines.MetadataPipeline': 500,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'crawlers.middlewares.RetryMiddleware': 550,
    'crawlers.middlewares.UserAgentMiddleware': 400,
}

# File storage settings
FILES_STORE = 'data/crawl'
FILES_EXPIRES = 0  # Never expire downloaded files

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'data/crawl_cache'

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/crawler.log'

# Custom settings
LEGAL_CRAWL_BASE_DIR = 'data/crawl'
LEGAL_CRAWL_OCR_ENABLED = False
LEGAL_CRAWL_PRIVACY_MASKING = True

# Personal data patterns for masking
PERSONAL_DATA_PATTERNS = [
    r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+ич\b',  # Full Russian names
    r'\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+\b',  # Initials + surname
    r'\b\d{4}\s*\d{6}\b',  # Passport series + number
    r'\b\d{11}\b',  # SNILS
    r'\b\d{12}\b',  # INN individual
] 