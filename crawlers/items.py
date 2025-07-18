import scrapy
from datetime import datetime
from typing import Optional

class LegalDocumentItem(scrapy.Item):
    """Base item for legal documents"""
    
    # Document identification
    title = scrapy.Field()
    document_id = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    file_urls = scrapy.Field()
    files = scrapy.Field()
    
    # Document metadata
    document_type = scrapy.Field()
    publication_date = scrapy.Field()
    effective_date = scrapy.Field()
    author_organization = scrapy.Field()
    legal_category = scrapy.Field()
    
    # Content information
    text_content = scrapy.Field()
    language = scrapy.Field()
    page_count = scrapy.Field()
    file_size = scrapy.Field()
    
    # Technical metadata
    crawl_timestamp = scrapy.Field()
    content_hash = scrapy.Field()
    processing_status = scrapy.Field()
    
    def __repr__(self):
        return f"<LegalDocumentItem: {self.get('title', 'Unknown')}>"

class PravoDocumentItem(LegalDocumentItem):
    """Item for documents from pravo.gov.ru"""
    
    # Pravo.gov.ru specific fields
    bulletin_number = scrapy.Field()
    registration_number = scrapy.Field()
    adopting_authority = scrapy.Field()
    document_status = scrapy.Field()
    
class ArbitrageDocumentItem(LegalDocumentItem):
    """Item for arbitration court documents"""
    
    # Court-specific fields
    case_number = scrapy.Field()
    court_name = scrapy.Field()
    judge_name = scrapy.Field()
    case_category = scrapy.Field()
    decision_type = scrapy.Field()
    parties = scrapy.Field()
    
    # Bill of exchange specific fields
    bill_amount = scrapy.Field()
    bill_currency = scrapy.Field()
    bill_parties = scrapy.Field()
    
class TemplateDocumentItem(LegalDocumentItem):
    """Item for document templates"""
    
    # Template-specific fields
    template_category = scrapy.Field()
    template_version = scrapy.Field()
    license_type = scrapy.Field()
    download_format = scrapy.Field() 