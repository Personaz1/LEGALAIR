import scrapy
import re
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, quote
from typing import Iterator, Optional

from ..items import ArbitrageDocumentItem


class KadSpider(scrapy.Spider):
    """
    KadSpider - Spider for collecting arbitration court decisions from kad.arbitr.ru
    
    Focuses on bill of exchange (вексель) cases and other commercial disputes.
    Uses search interface to filter relevant cases.
    """
    
    name = 'kad'
    allowed_domains = ['kad.arbitr.ru']
    
    # Base URLs for search and document access
    base_url = 'https://kad.arbitr.ru'
    search_url = 'https://kad.arbitr.ru/Kad/SearchInstances'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # More respectful for court system
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'COOKIES_ENABLED': True,  # Needed for session management
    }
    
    def __init__(self, 
                 limit: Optional[str] = None, 
                 since: Optional[str] = None,
                 keywords: Optional[str] = None,
                 court: Optional[str] = None,
                 case_category: Optional[str] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Parse command line arguments
        self.limit = int(limit) if limit else 50
        self.since_date = self._parse_date(since) if since else None
        self.keywords = keywords or "вексель"  # Default to bill of exchange cases
        self.court = court  # Specific court filter
        self.case_category = case_category or "Экономические споры"
        self.documents_collected = 0
        
        self.logger.info(f"KadSpider initialized: limit={self.limit}, keywords='{self.keywords}'")
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            self.logger.error(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
            return None
    
    def start_requests(self):
        """Generate initial search request"""
        
        # Prepare search parameters
        search_params = self._build_search_params()
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # First, get the search form to extract any required tokens
        yield scrapy.Request(
            url=self.base_url,
            headers=headers,
            callback=self.parse_search_form,
            meta={'search_params': search_params}
        )
    
    def _build_search_params(self) -> dict:
        """Build search parameters for court case search"""
        
        params = {
            'page': 1,
            'count': 25,  # Results per page
            'searchText': self.keywords,
            'caseCategory': self.case_category,
        }
        
        # Add date range if specified
        if self.since_date:
            params['dateFrom'] = self.since_date.strftime('%d.%m.%Y')
            params['dateTo'] = datetime.now().strftime('%d.%m.%Y')
        
        # Add court filter if specified
        if self.court:
            params['court'] = self.court
        
        return params
    
    def parse_search_form(self, response):
        """Parse search form and extract any required tokens"""
        
        search_params = response.meta['search_params']
        
        # Look for CSRF tokens or other required form fields
        csrf_token = response.css('input[name="__RequestVerificationToken"]::attr(value)').get()
        if csrf_token:
            search_params['__RequestVerificationToken'] = csrf_token
        
        # Submit search request
        yield scrapy.FormRequest(
            url=self.search_url,
            formdata={k: str(v) for k, v in search_params.items()},
            callback=self.parse_search_results,
            meta={'search_params': search_params, 'page': 1}
        )
    
    def parse_search_results(self, response):
        """Parse search results page"""
        
        search_params = response.meta['search_params']
        current_page = response.meta['page']
        
        # Extract case links from search results
        case_links = self._extract_case_links(response)
        
        for link_data in case_links:
            if self.documents_collected >= self.limit:
                self.logger.info(f"Reached limit of {self.limit} documents")
                return
            
            # Check date filter
            if self.since_date and link_data.get('date'):
                case_date = self._parse_date_flexible(link_data['date'])
                if case_date and case_date < self.since_date:
                    continue
            
            # Create request for case detail page
            yield scrapy.Request(
                url=link_data['url'],
                callback=self.parse_case,
                meta={'preview_data': link_data}
            )
        
        # Follow pagination if we haven't reached the limit
        if self.documents_collected < self.limit and len(case_links) > 0:
            next_page = current_page + 1
            search_params['page'] = next_page
            
            yield scrapy.FormRequest(
                url=self.search_url,
                formdata={k: str(v) for k, v in search_params.items()},
                callback=self.parse_search_results,
                meta={'search_params': search_params, 'page': next_page}
            )
    
    def _extract_case_links(self, response) -> Iterator[dict]:
        """Extract case links from search results"""
        
        # Look for different possible case result containers
        case_selectors = [
            '.case-item',
            '.search-result',
            '.kad-case',
            'tr[data-case-id]',
            '.case-row'
        ]
        
        cases = []
        for selector in case_selectors:
            cases = response.css(selector)
            if cases:
                break
        
        # Fallback: look for any links that look like case URLs
        if not cases:
            cases = response.css('a[href*="/Card/"]')
        
        for case in cases:
            link_data = self._extract_case_link_data(case, response)
            if link_data:
                yield link_data
    
    def _extract_case_link_data(self, element, response) -> Optional[dict]:
        """Extract basic data from case link element"""
        try:
            # Try to find the main link
            link = element.css('a::attr(href)').get()
            if not link:
                # Look for data attributes or other link sources
                case_id = element.attrib.get('data-case-id')
                if case_id:
                    link = f"/Card/{case_id}"
            
            if not link:
                return None
            
            # Make absolute URL
            url = urljoin(response.url, link)
            
            # Extract case number
            case_number = (
                element.css('.case-number::text').get() or
                element.css('[class*="number"]::text').get() or
                element.css('::text').re_first(r'А\d+-\d+/\d+') or
                'Unknown'
            )
            
            # Extract court name
            court_name = (
                element.css('.court-name::text').get() or
                element.css('[class*="court"]::text').get() or
                'Unknown Court'
            )
            
            # Extract date
            date_text = (
                element.css('.date::text').get() or
                element.css('[class*="date"]::text').get() or
                element.css('::text').re_first(r'\d{2}\.\d{2}\.\d{4}')
            )
            
            # Extract case category/type
            case_type = (
                element.css('.case-type::text').get() or
                element.css('[class*="type"]::text').get() or
                'Экономический спор'
            )
            
            return {
                'url': url,
                'case_number': case_number.strip() if case_number else 'Unknown',
                'court_name': court_name.strip() if court_name else 'Unknown Court',
                'date': date_text.strip() if date_text else None,
                'case_type': case_type.strip() if case_type else 'Unknown Type',
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting case link data: {e}")
            return None
    
    def parse_case(self, response):
        """Parse individual case page"""
        
        preview_data = response.meta.get('preview_data', {})
        
        # Extract detailed case information
        item = ArbitrageDocumentItem()
        
        # Basic fields
        item['source'] = 'kad.arbitr.ru'
        item['url'] = response.url
        item['crawl_timestamp'] = datetime.now().isoformat()
        item['document_type'] = 'court_decision'
        item['language'] = 'ru'
        
        # Case-specific fields
        item['case_number'] = self._extract_case_number(response, preview_data)
        item['court_name'] = self._extract_court_name(response, preview_data)
        item['judge_name'] = self._extract_judge_name(response)
        item['case_category'] = self._extract_case_category(response)
        item['decision_type'] = self._extract_decision_type(response)
        
        # Title
        item['title'] = self._build_case_title(item)
        
        # Document ID
        item['document_id'] = self._extract_case_id(response)
        
        # Dates
        item['publication_date'] = self._extract_case_date(response, preview_data)
        
        # Parties information
        item['parties'] = self._extract_parties(response)
        
        # Bill of exchange specific fields (if applicable)
        if self._is_bill_case(response, item):
            item['bill_amount'] = self._extract_bill_amount(response)
            item['bill_currency'] = self._extract_bill_currency(response)
            item['bill_parties'] = self._extract_bill_parties(response)
        
        # Find document download links (decisions, rulings, etc.)
        document_urls = self._extract_document_urls(response)
        
        if document_urls:
            item['file_urls'] = document_urls
            
            # Increment counter only when we have actual downloadable content
            self.documents_collected += 1
            
            self.logger.info(f"Found case {self.documents_collected}/{self.limit}: {item.get('case_number', 'Unknown')}")
            
            yield item
        else:
            self.logger.warning(f"No documents found for case: {response.url}")
    
    def _extract_case_number(self, response, preview_data: dict) -> str:
        """Extract case number"""
        selectors = [
            '.case-number::text',
            '[class*="number"]::text',
            'h1::text',
        ]
        
        for selector in selectors:
            case_number = response.css(selector).get()
            if case_number and 'А' in case_number:
                return case_number.strip()
        
        return preview_data.get('case_number', 'Unknown')
    
    def _extract_court_name(self, response, preview_data: dict) -> str:
        """Extract court name"""
        selectors = [
            '.court-name::text',
            '[class*="court"]::text',
            '.court-info::text',
        ]
        
        for selector in selectors:
            court = response.css(selector).get()
            if court:
                return court.strip()
        
        return preview_data.get('court_name', 'Unknown Court')
    
    def _extract_judge_name(self, response) -> Optional[str]:
        """Extract judge name"""
        selectors = [
            '.judge-name::text',
            '[class*="judge"]::text',
            '.composition::text',
        ]
        
        for selector in selectors:
            judge = response.css(selector).get()
            if judge and ('судья' in judge.lower() or 'председатель' in judge.lower()):
                return judge.strip()
        
        return None
    
    def _extract_case_category(self, response) -> Optional[str]:
        """Extract case category"""
        selectors = [
            '.case-category::text',
            '[class*="category"]::text',
            '.dispute-type::text',
        ]
        
        for selector in selectors:
            category = response.css(selector).get()
            if category:
                return category.strip()
        
        return None
    
    def _extract_decision_type(self, response) -> Optional[str]:
        """Extract type of decision"""
        selectors = [
            '.decision-type::text',
            '[class*="decision"]::text',
            '.ruling-type::text',
        ]
        
        for selector in selectors:
            decision_type = response.css(selector).get()
            if decision_type:
                return decision_type.strip()
        
        return None
    
    def _build_case_title(self, item: ArbitrageDocumentItem) -> str:
        """Build case title from available information"""
        court = item.get('court_name', 'Арбитражный суд')
        case_num = item.get('case_number', 'Unknown')
        decision_type = item.get('decision_type', 'Решение')
        
        return f"{decision_type} {court} по делу № {case_num}"
    
    def _extract_case_id(self, response) -> Optional[str]:
        """Extract unique case identifier"""
        # Look in URL
        url_match = re.search(r'/Card/(\w+)', response.url)
        if url_match:
            return url_match.group(1)
        
        # Look for data attributes
        case_id = response.css('[data-case-id]::attr(data-case-id)').get()
        if case_id:
            return case_id
        
        return None
    
    def _extract_case_date(self, response, preview_data: dict) -> Optional[str]:
        """Extract case date"""
        selectors = [
            '.case-date::text',
            '[class*="date"]::text',
            '.decision-date::text',
        ]
        
        for selector in selectors:
            date_text = response.css(selector).get()
            if date_text:
                normalized_date = self._normalize_date(date_text)
                if normalized_date:
                    return normalized_date
        
        # Try preview data
        if preview_data.get('date'):
            return self._normalize_date(preview_data['date'])
        
        return None
    
    def _extract_parties(self, response) -> list:
        """Extract case parties information"""
        parties = []
        
        # Look for plaintiff/defendant sections
        party_selectors = [
            '.plaintiff',
            '.defendant', 
            '.parties',
            '[class*="party"]'
        ]
        
        for selector in party_selectors:
            party_elements = response.css(selector)
            for element in party_elements:
                party_name = element.css('::text').get()
                if party_name:
                    parties.append(party_name.strip())
        
        return parties
    
    def _is_bill_case(self, response, item: ArbitrageDocumentItem) -> bool:
        """Check if this is a bill of exchange case"""
        text_content = ' '.join(response.css('::text').getall()).lower()
        
        bill_keywords = ['вексель', 'векселедатель', 'векселедержатель', 'индоссамент', 'аваль']
        
        return any(keyword in text_content for keyword in bill_keywords)
    
    def _extract_bill_amount(self, response) -> Optional[str]:
        """Extract bill amount from case text"""
        text_content = ' '.join(response.css('::text').getall())
        
        # Look for amount patterns
        amount_patterns = [
            r'(\d+(?:\s\d+)*)\s*(?:руб|рубл|₽)',
            r'(\d+(?:\.\d+)?)\s*(?:руб|рубл|₽)',
            r'сумм[аеыи]?\s*(?:в\s*размере\s*)?(\d+(?:\s\d+)*)',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '')
        
        return None
    
    def _extract_bill_currency(self, response) -> Optional[str]:
        """Extract bill currency"""
        text_content = ' '.join(response.css('::text').getall()).lower()
        
        if 'руб' in text_content or '₽' in text_content:
            return 'RUB'
        elif 'долл' in text_content or '$' in text_content:
            return 'USD'
        elif 'евро' in text_content or '€' in text_content:
            return 'EUR'
        
        return 'RUB'  # Default for Russian courts
    
    def _extract_bill_parties(self, response) -> dict:
        """Extract bill-specific party roles"""
        text_content = ' '.join(response.css('::text').getall()).lower()
        
        parties = {}
        
        # Look for bill-specific roles
        if 'векселедатель' in text_content:
            drawer_match = re.search(r'векселедатель[:\-\s]*([^,\n.]+)', text_content)
            if drawer_match:
                parties['drawer'] = drawer_match.group(1).strip()
        
        if 'векселедержатель' in text_content:
            holder_match = re.search(r'векселедержатель[:\-\s]*([^,\n.]+)', text_content)
            if holder_match:
                parties['holder'] = holder_match.group(1).strip()
        
        return parties
    
    def _extract_document_urls(self, response) -> list:
        """Extract document download URLs"""
        document_urls = []
        
        # Look for document download links
        doc_selectors = [
            'a[href$=".pdf"]::attr(href)',
            'a[href*="download"]::attr(href)',
            'a[href*="document"]::attr(href)',
            '.document-link::attr(href)',
            '.download-link::attr(href)',
            'a:contains("Скачать")::attr(href)',
            'a:contains("Решение")::attr(href)',
            'a:contains("Постановление")::attr(href)',
        ]
        
        for selector in doc_selectors:
            links = response.css(selector).getall()
            for link in links:
                if link:
                    full_url = urljoin(response.url, link)
                    if full_url not in document_urls:
                        document_urls.append(full_url)
        
        return document_urls
    
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
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '.' in date_text:
                        # DD.MM.YYYY format
                        day, month, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        # YYYY-MM-DD format
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        
        return None
    
    def _parse_date_flexible(self, date_text: str) -> Optional[datetime]:
        """Parse date with flexible format support"""
        normalized = self._normalize_date(date_text)
        if normalized:
            try:
                return datetime.strptime(normalized, '%Y-%m-%d')
            except ValueError:
                pass
        return None 