"""
RAG (Retrieval-Augmented Generation) Service
Integrates with legal knowledge base for context-aware advisory responses
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)

class LegalRAGService:
    """RAG service for legal knowledge base integration"""
    
    def __init__(self, kb_dir: str = "data/legal_kb"):
        self.kb_dir = Path(kb_dir)
        self.client = None
        self.collection = None
        self.status = "disabled"
        self.kb_info = {}
        
        if CHROMADB_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB connection and load knowledge base"""
        try:
            chroma_dir = self.kb_dir / "chroma"
            
            if not chroma_dir.exists():
                logger.warning(f"Knowledge base not found at {chroma_dir}")
                return
            
            # Initialize client
            self.client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get collection
            self.collection = self.client.get_collection("legal_knowledge")
            
            # Load KB info
            info_file = self.kb_dir / "knowledge_base_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    self.kb_info = json.load(f)
            
            self.status = "active"
            logger.info(f"RAG service initialized with {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            self.status = "error"
    
    def search_legal_knowledge(
        self, 
        query: str, 
        n_results: int = 3,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search legal knowledge base for relevant context"""
        
        if not self.is_available():
            return []
        
        try:
            # Build where clause for filtering
            where_clause = {}
            if document_type:
                where_clause["document_type"] = document_type
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
                where=where_clause if where_clause else None
            )
            
            # Format results
            legal_context = []
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                legal_context.append({
                    "content": doc,
                    "source_title": metadata.get("document_title", "Неизвестный документ"),
                    "article_number": metadata.get("article_number", "N/A"),
                    "article_title": metadata.get("article_title", "N/A"),
                    "document_type": metadata.get("document_type", "legal_document"),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                    "chunk_type": metadata.get("chunk_type", "article_part"),
                    "metadata": metadata
                })
            
            return legal_context
            
        except Exception as e:
            logger.error(f"Error searching legal knowledge: {e}")
            return []
    
    def enhance_advisory_response(
        self, 
        document_text: str, 
        document_type: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance advisory response with legal context"""
        
        if not self.is_available():
            return {
                "enhanced": False,
                "legal_context": [],
                "legal_references": [],
                "context_summary": "RAG сервис недоступен"
            }
        
        try:
            # Use query if provided, otherwise extract key terms from document
            base_query = query or self._extract_key_terms(document_text, document_type)
            
            # Enhanced query expansion for better context matching
            search_query = f"{base_query} {document_type or ''}".strip()
            
            # Search for relevant legal context
            legal_context = self.search_legal_knowledge(
                query=search_query,
                n_results=5,
                document_type=document_type
            )
            
            # Filter high-relevance results with improved threshold
            high_relevance_context = [
                ctx for ctx in legal_context 
                if ctx["relevance_score"] > 0.25  # Improved threshold for relevance
            ]
            
            # Generate legal references
            legal_references = []
            for ctx in high_relevance_context[:3]:  # Top 3 references
                legal_references.append({
                    "text": f"См. {ctx['source_title']}, статья {ctx['article_number']}",
                    "article": ctx['article_number'],
                    "title": ctx['article_title'],
                    "document": ctx['source_title']
                })
            
            # Create context summary
            context_summary = self._create_context_summary(high_relevance_context)
            
            return {
                "enhanced": len(high_relevance_context) > 0,
                "legal_context": high_relevance_context,
                "legal_references": legal_references,
                "context_summary": context_summary,
                "search_query": search_query
            }
            
        except Exception as e:
            logger.error(f"Error enhancing advisory response: {e}")
            return {
                "enhanced": False,
                "legal_context": [],
                "legal_references": [],
                "context_summary": f"Ошибка RAG сервиса: {str(e)}"
            }
    
    def _extract_key_terms(self, document_text: str, document_type: Optional[str] = None) -> str:
        """Extract key terms from document for search"""
        
        # Simple keyword extraction based on document type
        if document_type == "bill_of_exchange" or "вексель" in document_text.lower():
            return "вексель обязательные реквизиты платеж"
        elif document_type == "fine_notice" or "штраф" in document_text.lower():
            return "административный штраф КоАП нарушение"
        elif document_type == "protocol" or "протокол" in document_text.lower():
            return "протокол заседание решение"
        else:
            # Extract common legal terms
            legal_terms = []
            text_lower = document_text.lower()
            
            if "платеж" in text_lower:
                legal_terms.append("платеж")
            if "штраф" in text_lower:
                legal_terms.append("штраф")
            if "нарушение" in text_lower:
                legal_terms.append("нарушение")
            if "обязательство" in text_lower:
                legal_terms.append("обязательство")
            if "ответственность" in text_lower:
                legal_terms.append("ответственность")
            
            return " ".join(legal_terms) if legal_terms else "правовые вопросы"
    
    def _create_context_summary(self, legal_context: List[Dict[str, Any]]) -> str:
        """Create summary of legal context"""
        
        if not legal_context:
            return "Релевантный правовой контекст не найден"
        
        # Group by document type
        federal_laws = [ctx for ctx in legal_context if ctx["document_type"] == "federal_law"]
        admin_codes = [ctx for ctx in legal_context if ctx["document_type"] == "administrative_code"]
        
        summary_parts = []
        
        if federal_laws:
            summary_parts.append(f"Найдено {len(federal_laws)} релевантных статей федерального законодательства")
        
        if admin_codes:
            summary_parts.append(f"Найдено {len(admin_codes)} релевантных статей КоАП РФ")
        
        if not summary_parts:
            summary_parts.append(f"Найдено {len(legal_context)} релевантных правовых норм")
        
        return ". ".join(summary_parts) + "."
    
    def is_available(self) -> bool:
        """Check if RAG service is available"""
        return self.status == "active" and self.collection is not None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get RAG service status information"""
        
        status_info = {
            "status": self.status,
            "chromadb_available": CHROMADB_AVAILABLE,
            "kb_directory": str(self.kb_dir),
            "document_count": 0
        }
        
        if self.is_available():
            status_info.update({
                "document_count": self.collection.count(),
                "collection_name": self.collection.name,
                "embedding_model": "all-MiniLM-L6-v2",  # Default Chroma model
                "kb_info": self.kb_info
            })
        
        return status_info

# Global RAG service instance
_rag_service: Optional[LegalRAGService] = None

def get_rag_service() -> LegalRAGService:
    """Get global RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        _rag_service = LegalRAGService()
    
    return _rag_service

def search_legal_knowledge(query: str, n_results: int = 3, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convenience function for searching legal knowledge"""
    return get_rag_service().search_legal_knowledge(query, n_results, document_type)

def enhance_advisory_response(document_text: str, document_type: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for enhancing advisory responses"""
    return get_rag_service().enhance_advisory_response(document_text, document_type, query)

def get_rag_status() -> Dict[str, Any]:
    """Convenience function for getting RAG status"""
    return get_rag_service().get_service_status() 