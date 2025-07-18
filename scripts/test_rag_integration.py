#!/usr/bin/env python3
"""
RAG Integration Test Script
Tests RAG retrieval from legal knowledge base with relevant queries
"""

import sys
import argparse
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ ChromaDB not installed. Run: pip install chromadb")
    sys.exit(1)

def test_rag_retrieval(kb_dir: Path, query: str, top_k: int = 3):
    """Test RAG retrieval from legal knowledge base"""
    
    print(f"🔍 Testing RAG retrieval for: '{query}'")
    print(f"📍 Knowledge Base: {kb_dir}")
    
    # Initialize Chroma client
    chroma_dir = kb_dir / "chroma"
    if not chroma_dir.exists():
        print(f"❌ Chroma database not found at {chroma_dir}")
        return None
    
    client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get collection
    try:
        collection = client.get_collection("legal_knowledge")
        print(f"📚 Found collection with {collection.count()} documents")
    except Exception as e:
        print(f"❌ Error accessing collection: {e}")
        return None
    
    # Perform semantic search
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\n🎯 Found {len(results['documents'][0])} relevant chunks:")
        print("=" * 80)
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"\n📖 Result {i+1} (similarity: {1-distance:.3f})")
            print(f"📄 Document: {metadata['document_title']}")
            print(f"📝 Article: {metadata['article_number']} - {metadata['article_title']}")
            print(f"🏷️ Type: {metadata['document_type']}")
            print(f"📊 Chunk: {metadata['chunk_type']}")
            print("\n📃 Content:")
            print("-" * 60)
            print(doc[:400] + "..." if len(doc) > 400 else doc)
            print("-" * 60)
        
        return results
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Test RAG Integration")
    parser.add_argument("--kb-dir", default="data/legal_kb", help="Knowledge base directory")
    parser.add_argument("--query", default="обязательные реквизиты векселя", help="Search query")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to return")
    
    args = parser.parse_args()
    
    kb_dir = Path(args.kb_dir).absolute()
    
    if not kb_dir.exists():
        print(f"❌ Knowledge base directory not found: {kb_dir}")
        sys.exit(1)
    
    # Load KB info
    info_file = kb_dir / "knowledge_base_info.json"
    if info_file.exists():
        with open(info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        print(f"📊 Knowledge Base Info:")
        print(f"   📅 Created: {kb_info['created_at']}")
        print(f"   📄 Documents: {kb_info['total_documents']}")
        print(f"   🧩 Chunks: {kb_info['total_chunks']}")
        print(f"   📏 Chunk size: {kb_info['chunk_size']} chars")
    
    # Test queries
    test_queries = [
        args.query,
        "административный штраф за нарушение связи",
        "протест векселя и сроки предъявления",
        "персональные данные и защита информации"
    ]
    
    for query in test_queries:
        print("\n" + "="*100)
        results = test_rag_retrieval(kb_dir, query, args.top_k)
        
        if results:
            print(f"\n✅ RAG retrieval successful for: '{query}'")
        else:
            print(f"\n❌ RAG retrieval failed for: '{query}'")
    
    print("\n" + "="*100)
    print("🎉 RAG Integration Test Complete!")

if __name__ == "__main__":
    main() 