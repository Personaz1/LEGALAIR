from fastapi import APIRouter, HTTPException, Depends
import structlog
import time
import re
from typing import Optional, List

from api.models.base import NERRequest, NERResponse, NEREntity, EntityType
from api.auth import current_annotator_user
from api.models.user import User

logger = structlog.get_logger()
router = APIRouter()

class NERService:
    """Placeholder service for Named Entity Recognition"""
    
    def __init__(self):
        self.model_loaded = False
        logger.info("NER service initialized (placeholder)")
    
    async def extract_entities(
        self, 
        text: str, 
        confidence_threshold: float = 0.7
    ) -> List[dict]:
        """
        Extract named entities from text
        
        This is a placeholder implementation using regex patterns.
        Will be replaced with trained spaCy model in Day 4.
        """
        entities = []
        
        # Simple regex patterns for common entity types
        patterns = {
            EntityType.DATE: [
                r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # DD.MM.YYYY
                r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4}',
            ],
            EntityType.MONEY: [
                r'\d+[\s,]?\d*\s*(руб|рублей|копеек|₽)',
                r'\d+[\s,]?\d*\s*(долларов|доллара|USD|\$)',
            ],
            EntityType.DOCUMENT_NUMBER: [
                r'№\s*\d+[\w\-\/]*',
                r'серия\s+\w+\s+№\s*\d+',
            ],
            EntityType.PERSON: [
                r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.',  # Фамилия И.О.
                r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+',  # Полное ФИО
            ],
            EntityType.ORGANIZATION: [
                r'ООО\s+"[^"]+"',
                r'ЗАО\s+"[^"]+"',
                r'ОАО\s+"[^"]+"',
                r'ИП\s+[А-ЯЁ][а-яё]+',
            ]
        }
        
        # Extract entities using patterns
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8  # Fixed confidence for regex matches
                    })
        
        # Filter by confidence threshold
        filtered_entities = [
            entity for entity in entities 
            if entity["confidence"] >= confidence_threshold
        ]
        
        # Remove duplicates and sort by position
        unique_entities = []
        seen_spans = set()
        
        for entity in sorted(filtered_entities, key=lambda x: x["start"]):
            span = (entity["start"], entity["end"])
            if span not in seen_spans:
                unique_entities.append(entity)
                seen_spans.add(span)
        
        return unique_entities

# Global service instance
_ner_service: Optional[NERService] = None

def get_ner_service() -> NERService:
    """Dependency to get NER service instance"""
    global _ner_service
    if _ner_service is None:
        _ner_service = NERService()
    return _ner_service

@router.post("/extract", response_model=NERResponse)
async def extract_entities(
    request: NERRequest,
    user: User = Depends(current_annotator_user),
    service: NERService = Depends(get_ner_service)
):
    """
    Extract named entities from text
    Requires annotator or admin role.
    
    - **text**: Text content for entity extraction
    - **confidence_threshold**: Minimum confidence for entity inclusion
    
    Note: Currently using regex patterns. Will be replaced with spaCy in Day 4.
    """
    try:
        start_time = time.time()
        
        # Validate input
        if len(request.text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Text too short for entity extraction (minimum 10 characters)"
            )
        
        # Extract entities
        raw_entities = await service.extract_entities(
            text=request.text,
            confidence_threshold=request.confidence_threshold
        )
        
        # Convert to Pydantic models
        entities = [
            NEREntity(
                text=entity["text"],
                label=entity["label"],
                start=entity["start"],
                end=entity["end"],
                confidence=entity["confidence"]
            )
            for entity in raw_entities
        ]
        
        processing_time = time.time() - start_time
        
        logger.info(
            "NER extraction completed",
            entity_count=len(entities),
            processing_time=processing_time
        )
        
        return NERResponse(
            entities=entities,
            processing_time=processing_time,
            entity_count=len(entities)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("NER extraction failed", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"NER extraction failed: {str(e)}"
        )

@router.get("/health")
async def ner_health_check():
    """Check NER service health"""
    try:
        global _ner_service
        if _ner_service is None:
            return {"status": "not_initialized", "ready": False}
        
        return {
            "status": "healthy",
            "ready": True,
            "model_type": "regex_placeholder",
            "supported_entities": [e.value for e in EntityType],
            "note": "Will be replaced with spaCy model in Day 4"
        }
    except Exception as e:
        logger.error("NER health check failed", exc_info=e)
        return {"status": "unhealthy", "ready": False, "error": str(e)} 