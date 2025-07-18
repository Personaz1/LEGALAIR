from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    BILL_OF_EXCHANGE = "bill_of_exchange"  # вексель
    FINE_NOTICE = "fine_notice"           # штраф
    PROTOCOL = "protocol"                 # протокол
    UNKNOWN = "unknown"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OCRRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image")
    language: str = Field(default="ru", description="OCR language code")
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

class OCRResponse(BaseModel):
    text: str
    confidence: float
    processing_time: float
    word_count: int
    character_count: int
    bbox_data: Optional[List[Dict]] = None

class ClassificationRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to classify")
    top_k: int = Field(default=3, ge=1, le=5)

class ClassificationResponse(BaseModel):
    document_type: DocumentType
    confidence: float
    predictions: List[Dict[str, float]]
    processing_time: float

class EntityType(str, Enum):
    PERSON = "PERSON"           # Физическое лицо
    ORGANIZATION = "ORG"        # Организация
    DATE = "DATE"               # Дата
    MONEY = "MONEY"             # Денежная сумма
    LOCATION = "LOC"            # Местоположение
    DOCUMENT_NUMBER = "DOC_NUM" # Номер документа
    LEGAL_BASIS = "LEGAL_BASIS" # Правовое основание

class NEREntity(BaseModel):
    text: str
    label: EntityType
    start: int
    end: int
    confidence: float

class NERRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text for entity extraction")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class NERResponse(BaseModel):
    entities: List[NEREntity]
    processing_time: float
    entity_count: int

class DocumentAnalysisRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded document image")
    analysis_type: str = Field(default="full", pattern="^(ocr_only|classify_only|full)$")
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    status: ProcessingStatus
    ocr_result: Optional[OCRResponse] = None
    classification_result: Optional[ClassificationResponse] = None
    ner_result: Optional[NERResponse] = None
    total_processing_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 