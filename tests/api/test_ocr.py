import pytest
from unittest.mock import patch, AsyncMock

class TestOCREndpoints:
    """Test OCR API endpoints."""
    
    def test_ocr_health_check(self, client):
        """Test OCR health check endpoint."""
        response = client.get("/api/v1/ocr/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "ready" in data

    @patch('api.routers.ocr.get_ocr_service')
    def test_extract_text_success(self, mock_get_service, client, sample_image_base64, mock_ocr_service):
        """Test successful text extraction."""
        mock_get_service.return_value = mock_ocr_service
        
        payload = {
            "image_base64": sample_image_base64,
            "language": "ru",
            "confidence_threshold": 0.8
        }
        
        response = client.post("/api/v1/ocr/extract", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "text" in data
        assert "confidence" in data
        assert "processing_time" in data
        assert "word_count" in data
        assert "character_count" in data

    def test_extract_text_invalid_base64(self, client):
        """Test OCR with invalid base64 image."""
        payload = {
            "image_base64": "invalid_base64_string",
            "language": "ru",
            "confidence_threshold": 0.8
        }
        
        response = client.post("/api/v1/ocr/extract", json=payload)
        assert response.status_code == 400
        assert "Invalid image format" in response.json()["detail"]

    def test_extract_text_missing_image(self, client):
        """Test OCR with missing image data."""
        payload = {
            "language": "ru",
            "confidence_threshold": 0.8
        }
        
        response = client.post("/api/v1/ocr/extract", json=payload)
        assert response.status_code == 422  # Validation error

    def test_extract_text_invalid_confidence(self, client, sample_image_base64):
        """Test OCR with invalid confidence threshold."""
        payload = {
            "image_base64": sample_image_base64,
            "language": "ru",
            "confidence_threshold": 1.5  # Invalid: > 1.0
        }
        
        response = client.post("/api/v1/ocr/extract", json=payload)
        assert response.status_code == 422  # Validation error

    @patch('api.routers.ocr.get_ocr_service')
    def test_extract_text_service_error(self, mock_get_service, client, sample_image_base64):
        """Test OCR service error handling."""
        # Mock service that raises an exception
        mock_service = AsyncMock()
        mock_service.extract_text.side_effect = Exception("OCR service error")
        mock_get_service.return_value = mock_service
        
        payload = {
            "image_base64": sample_image_base64,
            "language": "ru",
            "confidence_threshold": 0.8
        }
        
        response = client.post("/api/v1/ocr/extract", json=payload)
        assert response.status_code == 500
        assert "OCR processing failed" in response.json()["detail"] 