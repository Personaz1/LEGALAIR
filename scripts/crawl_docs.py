#!/usr/bin/env python3
"""
Legal AI Document Crawler - Universal CLI Tool
ΔΣ::Cursor - Automated legal document collection

Usage:
    python scripts/crawl_docs.py pravo --limit 10 --since 2023-01-01
    python scripts/crawl_docs.py kad --limit 20 --keywords "вексель"
    python scripts/crawl_docs.py all --limit 50 --run-ocr
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import custom settings
from crawlers.settings import *


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / f"crawl_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )
    
    return logging.getLogger("legal_crawler_cli")


def validate_date(date_string: str) -> str:
    """Validate date string format"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return date_string
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")


def get_spider_settings(spider_name: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Get Scrapy settings for specific spider"""
    
    # Base settings
    settings = get_project_settings()
    settings.setmodule('crawlers.settings')
    
    # Override with CLI arguments
    if args.delay:
        settings.set('DOWNLOAD_DELAY', args.delay)
    
    if args.concurrent:
        settings.set('CONCURRENT_REQUESTS', args.concurrent)
        settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', max(1, args.concurrent // 2))
    
    if args.user_agent:
        settings.set('USER_AGENT', args.user_agent)
    
    if args.run_ocr:
        settings.set('LEGAL_CRAWL_OCR_ENABLED', True)
    
    if args.output_dir:
        output_path = Path(args.output_dir).absolute()
        output_path.mkdir(parents=True, exist_ok=True)
        settings.set('FILES_STORE', str(output_path))
    
    # Log level
    settings.set('LOG_LEVEL', args.log_level.upper())
    
    return settings


def prepare_spider_args(spider_name: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Prepare spider-specific arguments"""
    
    spider_args = {}
    
    # Common arguments
    if args.limit:
        spider_args['limit'] = str(args.limit)
    
    if args.since:
        spider_args['since'] = args.since
    
    # Spider-specific arguments
    if spider_name == 'kad':
        if args.keywords:
            spider_args['keywords'] = args.keywords
        if args.court:
            spider_args['court'] = args.court
        if args.case_category:
            spider_args['case_category'] = args.case_category
    
    elif spider_name == 'gibdd':
        if args.template_type:
            spider_args['template_type'] = args.template_type
    
    elif spider_name == 'github':
        if args.repo:
            spider_args['repo'] = args.repo
        if args.license_filter:
            spider_args['license_filter'] = args.license_filter
    
    return spider_args


def run_spider(spider_name: str, args: argparse.Namespace, logger: logging.Logger) -> bool:
    """Run a specific spider"""
    
    logger.info(f"Starting spider: {spider_name}")
    
    try:
        # Get settings and arguments
        settings = get_spider_settings(spider_name, args)
        spider_args = prepare_spider_args(spider_name, args)
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Add spider to process
        process.crawl(spider_name, **spider_args)
        
        # Start crawling
        process.start()
        
        logger.info(f"Spider {spider_name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Spider {spider_name} failed: {e}")
        return False


def run_all_spiders(args: argparse.Namespace, logger: logging.Logger) -> Dict[str, bool]:
    """Run all available spiders"""
    
    available_spiders = ['pravo', 'kad', 'gibdd', 'github']
    results = {}
    
    for spider_name in available_spiders:
        logger.info(f"Running spider {spider_name} ({len(results) + 1}/{len(available_spiders)})")
        
        try:
            # Create a new process for each spider
            success = run_spider(spider_name, args, logger)
            results[spider_name] = success
            
            if not success:
                logger.warning(f"Spider {spider_name} failed, continuing with others")
                
        except Exception as e:
            logger.error(f"Failed to run spider {spider_name}: {e}")
            results[spider_name] = False
    
    return results


def generate_summary_report(results: Dict[str, bool], output_dir: Path, logger: logging.Logger):
    """Generate crawling summary report"""
    
    timestamp = datetime.now().isoformat()
    
    # Count statistics
    total_spiders = len(results)
    successful_spiders = sum(1 for success in results.values() if success)
    failed_spiders = total_spiders - successful_spiders
    
    # Collect file statistics
    crawl_stats = {}
    for spider_name in results.keys():
        spider_dir = output_dir / spider_name
        if spider_dir.exists():
            pdf_files = list(spider_dir.rglob("*.pdf"))
            meta_files = list(spider_dir.rglob("*.meta.json"))
            
            crawl_stats[spider_name] = {
                "pdf_files": len(pdf_files),
                "meta_files": len(meta_files),
                "total_size_mb": sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
            }
    
    # Generate report
    report = {
        "crawl_summary": {
            "timestamp": timestamp,
            "total_spiders": total_spiders,
            "successful_spiders": successful_spiders,
            "failed_spiders": failed_spiders,
            "success_rate": successful_spiders / total_spiders if total_spiders > 0 else 0,
        },
        "spider_results": results,
        "file_statistics": crawl_stats,
        "total_documents": sum(stats.get("pdf_files", 0) for stats in crawl_stats.values()),
        "total_size_mb": sum(stats.get("total_size_mb", 0) for stats in crawl_stats.values()),
    }
    
    # Save report
    report_path = output_dir / f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Summary report saved: {report_path}")
        
        # Print summary to console
        print("\n" + "="*60)
        print("CRAWLING SUMMARY")
        print("="*60)
        print(f"Timestamp: {timestamp}")
        print(f"Spiders run: {total_spiders}")
        print(f"Successful: {successful_spiders}")
        print(f"Failed: {failed_spiders}")
        print(f"Success rate: {successful_spiders/total_spiders*100:.1f}%")
        print(f"Total documents: {report['total_documents']}")
        print(f"Total size: {report['total_size_mb']:.1f} MB")
        print("\nSpider Results:")
        for spider, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            docs = crawl_stats.get(spider, {}).get("pdf_files", 0)
            print(f"  {spider:12} {status:10} ({docs} documents)")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to save summary report: {e}")


def main():
    """Main CLI entry point"""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Legal AI Document Crawler - Automated legal document collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s pravo --limit 10 --since 2023-01-01
  %(prog)s kad --limit 20 --keywords "вексель"
  %(prog)s all --limit 50 --run-ocr
  %(prog)s gibdd --template-type fine
        """
    )
    
    # Spider selection
    parser.add_argument(
        'spider',
        choices=['pravo', 'kad', 'gibdd', 'github', 'all'],
        help='Spider to run (or "all" for all spiders)'
    )
    
    # Common arguments
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of documents to crawl (default: 50)'
    )
    
    parser.add_argument(
        '--since',
        type=validate_date,
        help='Only crawl documents published since this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/crawl',
        help='Output directory for downloaded files (default: data/crawl)'
    )
    
    parser.add_argument(
        '--run-ocr',
        action='store_true',
        help='Run OCR processing on downloaded PDFs'
    )
    
    # Technical arguments
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--concurrent',
        type=int,
        default=2,
        help='Number of concurrent requests (default: 2)'
    )
    
    parser.add_argument(
        '--user-agent',
        type=str,
        help='Custom User-Agent string'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    
    # Spider-specific arguments
    parser.add_argument(
        '--keywords',
        type=str,
        help='Keywords to search for (kad spider)'
    )
    
    parser.add_argument(
        '--court',
        type=str,
        help='Specific court to search (kad spider)'
    )
    
    parser.add_argument(
        '--case-category',
        type=str,
        help='Case category filter (kad spider)'
    )
    
    parser.add_argument(
        '--template-type',
        choices=['fine', 'protocol', 'form'],
        help='Template type to download (gibdd spider)'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        help='GitHub repository to crawl (github spider)'
    )
    
    parser.add_argument(
        '--license-filter',
        type=str,
        help='License filter for templates (github spider)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Print banner
    print("🕷️  Legal AI Document Crawler")
    print("   ΔΣ::Cursor - Automated Collection")
    print(f"   Target: {args.spider}")
    print(f"   Limit: {args.limit} documents")
    if args.since:
        print(f"   Since: {args.since}")
    print()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run crawling
    if args.spider == 'all':
        results = run_all_spiders(args, logger)
    else:
        success = run_spider(args.spider, args, logger)
        results = {args.spider: success}
    
    # Generate summary report
    generate_summary_report(results, output_dir, logger)
    
    # Exit with appropriate code
    if all(results.values()):
        logger.info("All crawling tasks completed successfully")
        sys.exit(0)
    else:
        logger.error("Some crawling tasks failed")
        sys.exit(1)


if __name__ == '__main__':
    main() 