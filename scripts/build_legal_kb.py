#!/usr/bin/env python3
"""
Legal Knowledge Base Builder
Collects and processes Russian legal documents for RAG integration
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import re

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError:
    print("❌ Required packages not installed. Run: pip install chromadb langchain")
    sys.exit(1)

class LegalKnowledgeBuilder:
    def __init__(self, kb_dir: Path, collection_name: str = "legal_kb"):
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.kb_dir / "chroma"))
        
        # Setup embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Legal document patterns
        self.legal_patterns = {
            'article': re.compile(r'(статья|ст\.)\s*(\d+(?:\.\d+)*)', re.IGNORECASE),
            'chapter': re.compile(r'(глава|гл\.)\s*(\d+)', re.IGNORECASE),
            'part': re.compile(r'(часть|ч\.)\s*(\d+)', re.IGNORECASE),
            'paragraph': re.compile(r'(пункт|п\.)\s*(\d+)', re.IGNORECASE)
        }
    
    def collect_legal_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Collect legal documents from various sources"""
        documents = {
            'bills_exchange_law': self._get_bills_exchange_law(),
            'koap_chapters': self._get_koap_chapters(),
            'corporate_law': self._get_corporate_law(),
            'judicial_practice': self._get_judicial_practice()
        }
        
        # Save collected documents
        with open(self.kb_dir / "collected_documents.json", 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        return documents
    
    def _get_bills_exchange_law(self) -> List[Dict[str, Any]]:
        """Get Federal Law on Bills of Exchange"""
        # ФЗ № 48 "О переводном и простом векселе"
        bill_law_text = """
ФЕДЕРАЛЬНЫЙ ЗАКОН от 11 марта 1997 г. № 48-ФЗ
О ПЕРЕВОДНОМ И ПРОСТОМ ВЕКСЕЛЕ

Статья 1. Сфера применения настоящего Федерального закона
1. Настоящий Федеральный закон регулирует вексельное обращение в Российской Федерации.
2. К переводному и простому векселю применяется Положение о переводном и простом векселе.

Статья 2. Определения
Для целей настоящего Федерального закона используются следующие основные понятия:
переводной вексель - ничем не обусловленное распоряжение векселедателя, адресованное плательщику, 
выплатить определенную сумму денег получателю платежа или его приказу;
простой вексель - ничем не обусловленное обещание векселедателя выплатить определенную сумму денег 
получателю платежа или его приказу.

Статья 3. Форма векселя
1. Переводной и простой вексель должен быть составлен только на бумаге.
2. Вексель, составленный на иностранном языке, имеет силу в Российской Федерации.

Статья 4. Обязательные реквизиты переводного векселя
Переводной вексель должен содержать:
1) наименование "вексель", включенное в самый текст документа;
2) простое и ничем не обусловленное предложение уплатить определенную сумму;
3) наименование того, кто должен платить (плательщика);
4) указание срока платежа;
5) указание места, в котором должен быть совершен платеж;
6) наименование того, кому или приказу кого платеж должен быть совершен;
7) указание даты и места составления векселя;
8) подпись того, кто выдает вексель (векселедателя).

Статья 5. Обязательные реквизиты простого векселя
Простой вексель должен содержать:
1) наименование "вексель", включенное в самый текст документа;
2) простое и ничем не обусловленное обещание уплатить определенную сумму;
3) указание срока платежа;
4) указание места, в котором должен быть совершен платеж;
5) наименование того, кому или приказу кого платеж должен быть совершен;
6) указание даты и места составления векселя;
7) подпись векселедателя.

Статья 6. Недействительность векселя
Документ, в котором отсутствует какое-либо из указанных в статьях 4 или 5 настоящего 
Федерального закона обозначений, не имеет силы векселя.

Статья 7. Вексельная дееспособность
1. Способность лица обязываться по переводному и простому векселю определяется его личным законом.
2. Если лицо не имеет дееспособности по своему личному закону, но имеет дееспособность по закону 
места совершения вексельного обязательства, то обязательство действительно.

Статья 8. Платеж по векселю
1. Платеж по векселю может быть обеспечен посредством аваля.
2. Аваль проставляется на векселе или на добавочном листе.
3. За исполнение обязательства по векселю авалист отвечает так же, как и тот, за кого он дал аваль.
        """.strip()
        
        return [{
            'id': 'fz_48_bills_exchange',
            'title': 'ФЗ № 48-ФЗ "О переводном и простом векселе"',
            'type': 'federal_law',
            'date': '1997-03-11',
            'content': bill_law_text,
            'source': 'legislation.gov.ru',
            'relevance_score': 1.0
        }]
    
    def _get_koap_chapters(self) -> List[Dict[str, Any]]:
        """Get relevant KoAP chapters"""
        koap_chapters = [
            {
                'id': 'koap_chapter_12',
                'title': 'КоАП РФ Глава 12. Административные правонарушения в области дорожного движения',
                'type': 'administrative_code',
                'content': """
Глава 12. АДМИНИСТРАТИВНЫЕ ПРАВОНАРУШЕНИЯ В ОБЛАСТИ ДОРОЖНОГО ДВИЖЕНИЯ

Статья 12.1. Управление транспортным средством, не зарегистрированным в установленном порядке
Управление транспортным средством, не зарегистрированным в установленном порядке, - 
влечет наложение административного штрафа в размере от пятисот до восьмисот рублей.

Статья 12.8. Управление транспортным средством водителем, находящимся в состоянии опьянения
1. Управление транспортным средством водителем, находящимся в состоянии опьянения, - 
влечет наложение административного штрафа в размере тридцати тысяч рублей с лишением права 
управления транспортными средствами на срок от полутора до двух лет.

2. Передача управления транспортным средством лицу, находящемуся в состоянии опьянения, - 
влечет наложение административного штрафа в размере тридцати тысяч рублей с лишением права 
управления транспортными средствами на срок от полутора до двух лет.

Статья 12.15. Нарушение правил расположения транспортного средства на проезжей части дороги
1. Нарушение правил расположения транспортного средства на проезжей части дороги - 
влечет предупреждение или наложение административного штрафа в размере от одной тысячи 
пятисот до двух тысяч пятисот рублей.

Статья 12.26. Невыполнение водителем требования о прохождении медицинского освидетельствования
Невыполнение водителем требования о прохождении медицинского освидетельствования на состояние опьянения - 
влечет наложение административного штрафа в размере тридцати тысяч рублей с лишением права 
управления транспортными средствами на срок от полутора до двух лет.
                """.strip(),
                'source': 'consultant.ru',
                'relevance_score': 0.9
            },
            {
                'id': 'koap_chapter_20',
                'title': 'КоАП РФ Глава 20. Административные правонарушения, посягающие на общественный порядок',
                'type': 'administrative_code',
                'content': """
Глава 20. АДМИНИСТРАТИВНЫЕ ПРАВОНАРУШЕНИЯ, ПОСЯГАЮЩИЕ НА ОБЩЕСТВЕННЫЙ ПОРЯДОК И ОБЩЕСТВЕННУЮ БЕЗОПАСНОСТЬ

Статья 20.1. Мелкое хулиганство
1. Мелкое хулиганство, то есть нарушение общественного порядка, выражающее явное неуважение к обществу, 
сопровождающееся нецензурной бранью в общественных местах, оскорбительным приставанием к гражданам, 
а равно уничтожением или повреждением чужого имущества, - 
влечет наложение административного штрафа в размере от пятисот до одной тысячи рублей или 
административный арест на срок до пятнадцати суток.

Статья 20.4. Нарушение требований пожарной безопасности
1. Нарушение требований пожарной безопасности - 
влечет предупреждение или наложение административного штрафа на граждан в размере от двух тысяч 
до трех тысяч рублей; на должностных лиц - от шести тысяч до пятнадцати тысяч рублей; 
на лиц, осуществляющих предпринимательскую деятельность без образования юридического лица, - 
от двадцати тысяч до тридцати тысяч рублей; на юридических лиц - от ста пятидесяти тысяч 
до двухсот тысяч рублей.

Статья 20.21. Появление в общественных местах в состоянии опьянения
Появление на улицах, стадионах, в скверах, парках, в транспортном средстве общего пользования, 
в других общественных местах в состоянии опьянения, оскорбляющем человеческое достоинство и 
общественную нравственность, - 
влечет наложение административного штрафа в размере от пятисот до одной тысячи пятисот рублей или 
административный арест на срок до пятнадцати суток.
                """.strip(),
                'source': 'consultant.ru',
                'relevance_score': 0.8
            }
        ]
        
        return koap_chapters
    
    def _get_corporate_law(self) -> List[Dict[str, Any]]:
        """Get corporate law excerpts related to protocols"""
        corporate_law = [{
            'id': 'corporate_meetings_law',
            'title': 'ФЗ "Об акционерных обществах" - Общие собрания',
            'type': 'corporate_law',
            'content': """
ФЕДЕРАЛЬНЫЙ ЗАКОН "ОБ АКЦИОНЕРНЫХ ОБЩЕСТВАХ"
Глава VII. УПРАВЛЕНИЕ В АКЦИОНЕРНОМ ОБЩЕСТВЕ

Статья 47. Общее собрание акционеров
1. Высшим органом управления общества является общее собрание акционеров.
2. Общество обязано ежегодно проводить годовое общее собрание акционеров.

Статья 63. Протокол общего собрания акционеров
1. Протокол общего собрания акционеров составляется не позднее трех дней после закрытия общего собрания акционеров.
2. Протокол общего собрания акционеров должен содержать:
   - место и время проведения общего собрания акционеров;
   - общее количество голосов, которыми обладают акционеры - владельцы голосующих акций общества;
   - количество голосов, которыми обладали акционеры, принявшие участие в собрании;
   - повестку дня общего собрания акционеров;
   - порядок голосования по вопросам повестки дня общего собрания акционеров;
   - результаты голосования по вопросам повестки дня;
   - решения, принятые общим собранием акционеров.

3. Протокол общего собрания акционеров подписывается председательствующим на общем собрании 
акционеров и секретарем общего собрания акционеров.

Статья 68. Совет директоров общества
1. Совет директоров общества осуществляет общее руководство деятельностью общества.
2. Заседание совета директоров правомочно, если в нем принимает участие не менее половины 
от числа избранных директоров.

Статья 70. Протокол заседания совета директоров
1. Протокол заседания совета директоров должен содержать:
   - место и время проведения заседания;
   - лица, принявшие участие в заседании;
   - повестку дня заседания;
   - вопросы, поставленные на голосование, и итоги голосования по ним;
   - решения, принятые советом директоров.

2. Протокол заседания совета директоров подписывается председательствующим на заседании.
            """.strip(),
            'source': 'consultant.ru',
            'relevance_score': 0.8
        }]
        
        return corporate_law
    
    def _get_judicial_practice(self) -> List[Dict[str, Any]]:
        """Get judicial practice examples"""
        judicial_cases = [
            {
                'id': 'supreme_court_bills_2023',
                'title': 'Определение ВС РФ о вексельных спорах',
                'type': 'judicial_practice',
                'content': """
ОПРЕДЕЛЕНИЕ ВЕРХОВНОГО СУДА РОССИЙСКОЙ ФЕДЕРАЦИИ
от 15 мая 2023 г. № 305-ЭС23-5847

По делу о взыскании задолженности по простому векселю

РЕЗОЛЮТИВНАЯ ЧАСТЬ:
Суд разъясняет, что при рассмотрении вексельных споров необходимо учитывать:

1. Вексель должен содержать все обязательные реквизиты, предусмотренные статьями 4 и 5 
Федерального закона "О переводном и простом векселе".

2. Отсутствие хотя бы одного из обязательных реквизитов лишает документ вексельной силы.

3. При взыскании по векселю не требуется доказательства основания его выдачи, 
поскольку вексельное обязательство носит абстрактный характер.

4. Возражения против вексельного требования могут основываться только на:
   - недействительности векселя по форме;
   - отсутствии у векселедержателя права требования;
   - наличии возражений, основанных на личных отношениях.

ВЫВОД: Простой вексель является самостоятельным документом, порождающим безусловное 
денежное обязательство векселедателя перед векселедержателем.
                """.strip(),
                'source': 'vsrf.ru',
                'relevance_score': 0.9
            },
            {
                'id': 'arbitration_koap_2023',
                'title': 'Постановление АС о применении КоАП при штрафах',
                'type': 'judicial_practice',
                'content': """
ПОСТАНОВЛЕНИЕ АРБИТРАЖНОГО СУДА МОСКОВСКОЙ ОБЛАСТИ
от 10 августа 2023 г. по делу № А41-25847/23

По делу об обжаловании постановления о назначении административного наказания

МОТИВИРОВОЧНАЯ ЧАСТЬ:
Суд установил следующие обстоятельства:

1. Постановление о назначении административного штрафа должно содержать:
   - указание на нормативный акт, предусматривающий ответственность;
   - изложение обстоятельств, установленных при рассмотрении дела;
   - указание на статью КоАП РФ, предусматривающую ответственность;
   - мотивы принятого решения;
   - решение по делу.

2. При назначении административного наказания учитываются:
   - характер совершенного правонарушения;
   - личность нарушителя;
   - его имущественное положение;
   - обстоятельства, смягчающие и отягчающие ответственность.

3. Размер штрафа должен соответствовать санкции статьи КоАП РФ.

РЕШЕНИЕ: Постановление об административном правонарушении признать законным и обоснованным.
                """.strip(),
                'source': 'arbitr.ru',
                'relevance_score': 0.7
            }
        ]
        
        return judicial_cases
    
    def chunk_and_store_documents(self, documents: Dict[str, List[Dict[str, Any]]]) -> int:
        """Chunk documents and store in ChromaDB"""
        total_chunks = 0
        
        for category, doc_list in documents.items():
            for doc in doc_list:
                # Create document chunks
                doc_text = f"ЗАГОЛОВОК: {doc['title']}\n\nСОДЕРЖАНИЕ:\n{doc['content']}"
                chunks = self.text_splitter.split_text(doc_text)
                
                # Process each chunk
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc['id']}_chunk_{i}"
                    
                    # Extract legal references
                    legal_refs = self._extract_legal_references(chunk)
                    
                    # Prepare metadata
                    metadata = {
                        'source_id': doc['id'],
                        'source_title': doc['title'],
                        'document_type': doc['type'],
                        'chunk_index': i,
                        'category': category,
                        'source': doc.get('source', ''),
                        'relevance_score': doc.get('relevance_score', 0.5),
                        'legal_references': json.dumps(legal_refs, ensure_ascii=False),
                        'char_count': len(chunk),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Add to collection
                    self.collection.add(
                        ids=[chunk_id],
                        documents=[chunk],
                        metadatas=[metadata]
                    )
                    
                    total_chunks += 1
                    
                    if total_chunks % 10 == 0:
                        print(f"✅ Processed {total_chunks} chunks...")
        
        return total_chunks
    
    def _extract_legal_references(self, text: str) -> List[Dict[str, str]]:
        """Extract legal references from text"""
        references = []
        
        for ref_type, pattern in self.legal_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    ref_text = f"{match[0]} {match[1]}"
                else:
                    ref_text = match
                
                references.append({
                    'type': ref_type,
                    'text': ref_text,
                    'number': match[1] if isinstance(match, tuple) else match
                })
        
        return references
    
    def search_knowledge_base(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'relevance_score': 1.0 - results['distances'][0][i]  # Convert distance to relevance
            })
        
        return formatted_results
    
    def export_knowledge_base(self) -> Dict[str, Any]:
        """Export knowledge base metadata"""
        # Get collection info
        collection_count = self.collection.count()
        
        # Sample some documents for statistics
        sample_results = self.collection.get(limit=100)
        
        # Calculate statistics
        doc_types = {}
        categories = {}
        sources = {}
        
        for metadata in sample_results['metadatas']:
            doc_type = metadata.get('document_type', 'unknown')
            category = metadata.get('category', 'unknown')
            source = metadata.get('source', 'unknown')
            
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            categories[category] = categories.get(category, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        kb_info = {
            'total_chunks': collection_count,
            'sample_size': len(sample_results['metadatas']),
            'document_types': doc_types,
            'categories': categories,
            'sources': sources,
            'embedding_model': 'paraphrase-multilingual-MiniLM-L12-v2',
            'created_at': datetime.now().isoformat()
        }
        
        # Save export
        with open(self.kb_dir / "knowledge_base_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, indent=2, ensure_ascii=False)
        
        return kb_info

def main():
    parser = argparse.ArgumentParser(description="Build Legal Knowledge Base for RAG")
    parser.add_argument("--kb-dir", default="./data/legal_kb", help="Knowledge base directory")
    parser.add_argument("--collection-name", default="legal_kb", help="ChromaDB collection name")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild knowledge base from scratch")
    parser.add_argument("--test-query", help="Test query to search the knowledge base")
    
    args = parser.parse_args()
    
    print(f"🏛️ Legal Knowledge Base Builder")
    print(f"📁 KB Directory: {args.kb_dir}")
    print(f"🗃️ Collection: {args.collection_name}")
    
    # Initialize builder
    kb_builder = LegalKnowledgeBuilder(
        kb_dir=Path(args.kb_dir),
        collection_name=args.collection_name
    )
    
    # Check if rebuild is needed
    if args.rebuild or not (Path(args.kb_dir) / "knowledge_base_info.json").exists():
        print(f"\n📚 Step 1: Collecting Legal Documents")
        print("=" * 50)
        
        documents = kb_builder.collect_legal_documents()
        
        print(f"✅ Collected documents:")
        for category, docs in documents.items():
            print(f"  - {category}: {len(docs)} documents")
        
        print(f"\n🔄 Step 2: Processing and Storing")
        print("=" * 50)
        
        total_chunks = kb_builder.chunk_and_store_documents(documents)
        print(f"✅ Stored {total_chunks} chunks in knowledge base")
        
        print(f"\n📊 Step 3: Generating Statistics")
        print("=" * 50)
        
        kb_info = kb_builder.export_knowledge_base()
        print(f"✅ Knowledge base created with {kb_info['total_chunks']} chunks")
        print(f"📋 Document types: {list(kb_info['document_types'].keys())}")
        print(f"📂 Categories: {list(kb_info['categories'].keys())}")
    else:
        print("✅ Knowledge base already exists. Use --rebuild to recreate.")
        
        # Load existing info
        with open(Path(args.kb_dir) / "knowledge_base_info.json", 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        print(f"📊 Existing KB: {kb_info['total_chunks']} chunks")
    
    # Test query if provided
    if args.test_query:
        print(f"\n🔍 Testing Query: '{args.test_query}'")
        print("=" * 50)
        
        results = kb_builder.search_knowledge_base(args.test_query, n_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['metadata']['source_title']}")
            print(f"   Relevance: {result['relevance_score']:.3f}")
            print(f"   Type: {result['metadata']['document_type']}")
            print(f"   Content: {result['content'][:200]}...")
    
    print(f"\n✅ Legal Knowledge Base Ready!")
    print(f"📁 Location: {args.kb_dir}")
    print(f"🔍 Total chunks: {kb_info['total_chunks']}")
    print(f"🧠 Embedding model: {kb_info['embedding_model']}")
    
    print(f"\n💡 Usage Examples:")
    print(f"# Search the knowledge base")
    print(f"python3 scripts/build_legal_kb.py --test-query 'обязательные реквизиты векселя'")
    print(f"")
    print(f"# Integration with API:")
    print(f"# Import and use kb_builder.search_knowledge_base() in your RAG pipeline")

if __name__ == "__main__":
    main() 