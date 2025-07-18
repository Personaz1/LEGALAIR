import os
import re
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from scrapy.http import Request

from .items import LegalDocumentItem


class ValidationPipeline:
    """Validate item data before processing"""
    
    def process_item(self, item: LegalDocumentItem, spider) -> LegalDocumentItem:
        """Validate required fields"""
        required_fields = ['source', 'url', 'title']
        
        for field in required_fields:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field}")
        
        # Validate URLs
        if not self._is_valid_url(item['url']):
            raise DropItem(f"Invalid URL: {item['url']}")
        
        if item.get('file_urls'):
            valid_urls = []
            for url in item['file_urls']:
                if self._is_valid_url(url):
                    valid_urls.append(url)
            item['file_urls'] = valid_urls
            
            if not valid_urls:
                raise DropItem("No valid file URLs found")
        
        spider.logger.debug(f"Validated item: {item.get('title', 'Unknown')}")
        return item
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


class DuplicatesPipeline:
    """Filter out duplicate documents"""
    
    def __init__(self):
        self.seen_urls = set()
        self.seen_hashes = set()
    
    def process_item(self, item: LegalDocumentItem, spider) -> LegalDocumentItem:
        """Check for duplicates by URL and content hash"""
        
        # Check URL duplicates
        url = item['url']
        if url in self.seen_urls:
            raise DropItem(f"Duplicate URL: {url}")
        
        # Generate content hash for deduplication
        content_parts = [
            str(item.get('title', '')),
            str(item.get('document_id', '')),
            str(item.get('publication_date', '')),
        ]
        content_hash = hashlib.md5('|'.join(content_parts).encode('utf-8')).hexdigest()
        
        if content_hash in self.seen_hashes:
            raise DropItem(f"Duplicate content hash: {content_hash}")
        
        # Mark as seen
        self.seen_urls.add(url)
        self.seen_hashes.add(content_hash)
        item['content_hash'] = content_hash
        
        spider.logger.debug(f"Passed duplicate check: {item.get('title', 'Unknown')}")
        return item


