#!/usr/bin/env python3
"""
Legal AI Crawler Offline Demo
ΔΣ::Cursor - Demonstrate crawler functionality without network connectivity

Creates mock data to simulate successful crawling when target sites are unreachable.
Perfect for testing, development, and demonstrations.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import random
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class OfflineCrawlerDemo:
    """Simulate crawler functionality offline"""
    
    def __init__(self):
        self.base_dir = Path("data/crawl")
        self.ocr_dir = Path("data/ocr_txt")
        self.logs_dir = Path("logs")
        
    def create_mock_documents(self, source: str, count: int = 10) -> list:
        """Create mock legal documents for demonstration"""
        
        documents = []
        
        # Mock document templates by source
        templates = {
            'pravo.gov.ru': [
                "Федеральный закон от {date} № {num}-ФЗ «О {topic}»",
                "Постановление Правительства РФ от {date} № {num} «Об утверждении {topic}»", 
                "Приказ Минфина России от {date} № {num}н «О {topic}»",
                "Распоряжение Правительства РФ от {date} № {num}-р «О {topic}»",
                "Инструкция ЦБ РФ от {date} № {num}-И «О {topic}»"
            ],
            'kad.arbitr.ru': [
                "Решение Арбитражного суда {region} от {date} по делу № А{num}-{case}/{year}",
                "Постановление суда по делу о взыскании задолженности № А{num}-{case}/{year}",
                "Определение суда о применении обеспечительных мер № А{num}-{case}/{year}",
                "Решение по вексельному спору № А{num}-{case}/{year}",
            ],
            'gibdd.ru': [
                "Форма постановления по делу об административном правонарушении",
                "Протокол об административном правонарушении в области дорожного движения", 
                "Форма уведомления о нарушении ПДД",
                "Постановление о наложении административного штрафа",
            ]
        }
        
        topics = [
            "векселях", "валютном регулировании", "налогообложении", 
            "административных правонарушениях", "дорожном движении",
            "финансовых операциях", "банковской деятельности",
            "страховании", "лицензировании", "государственной регистрации"
        ]
        
        regions = ["г. Москвы", "Московской области", "г. Санкт-Петербурга", 
                  "Ленинградской области", "Свердловской области"]
        
        for i in range(count):
            # Generate mock metadata
            doc_date = datetime.now() - timedelta(days=random.randint(1, 365))
            doc_num = random.randint(1, 999)
            case_num = random.randint(1000, 9999)
            year = doc_date.year
            
            # Select template and format
            template_list = templates.get(source, templates['pravo.gov.ru'])
            template = random.choice(template_list)
            
            title = template.format(
                date=doc_date.strftime('%d.%m.%Y'),
                num=doc_num,
                case=case_num,
                year=year,
                topic=random.choice(topics),
                region=random.choice(regions)
            )
            
            # Create document metadata
            doc_id = str(uuid.uuid4())[:8]
            file_uuid = str(uuid.uuid4())[:8]
            
            document = {
                'id': doc_id,
                'title': title,
                'source': source,
                'url': f"https://{source}/document/{doc_id}",
                'publication_date': doc_date.strftime('%Y-%m-%d'),
                'document_type': self._get_doc_type(template),
                'file_uuid': file_uuid,
                'content': self._generate_mock_content(title, source)
            }
            
            documents.append(document)
        
        return documents
    
    def _get_doc_type(self, template: str) -> str:
        """Determine document type from template"""
        if "Федеральный закон" in template:
            return "federal_law"
        elif "Постановление" in template:
            return "government_decree"
        elif "Приказ" in template:
            return "ministerial_order"
        elif "Решение" in template or "дело" in template:
            return "court_decision"
        elif "Протокол" in template:
            return "protocol"
        elif "Форма" in template:
            return "form_template"
        else:
            return "other_document"
    
    def _generate_mock_content(self, title: str, source: str) -> str:
        """Generate realistic mock document content"""
        
        if "вексель" in title.lower():
            return f"""
{title}

