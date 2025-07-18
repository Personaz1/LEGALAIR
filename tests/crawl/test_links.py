#!/usr/bin/env python3
"""
Legal AI Crawler Tests
ΔΣ::Cursor - Test crawler link extraction and validation

Tests ensure crawlers can parse ≥ 5 URLs from target sources
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from scrapy.http import HtmlResponse, Request

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawlers.spiders.pravo import PravoSpider
from crawlers.items import PravoDocumentItem


class TestPravoCrawlerLinks:
    """Test PravoCrawler link extraction functionality"""
    
    @pytest.fixture
    def pravo_spider(self):
        """Create PravoCrawler instance for testing"""
        return PravoSpider(limit="10")
    
    @pytest.fixture
    def mock_pravo_html(self):
        """Mock HTML response from pravo.gov.ru"""
        return """
        <html>
        <body>
            <div class="document-item">
                <a href="/document/123456">Федеральный закон от 01.01.2024</a>
                <span class="date">01.01.2024</span>
                <span class="type">Федеральный закон</span>
            </div>
            <div class="document-item">
                <a href="/document/123457">Постановление Правительства от 02.01.2024</a>
                <span class="date">02.01.2024</span>
                <span class="type">Постановление</span>
            </div>
            <div class="document-item">
                <a href="/document/123458">Приказ Минфина от 03.01.2024</a>
                <span class="date">03.01.2024</span>
                <span class="type">Приказ</span>
            </div>
            <div class="document-item">
                <a href="/document/123459">Распоряжение от 04.01.2024</a>
                <span class="date">04.01.2024</span>
                <span class="type">Распоряжение</span>
            </div>
            <div class="document-item">
                <a href="/document/123460">Инструкция от 05.01.2024</a>
                <span class="date">05.01.2024</span>
                <span class="type">Инструкция</span>
            </div>
            <div class="document-item">
                <a href="/document/123461">Методические рекомендации от 06.01.2024</a>
                <span class="date">06.01.2024</span>
                <span class="type">Методические рекомендации</span>
            </div>
            <a class="next" href="/page/2">Следующая страница</a>
        </body>
        </html>
        """
    
    @pytest.fixture
    def mock_document_html(self):
        """Mock HTML response for individual document page"""
        return """
        <html>
        <body>
            <h1 class="document-title">Федеральный закон "О векселях"</h1>
            <div class="document-info">
                <span class="publication-date">01.01.2024</span>
                <span class="registration-number">№ 48-ФЗ</span>
                <span class="authority">Государственная Дума</span>
            </div>
            <div class="download-links">
                <a href="/download/123456.pdf" class="pdf-download">Скачать PDF</a>
                <a href="/download/123456.doc">Скачать DOC</a>
            </div>
        </body>
        </html>
        """
    
    def create_response(self, url: str, html: str) -> HtmlResponse:
        """Create mock HTTP response"""
        request = Request(url=url)
        return HtmlResponse(
            url=url,
            request=request,
            body=html.encode('utf-8'),
            encoding='utf-8'
        )
    
    def test_extract_document_links_minimum_count(self, pravo_spider, mock_pravo_html):
        """Test that crawler extracts ≥ 5 document URLs"""
        response = self.create_response(
            'https://publication.pravo.gov.ru/documents',
            mock_pravo_html
        )
        
        # Extract document links
        links = list(pravo_spider._extract_document_links(response))
        
        # Verify minimum count requirement
        assert len(links) >= 5, f"Expected ≥ 5 links, got {len(links)}"
        
        # Verify link structure
        for link in links:
            assert 'url' in link
            assert 'title' in link
            assert link['url'].startswith('https://publication.pravo.gov.ru/')
    
    def test_extract_link_data_validity(self, pravo_spider, mock_pravo_html):
        """Test that extracted links contain valid data"""
        response = self.create_response(
            'https://publication.pravo.gov.ru/documents',
            mock_pravo_html
        )
        
        links = list(pravo_spider._extract_document_links(response))
        
        for link in links:
            # Check URL validity
            assert link['url'], "URL should not be empty"
            assert link['url'].startswith('http'), "URL should be absolute"
            
            # Check title validity
            assert link['title'], "Title should not be empty"
            assert len(link['title']) > 5, "Title should be meaningful"
            
            # Check optional fields
            if link.get('date'):
                assert len(link['date']) >= 8, "Date should be in valid format"
    
    def test_parse_document_pdf_extraction(self, pravo_spider, mock_document_html):
        """Test PDF URL extraction from document pages"""
        response = self.create_response(
            'https://publication.pravo.gov.ru/document/123456',
            mock_document_html
        )
        
        # Extract PDF URLs
        pdf_urls = pravo_spider._extract_pdf_urls(response)
        
        # Verify PDF extraction
        assert len(pdf_urls) >= 1, "Should extract at least one PDF URL"
        
        for url in pdf_urls:
            assert url.endswith('.pdf'), f"URL should be PDF: {url}"
            assert url.startswith('https://publication.pravo.gov.ru/'), "PDF URL should be absolute"
    
    def test_pagination_extraction(self, pravo_spider, mock_pravo_html):
        """Test pagination link extraction"""
        response = self.create_response(
            'https://publication.pravo.gov.ru/documents',
            mock_pravo_html
        )
        
        # Extract next page URL
        next_url = pravo_spider._extract_next_page(response)
        
        # Verify pagination
        assert next_url is not None, "Should extract next page URL"
        assert next_url.startswith('https://publication.pravo.gov.ru/'), "Next page URL should be absolute"
        assert '/page/2' in next_url, "Should point to next page"
    
    def test_date_normalization(self, pravo_spider):
        """Test date string normalization"""
        test_cases = [
            ('01.01.2024', '2024-01-01'),
            ('1.1.2024', '2024-01-01'),
            ('31.12.2023', '2023-12-31'),
            ('invalid-date', None),
            ('', None),
        ]
        
        for input_date, expected in test_cases:
            result = pravo_spider._normalize_date(input_date)
            assert result == expected, f"Date {input_date} should normalize to {expected}, got {result}"
    
    def test_document_id_extraction(self, pravo_spider):
        """Test document ID extraction from URLs"""
        test_urls = [
            'https://publication.pravo.gov.ru/document/123456',
            'https://publication.pravo.gov.ru/Document/654321/Info',
            'https://publication.pravo.gov.ru/invalid-url',
        ]
        
        expected_ids = ['123456', '654321', None]
        
        for url, expected_id in zip(test_urls, expected_ids):
            response = self.create_response(url, '<html></html>')
            doc_id = pravo_spider._extract_document_id(response)
            
            if expected_id:
                assert doc_id == expected_id, f"Should extract ID {expected_id} from {url}"
    
    def test_spider_initialization(self):
        """Test spider initialization with parameters"""
        # Test with limit
        spider1 = PravoSpider(limit="25")
        assert spider1.limit == 25
        
        # Test with since date
        spider2 = PravoSpider(since="2024-01-01")
        assert spider2.since_date is not None
        
        # Test with invalid date
        spider3 = PravoSpider(since="invalid-date")
        assert spider3.since_date is None
    
    @patch('crawlers.spiders.pravo.PravoSpider._extract_pdf_urls')
    def test_parse_document_item_creation(self, mock_pdf_extract, pravo_spider, mock_document_html):
        """Test document item creation during parsing"""
        # Mock PDF extraction
        mock_pdf_extract.return_value = ['https://publication.pravo.gov.ru/download/123456.pdf']
        
        response = self.create_response(
            'https://publication.pravo.gov.ru/document/123456',
            mock_document_html
        )
        response.meta = {
            'source_type': 'federal_law',
            'preview_data': {'title': 'Test Document'}
        }
        
        # Parse document
        items = list(pravo_spider.parse_document(response))
        
        # Verify item creation
        assert len(items) == 1
        item = items[0]
        
        assert isinstance(item, PravoDocumentItem)
        assert item['source'] == 'pravo.gov.ru'
        assert item['url'] == response.url
        assert item['document_type'] == 'federal_law'
        assert item['file_urls'] == ['https://publication.pravo.gov.ru/download/123456.pdf']


class TestCrawlerConnectivity:
    """Test crawler network connectivity and error handling"""
    
    def test_connection_timeout_handling(self):
        """Test handling of connection timeouts"""
        spider = PravoSpider(limit="5")
        
        # Verify spider can handle connection errors gracefully
        assert spider.custom_settings['DOWNLOAD_DELAY'] >= 2
        assert spider.custom_settings['CONCURRENT_REQUESTS_PER_DOMAIN'] <= 1
    
    def test_user_agent_configuration(self):
        """Test user agent configuration for stealth"""
        from crawlers.middlewares import UserAgentMiddleware
        from scrapy.settings import Settings
        
        settings = Settings()
        middleware = UserAgentMiddleware(settings)
        
        # Verify user agents are configured
        assert len(middleware.user_agents) > 0
        assert any('Legal-AI-Crawler' in ua for ua in middleware.user_agents)
    
    def test_robots_txt_compliance(self):
        """Test robots.txt compliance settings"""
        from crawlers.settings import ROBOTSTXT_OBEY
        
        # Verify robots.txt compliance is enabled
        assert ROBOTSTXT_OBEY is True
    
    def test_retry_mechanism(self):
        """Test retry settings for failed connections"""
        from crawlers.settings import RETRY_TIMES, RETRY_HTTP_CODES
        
        # Verify retry configuration
        assert RETRY_TIMES >= 3
        assert 503 in RETRY_HTTP_CODES  # Service unavailable
        assert 429 in RETRY_HTTP_CODES  # Too many requests


class TestCrawlerValidation:
    """Test crawler validation and acceptance criteria"""
    
    def test_acceptance_criteria_minimum_urls(self, mock_pravo_html):
        """Acceptance test: parse ≥ 5 URLs from pravo.gov.ru"""
        spider = PravoSpider(limit="10")
        
        response = HtmlResponse(
            url='https://publication.pravo.gov.ru/documents',
            body=mock_pravo_html.encode('utf-8'),
            encoding='utf-8'
        )
        
        # Extract links
        links = list(spider._extract_document_links(response))
        
        # ACCEPTANCE CRITERIA: ≥ 5 URLs
        assert len(links) >= 5, f"FAILED: Expected ≥ 5 URLs, got {len(links)}"
        
        print(f"✅ PASSED: Extracted {len(links)} URLs (≥ 5 required)")
        
        # Verify URL validity
        valid_urls = [link for link in links if link.get('url') and link['url'].startswith('http')]
        assert len(valid_urls) >= 5, f"FAILED: Expected ≥ 5 valid URLs, got {len(valid_urls)}"
        
        print(f"✅ PASSED: {len(valid_urls)} valid URLs extracted")
    
    def test_spider_configuration_completeness(self):
        """Test that spider configuration is complete"""
        spider = PravoSpider()
        
        # Required attributes
        assert hasattr(spider, 'name')
        assert hasattr(spider, 'allowed_domains')
        assert hasattr(spider, 'start_urls')
        
        # Spider configuration
        assert spider.name == 'pravo'
        assert len(spider.start_urls) > 0
        assert len(spider.allowed_domains) > 0
        
        print("✅ PASSED: Spider configuration complete")
    
    def test_integration_readiness(self):
        """Test integration readiness checklist"""
        checks = {
            "Spider class exists": PravoSpider is not None,
            "Item class exists": PravoDocumentItem is not None,
            "CLI tool exists": Path("scripts/crawl_docs.py").exists(),
            "Docker file exists": Path("Dockerfile.crawler").exists(),
            "Requirements file exists": Path("requirements-crawler.txt").exists(),
        }
        
        for check_name, result in checks.items():
            assert result, f"FAILED: {check_name}"
            print(f"✅ PASSED: {check_name}")
        
        print("✅ PASSED: All integration readiness checks")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short']) 