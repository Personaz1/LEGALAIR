#!/usr/bin/env python3
"""
Enhanced Legal Knowledge Base Builder
Builds RAG corpus with ФЗ-48 and КоАП articles for context-aware legal advisory
"""

import argparse
import os
import sys
from pathlib import Path
import json
from typing import List, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import chromadb
    from chromadb.config import Settings
    import hashlib
    import re
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install chromadb")
    sys.exit(1)

def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks with metadata"""
    
    # Split by articles first (preserving structure)
    article_pattern = r'Статья \d+\..+?(?=Статья \d+\.|$)'
    articles = re.findall(article_pattern, text, re.DOTALL)
    
    chunks = []
    chunk_id = 0
    
    for article in articles:
        article_lines = article.strip().split('\n')
        if not article_lines:
            continue
            
        # Extract article number and title
        first_line = article_lines[0].strip()
        article_match = re.match(r'Статья (\d+(?:\.\d+)?)\.\s*(.+)', first_line)
        
        if article_match:
            article_num = article_match.group(1)
            article_title = article_match.group(2)
        else:
            article_num = f"unknown_{chunk_id}"
            article_title = "Без названия"
        
        # For longer articles, create sub-chunks
        article_text = '\n'.join(article_lines)
        
        if len(article_text) <= chunk_size:
            # Single chunk for small articles
            chunks.append({
                "id": f"article_{article_num}",
                "text": article_text,
                "metadata": {
                    "article_number": article_num,
                    "article_title": article_title,
                    "chunk_type": "full_article",
                    "char_count": len(article_text)
                }
            })
        else:
            # Split large articles into sub-chunks
            words = article_text.split()
            sub_chunk_words = chunk_size // 6  # Approximate words per chunk
            overlap_words = chunk_overlap // 6
            
            for i in range(0, len(words), sub_chunk_words - overlap_words):
                chunk_words = words[i:i + sub_chunk_words]
                sub_chunk_text = ' '.join(chunk_words)
                
                chunks.append({
                    "id": f"article_{article_num}_part_{i // (sub_chunk_words - overlap_words) + 1}",
                    "text": sub_chunk_text,
                    "metadata": {
                        "article_number": article_num,
                        "article_title": article_title,
                        "chunk_type": "article_part",
                        "part_number": i // (sub_chunk_words - overlap_words) + 1,
                        "char_count": len(sub_chunk_text)
                    }
                })
        
        chunk_id += 1
    
    return chunks

def build_knowledge_base(
    kb_dir: Path,
    sources: List[str],
    chunk_size: int = 512,
    chunk_overlap: int = 64
) -> Dict[str, Any]:
    """Build legal knowledge base with Chroma DB"""
    
    print(f"🏗️ Building Legal Knowledge Base in {kb_dir}")
    
    # Create directories
    kb_dir.mkdir(parents=True, exist_ok=True)
    chroma_dir = kb_dir / "chroma"
    
    # Initialize Chroma client
    client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Create or get collection
    collection_name = "legal_knowledge"
    try:
        collection = client.get_collection(collection_name)
        print(f"📚 Found existing collection: {collection_name}")
        client.delete_collection(collection_name)  # Reset for clean build
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Russian Legal Knowledge Base for RAG"}
    )
    
    # Process each source document
    all_chunks = []
    document_info = {}
    
    for source_file in sources:
        source_path = Path(source_file)
        if not source_path.exists():
            print(f"⚠️ Source file not found: {source_path}")
            continue
        
        print(f"📖 Processing: {source_path.name}")
        
        # Read document
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract document metadata
        doc_id = source_path.stem
        if "fz48" in doc_id.lower():
            doc_type = "federal_law"
            doc_title = "ФЗ-48 О переводном и простом векселе"
        elif "koap" in doc_id.lower():
            doc_type = "administrative_code"
            doc_title = "КоАП РФ Глава 13"
        else:
            doc_type = "legal_document"
            doc_title = doc_id
        
        # Chunk the document
        chunks = chunk_text(content, chunk_size, chunk_overlap)
        
        # Add document metadata to chunks
        for chunk in chunks:
            chunk["metadata"].update({
                "document_id": doc_id,
                "document_type": doc_type,
                "document_title": doc_title,
                "source_file": source_path.name
            })
        
        all_chunks.extend(chunks)
        document_info[doc_id] = {
            "title": doc_title,
            "type": doc_type,
            "chunks_count": len(chunks),
            "source_file": source_path.name,
            "total_chars": len(content)
        }
        
        print(f"  ✅ Created {len(chunks)} chunks")
    
    # Add to Chroma collection
    if all_chunks:
        print(f"🔄 Adding {len(all_chunks)} chunks to vector database...")
        
        ids = [chunk["id"] for chunk in all_chunks]
        documents = [chunk["text"] for chunk in all_chunks]
        metadatas = [chunk["metadata"] for chunk in all_chunks]
        
        # Add in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            
            print(f"  📦 Batch {i//batch_size + 1}: {len(batch_ids)} chunks added")
    
    # Save knowledge base info
    kb_info = {
        "created_at": datetime.now().isoformat(),
        "total_documents": len(document_info),
        "total_chunks": len(all_chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "collection_name": collection_name,
        "documents": document_info
    }
    
    info_file = kb_dir / "knowledge_base_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(kb_info, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Knowledge Base built successfully!")
    print(f"📊 Total: {len(all_chunks)} chunks from {len(document_info)} documents")
    print(f"💾 Saved to: {kb_dir}")
    
    return kb_info

def main():
    parser = argparse.ArgumentParser(description="Build Legal Knowledge Base for RAG")
    parser.add_argument("--kb-dir", default="data/legal_kb", help="Knowledge base directory")
    parser.add_argument("--sources", nargs="+", 
                       default=["data/legal_sources/fz48_veksel.txt", "data/legal_sources/koap_chapter13.txt"],
                       help="Source legal documents")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, default=64, help="Chunk overlap in characters")
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    kb_dir = Path(args.kb_dir).absolute()
    sources = [Path(s).absolute() for s in args.sources]
    
    # Validate sources exist
    missing_sources = [s for s in sources if not s.exists()]
    if missing_sources:
        print(f"❌ Missing source files:")
        for s in missing_sources:
            print(f"   {s}")
        sys.exit(1)
    
    try:
        kb_info = build_knowledge_base(
            kb_dir=kb_dir,
            sources=sources,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        print(f"\n🎉 Legal Knowledge Base ready for RAG integration!")
        print(f"📍 Location: {kb_dir}")
        print(f"🔗 Collection: {kb_info['collection_name']}")
        
    except Exception as e:
        print(f"❌ Error building knowledge base: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 