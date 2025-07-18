import easyocr
import numpy as np
from PIL import Image
import cv2
import structlog
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()

class OCRService:
    """EasyOCR service for text extraction from legal documents"""
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR service
        
        Args:
            languages: List of language codes (default: ['ru', 'en'])
        """
        self.languages = languages or ['ru', 'en']
        self.reader = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialize EasyOCR reader"""
        try:
            logger.info("Initializing EasyOCR reader", languages=self.languages)
            self.reader = easyocr.Reader(
                self.languages,
                gpu=False,  # CPU-only for now
                verbose=False
            )
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize EasyOCR reader", exc_info=e)
            raise
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image as numpy array
        """
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        
        # Convert RGB to BGR if needed
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale for better text recognition
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array
        
        # Apply adaptive thresholding for better contrast
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise removal with morphological operations
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        return processed
    
    def _extract_text_sync(
        self, 
        image: Image.Image, 
        language: str, 
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """
        Synchronous text extraction (to be called in executor)
        
        Args:
            image: PIL Image object
            language: Language code for OCR
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Preprocess image
            processed_img = self._preprocess_image(image)
            
            # Perform OCR
            results = self.reader.readtext(
                processed_img,
                paragraph=True,  # Group text into paragraphs
                width_ths=0.7,   # Text width threshold
                height_ths=0.7,  # Text height threshold
                detail=1         # Return detailed results with bounding boxes
            )
            
            # Filter results by confidence threshold
            filtered_results = [
                result for result in results 
                if result[2] >= confidence_threshold
            ]
            
            if not filtered_results:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "bbox_data": []
                }
            
            # Extract text and calculate average confidence
            texts = [result[1] for result in filtered_results]
            confidences = [result[2] for result in filtered_results]
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences)
            
            # Prepare bounding box data
            bbox_data = [
                {
                    "text": result[1],
                    "confidence": result[2],
                    "bbox": result[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                }
                for result in filtered_results
            ]
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "bbox_data": bbox_data
            }
            
        except Exception as e:
            logger.error("OCR extraction failed", exc_info=e)
            return {
                "text": "",
                "confidence": 0.0,
                "bbox_data": [],
                "error": str(e)
            }
    
    async def extract_text(
        self, 
        image: Image.Image, 
        language: str = "ru", 
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Extract text from image asynchronously
        
        Args:
            image: PIL Image object
            language: Language code for OCR
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if self.reader is None:
            raise RuntimeError("OCR reader not initialized")
        
        # Validate language
        if language not in self.languages:
            logger.warning(
                "Unsupported language requested", 
                requested=language, 
                supported=self.languages
            )
            language = "ru"  # Fallback to Russian
        
        # Run OCR in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._extract_text_sync,
            image,
            language,
            confidence_threshold
        )
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded OCR model"""
        return {
            "engine": "EasyOCR",
            "languages": self.languages,
            "gpu_enabled": False,
            "version": easyocr.__version__ if hasattr(easyocr, '__version__') else "unknown"
        }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 