#!/usr/bin/env python3
"""
Legal AI End-to-End Flow Test
ΔΣ::Cursor - Validate complete document processing pipeline

Tests the full workflow: Upload → OCR → Classification → NER → AI Advisory
"""

import requests
import time
import json
import sys
from pathlib import Path

class EndToEndTester:
    """Test complete document processing workflow"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()
        
    def test_api_health(self):
        """Test API health endpoint"""
        print("🔍 Testing API health...")
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API health check passed")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API not accessible: {e}")
            return False
    
    def test_ocr_endpoint(self, test_file_path):
        """Test OCR processing"""
        print(f"📄 Testing OCR with: {test_file_path}")
        
        if not Path(test_file_path).exists():
            print(f"❌ Test file not found: {test_file_path}")
            return None
            
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.api_url}/api/v1/ocr/process",
                    files=files,
                    timeout=30
                )
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OCR successful: {len(result.get('text', ''))} characters extracted")
                return result
            else:
                print(f"❌ OCR failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OCR error: {e}")
            return None
    
    def test_classification_endpoint(self, text):
        """Test document classification"""
        print("🏷️ Testing classification...")
        
        try:
            payload = {'text': text}
            response = self.session.post(
                f"{self.api_url}/api/v1/classify",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                doc_type = result.get('document_type', 'unknown')
                confidence = result.get('confidence', 0)
                print(f"✅ Classification: {doc_type} (confidence: {confidence:.2f})")
                return result
            else:
                print(f"❌ Classification failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return None
    
    def test_ner_endpoint(self, text):
        """Test Named Entity Recognition"""
        print("👥 Testing NER extraction...")
        
        try:
            payload = {'text': text}
            response = self.session.post(
                f"{self.api_url}/api/v1/ner/extract",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                entities = result.get('entities', [])
                print(f"✅ NER extracted {len(entities)} entities")
                
                # Show entity types
                entity_types = {}
                for entity in entities:
                    etype = entity.get('label', 'unknown')
                    entity_types[etype] = entity_types.get(etype, 0) + 1
                
                for etype, count in entity_types.items():
                    print(f"   - {etype}: {count}")
                    
                return result
            else:
                print(f"❌ NER failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ NER error: {e}")
            return None
    
    def test_advisory_endpoint(self, text, document_type=None):
        """Test AI Advisory service"""
        print("🤖 Testing AI Advisory...")
        
        try:
            payload = {
                'document_text': text,
                'document_type': document_type,
                'query': 'Проанализируйте этот документ'
            }
            response = self.session.post(
                f"{self.api_url}/api/v1/advise",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                advice = result.get('advice', '')
                risk_level = result.get('risk_assessment', {}).get('level', 'unknown')
                
                print(f"✅ AI Advisory generated: {len(advice)} characters")
                print(f"   Risk level: {risk_level}")
                
                # Check for legal references
                references = result.get('legal_references', [])
                if references:
                    print(f"   📚 Legal references: {len(references)} found")
                    for ref in references[:2]:  # Show first 2
                        print(f"      - {ref.get('title', 'Unknown')}")
                
                return result
            else:
                print(f"❌ Advisory failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Advisory error: {e}")
            return None
    
    def run_complete_test(self, test_file_path):
        """Run complete end-to-end test"""
        print("🎯 Legal AI End-to-End Flow Test")
        print("=" * 40)
        print("")
        
        # Step 1: Health check
        if not self.test_api_health():
            print("❌ Cannot proceed - API not available")
            return False
        
        print("")
        
        # Step 2: OCR
        ocr_result = self.test_ocr_endpoint(test_file_path)
        if not ocr_result:
            print("❌ Cannot proceed - OCR failed")
            return False
        
        text = ocr_result.get('text', '')
        if not text:
            print("❌ No text extracted from document")
            return False
            
        print("")
        
        # Step 3: Classification
        classification_result = self.test_classification_endpoint(text)
        document_type = None
        if classification_result:
            document_type = classification_result.get('document_type')
        
        print("")
        
        # Step 4: NER
        ner_result = self.test_ner_endpoint(text)
        
        print("")
        
        # Step 5: AI Advisory
        advisory_result = self.test_advisory_endpoint(text, document_type)
        
        print("")
        print("🎯 End-to-End Test Summary")
        print("=" * 30)
        print(f"✅ OCR: {'✓' if ocr_result else '✗'}")
        print(f"✅ Classification: {'✓' if classification_result else '✗'}")
        print(f"✅ NER: {'✓' if ner_result else '✗'}")
        print(f"✅ AI Advisory: {'✓' if advisory_result else '✗'}")
        
        success_count = sum([
            bool(ocr_result),
            bool(classification_result), 
            bool(ner_result),
            bool(advisory_result)
        ])
        
        print(f"📊 Success rate: {success_count}/4 ({success_count/4*100:.0f}%)")
        
        if success_count == 4:
            print("🎉 Complete end-to-end pipeline working!")
            return True
        else:
            print("⚠️ Some components need attention")
            return False


def main():
    """Main entry point"""
    
    # Find a test document
    test_files = [
        "data/synthetic_v3/pdf/doc_000.pdf",
        "data/synthetic_v2/pdf/doc_000.pdf", 
        "data/synthetic/bills/bill_001.txt"
    ]
    
    test_file = None
    for file_path in test_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if not test_file:
        print("❌ No test files found. Generate some first:")
        print("   python3 scripts/gen_synthetic_v3.py --count 1")
        sys.exit(1)
    
    print(f"📄 Using test file: {test_file}")
    print("")
    
    # Run test
    tester = EndToEndTester()
    success = tester.run_complete_test(test_file)
    
    if success:
        print("")
        print("🚀 Ready for demo! Try opening:")
        print("   Frontend: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("")
        print("🔧 Fix the failed components before demo")
        sys.exit(1)


if __name__ == "__main__":
    main() 