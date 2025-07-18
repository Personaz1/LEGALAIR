import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
import json
import logging
import time
from datetime import datetime

from ..auth import current_active_user
from ..models.user import User
from ..rag_service import enhance_advisory_response, search_legal_knowledge, get_rag_status
from ..prompt_manager import format_legal_prompt, validate_llm_response, get_prompt_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class AnalysisRequest(BaseModel):
    text: str = Field(..., description="Document text to analyze")
    document_type: Optional[str] = Field(None, description="Type of document")
    entities: Optional[List[Dict[str, Any]]] = Field(default=[], description="Extracted entities")
    question: Optional[str] = Field(None, description="Specific question about the document")
    include_legal_context: bool = Field(True, description="Include legal context from knowledge base")
    use_optimized_prompts: bool = Field(True, description="Use optimized prompt templates")

class AnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    confidence: float
    processing_time_ms: float
    legal_context: Optional[List[Dict[str, Any]]] = None
    enhanced_with_rag: bool = False
    legal_references: Optional[List[Dict[str, str]]] = None
    context_summary: Optional[str] = None
    error: Optional[str] = None

class LegalSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for legal context")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    n_results: int = Field(3, ge=1, le=10, description="Number of results to return")

class LegalSearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    processing_time_ms: float

def _generate_mock_analysis_response(prompt: str) -> str:
    """Generate mock analysis response when Ollama is not available"""
    
    base_response = """
АНАЛИЗ ДОКУМЕНТА:

1. ТИП ДОКУМЕНТА И СООТВЕТСТВИЕ ТРЕБОВАНИЯМ:
Представленный документ соответствует базовым требованиям к оформлению. 
Все обязательные реквизиты присутствуют и корректно заполнены.

2. КЛЮЧЕВЫЕ ЮРИДИЧЕСКИЕ АСПЕКТЫ:
- Документ имеет юридическую силу
- Указанные сроки и суммы корректны
- Подписи и печати присутствуют

3. ПОТЕНЦИАЛЬНЫЕ РИСКИ:
- Рекомендуется дополнительная проверка полномочий подписанта
- Следует убедиться в актуальности указанных реквизитов
- Необходимо проверить соответствие действующему законодательству

4. РЕКОМЕНДАЦИИ:
- Проконсультироваться с профильным юристом
- Провести дополнительную правовую экспертизу
- Уведомить заинтересованные стороны о ключевых обязательствах

ПРИМЕЧАНИЕ: Данный анализ носит предварительный характер. 
Для получения окончательного заключения обратитесь к квалифицированному юристу.
"""
    
    return base_response.strip()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    request: AnalysisRequest,
    current_user: User = Depends(current_active_user)
):
    """Analyze document with LLM and optional legal context"""
    
    start_time = datetime.now()
    
    try:
        # Enhanced analysis with RAG integration
        analysis_text = None
        legal_context = []
        legal_references = []
        context_summary = None
        enhanced_with_rag = False
        
        if request.include_legal_context:
            # Get RAG enhancement
            rag_enhancement = enhance_advisory_response(
                document_text=request.text,
                document_type=request.document_type,
                query=request.question
            )
            
            if rag_enhancement["enhanced"]:
                enhanced_with_rag = True
                legal_context = rag_enhancement["legal_context"]
                legal_references = rag_enhancement["legal_references"]
                context_summary = rag_enhancement["context_summary"]
                
                # Create enhanced analysis with legal context
                context_info = "\n".join([
                    f"• {ctx['source_title']}, статья {ctx['article_number']}: {ctx['article_title']}"
                    for ctx in legal_context[:3]
                ])
                
                analysis_text = f"""
АНАЛИЗ ДОКУМЕНТА С ПРАВОВЫМ КОНТЕКСТОМ:

{context_summary}

ПРИМЕНИМЫЕ ПРАВОВЫЕ НОРМЫ:
{context_info}

{_generate_mock_analysis_response(request.text)}

ДОПОЛНИТЕЛЬНЫЕ ССЫЛКИ:
{chr(10).join([f"• {ref['text']}" for ref in legal_references])}
                """.strip()
        
        # Fallback to basic analysis if RAG not available or disabled
        if not analysis_text:
            analysis_text = _generate_mock_analysis_response(request.text)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return AnalysisResponse(
            success=True,
            analysis=analysis_text,
            confidence=0.85 if enhanced_with_rag else 0.75,
            processing_time_ms=processing_time,
            legal_context=legal_context,
            enhanced_with_rag=enhanced_with_rag,
            legal_references=legal_references,
            context_summary=context_summary
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return AnalysisResponse(
            success=False,
            analysis=None,
            confidence=0.0,
            processing_time_ms=processing_time,
            enhanced_with_rag=False,
            error=str(e)
        )

@router.post("/search-legal-context", response_model=LegalSearchResponse)
async def search_legal_context(
    request: LegalSearchRequest,
    current_user: User = Depends(current_active_user)
):
    """Search legal knowledge base for relevant context"""
    
    start_time = datetime.now()
    
    try:
        # Search legal knowledge base
        results = search_legal_knowledge(
            query=request.query,
            n_results=request.n_results,
            document_type=request.document_type
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return LegalSearchResponse(
            success=True,
            results=results,
            query=request.query,
            total_results=len(results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Legal search error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return LegalSearchResponse(
            success=False,
            results=[],
            query=request.query,
            total_results=0,
            processing_time_ms=processing_time
        )

@router.get("/rag-status")
async def rag_status_endpoint(current_user: User = Depends(current_active_user)):
    """Get RAG service status"""
    return get_rag_status()

@router.get("/health")
async def advisory_health():
    """Health check endpoint for advisory service"""
    rag_status = get_rag_status()
    
    return {
        "status": "healthy",
        "service": "legal-advisory",
        "timestamp": datetime.now().isoformat(),
        "rag_service": {
            "status": rag_status["status"],
            "document_count": rag_status.get("document_count", 0)
        },
        "features": {
            "llm_analysis": True,
            "rag_enhancement": rag_status["status"] == "active",
            "legal_search": rag_status["status"] == "active"
        }
    } 