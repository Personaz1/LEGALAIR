import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from PIL import Image
import base64
import io

from api.main import app

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://legal_user:legal_pass@localhost:5432/legal_ai_test"
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_image_base64():
    """Create a sample image encoded as base64 for testing."""
    # Create a simple white image
    img = Image.new('RGB', (100, 50), color='white')
    
    # Add some text-like patterns
    pixels = img.load()
    # Draw some simple text-like patterns
    for x in range(10, 90):
        for y in range(15, 35):
            if (x + y) % 3 == 0:
                pixels[x, y] = (0, 0, 0)  # Black pixels for text
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64

@pytest.fixture
def sample_russian_text():
    """Sample Russian text for testing classification and NER."""
    return """
    Вексель № 12345 от 15.12.2023
    
    Обязательство: Иванов И.И. обязуется выплатить ООО "Рога и Копыта" 
    сумму в размере 50000 рублей до 31 декабря 2023 года.
    
    Подпись должника: _________________
    Дата: 15.12.2023
    """

@pytest.fixture
def sample_fine_text():
    """Sample fine notice text for testing."""
    return """
    ПОСТАНОВЛЕНИЕ об административном правонарушении
    № АА-001234 от 10.11.2023
    
    Гражданин Петров Петр Петрович совершил административное правонарушение,
    предусмотренное статьей 12.9 КоАП РФ (превышение скорости).
    
    Назначить административный штраф в размере 5000 рублей.
    """

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def mock_ocr_service():
    """Mock OCR service for testing without EasyOCR dependencies."""
    class MockOCRService:
        async def extract_text(self, image, language="ru", confidence_threshold=0.8):
            return {
                "text": "Sample extracted text",
                "confidence": 0.95,
                "bbox_data": [
                    {
                        "text": "Sample",
                        "confidence": 0.95,
                        "bbox": [[10, 10], [60, 10], [60, 30], [10, 30]]
                    }
                ]
            }
        
        def get_model_info(self):
            return {
                "engine": "MockOCR",
                "languages": ["ru", "en"],
                "gpu_enabled": False,
                "version": "test"
            }
    
    return MockOCRService()

@pytest.fixture
def api_headers():
    """Standard headers for API requests."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    } 