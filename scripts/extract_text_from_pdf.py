#!/usr/bin/env python3
"""
Legal AI PDF Text Extraction
ΔΣ::Cursor - Extract text from legal document PDFs

Supports:
- PyPDF2/PDFplumber for text extraction
- OCR fallback for scanned documents  
- Integration with existing OCR service
- Batch processing
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from ml.ocr_service import OCRService
    OCR_SERVICE_AVAILABLE = True
except ImportError:
    OCR_SERVICE_AVAILABLE = False


class PDFTextExtractor:
    """Extract text from PDF files with multiple fallback methods"""
    
    def __init__(self, use_ocr_fallback: bool = True):
        self.use_ocr_fallback = use_ocr_fallback
        self.ocr_service = None
        
        if use_ocr_fallback and OCR_SERVICE_AVAILABLE:
            try:
                self.ocr_service = OCRService()
            except Exception as e:
                logging.warning(f"Failed to initialize OCR service: {e}")
    
    def extract_text(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text from PDF using best available method"""
        
        result = {
            'file_path': str(pdf_path),
            'file_size': pdf_path.stat().st_size,
            'extraction_timestamp': datetime.now().isoformat(),
            'methods_tried': [],
            'text': '',
            'page_count': 0,
            'success': False,
            'extraction_method': None,
            'confidence': 0.0,
            'errors': []
        }
        
        # Try PDFplumber first (most reliable)
        if PDFPLUMBER_AVAILABLE:
            try:
                text, page_count = self._extract_with_pdfplumber(pdf_path)
                if text and len(text.strip()) > 50:  # Reasonable amount of text
                    result.update({
                        'text': text,
                        'page_count': page_count,
                        'success': True,
                        'extraction_method': 'pdfplumber',
                        'confidence': 0.95
                    })
                    result['methods_tried'].append('pdfplumber')
                    return result
                else:
                    result['methods_tried'].append('pdfplumber_insufficient')
            except Exception as e:
                result['errors'].append(f"PDFplumber error: {str(e)}")
                result['methods_tried'].append('pdfplumber_failed')
        
        # Try PyPDF2 as backup
        if PYPDF2_AVAILABLE:
            try:
                text, page_count = self._extract_with_pypdf2(pdf_path)
                if text and len(text.strip()) > 50:
                    result.update({
                        'text': text,
                        'page_count': page_count,
                        'success': True,
                        'extraction_method': 'pypdf2',
                        'confidence': 0.85
                    })
                    result['methods_tried'].append('pypdf2')
                    return result
                else:
                    result['methods_tried'].append('pypdf2_insufficient')
            except Exception as e:
                result['errors'].append(f"PyPDF2 error: {str(e)}")
                result['methods_tried'].append('pypdf2_failed')
        
        # OCR fallback for scanned documents
        if self.use_ocr_fallback and self.ocr_service:
            try:
                text = self._extract_with_ocr(pdf_path)
                if text and len(text.strip()) > 20:
                    result.update({
                        'text': text,
                        'page_count': 1,  # OCR service handles page counting separately
                        'success': True,
                        'extraction_method': 'ocr',
                        'confidence': 0.75
                    })
                    result['methods_tried'].append('ocr')
                    return result
                else:
                    result['methods_tried'].append('ocr_insufficient')
            except Exception as e:
                result['errors'].append(f"OCR error: {str(e)}")
                result['methods_tried'].append('ocr_failed')
        
        # No extraction method worked
        result['success'] = False
        result['extraction_method'] = None
        
        return result
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> tuple[str, int]:
        """Extract text using pdfplumber"""
        
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            page_count = len(pdf.pages)
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n\n'.join(text_parts), page_count
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> tuple[str, int]:
        """Extract text using PyPDF2"""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_parts = []
            page_count = len(pdf_reader.pages)
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n\n'.join(text_parts), page_count
    
    def _extract_with_ocr(self, pdf_path: Path) -> str:
        """Extract text using OCR service"""
        
        if not self.ocr_service:
            raise Exception("OCR service not available")
        
        # Convert PDF to images and run OCR
        result = self.ocr_service.process_pdf(str(pdf_path))
        
        if result.get('success'):
            return result.get('text', '')
        else:
            raise Exception(f"OCR failed: {result.get('error', 'Unknown error')}")


def process_single_file(pdf_path: Path, output_dir: Path, extractor: PDFTextExtractor, 
                       logger: logging.Logger) -> bool:
    """Process a single PDF file"""
    
    logger.info(f"Processing: {pdf_path}")
    
    try:
        # Extract text
        result = extractor.extract_text(pdf_path)
        
        # Generate output filenames
        file_stem = pdf_path.stem
        txt_path = output_dir / f"{file_stem}.txt"
        meta_path = output_dir / f"{file_stem}.extraction.json"
        
        # Save extracted text
        if result['success']:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            
            logger.info(f"Extracted text ({len(result['text'])} chars) using {result['extraction_method']}")
        else:
            logger.warning(f"Text extraction failed: {result['errors']}")
        
        # Save metadata
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result['success']
        
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return False


def process_batch(input_path: Path, output_dir: Path, recursive: bool, 
                 use_ocr: bool, logger: logging.Logger) -> Dict[str, Any]:
    """Process multiple PDF files"""
    
    # Find PDF files
    if input_path.is_file():
        pdf_files = [input_path] if input_path.suffix.lower() == '.pdf' else []
    else:
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(input_path.glob(pattern))
    
    if not pdf_files:
        logger.warning("No PDF files found")
        return {'total': 0, 'successful': 0, 'failed': 0}
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    extractor = PDFTextExtractor(use_ocr_fallback=use_ocr)
    
    # Process files
    results = {'total': len(pdf_files), 'successful': 0, 'failed': 0, 'files': []}
    
    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_path.name}")
        
        success = process_single_file(pdf_path, output_dir, extractor, logger)
        
        if success:
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        results['files'].append({
            'path': str(pdf_path),
            'success': success
        })
    
    return results


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/crawl/pravo.gov.ru/2024-01-15/
  %(prog)s document.pdf --output-dir extracted_text/
  %(prog)s data/crawl/ --recursive --use-ocr
        """
    )
    
    parser.add_argument(
        'input',
        type=Path,
        help='Input PDF file or directory'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/ocr_txt'),
        help='Output directory for extracted text (default: data/ocr_txt)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process directories recursively'
    )
    
    parser.add_argument(
        '--use-ocr',
        action='store_true',
        help='Use OCR as fallback for scanned documents'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/pdf_extraction.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Validate input
    if not args.input.exists():
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)
    
    # Check dependencies
    if not (PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE):
        logger.error("No PDF processing library available. Install PyPDF2 or pdfplumber.")
        sys.exit(1)
    
    if args.use_ocr and not OCR_SERVICE_AVAILABLE:
        logger.warning("OCR requested but service not available. Continuing without OCR.")
        args.use_ocr = False
    
    # Print banner
    print("📄 Legal AI PDF Text Extraction")
    print("   ΔΣ::Cursor - Document Processing")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output_dir}")
    print(f"   OCR enabled: {args.use_ocr}")
    print()
    
    # Process files
    results = process_batch(
        args.input, 
        args.output_dir, 
        args.recursive, 
        args.use_ocr, 
        logger
    )
    
    # Print summary
    print("\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    print(f"Total files: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    success_rate = (results['successful'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print("="*50)
    
    # Exit with appropriate code
    if results['successful'] > 0:
        logger.info("Text extraction completed")
        sys.exit(0)
    else:
        logger.error("No files processed successfully")
        sys.exit(1)


if __name__ == '__main__':
    main() 