Статья 1. Основные положения
1. Простой вексель должен содержать:
   - наименование "вексель", включенное в самый текст документа;
   - простое и ничем не обусловленное обещание уплатить определенную сумму;
   - указание срока платежа;
   - указание места, в котором должен быть совершен платеж;
   - наименование того, кому или приказу кого платеж должен быть совершен;
   - указание даты и места составления векселя;
   - подпись того, кто выдает вексель (векселедателя).

Статья 2. Сумма векселя
Сумма векселя считается написанной прописью и цифрами.

Статья 3. Сроки платежа
Вексель может быть выдан:
- по предъявлении;
- во столько-то времени от предъявления;
- во столько-то времени от составления;
- на определенный день.

Настоящий документ вступает в силу с момента официального опубликования.
            """.strip()
        
        elif "штраф" in title.lower() or "административн" in title.lower():
            return f"""
{title}

ПОСТАНОВЛЕНИЕ
по делу об административном правонарушении

Должностное лицо: Инспектор ДПС
Дата составления: {datetime.now().strftime('%d.%m.%Y')}
Место составления: г. Москва

УСТАНОВЛЕНО:
Нарушение требований дорожных знаков или разметки проезжей части дороги.

Статья 12.16 КоАП РФ - Несоблюдение требований, предписанных дорожными знаками или разметкой проезжей части дороги.

ПОСТАНОВИЛ:
Признать виновным в совершении административного правонарушения.
Назначить административное наказание в виде штрафа в размере 1500 рублей.

Постановление может быть обжаловано в течение 10 суток.
            """.strip()
        
        else:
            return f"""
{title}

ОБЩИЕ ПОЛОЖЕНИЯ

Настоящий документ разработан в соответствии с действующим законодательством Российской Федерации.

Основные принципы:
1. Законность
2. Обоснованность
3. Целесообразность
4. Соразмерность

ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ

