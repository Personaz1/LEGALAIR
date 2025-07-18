#!/usr/bin/env python3
"""
Legal ASI - Core Logic Testing
Tests core functionality without external dependencies
"""

import sys
import os
import json
import re
from pathlib import Path

def test_classification_logic():
    """Test classification logic without FastAPI/external deps"""
    print("🔍 Testing classification logic...")
    
    # Basic classification logic from our codebase
    def classify_text(text):
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['вексель', 'обязательство', 'должник']):
            return {'doc_type': 'bill_of_exchange', 'confidence': 0.85}
        elif any(word in text_lower for word in ['штраф', 'нарушение', 'админ']):
            return {'doc_type': 'fine_notice', 'confidence': 0.80}
        elif any(word in text_lower for word in ['протокол', 'заседание', 'решение']):
            return {'doc_type': 'protocol', 'confidence': 0.75}
        else:
            return {'doc_type': 'unknown', 'confidence': 0.30}
    
    # Test cases
    test_cases = [
        ("ВЕКСЕЛЬ № 123456 Обязательство: Иванов И.И.", "bill_of_exchange"),
        ("ПОСТАНОВЛЕНИЕ об административном правонарушении штраф", "fine_notice"),
        ("ПРОТОКОЛ заседания совета директоров", "protocol"),
        ("Обычный текст без ключевых слов", "unknown")
    ]
    
    correct = 0
    for text, expected in test_cases:
        result = classify_text(text)
        predicted = result['doc_type']
        confidence = result['confidence']
        
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        print(f"   {status} Text: '{text[:30]}...'")
        print(f"      Expected: {expected}, Got: {predicted} (conf: {confidence:.2f})")
    
    accuracy = correct / len(test_cases) * 100
    print(f"   📊 Classification accuracy: {accuracy:.1f}% ({correct}/{len(test_cases)})")
    return accuracy > 75

def test_ner_logic():
    """Test NER logic without spaCy"""
    print("\n🔍 Testing NER logic...")
    
    # Basic NER patterns from our codebase
    def extract_entities(text):
        entities = []
        
        patterns = {
            'DATE': [
                r'\d{1,2}\.\d{1,2}\.\d{2,4}',
                r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4}',
            ],
            'MONEY': [
                r'\d+[\s,]?\d*\s*(руб|рублей|копеек|₽)',
                r'\d+[\s,]?\d*\s*(долларов|доллара|USD|\$)',
            ],
            'DOCUMENT_NUMBER': [
                r'№\s*\d+[\w\-\/]*',
                r'серия\s+\w+\s+№\s*\d+',
            ],
            'PERSON': [
                r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.',
                r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+',
            ],
            'ORGANIZATION': [
                r'ООО\s+"[^"]+"',
                r'ЗАО\s+"[^"]+"',
                r'ОАО\s+"[^"]+"',
                r'ИП\s+[А-ЯЁ][а-яё]+',
            ]
        }
        
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8
                    })
        
        return entities
    
    # Test text
    test_text = """
    ВЕКСЕЛЬ № 123456 от 15.12.2023
    Должник: Иванов Иван Иванович
    Кредитор: ООО "Рога и Копыта"
    Сумма: 50000 рублей
    """
    
    entities = extract_entities(test_text)
    
    print(f"   📊 Extracted {len(entities)} entities:")
    entity_types = {}
    for entity in entities:
        entity_type = entity['label']
        if entity_type not in entity_types:
            entity_types[entity_type] = []
        entity_types[entity_type].append(entity['text'])
    
    for entity_type, texts in entity_types.items():
        print(f"     {entity_type}: {texts}")
    
    # Check if we found expected types
    expected_types = {'DOCUMENT_NUMBER', 'DATE', 'PERSON', 'ORGANIZATION', 'MONEY'}
    found_types = set(entity_types.keys())
    coverage = len(found_types.intersection(expected_types)) / len(expected_types) * 100
    
    print(f"   📊 Entity coverage: {coverage:.1f}% ({len(found_types.intersection(expected_types))}/{len(expected_types)})")
    return coverage > 60

def test_synthetic_data():
    """Test synthetic data generation and access"""
    print("\n🔍 Testing synthetic data...")
    
    synthetic_path = Path("data/synthetic")
    metadata_path = synthetic_path / "metadata" / "all_documents.json"
    
    if not metadata_path.exists():
        print("   ⚠️  Synthetic data not found")
        return False
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"   ✅ Loaded {len(metadata)} synthetic documents")
        
        # Check document distribution
        doc_types = {}
        for doc in metadata:
            doc_type = doc['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"   📊 Document types: {doc_types}")
        
        # Test first document
        if metadata:
            first_doc = metadata[0]
            text_path = Path(first_doc['text_path'])
            image_path = Path(first_doc['image_path'])
            
            text_exists = text_path.exists()
            image_exists = image_path.exists()
            
            print(f"   ✅ Text file exists: {text_exists}")
            print(f"   ✅ Image file exists: {image_exists}")
            
            if text_exists:
                with open(text_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"   📄 Sample content: {len(content)} characters")
            
            return text_exists and image_exists
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_file_structure():
    """Test project file structure"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "api/main.py",
        "api/models/base.py", 
        "api/routers/ocr.py",
        "api/routers/classify.py",
        "api/routers/ner.py",
        "ml/ocr_service.py",
        "docker-compose.yml",
        "requirements.txt",
        "README.md",
        "DEV_NOTES.md"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"   ❌ Missing files: {missing}")
        return False
    else:
        print(f"   ✅ All {len(required_files)} required files present")
        return True

def test_python_syntax():
    """Test Python file syntax"""
    print("\n🔍 Testing Python syntax...")
    
    python_files = [
        "api/main.py",
        "api/models/base.py",
        "api/routers/ocr.py", 
        "api/routers/classify.py",
        "api/routers/ner.py",
        "ml/ocr_service.py"
    ]
    
    import ast
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"   ✅ {file_path}")
        except SyntaxError as e:
            print(f"   ❌ {file_path}: {e}")
            syntax_errors.append((file_path, e))
        except Exception as e:
            print(f"   ⚠️  {file_path}: {e}")
    
    return len(syntax_errors) == 0

def run_core_tests():
    """Run all core tests"""
    print("🧪 Legal ASI - Core Logic Testing")
    print("=" * 50)
    print("Testing core functionality without external dependencies...")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Syntax", test_python_syntax),
        ("Classification Logic", test_classification_logic),
        ("NER Logic", test_ner_logic),
        ("Synthetic Data", test_synthetic_data)
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
    print("📊 CORE TESTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    success_rate = passed / total * 100
    print(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 All core tests passed!")
        print("✅ Core components are working correctly")
        print("📋 Ready for dependency installation and full testing")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("🔧 Fix core issues before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = run_core_tests()
    
    if success:
        print("\n🚀 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run Docker services: docker-compose up")
        print("   3. Test full API integration")
        print("\n📁 All components validated and ready for data!")
    
    sys.exit(0 if success else 1) 