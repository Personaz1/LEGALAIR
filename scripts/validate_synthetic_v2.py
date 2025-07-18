#!/usr/bin/env python3
"""
Legal ASI - Synthetic Dataset v2 Validation
Validates generated synthetic documents for quality and parsing accuracy
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.preprocess import split_sections, analyze_document_structure
from ml.extract_fields import extract_fields_from_sections
from api.routers.classify import DocumentClassifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyntheticDatasetValidator:
    """Validator for synthetic dataset v2"""
    
    def __init__(self, dataset_dir: str = "data/synthetic_v2"):
        self.dataset_dir = Path(dataset_dir)
        self.classifier = DocumentClassifier()
        
        # Load metadata
        metadata_path = self.dataset_dir / "dataset_v2.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")
    
    def validate_file_structure(self) -> Dict[str, Any]:
        """Validate file structure and presence"""
        logger.info("Validating file structure...")
        
        results = {
            "total_documents": len(self.metadata["documents"]),
            "missing_files": [],
            "file_types": {"txt": 0, "pdf": 0, "png": 0},
            "file_sizes": {"txt": [], "pdf": [], "png": []},
            "structure_valid": True
        }
        
        for doc in self.metadata["documents"]:
            doc_id = doc["id"]
            filename = doc["filename"]
            
            # Check each file type
            for file_type, relative_path in doc["files"].items():
                file_path = self.dataset_dir / relative_path
                
                if file_path.exists():
                    results["file_types"][file_type] += 1
                    results["file_sizes"][file_type].append(file_path.stat().st_size)
                else:
                    results["missing_files"].append(str(file_path))
                    results["structure_valid"] = False
        
        # Calculate average file sizes
        for file_type in results["file_sizes"]:
            sizes = results["file_sizes"][file_type]
            if sizes:
                results["file_sizes"][file_type] = {
                    "count": len(sizes),
                    "avg_size": sum(sizes) // len(sizes),
                    "min_size": min(sizes),
                    "max_size": max(sizes)
                }
        
        logger.info(f"File structure validation: {'✅ PASSED' if results['structure_valid'] else '❌ FAILED'}")
        return results
    
    def validate_text_content(self) -> Dict[str, Any]:
        """Validate text content quality"""
        logger.info("Validating text content...")
        
        results = {
            "documents_processed": 0,
            "parsing_success": 0,
            "classification_accuracy": 0,
            "field_extraction_success": 0,
            "content_quality": {
                "avg_length": 0,
                "russian_ratio": 0,
                "completeness_scores": []
            },
            "errors": []
        }
        
        total_length = 0
        total_russian_chars = 0
        total_chars = 0
        
        for doc in self.metadata["documents"]:
            try:
                # Read text file
                txt_path = self.dataset_dir / doc["files"]["txt"]
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                results["documents_processed"] += 1
                
                # Basic text analysis
                total_length += len(text)
                russian_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
                total_russian_chars += russian_chars
                total_chars += len(text)
                
                # Test parsing
                try:
                    structure_result = analyze_document_structure(text)
                    sections = structure_result["sections"]
                    analysis = structure_result["analysis"]
                    
                    # Check if sections are non-empty
                    if (sections["header"] or sections["body"] or sections["footer"]):
                        results["parsing_success"] += 1
                    
                    results["content_quality"]["completeness_scores"].append(
                        analysis["completeness_score"]
                    )
                    
                except Exception as e:
                    results["errors"].append(f"Parsing error in {doc['filename']}: {e}")
                
                # Test classification
                try:
                    classification = self.classifier.classify_document(
                        text, include_sections=False, include_fields=False
                    )
                    
                    expected_type = doc["document_type"]
                    predicted_type = classification["document_type"]
                    
                    if expected_type == predicted_type:
                        results["classification_accuracy"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Classification error in {doc['filename']}: {e}")
                
                # Test field extraction
                try:
                    sections = split_sections(text)
                    fields = extract_fields_from_sections(sections)
                    
                    # Check if any fields were extracted
                    fields_found = any(len(fields[key]) > 0 for key in fields if key != "extraction_summary")
                    if fields_found:
                        results["field_extraction_success"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Field extraction error in {doc['filename']}: {e}")
                
            except Exception as e:
                results["errors"].append(f"General error processing {doc['filename']}: {e}")
        
        # Calculate averages
        if results["documents_processed"] > 0:
            results["content_quality"]["avg_length"] = total_length // results["documents_processed"]
            results["content_quality"]["russian_ratio"] = total_russian_chars / total_chars if total_chars > 0 else 0
            
            # Calculate success rates
            doc_count = results["documents_processed"]
            results["parsing_success_rate"] = results["parsing_success"] / doc_count
            results["classification_accuracy_rate"] = results["classification_accuracy"] / doc_count
            results["field_extraction_success_rate"] = results["field_extraction_success"] / doc_count
        
        # Average completeness score
        completeness_scores = results["content_quality"]["completeness_scores"]
        if completeness_scores:
            results["content_quality"]["avg_completeness"] = sum(completeness_scores) / len(completeness_scores)
        
        logger.info(f"Text content validation complete: {results['documents_processed']} documents processed")
        return results
    
    def validate_document_types(self) -> Dict[str, Any]:
        """Validate document type distribution and quality"""
        logger.info("Validating document types...")
        
        results = {
            "type_distribution": {},
            "type_quality": {},
            "expected_vs_actual": {}
        }
        
        # Count actual types from metadata
        for doc in self.metadata["documents"]:
            doc_type = doc["document_type"]
            if doc_type not in results["type_distribution"]:
                results["type_distribution"][doc_type] = 0
            results["type_distribution"][doc_type] += 1
        
        # Validate each type
        for doc_type in results["type_distribution"]:
            type_docs = [doc for doc in self.metadata["documents"] if doc["document_type"] == doc_type]
            
            # Sample a few documents for quality check
            sample_size = min(3, len(type_docs))
            sample_docs = type_docs[:sample_size]
            
            type_quality = {
                "sample_size": sample_size,
                "classification_accuracy": 0,
                "field_extraction_quality": 0,
                "content_examples": []
            }
            
            for doc in sample_docs:
                try:
                    # Read and test document
                    txt_path = self.dataset_dir / doc["files"]["txt"]
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    # Test classification
                    classification = self.classifier.classify_document(
                        text, include_sections=True, include_fields=True
                    )
                    
                    if classification["document_type"] == doc_type:
                        type_quality["classification_accuracy"] += 1
                    
                    # Test field extraction quality
                    if classification["extracted_fields"]:
                        fields = classification["extracted_fields"]
                        
                        # Document type specific field validation
                        if doc_type == "bill_of_exchange":
                            if len(fields.amounts) > 0 and len(fields.persons) > 0:
                                type_quality["field_extraction_quality"] += 1
                        elif doc_type == "fine_notice":
                            if len(fields.amounts) > 0 and len(fields.legal_articles) > 0:
                                type_quality["field_extraction_quality"] += 1
                        elif doc_type == "protocol":
                            if len(fields.persons) > 0 and len(fields.organizations) > 0:
                                type_quality["field_extraction_quality"] += 1
                    
                    # Store content example
                    type_quality["content_examples"].append({
                        "filename": doc["filename"],
                        "length": len(text),
                        "first_line": text.split('\n')[0] if text else ""
                    })
                    
                except Exception as e:
                    logger.warning(f"Error validating {doc_type} document {doc['filename']}: {e}")
            
            # Calculate rates
            if sample_size > 0:
                type_quality["classification_accuracy_rate"] = type_quality["classification_accuracy"] / sample_size
                type_quality["field_extraction_quality_rate"] = type_quality["field_extraction_quality"] / sample_size
            
            results["type_quality"][doc_type] = type_quality
        
        # Compare with expected distribution
        expected_distribution = self.metadata.get("document_types", {})
        results["expected_vs_actual"] = {
            "expected": expected_distribution,
            "actual": results["type_distribution"],
            "matches": expected_distribution == results["type_distribution"]
        }
        
        logger.info(f"Document type validation complete: {len(results['type_distribution'])} types found")
        return results
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")
        
        # Run all validations
        file_validation = self.validate_file_structure()
        content_validation = self.validate_text_content()
        type_validation = self.validate_document_types()
        
        # Overall assessment
        overall_score = 0
        max_score = 0
        
        # File structure score (20%)
        if file_validation["structure_valid"]:
            overall_score += 20
        max_score += 20
        
        # Content quality score (40%)
        content_score = (
            content_validation.get("parsing_success_rate", 0) * 0.4 +
            content_validation.get("classification_accuracy_rate", 0) * 0.3 +
            content_validation.get("field_extraction_success_rate", 0) * 0.3
        ) * 40
        overall_score += content_score
        max_score += 40
        
        # Type quality score (40%)
        type_scores = []
        for doc_type, quality in type_validation["type_quality"].items():
            type_score = (
                quality.get("classification_accuracy_rate", 0) * 0.6 +
                quality.get("field_extraction_quality_rate", 0) * 0.4
            )
            type_scores.append(type_score)
        
        if type_scores:
            avg_type_score = sum(type_scores) / len(type_scores) * 40
            overall_score += avg_type_score
        max_score += 40
        
        overall_percentage = (overall_score / max_score) * 100 if max_score > 0 else 0
        
        report = {
            "validation_timestamp": self.metadata.get("generated_at"),
            "dataset_info": {
                "total_documents": self.metadata["total_documents"],
                "document_types": self.metadata["document_types"],
                "version": self.metadata["version"]
            },
            "file_structure": file_validation,
            "content_quality": content_validation,
            "document_types": type_validation,
            "overall_assessment": {
                "score": overall_percentage,
                "grade": self._get_grade(overall_percentage),
                "issues": len(content_validation.get("errors", [])),
                "recommendation": self._get_recommendation(overall_percentage)
            }
        }
        
        return report
    
    def _get_grade(self, score: float) -> str:
        """Get letter grade based on score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 90:
            return "Excellent quality dataset, ready for production use"
        elif score >= 80:
            return "Good quality dataset, minor improvements recommended"
        elif score >= 70:
            return "Acceptable quality, moderate improvements needed"
        elif score >= 60:
            return "Below average quality, significant improvements required"
        else:
            return "Poor quality dataset, major revision needed"

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate synthetic dataset v2')
    parser.add_argument('--dataset', type=str, default='data/synthetic_v2', help='Dataset directory')
    parser.add_argument('--output', type=str, help='Output report file (JSON)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create validator
        validator = SyntheticDatasetValidator(args.dataset)
        
        # Generate report
        report = validator.generate_validation_report()
        
        # Print summary
        print(f"\n🧪 Synthetic Dataset v2 Validation Report")
        print(f"=" * 50)
        print(f"📊 Dataset: {validator.dataset_dir}")
        print(f"📄 Total Documents: {report['dataset_info']['total_documents']}")
        print(f"📈 Document Types: {report['dataset_info']['document_types']}")
        print(f"⭐ Overall Score: {report['overall_assessment']['score']:.1f}% ({report['overall_assessment']['grade']})")
        print(f"💡 Recommendation: {report['overall_assessment']['recommendation']}")
        
        # Detailed results
        print(f"\n📁 File Structure:")
        file_results = report['file_structure']
        print(f"   Valid: {'✅' if file_results['structure_valid'] else '❌'}")
        print(f"   Files: TXT={file_results['file_types']['txt']}, PDF={file_results['file_types']['pdf']}, PNG={file_results['file_types']['png']}")
        
        print(f"\n📝 Content Quality:")
        content_results = report['content_quality']
        print(f"   Parsing Success: {content_results.get('parsing_success_rate', 0):.1%}")
        print(f"   Classification Accuracy: {content_results.get('classification_accuracy_rate', 0):.1%}")
        print(f"   Field Extraction Success: {content_results.get('field_extraction_success_rate', 0):.1%}")
        print(f"   Average Russian Text Ratio: {content_results.get('content_quality', {}).get('russian_ratio', 0):.1%}")
        
        print(f"\n📋 Document Types:")
        for doc_type, quality in report['document_types']['type_quality'].items():
            print(f"   {doc_type}: Classification={quality.get('classification_accuracy_rate', 0):.1%}, Fields={quality.get('field_extraction_quality_rate', 0):.1%}")
        
        if report['overall_assessment']['issues'] > 0:
            print(f"\n⚠️  Issues Found: {report['overall_assessment']['issues']}")
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Report saved: {args.output}")
        
        return 0 if report['overall_assessment']['score'] >= 70 else 1
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 