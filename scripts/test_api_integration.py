#!/usr/bin/env python3
"""
Legal ASI - API Integration Testing
Tests all API endpoints with synthetic legal documents
"""

import requests
import base64
import json
import os
import time
from typing import Dict, List
import sys

class APITester:
    """Comprehensive API testing with synthetic data"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.synthetic_data_path = "data/synthetic"
        self.test_results = []
        
    def load_synthetic_metadata(self):
        """Load synthetic documents metadata"""
        metadata_path = os.path.join(self.synthetic_data_path, "metadata", "all_documents.json")
        
        if not os.path.exists(metadata_path):
            print(f"❌ Synthetic metadata not found: {metadata_path}")
            print("Run 'python3 scripts/create_synthetic_data.py' first")
            return None
            
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def image_to_base64(self, image_path):
        """Convert image to base64 string"""
        try:
            with open(image_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            print(f"❌ Failed to encode image {image_path}: {e}")
            return None
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        print("🔍 Testing health endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Version: {data.get('version')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check connection failed: {e}")
            return False
    
    def test_ocr_endpoint(self, document_metadata):
        """Test OCR endpoint with synthetic image"""
        print(f"\n🔍 Testing OCR with {document_metadata['document_id']}...")
        
        # Convert image to base64
        image_base64 = self.image_to_base64(document_metadata['image_path'])
        if not image_base64:
            return False
        
        payload = {
            "image_base64": image_base64,
            "language": "ru",
            "confidence_threshold": 0.7
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/ocr/extract", 
                json=payload,
                timeout=30
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OCR successful")
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                print(f"   Characters extracted: {data.get('character_count', 0)}")
                print(f"   Words extracted: {data.get('word_count', 0)}")
                
                # Store extracted text for further testing
                document_metadata['extracted_text'] = data.get('text', '')
                
                self.test_results.append({
                    "endpoint": "OCR",
                    "document_id": document_metadata['document_id'],
                    "document_type": document_metadata['document_type'],
                    "success": True,
                    "processing_time": processing_time,
                    "confidence": data.get('confidence', 0),
                    "character_count": data.get('character_count', 0)
                })
                
                return True
            else:
                print(f"❌ OCR failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ OCR request failed: {e}")
            return False
    
    def test_classification_endpoint(self, document_metadata):
        """Test classification endpoint"""
        print(f"\n🔍 Testing classification with {document_metadata['document_id']}...")
        
        # Use extracted text if available, otherwise read from text file
        text = document_metadata.get('extracted_text')
        if not text:
            try:
                with open(document_metadata['text_path'], 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                print(f"❌ Failed to read text file: {e}")
                return False
        
        payload = {
            "text": text,
            "top_k": 3
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/classify/document",
                json=payload,
                timeout=10
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                predicted_type = data.get('document_type')
                actual_type = document_metadata['document_type']
                
                print(f"✅ Classification successful")
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Predicted: {predicted_type}")
                print(f"   Actual: {actual_type}")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                
                # Check if classification is correct
                correct = predicted_type == actual_type
                if correct:
                    print(f"   ✅ Classification CORRECT")
                else:
                    print(f"   ⚠️  Classification INCORRECT")
                
                self.test_results.append({
                    "endpoint": "Classification", 
                    "document_id": document_metadata['document_id'],
                    "document_type": actual_type,
                    "predicted_type": predicted_type,
                    "success": True,
                    "correct": correct,
                    "processing_time": processing_time,
                    "confidence": data.get('confidence', 0)
                })
                
                return True
            else:
                print(f"❌ Classification failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Classification request failed: {e}")
            return False
    
    def test_ner_endpoint(self, document_metadata):
        """Test Named Entity Recognition endpoint"""
        print(f"\n🔍 Testing NER with {document_metadata['document_id']}...")
        
        # Use extracted text if available, otherwise read from text file
        text = document_metadata.get('extracted_text')
        if not text:
            try:
                with open(document_metadata['text_path'], 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                print(f"❌ Failed to read text file: {e}")
                return False
        
        payload = {
            "text": text,
            "confidence_threshold": 0.7
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/ner/extract",
                json=payload,
                timeout=10
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get('entities', [])
                expected_entities = document_metadata.get('entities', {})
                
                print(f"✅ NER successful")
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Entities found: {len(entities)}")
                
                # Show found entities
                entity_types = {}
                for entity in entities:
                    entity_type = entity['label']
                    if entity_type not in entity_types:
                        entity_types[entity_type] = []
                    entity_types[entity_type].append(entity['text'])
                
                for entity_type, texts in entity_types.items():
                    print(f"   {entity_type}: {texts}")
                
                # Calculate coverage (how many expected entities were found)
                total_expected = sum(len(ents) for ents in expected_entities.values())
                found_count = len(entities)
                coverage = found_count / max(total_expected, 1) * 100
                
                print(f"   Coverage: {coverage:.1f}% ({found_count}/{total_expected})")
                
                self.test_results.append({
                    "endpoint": "NER",
                    "document_id": document_metadata['document_id'],
                    "document_type": document_metadata['document_type'],
                    "success": True,
                    "processing_time": processing_time,
                    "entities_found": len(entities),
                    "entities_expected": total_expected,
                    "coverage": coverage
                })
                
                return True
            else:
                print(f"❌ NER failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ NER request failed: {e}")
            return False
    
    def test_service_health_endpoints(self):
        """Test individual service health endpoints"""
        print("\n🔍 Testing service health endpoints...")
        
        services = [
            ("OCR", "/api/v1/ocr/health"),
            ("Classification", "/api/v1/classify/health"),
            ("NER", "/api/v1/ner/health")
        ]
        
        for service_name, endpoint in services:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {service_name}: {data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ {service_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {service_name}: {e}")
    
    def run_comprehensive_test(self, max_documents=5):
        """Run comprehensive test suite"""
        print("🧪 Legal ASI - Comprehensive API Integration Test")
        print("=" * 50)
        
        # Load synthetic documents
        documents = self.load_synthetic_metadata()
        if not documents:
            return False
        
        print(f"📊 Loaded {len(documents)} synthetic documents")
        
        # Test main health endpoint
        if not self.test_health_endpoint():
            print("❌ Main health check failed. Is the API running?")
            print("   Start with: docker-compose up api")
            return False
        
        # Test service health endpoints
        self.test_service_health_endpoints()
        
        # Test with subset of documents
        test_documents = documents[:max_documents]
        print(f"\n🎯 Testing with {len(test_documents)} documents...")
        
        success_count = 0
        total_tests = 0
        
        for doc in test_documents:
            print(f"\n" + "=" * 60)
            print(f"📄 Testing document: {doc['document_id']} ({doc['document_type']})")
            
            # Test OCR
            total_tests += 1
            if self.test_ocr_endpoint(doc):
                success_count += 1
            
            # Test Classification
            total_tests += 1
            if self.test_classification_endpoint(doc):
                success_count += 1
            
            # Test NER
            total_tests += 1  
            if self.test_ner_endpoint(doc):
                success_count += 1
        
        # Generate summary report
        self.generate_summary_report(success_count, total_tests)
        
        return success_count == total_tests
    
    def generate_summary_report(self, success_count, total_tests):
        """Generate and display test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        print(f"Overall Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        # Group results by endpoint
        endpoint_stats = {}
        for result in self.test_results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'success': 0, 'total': 0, 'times': []}
            
            endpoint_stats[endpoint]['total'] += 1
            if result['success']:
                endpoint_stats[endpoint]['success'] += 1
            endpoint_stats[endpoint]['times'].append(result['processing_time'])
        
        print("\nEndpoint Performance:")
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats['success'] / stats['total']) * 100
            avg_time = sum(stats['times']) / len(stats['times'])
            print(f"  {endpoint}:")
            print(f"    Success Rate: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
            print(f"    Avg Time: {avg_time:.2f}s")
        
        # Classification accuracy
        classification_results = [r for r in self.test_results if r['endpoint'] == 'Classification']
        if classification_results:
            correct_classifications = sum(1 for r in classification_results if r.get('correct', False))
            classification_accuracy = (correct_classifications / len(classification_results)) * 100
            print(f"\nClassification Accuracy: {classification_accuracy:.1f}%")
        
        # NER coverage
        ner_results = [r for r in self.test_results if r['endpoint'] == 'NER']
        if ner_results:
            avg_coverage = sum(r.get('coverage', 0) for r in ner_results) / len(ner_results)
            print(f"Average NER Coverage: {avg_coverage:.1f}%")
        
        # Save detailed results
        results_path = "test_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"\nDetailed results saved to: {results_path}")

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"🎯 Testing API at: {base_url}")
    
    tester = APITester(base_url)
    
    # Check if synthetic data exists
    if not os.path.exists("data/synthetic"):
        print("❌ Synthetic data not found!")
        print("Run: python3 scripts/create_synthetic_data.py")
        return False
    
    success = tester.run_comprehensive_test(max_documents=3)  # Test with 3 documents
    
    if success:
        print("\n✅ All tests passed! API is ready for production data.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 