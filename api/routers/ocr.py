from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import base64
import io
from PIL import Image
import structlog
import time
from typing import Optional

from api.models.base import OCRRequest, OCRResponse, ErrorResponse
from ml.ocr_service import OCRService
from api.auth import current_annotator_user
from api.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# Global OCR service instance (will be initialized on first use)
_ocr_service: Optional[OCRService] = None

def get_ocr_service() -> OCRService:
    """Dependency to get OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        logger.info("Initializing OCR service...")
        _ocr_service = OCRService()
        logger.info("OCR service initialized")
    return _ocr_service

@router.post("/extract", response_model=OCRResponse)
async def extract_text(
    request: OCRRequest,
    user: User = Depends(current_annotator_user),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Extract text from image using EasyOCR
    Requires annotator or admin role.
    
    - **image_base64**: Base64 encoded image (JPEG, PNG)
    - **language**: OCR language code (default: 'ru')
    - **confidence_threshold**: Minimum confidence for text extraction
    """
    try:
        start_time = time.time()
        
        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_base64)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error("Failed to decode image", error=str(e))
            raise HTTPException(
                status_code=400,
                detail="Invalid image format or encoding"
            )
        
        # Extract text using OCR service
        ocr_result = await ocr_service.extract_text(
            image=image,
            language=request.language,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "OCR completed",
            text_length=len(ocr_result["text"]),
            confidence=ocr_result["confidence"],
            processing_time=processing_time
        )
        
        return OCRResponse(
            text=ocr_result["text"],
            confidence=ocr_result["confidence"],
            processing_time=processing_time,
            word_count=len(ocr_result["text"].split()),
            character_count=len(ocr_result["text"]),
            bbox_data=ocr_result.get("bbox_data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OCR processing failed", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )

@router.get("/health")
async def ocr_health_check():
    """Check OCR service health"""
    try:
        global _ocr_service
        if _ocr_service is None:
            return {"status": "not_initialized", "ready": False}
        
        # Simple health check - could be extended with actual model test
        return {
            "status": "healthy",
            "ready": True,
            "supported_languages": ["ru", "en"],
            "model_info": _ocr_service.get_model_info()
        }
    except Exception as e:
        logger.error("OCR health check failed", exc_info=e)
        return {"status": "unhealthy", "ready": False, "error": str(e)} 