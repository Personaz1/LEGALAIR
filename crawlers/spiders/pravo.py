import scrapy
import re
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import Iterator, Optional

from ..items import PravoDocumentItem


class PravoSpider(scrapy.Spider):
    """
    PravoCrawler - Spider for collecting legal documents from pravo.gov.ru
    
    Collects federal laws, regulations, and normative acts from the official
    Russian legal publication portal.
    """
    
    name = 'pravo'
    allowed_domains = ['pravo.gov.ru', 'publication.pravo.gov.ru']
    
    # Base URLs for different content types
    start_urls = [
        'https://publication.pravo.gov.ru/documents',  # Main documents feed
        'https://publication.pravo.gov.ru/SignatoryAuthority/fz',  # Federal laws
        'https://publication.pravo.gov.ru/SignatoryAuthority/government',  # Government docs
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    }
    
    def __init__(self, limit: Optional[str] = None, since: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Parse command line arguments
        self.limit = int(limit) if limit else 50
        self.since_date = self._parse_date(since) if since else None
        self.documents_collected = 0
        
        self.logger.info(f"PravoCrawler initialized: limit={self.limit}, since={since}")
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            self.logger.error(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
            return None
    
    def start_requests(self):
        """Generate initial requests with custom headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
        }
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={'source_type': self._get_source_type(url)}
            )
    
    def _get_source_type(self, url: str) -> str:
        """Determine document source type from URL"""
        if '/fz' in url:
            return 'federal_law'
        elif '/government' in url:
            return 'government_decree'
        else:
            return 'general_document'
    
    def parse(self, response):
        """Parse main document listing pages"""
        source_type = response.meta.get('source_type', 'general_document')
        
        # Extract document links from the page
        document_links = self._extract_document_links(response)
        
        for link_data in document_links:
            if self.documents_collected >= self.limit:
                self.logger.info(f"Reached limit of {self.limit} documents")
                return
            
            # Check date filter
            if self.since_date and link_data.get('date'):
                doc_date = self._parse_date(link_data['date'])
                if doc_date and doc_date < self.since_date:
                    continue
            
            # Create request for document detail page
            yield scrapy.Request(
                url=link_data['url'],
                callback=self.parse_document,
                meta={
                    'source_type': source_type,
                    'preview_data': link_data
                }
            )
        
        # Follow pagination links
        next_page = self._extract_next_page(response)
        if next_page and self.documents_collected < self.limit:
            yield scrapy.Request(
                url=next_page,
                callback=self.parse,
                meta={'source_type': source_type}
            )
    
    def _extract_document_links(self, response) -> Iterator[dict]:
        """Extract document links from listing page"""
        # Look for document containers
        document_selectors = [
            '.document-item',
            '.doc-item',
            '.publication-item',
            'article.document',
            '.search-result-item'
        ]
        
        for selector in document_selectors:
            documents = response.css(selector)
            if documents:
                break
        
        if not documents:
            # Fallback: look for any links that might be documents
            documents = response.css('a[href*="document"]')
        
        for doc in documents:
            link_data = self._extract_link_data(doc, response)
            if link_data:
                yield link_data
    
    def _extract_link_data(self, element, response) -> Optional[dict]:
        """Extract basic data from document link element"""
        try:
            # Try to find the main link
            link = element.css('a::attr(href)').get()
            if not link:
                link = element.attrib.get('href')
            
            if not link:
                return None
            
            # Make absolute URL
            url = urljoin(response.url, link)
            
            # Extract title
            title = (
                element.css('a::text').get() or
                element.css('.title::text').get() or
                element.css('.doc-title::text').get() or
                element.css('::text').get()
            )
            
            if title:
                title = title.strip()
            
            # Try to extract date
            date_text = (
                element.css('.date::text').get() or
                element.css('.publication-date::text').get() or
                element.css('[class*="date"]::text').get()
            )
            
            # Extract document type/category
            doc_type = (
                element.css('.type::text').get() or
                element.css('.category::text').get() or
                element.css('[class*="type"]::text').get()
            )
            
            return {
                'url': url,
                'title': title,
                'date': date_text,
                'type': doc_type,
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting link data: {e}")
            return None
    
    def _extract_next_page(self, response) -> Optional[str]:
        """Extract next page URL from pagination"""
        next_selectors = [
            'a.next::attr(href)',
            'a[rel="next"]::attr(href)',
            '.pagination a.next::attr(href)',
            '.pager a.next::attr(href)',
            'a:contains("Следующая")::attr(href)',
            'a:contains("далее")::attr(href)',
        ]
        
        for selector in next_selectors:
            next_url = response.css(selector).get()
            if next_url:
                return urljoin(response.url, next_url)
        
        return None
    
    def parse_document(self, response):
        """Parse individual document page"""
        preview_data = response.meta.get('preview_data', {})
        source_type = response.meta.get('source_type', 'general_document')
        
        # Extract detailed document information
        item = PravoDocumentItem()
        
        # Basic fields
        item['source'] = 'pravo.gov.ru'
        item['url'] = response.url
        item['crawl_timestamp'] = datetime.now().isoformat()
        item['document_type'] = source_type
        item['language'] = 'ru'
        
        # Title
        item['title'] = self._extract_title(response, preview_data)
        
        # Document ID
        item['document_id'] = self._extract_document_id(response)
        
        # Dates
        item['publication_date'] = self._extract_publication_date(response)
        item['effective_date'] = self._extract_effective_date(response)
        
        # Organization/Authority
        item['author_organization'] = self._extract_authority(response)
        
        # Pravo.gov.ru specific fields
        item['registration_number'] = self._extract_registration_number(response)
        item['bulletin_number'] = self._extract_bulletin_number(response)
        item['document_status'] = self._extract_status(response)
        
        # Find PDF download links
        pdf_urls = self._extract_pdf_urls(response)
        if pdf_urls:
            item['file_urls'] = pdf_urls
            
            # Increment counter only when we have actual downloadable content
            self.documents_collected += 1
            
            self.logger.info(f"Found document {self.documents_collected}/{self.limit}: {item.get('title', 'Unknown')}")
            
            yield item
        else:
            self.logger.warning(f"No PDF found for document: {response.url}")
    
    def _extract_title(self, response, preview_data: dict) -> str:
        """Extract document title"""
        title_selectors = [
            'h1.document-title::text',
            'h1.title::text', 
            '.doc-header h1::text',
            '.document-info h1::text',
            'h1::text',
            '.main-title::text',
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        
        # Fallback to preview data
        return preview_data.get('title', 'Unknown Document')
    
    def _extract_document_id(self, response) -> Optional[str]:
        """Extract unique document identifier"""
        # Look in URL
        url_match = re.search(r'/document/(\d+)', response.url)
        if url_match:
            return url_match.group(1)
        
        # Look in page content
        id_selectors = [
            '[data-document-id]::attr(data-document-id)',
            '.document-id::text',
            '.doc-number::text',
        ]
        
        for selector in id_selectors:
            doc_id = response.css(selector).get()
            if doc_id:
                return doc_id.strip()
        
        return None
    
    def _extract_publication_date(self, response) -> Optional[str]:
        """Extract publication date"""
        date_selectors = [
            '.publication-date::text',
            '.pub-date::text',
            '.date-published::text',
            '[class*="date"]::text',
        ]
        
        for selector in date_selectors:
            date_text = response.css(selector).get()
            if date_text:
                # Try to normalize date format
                normalized_date = self._normalize_date(date_text)
                if normalized_date:
                    return normalized_date
        
        return None
    
    def _extract_effective_date(self, response) -> Optional[str]:
        """Extract effective date"""
        effective_selectors = [
            '.effective-date::text',
            '.date-effective::text',
            '.entry-into-force::text',
        ]
        
        for selector in effective_selectors:
            date_text = response.css(selector).get()
            if date_text:
                normalized_date = self._normalize_date(date_text)
                if normalized_date:
                    return normalized_date
        
        return None
    
    def _extract_authority(self, response) -> Optional[str]:
        """Extract adopting authority/organization"""
        authority_selectors = [
            '.authority::text',
            '.adopting-authority::text',
            '.organization::text',
            '.issuer::text',
        ]
        
        for selector in authority_selectors:
            authority = response.css(selector).get()
            if authority:
                return authority.strip()
        
        return None
    
    def _extract_registration_number(self, response) -> Optional[str]:
        """Extract registration number"""
        reg_selectors = [
            '.registration-number::text',
            '.reg-number::text',
            '.document-number::text',
        ]
        
        for selector in reg_selectors:
            reg_num = response.css(selector).get()
            if reg_num:
                return reg_num.strip()
        
        return None
    
    def _extract_bulletin_number(self, response) -> Optional[str]:
        """Extract bulletin number"""
        bulletin_selectors = [
            '.bulletin-number::text',
            '.issue-number::text',
        ]
        
        for selector in bulletin_selectors:
            bulletin = response.css(selector).get()
            if bulletin:
                return bulletin.strip()
        
        return None
    
    def _extract_status(self, response) -> Optional[str]:
        """Extract document status"""
        status_selectors = [
            '.document-status::text',
            '.status::text',
            '.doc-status::text',
        ]
        
        for selector in status_selectors:
            status = response.css(selector).get()
            if status:
                return status.strip()
        
        return None
    
    def _extract_pdf_urls(self, response) -> list:
        """Extract PDF download URLs"""
        pdf_urls = []
        
        # Look for direct PDF links
        pdf_selectors = [
            'a[href$=".pdf"]::attr(href)',
            'a[href*=".pdf"]::attr(href)',
            '.download-pdf::attr(href)',
            '.pdf-download::attr(href)',
            'a:contains("PDF")::attr(href)',
            'a:contains("Скачать")::attr(href)',
        ]
        
        for selector in pdf_selectors:
            links = response.css(selector).getall()
            for link in links:
                if link:
                    full_url = urljoin(response.url, link)
                    if full_url not in pdf_urls:
                        pdf_urls.append(full_url)
        
        return pdf_urls
    
    def _normalize_date(self, date_text: str) -> Optional[str]:
        """Normalize date text to ISO format"""
        if not date_text:
            return None
        
        # Clean up the text
        date_text = re.sub(r'[^\d\.\-\s]', '', date_text.strip())
        
        # Common Russian date patterns
        patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',   # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',   # DD/MM/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '.' in date_text or '/' in date_text:
                        # DD.MM.YYYY or DD/MM/YYYY format
                        day, month, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        # YYYY-MM-DD format
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        
        return None 