class PrivacyMaskingPipeline:
    """Mask personal data in document content"""
    
    def __init__(self):
        # Personal data patterns for Russian documents
        self.patterns = [
            (r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+ич\b', '*** *** ***ич'),  # Full names
            (r'\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+\b', '***. ***. ***'),  # Initials + surname
            (r'\b\d{4}\s*\d{6}\b', '****-******'),  # Passport series + number
            (r'\b\d{11}\b', '***-***-***-**'),  # SNILS
            (r'\b\d{10}\b', '**********'),  # INN individual (10 digits)
            (r'\b\d{12}\b', '************'),  # INN individual (12 digits)
            (r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', '**.**.****'),  # Dates (potential birthdates)
        ]
    
    def process_item(self, item: LegalDocumentItem, spider) -> LegalDocumentItem:
        """Mask personal data in text fields"""
        
        text_fields = ['title', 'text_content']
        
        for field in text_fields:
            if item.get(field):
                original_text = item[field]
                masked_text = self._mask_personal_data(original_text)
                
                if masked_text != original_text:
                    item[field] = masked_text
                    spider.logger.info(f"Masked personal data in field '{field}'")
        
        return item
    
    def _mask_personal_data(self, text: str) -> str:
        """Apply privacy masking patterns to text"""
        masked_text = text
        
        for pattern, replacement in self.patterns:
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text


class FileDownloadPipeline(FilesPipeline):
    """Custom file download pipeline for legal documents"""
    
    def get_media_requests(self, item: LegalDocumentItem, info):
        """Generate download requests for files"""
        urls = item.get('file_urls', [])
        
        for url in urls:
            yield Request(
                url,
                meta={
                    'item': item,
                    'source': item.get('source', 'unknown')
                }
            )
    
    def file_path(self, request, response=None, info=None, *, item=None):
        """Generate file path for downloaded files"""
        source = request.meta.get('source', 'unknown')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Generate unique filename
        url_hash = hashlib.md5(request.url.encode('utf-8')).hexdigest()[:8]
        file_uuid = str(uuid.uuid4())[:8]
        
        # Extract file extension
        parsed_url = urlparse(request.url)
        path_parts = parsed_url.path.split('.')
        extension = path_parts[-1].lower() if len(path_parts) > 1 else 'pdf'
        
        # Ensure it's a valid extension
        if extension not in ['pdf', 'doc', 'docx', 'txt']:
            extension = 'pdf'
        
        filename = f"{url_hash}_{file_uuid}.{extension}"
        
        return f"{source}/{today}/{filename}"
    
    def item_completed(self, results, item: LegalDocumentItem, info):
        """Process completed downloads"""
        successful_downloads = []
        
        for success, file_info in results:
            if success:
                file_path = file_info['path']
                file_url = file_info['url']
                
                successful_downloads.append({
                    'url': file_url,
                    'path': file_path,
                    'checksum': file_info.get('checksum'),
                    'size': file_info.get('size', 0)
                })
        
        if successful_downloads:
            item['files'] = successful_downloads
            item['processing_status'] = 'downloaded'
        else:
            item['processing_status'] = 'download_failed'
            # Don't drop the item, just mark as failed
        
        return item


class MetadataPipeline:
    """Generate and save metadata for each document"""
    
    def __init__(self):
        self.base_dir = Path('data/crawl')
    
    def process_item(self, item: LegalDocumentItem, spider) -> LegalDocumentItem:
        """Save metadata as JSON file"""
        
        # Ensure we have downloaded files
        files = item.get('files', [])
        if not files:
            spider.logger.warning(f"No files downloaded for item: {item.get('title', 'Unknown')}")
            return item
        
        # Get the directory from the first file
        first_file_path = files[0]['path']
        file_dir = Path(self.base_dir) / Path(first_file_path).parent
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate metadata filename
        content_hash = item.get('content_hash', str(uuid.uuid4())[:8])
        metadata_filename = f"{content_hash}.meta.json"
        metadata_path = file_dir / metadata_filename
        
        # Prepare metadata
        metadata = {
            'document_info': {
                'title': item.get('title'),
                'document_id': item.get('document_id'),
                'source': item.get('source'),
                'url': item.get('url'),
                'document_type': item.get('document_type'),
                'publication_date': item.get('publication_date'),
                'effective_date': item.get('effective_date'),
                'author_organization': item.get('author_organization'),
                'language': item.get('language', 'ru'),
            },
            'source_specific': self._extract_source_specific_metadata(item),
            'technical_info': {
                'crawl_timestamp': item.get('crawl_timestamp'),
                'content_hash': item.get('content_hash'),
                'processing_status': item.get('processing_status'),
                'files': files,
            },
            'crawler_info': {
                'spider_name': spider.name,
                'crawler_version': '1.0.0',
            }
        }
        
        # Save metadata
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            spider.logger.info(f"Saved metadata: {metadata_path}")
            
        except Exception as e:
            spider.logger.error(f"Failed to save metadata: {e}")
        
        return item
    
    def _extract_source_specific_metadata(self, item: LegalDocumentItem) -> Dict[str, Any]:
        """Extract source-specific metadata fields"""
        source = item.get('source', '')
        
        if 'pravo.gov.ru' in source:
            return {
                'bulletin_number': item.get('bulletin_number'),
                'registration_number': item.get('registration_number'),
                'adopting_authority': item.get('adopting_authority'),
                'document_status': item.get('document_status'),
            }
        elif 'kad.arbitr.ru' in source:
            return {
                'case_number': item.get('case_number'),
                'court_name': item.get('court_name'),
                'judge_name': item.get('judge_name'),
                'case_category': item.get('case_category'),
                'decision_type': item.get('decision_type'),
                'parties': item.get('parties'),
                'bill_amount': item.get('bill_amount'),
                'bill_currency': item.get('bill_currency'),
                'bill_parties': item.get('bill_parties'),
            }
        else:
            return {
                'template_category': item.get('template_category'),
                'template_version': item.get('template_version'),
                'license_type': item.get('license_type'),
                'download_format': item.get('download_format'),
            }


class OCRIntegrationPipeline:
    """Optional pipeline to trigger OCR processing"""
    
    def __init__(self):
        self.ocr_enabled = False  # Will be set from settings
    
    def open_spider(self, spider):
        """Initialize OCR settings"""
        self.ocr_enabled = spider.settings.getbool('LEGAL_CRAWL_OCR_ENABLED', False)
        spider.logger.info(f"OCR integration: {'enabled' if self.ocr_enabled else 'disabled'}")
    
    def process_item(self, item: LegalDocumentItem, spider) -> LegalDocumentItem:
        """Trigger OCR processing if enabled"""
        
        if not self.ocr_enabled:
            return item
        
        files = item.get('files', [])
        if not files:
            return item
        
        # Trigger OCR for each downloaded file
        for file_info in files:
            file_path = Path('data/crawl') / file_info['path']
            
            if file_path.suffix.lower() == '.pdf':
                self._trigger_ocr(file_path, spider)
        
        return item
    
    def _trigger_ocr(self, file_path: Path, spider):
        """Trigger OCR processing for a file"""
        try:
            # This would integrate with the existing OCR service
            spider.logger.info(f"Triggering OCR for: {file_path}")
            
            # TODO: Integrate with ml/ocr_service.py
            # For now, just log the action
            
        except Exception as e:
            spider.logger.error(f"OCR processing failed for {file_path}: {e}") 