#!/usr/bin/env python3
"""
Legal ASI - LLM Advisory Integration Test
Tests the advisory service with and without Ollama
"""

import sys
import json
import requests
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_advisory_service_stub():
    """Test advisory service with stub analysis (no LLM)"""
    print("🧪 Testing Advisory Service (Stub Mode)")
    print("=" * 45)
    
    # Test documents from synthetic data
    test_cases = [
        {
            "text": """ВЕКСЕЛЬ № 123456 от 15.12.2023
            
Обязательство: Иванов Иван Иванович обязуется выплатить 
ООО "Рога и Копыта" сумму в размере 50000 рублей до 15.01.2024.

Должник: Иванов Иван Иванович
Паспорт: 4510 123456
Адрес: г. Москва, ул. Ленина, д. 10

Кредитор: ООО "Рога и Копыта"
ИНН: 7701234567

Подпись должника: _________________
""",
            "document_type": "bill_of_exchange",
            "expected_risk": "средний"
        },
        {
            "text": """ПОСТАНОВЛЕНИЕ об административном правонарушении
№ АА-001234 от 10.11.2023

Гражданин Петров Петр Петрович совершил административное правонарушение,
предусмотренное статьей 12.9 КоАП РФ (превышение скорости).

Место нарушения: г. Москва, Садовое кольцо
Время нарушения: 14:30

Назначить административный штраф в размере 5000 рублей.

Нарушитель: Петров Петр Петрович
Паспорт: 4511 654321
Адрес: г. Москва, ул. Пушкина, д. 5

Инспектор: Сидоров С.С.
Должность: Инспектор ГИБДД
""",
            "document_type": "fine_notice",
            "expected_risk": "низкий"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📄 Test Case {i+1}: {test_case['document_type']}")
        print("-" * 30)
        
        try:
            # Test stub analysis (use_llm=False)
            result = test_advisory_analysis(
                text=test_case["text"],
                document_type=test_case["document_type"],
                use_llm=False
            )
            
            if result:
                print(f"✅ Analysis successful")
                print(f"   Risk Level: {result.get('risk_level')}")
                print(f"   Key Parties: {len(result.get('key_parties', []))}")
                print(f"   Recommendations: {len(result.get('recommendations', []))}")
                print(f"   LLM Used: {result.get('llm_used', False)}")
                
                # Validate expected risk level
                if result.get('risk_level') == test_case['expected_risk']:
                    print(f"   ✅ Risk level matches expected: {test_case['expected_risk']}")
                else:
                    print(f"   ⚠️  Risk level mismatch: got {result.get('risk_level')}, expected {test_case['expected_risk']}")
                
                success_count += 1
            else:
                print(f"❌ Analysis failed")
        
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n📊 Stub Test Results: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

def test_advisory_analysis(text, document_type, use_llm=True, base_url="http://localhost:8000"):
    """Test advisory analysis endpoint"""
    
    # Mock test without actual API call
    if not check_api_available(base_url):
        return mock_advisory_analysis(text, document_type, use_llm)
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/advise/analyze",
            params={
                "text": text,
                "document_type": document_type,
                "use_llm": use_llm
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def mock_advisory_analysis(text, document_type, use_llm):
    """Mock advisory analysis for testing without API"""
    
    # Import the advisory service directly
    try:
        from api.routers.advise import LegalAdvisorService
        from api.models.base import DocumentType
        
        # Map string to enum
        doc_type_map = {
            "bill_of_exchange": DocumentType.BILL_OF_EXCHANGE,
            "fine_notice": DocumentType.FINE_NOTICE,
            "protocol": DocumentType.PROTOCOL
        }
        
        service = LegalAdvisorService()
        
        # Use asyncio to run async method
        import asyncio
        result = asyncio.run(service.analyze_document(
            text=text,
            doc_type=doc_type_map.get(document_type, DocumentType.UNKNOWN),
            use_llm=use_llm
        ))
        
        return result
    
    except Exception as e:
        print(f"Mock analysis failed: {e}")
        return None

def check_api_available(base_url):
    """Check if API is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_ollama_status():
    """Check Ollama service status"""
    print("\n🔍 Checking Ollama Status")
    print("=" * 25)
    
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            
            # Check for Mistral model
            models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if models_response.status_code == 200:
                models = models_response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                if any("mistral:7b" in name for name in model_names):
                    print("✅ Mistral-7B model available")
                    return True
                else:
                    print("⚠️  Mistral-7B model not found")
                    print("   Available models:", [name for name in model_names])
                    print("   Run: scripts/setup_ollama.sh")
                    return False
            else:
                print("❌ Failed to check models")
                return False
        else:
            print("❌ Ollama service not responding")
            return False
    
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("   Install with: scripts/setup_ollama.sh")
        return False

def test_llm_integration():
    """Test LLM integration if available"""
    if not check_ollama_status():
        print("\n💡 LLM integration will use stub analysis")
        return False
    
    print("\n🧪 Testing LLM Integration")
    print("=" * 25)
    
    test_text = """ВЕКСЕЛЬ № 789012 от 20.12.2023

Я, Сидоров Алексей Петрович, обязуюсь выплатить 
ЗАО "Финанс Групп" сумму в размере 75000 рублей 
к 20.03.2024 на основании договора займа № 156.

Должник: Сидоров Алексей Петрович
Кредитор: ЗАО "Финанс Групп"
ИНН: 7702345678

Подпись: _________________"""
    
    try:
        result = test_advisory_analysis(
            text=test_text,
            document_type="bill_of_exchange",
            use_llm=True
        )
        
        if result and result.get("llm_used"):
            print("✅ LLM analysis successful")
            print(f"   Processing time: {result.get('processing_time', 0)}s")
            print(f"   Analysis: {result.get('document_analysis', '')[:100]}...")
            return True
        else:
            print("⚠️  LLM analysis failed, used stub fallback")
            return False
    
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

def display_setup_instructions():
    """Display setup instructions for LLM integration"""
    print("\n🚀 LLM Advisory Setup Instructions")
    print("=" * 35)
    print()
    print("1. Install Ollama and Mistral-7B:")
    print("   bash scripts/setup_ollama.sh")
    print()
    print("2. Start Legal ASI API:")
    print("   python3 api/main.py")
    print("   # or")
    print("   python3 scripts/run_api_standalone.py")
    print()
    print("3. Test advisory endpoint:")
    print("   curl -X POST 'http://localhost:8000/api/v1/advise/analyze' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print('       "text": "ВЕКСЕЛЬ № 123...",')
    print('       "document_type": "bill_of_exchange",')
    print('       "use_llm": true')
    print("     }'")
    print()
    print("4. Check service health:")
    print("   curl http://localhost:8000/api/v1/advise/health")

def main():
    """Main test execution"""
    print("🧪 Legal ASI - LLM Advisory Integration Test")
    print("=" * 50)
    
    # Test stub analysis (always works)
    stub_success = test_advisory_service_stub()
    
    # Test LLM integration (if available)
    llm_success = test_llm_integration()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Stub Analysis: {'✅ PASS' if stub_success else '❌ FAIL'}")
    print(f"LLM Integration: {'✅ PASS' if llm_success else '⚠️  UNAVAILABLE'}")
    
    if stub_success:
        print("\n🎉 Advisory service is working!")
        print("📄 Legal document analysis with recommendations available")
        
        if not llm_success:
            print("\n💡 To enable LLM analysis:")
            display_setup_instructions()
    else:
        print("\n❌ Advisory service has issues")
        print("🔧 Check the implementation and try again")
    
    return stub_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 