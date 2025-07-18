"""
Legal AI Platform - Custom Prometheus Metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Custom metrics for Legal AI platform
ocr_requests_total = Counter(
    'legal_ai_ocr_requests_total',
    'Total number of OCR requests',
    ['status', 'language']
)

ocr_processing_duration = Histogram(
    'legal_ai_ocr_processing_duration_seconds',
    'Time spent processing OCR requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

classification_requests_total = Counter(
    'legal_ai_classification_requests_total',
    'Total number of classification requests',
    ['document_type', 'status']
)

classification_confidence = Histogram(
    'legal_ai_classification_confidence',
    'Classification confidence scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

ner_requests_total = Counter(
    'legal_ai_ner_requests_total',
    'Total number of NER requests',
    ['status']
)

ner_entities_extracted = Counter(
    'legal_ai_ner_entities_extracted_total',
    'Total number of entities extracted',
    ['entity_type']
)

advisory_requests_total = Counter(
    'legal_ai_advisory_requests_total',
    'Total number of advisory requests',
    ['document_type', 'risk_level']
)

auth_login_attempts = Counter(
    'legal_ai_auth_login_attempts_total',
    'Total number of login attempts',
    ['status', 'role']
)

active_sessions = Gauge(
    'legal_ai_auth_active_sessions',
    'Number of active user sessions'
)

documents_processed_total = Counter(
    'legal_ai_documents_processed_total',
    'Total number of documents processed through full pipeline',
    ['document_type', 'processing_stage']
)

model_info = Info(
    'legal_ai_model_info',
    'Information about loaded models'
)

# Helper decorators for metrics
def track_ocr_metrics(func: Callable) -> Callable:
    """Decorator to track OCR metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        status = "success"
        language = kwargs.get('language', 'ru')
        
        try:
            result = await func(*args, **kwargs)
            if hasattr(result, 'success') and not result.success:
                status = "failed"
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            ocr_requests_total.labels(status=status, language=language).inc()
            ocr_processing_duration.observe(duration)
    
    return wrapper

def track_classification_metrics(func: Callable) -> Callable:
    """Decorator to track classification metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        status = "success"
        document_type = "unknown"
        
        try:
            result = await func(*args, **kwargs)
            if hasattr(result, 'document_type'):
                document_type = result.document_type
            if hasattr(result, 'confidence'):
                classification_confidence.observe(result.confidence)
            if hasattr(result, 'success') and not result.success:
                status = "failed"
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            classification_requests_total.labels(
                document_type=document_type,
                status=status
            ).inc()
    
    return wrapper

def track_ner_metrics(func: Callable) -> Callable:
    """Decorator to track NER metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        status = "success"
        
        try:
            result = await func(*args, **kwargs)
            if hasattr(result, 'entities'):
                for entity in result.entities:
                    if hasattr(entity, 'label'):
                        ner_entities_extracted.labels(entity_type=entity.label).inc()
            if hasattr(result, 'success') and not result.success:
                status = "failed"
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            ner_requests_total.labels(status=status).inc()
    
    return wrapper

def track_advisory_metrics(func: Callable) -> Callable:
    """Decorator to track advisory metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        document_type = "unknown"
        risk_level = "unknown"
        
        try:
            result = await func(*args, **kwargs)
            
            # Extract document type from request
            if args and hasattr(args[0], 'document_type'):
                document_type = args[0].document_type
            
            # Extract risk level from result
            if hasattr(result, 'analysis') and isinstance(result.analysis, dict):
                risk_level = result.analysis.get('risk_level', 'unknown')
            
            return result
        except Exception as e:
            raise
        finally:
            advisory_requests_total.labels(
                document_type=document_type,
                risk_level=risk_level
            ).inc()
    
    return wrapper

def track_auth_metrics(status: str, role: str = "unknown"):
    """Track authentication metrics"""
    auth_login_attempts.labels(status=status, role=role).inc()

def update_active_sessions(count: int):
    """Update active sessions gauge"""
    active_sessions.set(count)

def track_document_processing(document_type: str, stage: str):
    """Track document processing through pipeline"""
    documents_processed_total.labels(
        document_type=document_type,
        processing_stage=stage
    ).inc()

def set_model_info(model_name: str, version: str, framework: str):
    """Set model information"""
    model_info.info({
        'model_name': model_name,
        'version': version,
        'framework': framework
    })

# Initialize model info
set_model_info(
    model_name="Legal-AI-v1",
    version="1.0.0-preGPU",
    framework="FastAPI+spaCy+EasyOCR"
) 