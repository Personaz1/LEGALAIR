#!/usr/bin/env python3
"""
Locust Load Testing for Legal AI API
Stress test OCR, Classification, and full pipeline with correct endpoints and auth
"""

import random
import base64
import json
import time
from io import BytesIO
from pathlib import Path
from locust import HttpUser, task, between, events
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Test data pools
RUSSIAN_NAMES = [
    "Иванов Иван Иванович", "Петров Петр Петрович", "Сидоров Сергей Сергеевич",
    "Козлова Мария Александровна", "Смирнов Алексей Викторович"
]

ORGANIZATIONS = [
    'ООО "Тест-Компания"', 'ЗАО "Бета-Тех"', 'ПАО "Гамма-Инвест"'
]

class LegalAIUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.client.verify = False  # Disable SSL verification for local testing
        self.test_images = []
        self.test_texts = []
        
        # Generate test data
        self._generate_test_data()
    
    def _generate_test_data(self):
        """Generate synthetic test images and texts"""
        # Generate test images (synthetic document-like images)
        for i in range(5):
            # Create document-like image
            img = Image.new('RGB', (800, 600), 'white')
            draw = ImageDraw.Draw(img)
            
            # Add some text-like content
            y_pos = 50
            for line in range(15):
                # Random text line
                width = random.randint(200, 600)
                height = random.randint(10, 20)
                x_pos = random.randint(20, 50)
                
                draw.rectangle([x_pos, y_pos, x_pos + width, y_pos + height], 
                              fill='black')
                y_pos += random.randint(25, 40)
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            self.test_images.append(img_b64)
        
        # Generate test texts (legal document content)
        self.test_texts = [
            f"""ВЕКСЕЛЬ №{random.randint(100000, 999999)}
            
Дата: {random.randint(1, 28)}.{random.randint(1, 12)}.2024

Обязательство: {random.choice(RUSSIAN_NAMES)} обязуется выплатить {random.choice(ORGANIZATIONS)}
сумму в размере {random.randint(10000, 500000)} рублей до {random.randint(1, 28)}.{random.randint(1, 12)}.2024.

Основание: Договор поставки товара

Должник: {random.choice(RUSSIAN_NAMES)}
Паспорт: {random.randint(1000, 9999)} {random.randint(100000, 999999)}

Подпись должника: _________________""",
            
            f"""ПОСТАНОВЛЕНИЕ об административном правонарушении
№ {random.randint(100000, 999999)} от {random.randint(1, 28)}.{random.randint(1, 12)}.2024

Гражданин {random.choice(RUSSIAN_NAMES)} совершил административное правонарушение,
предусмотренное статьей 12.9 КоАП РФ (превышение скорости).

Место нарушения: г. Москва, ул. Тверская
Время нарушения: {random.randint(8, 22)}:{random.randint(10, 59):02d}

Назначить административный штраф в размере {random.randint(500, 5000)} рублей.""",
            
            f"""ПРОТОКОЛ заседания
№ {random.randint(1, 100)} от {random.randint(1, 28)}.{random.randint(1, 12)}.2024

Организация: {random.choice(ORGANIZATIONS)}
Тип заседания: Совет директоров

Председатель: {random.choice(RUSSIAN_NAMES)}
Секретарь: {random.choice(RUSSIAN_NAMES)}

ПОВЕСТКА ДНЯ:
1. Утверждение годового отчета
2. Распределение прибыли

РЕШЕНИЕ:
Утвердить предложенные изменения."""
        ]
    
    @task(3)
    def test_health_endpoint(self):
        """Test health endpoint (no auth required)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("Health check returned non-healthy status")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Health check failed: {response.status_code}")

class AuthenticatedLegalAIUser(LegalAIUser):
    """User that authenticates before making requests"""
    
    def on_start(self):
        """Login before starting load test"""
        super().on_start()
        self.auth_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate and get JWT token"""
        # Create unique test user for this instance
        user_email = f"loadtest_{random.randint(10000, 99999)}@example.com"
        user_password = "loadtest123"
        
        # Try to register user
        register_payload = {
            "email": user_email,
            "password": user_password,
            "role": "user"
        }
        
        register_response = self.client.post("/api/v1/auth/register", json=register_payload)
        
        # Login to get token (whether registration succeeded or failed)
        login_data = {
            "username": user_email,
            "password": user_password
        }
        
        login_response = self.client.post("/api/v1/auth/jwt/login", data=login_data)
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            self.auth_token = token_data.get("access_token")
            if self.auth_token:
                self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print(f"✅ Authenticated user: {user_email}")
            else:
                print("⚠️ Login successful but no token received")
        else:
            print(f"⚠️ Authentication failed: {login_response.status_code}")
    
    @task(2)
    def test_ocr_endpoint(self):
        """Test OCR endpoint with synthetic image"""
        if not self.test_images or not self.auth_token:
            return
        
        image_b64 = random.choice(self.test_images)
        
        payload = {
            "image_base64": image_b64,
            "language": "ru",
            "confidence_threshold": 0.7
        }
        
        with self.client.post("/api/v1/ocr/extract", 
                            json=payload, 
                            catch_response=True,
                            timeout=30) as response:
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("text"):
                        response.success()
                    else:
                        response.failure("OCR returned no text")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"OCR failed: {response.status_code}")
    
    @task(2)
    def test_classification_endpoint(self):
        """Test classification endpoint with correct path"""
        if not self.auth_token:
            return
            
        text = random.choice(self.test_texts)
        
        payload = {
            "text": text,
            "include_sections": True,
            "include_fields": True,
            "confidence_threshold": 0.5
        }
        
        # Fixed endpoint path: /api/v1/classify/ instead of /api/v1/classify/document
        with self.client.post("/api/v1/classify/", 
                            json=payload, 
                            catch_response=True,
                            timeout=15) as response:
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success") and result.get("document_type"):
                        response.success()
                    else:
                        response.failure("Classification returned no document type")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"Classification failed: {response.status_code}")
    
    @task(1)
    def test_ner_endpoint(self):
        """Test NER endpoint"""
        if not self.auth_token:
            return
            
        text = random.choice(self.test_texts)
        
        payload = {
            "text": text,
            "confidence_threshold": 0.7
        }
        
        with self.client.post("/api/v1/ner/extract", 
                            json=payload, 
                            catch_response=True,
                            timeout=15) as response:
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "entities" in result:
                        response.success()
                    else:
                        response.failure("NER processing failed")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"NER failed: {response.status_code}")
    
    @task(1)
    def test_advice_endpoint(self):
        """Test advice endpoint"""
        if not self.auth_token:
            return
            
        text = random.choice(self.test_texts)
        doc_type = random.choice(["bill_of_exchange", "fine_notice", "protocol"])
        
        payload = {
            "text": text,
            "document_type": doc_type,
            "entities": []
        }
        
        with self.client.post("/api/v1/advise/analyze", 
                            json=payload, 
                            catch_response=True,
                            timeout=30) as response:
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success") and result.get("analysis"):
                        response.success()
                    else:
                        response.failure("Advice analysis failed")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"Advice failed: {response.status_code}")
    
    @task(1)
    def test_full_pipeline(self):
        """Test full document processing pipeline with authentication"""
        if not self.test_images or not self.test_texts or not self.auth_token:
            return
        
        # Step 1: OCR
        image_b64 = random.choice(self.test_images)
        ocr_payload = {
            "image_base64": image_b64,
            "language": "ru",
            "confidence_threshold": 0.7
        }
        
        start_time = time.time()
        
        with self.client.post("/api/v1/ocr/extract", 
                            json=ocr_payload, 
                            catch_response=True,
                            timeout=30) as ocr_response:
            
            if ocr_response.status_code != 200:
                ocr_response.failure("Pipeline: OCR step failed")
                return
            
            try:
                ocr_result = ocr_response.json()
                extracted_text = ocr_result.get("text", "")
                
                if not extracted_text:
                    # Fallback to test text if OCR fails
                    extracted_text = random.choice(self.test_texts)
                    
            except json.JSONDecodeError:
                ocr_response.failure("Pipeline: OCR invalid JSON")
                return
        
        # Step 2: Classification (with correct endpoint)
        classify_payload = {
            "text": extracted_text,
            "include_sections": True,
            "include_fields": True
        }
        
        with self.client.post("/api/v1/classify/", 
                            json=classify_payload, 
                            catch_response=True,
                            timeout=15) as classify_response:
            
            if classify_response.status_code != 200:
                classify_response.failure("Pipeline: Classification step failed")
                return
            
            try:
                classify_result = classify_response.json()
                doc_type = classify_result.get("document_type", "")
                
                if not doc_type:
                    classify_response.failure("Pipeline: Classification returned no type")
                    return
                    
            except json.JSONDecodeError:
                classify_response.failure("Pipeline: Classification invalid JSON")
                return
        
        # Step 3: NER
        ner_payload = {
            "text": extracted_text,
            "confidence_threshold": 0.7
        }
        
        with self.client.post("/api/v1/ner/extract", 
                            json=ner_payload, 
                            catch_response=True,
                            timeout=15) as ner_response:
            
            if ner_response.status_code != 200:
                ner_response.failure("Pipeline: NER step failed")
                return
            
            try:
                ner_result = ner_response.json()
                entities = ner_result.get("entities", [])
                
            except json.JSONDecodeError:
                ner_response.failure("Pipeline: NER invalid JSON")
                return
        
        # Step 4: Advice
        advice_payload = {
            "text": extracted_text,
            "document_type": doc_type,
            "entities": entities
        }
        
        with self.client.post("/api/v1/advise/analyze", 
                            json=advice_payload, 
                            catch_response=True,
                            timeout=30) as advice_response:
            
            total_time = time.time() - start_time
            
            if advice_response.status_code == 200:
                try:
                    advice_result = advice_response.json()
                    if advice_result.get("success"):
                        # Log successful full pipeline
                        events.request.fire(
                            request_type="PIPELINE",
                            name="full_document_processing",
                            response_time=total_time * 1000,
                            response_length=len(str(advice_result)),
                            exception=None,
                            context=self.context()
                        )
                        advice_response.success()
                    else:
                        advice_response.failure("Pipeline: Advice analysis failed")
                except json.JSONDecodeError:
                    advice_response.failure("Pipeline: Advice invalid JSON")
            else:
                advice_response.failure("Pipeline: Advice step failed")

# Custom event listeners for detailed metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log successful pipeline completions"""
    if request_type == "PIPELINE" and name == "full_document_processing":
        print(f"✅ Full pipeline completed in {response_time:.0f}ms")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print("🚀 Starting Legal AI load test with corrected endpoints and authentication")

@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("✅ Load test completed")
    
    # Print summary statistics
    stats = environment.stats
    print(f"\n📊 Load Test Summary:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Success rate: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.1f}%" if stats.total.num_requests > 0 else "0.0%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"RPS: {stats.total.current_rps:.2f}")
    
    # Print per-endpoint stats
    print(f"\n📈 Per-Endpoint Performance:")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            success_rate = ((entry.num_requests - entry.num_failures) / entry.num_requests * 100) if entry.num_requests > 0 else 0
            print(f"  {name}: {entry.avg_response_time:.0f}ms avg, {entry.num_requests} reqs, {success_rate:.1f}% success")

if __name__ == "__main__":
    # Run with: python -m locust -f tests/locust_load_test.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000
    pass 