Настоящий документ вступает в силу с момента официального опубликования.
Контроль за исполнением возлагается на соответствующие органы исполнительной власти.
            """.strip()
    
    def save_mock_crawl_data(self, source: str, documents: list) -> dict:
        """Save mock crawl data to filesystem"""
        
        # Create directories
        today = datetime.now().strftime('%Y-%m-%d')
        source_dir = self.base_dir / source / today
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Save documents
        saved_files = []
        
        for doc in documents:
            # Save PDF (mock)
            pdf_filename = f"{doc['file_uuid']}.pdf"
            pdf_path = source_dir / pdf_filename
            
            # Create mock PDF content (just text for demo)
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(f"MOCK PDF: {doc['content']}")
            
            # Save metadata
            meta_filename = f"{doc['file_uuid']}.meta.json"
            meta_path = source_dir / meta_filename
            
            metadata = {
                "document_info": {
                    "title": doc['title'],
                    "document_id": doc['id'],
                    "source": doc['source'],
                    "url": doc['url'],
                    "document_type": doc['document_type'],
                    "publication_date": doc['publication_date'],
                    "language": "ru"
                },
                "technical_info": {
                    "crawl_timestamp": datetime.now().isoformat(),
                    "content_hash": doc['file_uuid'],
                    "processing_status": "downloaded",
                    "files": [{
                        "url": doc['url'],
                        "path": f"{source}/{today}/{pdf_filename}",
                        "size": pdf_path.stat().st_size
                    }]
                },
                "crawler_info": {
                    "spider_name": source.replace('.', '_'),
                    "crawler_version": "1.0.0-demo",
                    "demo_mode": True
                }
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            saved_files.append({
                'pdf': str(pdf_path),
                'meta': str(meta_path),
                'doc': doc
            })
        
        return {
            'source': source,
            'count': len(documents),
            'directory': str(source_dir),
            'files': saved_files
        }
    
    def save_extracted_text(self, saved_files: list) -> int:
        """Save extracted text files"""
        
        self.ocr_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_count = 0
        
        for file_info in saved_files:
            doc = file_info['doc']
            
            # Save extracted text
            txt_filename = f"{doc['file_uuid']}.txt"
            txt_path = self.ocr_dir / txt_filename
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
            
            # Save extraction metadata
            extraction_meta = {
                'file_path': file_info['pdf'],
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_method': 'mock_demo',
                'success': True,
                'confidence': 1.0,
                'page_count': 1,
                'text_length': len(doc['content'])
            }
            
            meta_filename = f"{doc['file_uuid']}.extraction.json"
            meta_path = self.ocr_dir / meta_filename
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_meta, f, ensure_ascii=False, indent=2)
            
            extracted_count += 1
        
        return extracted_count
    
    def generate_crawl_report(self, results: dict) -> str:
        """Generate mock crawl report"""
        
        timestamp = datetime.now()
        
        report = {
            "crawl_summary": {
                "timestamp": timestamp.isoformat(),
                "total_spiders": 1,
                "successful_spiders": 1,
                "failed_spiders": 0,
                "success_rate": 1.0,
                "demo_mode": True
            },
            "spider_results": {
                results['source']: True
            },
            "file_statistics": {
                results['source']: {
                    "pdf_files": results['count'],
                    "meta_files": results['count'],
                    "total_size_mb": results['count'] * 0.1  # Mock size
                }
            },
            "total_documents": results['count'],
            "total_size_mb": results['count'] * 0.1
        }
        
        # Save report
        report_filename = f"crawl_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.base_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return str(report_path)
    
    def run_demo(self, source: str = "pravo.gov.ru", count: int = 10) -> dict:
        """Run complete offline crawler demo"""
        
        print(f"🎭 Legal AI Crawler Offline Demo")
        print(f"================================")
        print(f"Source: {source}")
        print(f"Documents: {count}")
        print()
        
        # Create mock documents
        print("📝 Generating mock legal documents...")
        documents = self.create_mock_documents(source, count)
        print(f"✅ Generated {len(documents)} documents")
        
        # Save crawl data
        print("\n💾 Saving crawl data...")
        crawl_results = self.save_mock_crawl_data(source, documents)
        print(f"✅ Saved to {crawl_results['directory']}")
        
        # Extract text
        print("\n📄 Extracting text...")
        extracted_count = self.save_extracted_text(crawl_results['files'])
        print(f"✅ Extracted text from {extracted_count} documents")
        
        # Generate report
        print("\n📊 Generating crawl report...")
        report_path = self.generate_crawl_report(crawl_results)
        print(f"✅ Report saved: {report_path}")
        
        # Final summary
        print(f"\n🎯 DEMO COMPLETE")
        print(f"================")
        print(f"📄 PDF files: {crawl_results['count']}")
        print(f"📋 Metadata files: {crawl_results['count']}")
        print(f"📝 Text files: {extracted_count}")
        print(f"📊 Total size: {crawl_results['count'] * 0.1:.1f} MB")
        print(f"💾 Data location: {crawl_results['directory']}")
        
        return {
            'success': True,
            'documents_generated': len(documents),
            'files_saved': crawl_results['count'] * 2,  # PDF + meta
            'text_extracted': extracted_count,
            'data_directory': crawl_results['directory'],
            'report_path': report_path
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Legal AI Crawler Offline Demo")
    parser.add_argument('source', choices=['pravo.gov.ru', 'kad.arbitr.ru', 'gibdd.ru'], 
                       default='pravo.gov.ru', nargs='?',
                       help='Source to simulate')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of documents to generate')
    
    args = parser.parse_args()
    
    demo = OfflineCrawlerDemo()
    results = demo.run_demo(args.source, args.count)
    
    if results['success']:
        print(f"\n✅ Demo completed successfully!")
        print(f"   Run 'make crawl-status' to see statistics")
        sys.exit(0)
    else:
        print(f"\n❌ Demo failed")
        sys.exit(1)


if __name__ == '__main__':
    main() 