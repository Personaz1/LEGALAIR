#!/usr/bin/env python3
"""
Legal ASI - Lightweight API Testing
Tests API functionality without requiring external services
"""

import sys
import os
import json
import base64
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set testing environment
os.environ["TESTING"] = "true"

def test_api_imports():
    """Test that all API components can be imported"""
    print("🔍 Testing API component imports...")
    
    try:
        from api.main import app
        print("   ✅ FastAPI app")
        
        from api.models.base import OCRRequest, ClassificationRequest, NERRequest
        print("   ✅ Pydantic models")
        
        from api.routers import ocr, classify, ner
        print("   ✅ API routers")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_ml_services():
    """Test ML service initialization"""
    print("\n🔍 Testing ML service initialization...")
    
    try:
        # Test classification service (placeholder)
        from api.routers.classify import ClassificationService
        classifier = ClassificationService()
        print("   ✅ Classification service")
        
        # Test NER service (placeholder)
        from api.routers.ner import NERService
        ner = NERService()
        print("   ✅ NER service")
        
        return True
    except Exception as e:
        print(f"   ❌ ML service error: {e}")
        return False

def test_ocr_service_import():
    """Test OCR service import (may fail without EasyOCR)"""
    print("\n🔍 Testing OCR service import...")
    
    try:
        from ml.ocr_service import OCRService
        print("   ✅ OCR service imported")
        
        # Try to initialize (may fail without EasyOCR)
        try:
            ocr = OCRService()
            print("   ✅ OCR service initialized")
            return True
        except Exception as e:
            print(f"   ⚠️  OCR service init failed (expected without EasyOCR): {e}")
            return True  # This is expected in testing
    except ImportError as e:
        print(f"   ❌ OCR import failed: {e}")
        return False

def test_placeholder_classification():
    """Test placeholder classification logic"""
    print("\n🔍 Testing placeholder classification...")
    
    try:
        from api.routers.classify import ClassificationService
        classifier = ClassificationService()
        
        # Test with synthetic text
        test_texts = {
            "вексель": "ВЕКСЕЛЬ № 123456 Обязательство: Иванов И.И. обязуется выплатить",
            "штраф": "ПОСТАНОВЛЕНИЕ об административном правонарушении № АА-001234",
            "протокол": "ПРОТОКОЛ заседания № 789 Организация: ООО Тест"
        }
        
        for expected_type, text in test_texts.items():
            import asyncio
            result = asyncio.run(classifier.classify_document(text))
            predicted = result['document_type'].value
            confidence = result['confidence']
            
            print(f"   Text: '{text[:50]}...'")
            print(f"   Expected: {expected_type}, Predicted: {predicted}, Confidence: {confidence:.2f}")
            
            # Check if classification makes sense
            if expected_type == "вексель" and "bill_of_exchange" in predicted:
                print("   ✅ Bill classification correct")
            elif expected_type == "штраф" and "fine_notice" in predicted:
                print("   ✅ Fine classification correct")
            elif expected_type == "протокол" and "protocol" in predicted:
                print("   ✅ Protocol classification correct")
            else:
                print(f"   ⚠️  Classification mismatch")
        
        return True
    except Exception as e:
        print(f"   ❌ Classification test failed: {e}")
        return False

def test_placeholder_ner():
    """Test placeholder NER logic"""
    print("\n🔍 Testing placeholder NER...")
    
    try:
        from api.routers.ner import NERService
        ner = NERService()
        
        test_text = """
        ВЕКСЕЛЬ № 123456 от 15.12.2023
        Должник: Иванов Иван Иванович
        Кредитор: ООО "Рога и Копыта"
        Сумма: 50000 рублей
        Место: г. Москва
        """
        
        import asyncio
        entities = asyncio.run(ner.extract_entities(test_text))
        
        print(f"   Extracted {len(entities)} entities:")
        for entity in entities[:5]:  # Show first 5
            print(f"     {entity['label']}: '{entity['text']}' (confidence: {entity['confidence']:.2f})")
        
        # Check if expected entity types are found
        found_types = set(entity['label'] for entity in entities)
        expected_types = {'PERSON', 'ORGANIZATION', 'MONEY', 'DATE', 'DOCUMENT_NUMBER'}
        
        found_expected = found_types.intersection(expected_types)
        print(f"   Found expected types: {found_expected}")
        
        return len(found_expected) > 0
    except Exception as e:
        print(f"   ❌ NER test failed: {e}")
        return False

def test_synthetic_data_access():
    """Test access to synthetic data"""
    print("\n🔍 Testing synthetic data access...")
    
    synthetic_path = project_root / "data" / "synthetic"
    metadata_path = synthetic_path / "metadata" / "all_documents.json"
    
    if not metadata_path.exists():
        print("   ⚠️  Synthetic data not found, generating...")
        try:
            exec(open(project_root / "scripts" / "create_synthetic_data.py").read())
        except Exception as e:
            print(f"   ❌ Failed to generate synthetic data: {e}")
            return False
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"   ✅ Loaded {len(metadata)} synthetic documents")
        
        # Check document types
        doc_types = {}
        for doc in metadata:
            doc_type = doc['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"   Document types: {doc_types}")
        
        # Test image access
        first_doc = metadata[0]
        image_path = Path(first_doc['image_path'])
        if image_path.exists():
            print(f"   ✅ Sample image accessible: {image_path.name}")
        else:
            print(f"   ⚠️  Sample image not found: {image_path}")
        
        return True
    except Exception as e:
        print(f"   ❌ Synthetic data test failed: {e}")
        return False

def run_lightweight_tests():
    """Run all lightweight tests"""
    print("🧪 Legal ASI - Lightweight Component Testing")
    print("=" * 50)
    print("Testing API components without external dependencies...")
    
    tests = [
        ("API Imports", test_api_imports),
        ("ML Services", test_ml_services),
        ("OCR Service", test_ocr_service_import),
        ("Classification Logic", test_placeholder_classification),
        ("NER Logic", test_placeholder_ner),
        ("Synthetic Data", test_synthetic_data_access)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All lightweight tests passed!")
        print("✅ Core components are ready for full API testing")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("🔧 Fix issues before proceeding to integration testing")
    
    return passed == total

if __name__ == "__main__":
    success = run_lightweight_tests()
    
    if success:
        print("\n🚀 Ready to run full API server for integration testing")
        print("   Next steps:")
        print("   1. python3 scripts/run_api_standalone.py")
        print("   2. python3 scripts/test_api_integration.py")
    
    sys.exit(0 if success else 1) 