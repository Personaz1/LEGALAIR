#!/usr/bin/env python3
"""
Legal ASI - Data Upload Validation
Enhanced to support both real uploads and synthetic datasets v1/v2
"""

import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.preprocess import split_sections, analyze_document_structure
from ml.extract_fields import extract_fields_from_sections

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataUploadValidator:
    """Enhanced data upload validator supporting multiple dataset types"""
    
    def __init__(self):
        self.supported_formats = {'.txt', '.pdf', '.png', '.jpg', '.jpeg'}
        self.min_file_size = 100  # bytes
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Track processed files to avoid duplicates
        self.file_hashes: Set[str] = set()
        self.validation_results = []
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for duplicate detection"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def validate_file_format(self, file_path: Path) -> Dict[str, Any]:
        """Validate individual file format and properties"""
        result = {
            "file_path": str(file_path),
            "valid": False,
            "errors": [],
            "warnings": [],
            "properties": {}
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                result["errors"].append("File does not exist")
                return result
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_formats:
                result["errors"].append(f"Unsupported format: {file_path.suffix}")
                return result
            
            # Check file size
            file_size = file_path.stat().st_size
            result["properties"]["size_bytes"] = file_size
            
            if file_size < self.min_file_size:
                result["errors"].append(f"File too small: {file_size} bytes")
                return result
            
            if file_size > self.max_file_size:
                result["errors"].append(f"File too large: {file_size} bytes")
                return result
            
            # Calculate hash for duplicate detection
            file_hash = self.calculate_file_hash(file_path)
            result["properties"]["hash"] = file_hash
            
            if file_hash in self.file_hashes:
                result["warnings"].append("Duplicate file detected")
            else:
                self.file_hashes.add(file_hash)
            
            # Format-specific validation
            if file_path.suffix.lower() == '.txt':
                self._validate_text_file(file_path, result)
            elif file_path.suffix.lower() == '.pdf':
                self._validate_pdf_file(file_path, result)
            elif file_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                self._validate_image_file(file_path, result)
            
            # If no errors, mark as valid
            if not result["errors"]:
                result["valid"] = True
            
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
    
    def _validate_text_file(self, file_path: Path, result: Dict[str, Any]):
        """Validate text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result["properties"]["encoding"] = "utf-8"
            result["properties"]["char_count"] = len(content)
            result["properties"]["line_count"] = len(content.split('\n'))
            
            # Check for Russian content
            russian_chars = sum(1 for c in content if '\u0400' <= c <= '\u04FF')
            result["properties"]["russian_ratio"] = russian_chars / len(content) if content else 0
            
            if result["properties"]["russian_ratio"] < 0.1:
                result["warnings"].append("Low Russian text content")
            
            # Test document parsing
            try:
                structure_result = analyze_document_structure(content)
                result["properties"]["parsing_result"] = {
                    "completeness_score": structure_result["analysis"]["completeness_score"],
                    "document_type_indicators": structure_result["analysis"]["document_type_indicators"]
                }
            except Exception as e:
                result["warnings"].append(f"Parsing warning: {str(e)}")
            
        except UnicodeDecodeError:
            result["errors"].append("Text file encoding issue")
        except Exception as e:
            result["warnings"].append(f"Text validation warning: {str(e)}")
    
    def _validate_pdf_file(self, file_path: Path, result: Dict[str, Any]):
        """Validate PDF file"""
        try:
            # Basic PDF validation (header check)
            with open(file_path, 'rb') as f:
                header = f.read(8)
            
            if header.startswith(b'%PDF-'):
                result["properties"]["pdf_version"] = header.decode('ascii', errors='ignore')
            else:
                result["errors"].append("Invalid PDF header")
                
        except Exception as e:
            result["warnings"].append(f"PDF validation warning: {str(e)}")
    
    def _validate_image_file(self, file_path: Path, result: Dict[str, Any]):
        """Validate image file"""
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                result["properties"]["image_format"] = img.format
                result["properties"]["dimensions"] = img.size
                result["properties"]["mode"] = img.mode
                
                # Check resolution
                width, height = img.size
                if width < 300 or height < 300:
                    result["warnings"].append("Low resolution image")
                
                # Check for reasonable document aspect ratio
                aspect_ratio = width / height
                if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                    result["warnings"].append("Unusual aspect ratio for document")
                
        except Exception as e:
            result["errors"].append(f"Image validation error: {str(e)}")
    
    def validate_directory(self, directory: Path, recursive: bool = True) -> Dict[str, Any]:
        """Validate all files in a directory"""
        results = {
            "directory": str(directory),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "files_with_warnings": 0,
            "file_results": [],
            "summary": {},
            "recommendations": []
        }
        
        if not directory.exists():
            results["error"] = "Directory does not exist"
            return results
        
        # Find all files
        if recursive:
            files = [f for f in directory.rglob('*') if f.is_file()]
        else:
            files = [f for f in directory.iterdir() if f.is_file()]
        
        results["total_files"] = len(files)
        
        # Validate each file
        for file_path in files:
            # Skip hidden files and system files
            if file_path.name.startswith('.') or file_path.name.startswith('_'):
                continue
            
            file_result = self.validate_file_format(file_path)
            results["file_results"].append(file_result)
            
            if file_result["valid"]:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
            
            if file_result["warnings"]:
                results["files_with_warnings"] += 1
        
        # Generate summary
        self._generate_directory_summary(results)
        
        return results
    
    def _generate_directory_summary(self, results: Dict[str, Any]):
        """Generate summary and recommendations for directory validation"""
        total = results["total_files"]
        valid = results["valid_files"]
        invalid = results["invalid_files"]
        warnings = results["files_with_warnings"]
        
        results["summary"] = {
            "success_rate": valid / total if total > 0 else 0,
            "error_rate": invalid / total if total > 0 else 0,
            "warning_rate": warnings / total if total > 0 else 0
        }
        
        # Recommendations
        if results["summary"]["error_rate"] > 0.1:
            results["recommendations"].append("High error rate - check file formats and integrity")
        
        if results["summary"]["warning_rate"] > 0.3:
            results["recommendations"].append("Many files have warnings - review content quality")
        
        if valid < 10:
            results["recommendations"].append("Consider adding more documents for better dataset quality")
        
        # Format distribution
        format_counts = {}
        for file_result in results["file_results"]:
            if file_result["valid"]:
                file_path = Path(file_result["file_path"])
                ext = file_path.suffix.lower()
                format_counts[ext] = format_counts.get(ext, 0) + 1
        
        results["summary"]["format_distribution"] = format_counts
    
    def validate_synthetic_dataset(self, dataset_dir: Path) -> Dict[str, Any]:
        """Validate synthetic dataset with metadata"""
        results = {
            "dataset_type": "synthetic",
            "directory": str(dataset_dir),
            "metadata_valid": False,
            "structure_valid": False,
            "content_validation": {},
            "recommendations": []
        }
        
        # Check for metadata file
        metadata_files = ["dataset.json", "dataset_v2.json", "metadata.json"]
        metadata_path = None
        
        for metadata_file in metadata_files:
            potential_path = dataset_dir / metadata_file
            if potential_path.exists():
                metadata_path = potential_path
                break
        
        if metadata_path:
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                results["metadata"] = metadata
                results["metadata_valid"] = True
                
                # Validate structure based on metadata
                if "documents" in metadata:
                    structure_result = self._validate_synthetic_structure(dataset_dir, metadata)
                    results.update(structure_result)
                
            except Exception as e:
                results["metadata_error"] = str(e)
        else:
            results["recommendations"].append("Add metadata file for better tracking")
        
        # Validate file content regardless of metadata
        content_validation = self.validate_directory(dataset_dir)
        results["content_validation"] = content_validation
        
        return results
    
    def _validate_synthetic_structure(self, dataset_dir: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate synthetic dataset structure against metadata"""
        results = {
            "structure_valid": True,
            "expected_files": 0,
            "found_files": 0,
            "missing_files": [],
            "unexpected_files": []
        }
        
        expected_files = set()
        
        # Build expected file list from metadata
        for doc in metadata.get("documents", []):
            if "files" in doc:
                for file_type, relative_path in doc["files"].items():
                    expected_file = dataset_dir / relative_path
                    expected_files.add(str(expected_file))
        
        results["expected_files"] = len(expected_files)
        
        # Check which files exist
        for expected_file in expected_files:
            if Path(expected_file).exists():
                results["found_files"] += 1
            else:
                results["missing_files"].append(expected_file)
                results["structure_valid"] = False
        
        # Check for unexpected files
        all_files = {str(f) for f in dataset_dir.rglob('*') if f.is_file() and not f.name.startswith('.')}
        unexpected = all_files - expected_files - {str(dataset_dir / "dataset.json"), str(dataset_dir / "dataset_v2.json")}
        
        results["unexpected_files"] = list(unexpected)
        
        return results
    
    def generate_validation_report(self, directories: List[str]) -> Dict[str, Any]:
        """Generate comprehensive validation report for multiple directories"""
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "directories_validated": len(directories),
            "overall_summary": {
                "total_files": 0,
                "valid_files": 0,
                "invalid_files": 0,
                "total_datasets": 0
            },
            "directory_results": [],
            "recommendations": []
        }
        
        for directory_path in directories:
            directory = Path(directory_path)
            logger.info(f"Validating directory: {directory}")
            
            if directory.name.startswith('synthetic'):
                # Synthetic dataset validation
                dir_result = self.validate_synthetic_dataset(directory)
            else:
                # Regular directory validation
                dir_result = self.validate_directory(directory)
            
            report["directory_results"].append(dir_result)
            
            # Update overall summary
            if "content_validation" in dir_result:
                content = dir_result["content_validation"]
                report["overall_summary"]["total_files"] += content.get("total_files", 0)
                report["overall_summary"]["valid_files"] += content.get("valid_files", 0)
                report["overall_summary"]["invalid_files"] += content.get("invalid_files", 0)
            else:
                report["overall_summary"]["total_files"] += dir_result.get("total_files", 0)
                report["overall_summary"]["valid_files"] += dir_result.get("valid_files", 0)
                report["overall_summary"]["invalid_files"] += dir_result.get("invalid_files", 0)
            
            report["overall_summary"]["total_datasets"] += 1
        
        # Generate overall recommendations
        self._generate_overall_recommendations(report)
        
        return report
    
    def _generate_overall_recommendations(self, report: Dict[str, Any]):
        """Generate overall recommendations based on validation results"""
        total_files = report["overall_summary"]["total_files"]
        valid_files = report["overall_summary"]["valid_files"]
        
        if total_files == 0:
            report["recommendations"].append("No files found - add some documents to validate")
            return
        
        success_rate = valid_files / total_files
        
        if success_rate < 0.7:
            report["recommendations"].append("Low overall success rate - review data quality")
        elif success_rate < 0.9:
            report["recommendations"].append("Good data quality - minor improvements recommended")
        else:
            report["recommendations"].append("Excellent data quality - ready for use")
        
        if total_files < 50:
            report["recommendations"].append("Consider adding more documents for better model training")
        
        # Check for dataset diversity
        synthetic_count = sum(1 for result in report["directory_results"] 
                            if result.get("dataset_type") == "synthetic")
        
        if synthetic_count > 0:
            report["recommendations"].append(f"Found {synthetic_count} synthetic datasets - good for testing")

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate data uploads and datasets')
    parser.add_argument('directories', nargs='+', help='Directories to validate')
    parser.add_argument('--output', type=str, help='Output report file (JSON)')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create validator
        validator = DataUploadValidator()
        
        # Generate report
        report = validator.generate_validation_report(args.directories)
        
        # Output results
        if args.format == 'json' or args.output:
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"Report saved: {args.output}")
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            # Text format output
            print(f"\n📊 Data Validation Report")
            print(f"=" * 50)
            print(f"🕐 Timestamp: {report['validation_timestamp']}")
            print(f"📁 Directories: {report['directories_validated']}")
            print(f"📄 Total Files: {report['overall_summary']['total_files']}")
            print(f"✅ Valid Files: {report['overall_summary']['valid_files']}")
            print(f"❌ Invalid Files: {report['overall_summary']['invalid_files']}")
            
            success_rate = report['overall_summary']['valid_files'] / report['overall_summary']['total_files'] if report['overall_summary']['total_files'] > 0 else 0
            print(f"📈 Success Rate: {success_rate:.1%}")
            
            if report["recommendations"]:
                print(f"\n💡 Recommendations:")
                for rec in report["recommendations"]:
                    print(f"   • {rec}")
            
            # Directory details
            for dir_result in report["directory_results"]:
                print(f"\n📂 {dir_result['directory']}:")
                if dir_result.get("dataset_type") == "synthetic":
                    print(f"   Type: Synthetic Dataset")
                    print(f"   Metadata: {'✅' if dir_result.get('metadata_valid') else '❌'}")
                    print(f"   Structure: {'✅' if dir_result.get('structure_valid') else '❌'}")
                    if "content_validation" in dir_result:
                        content = dir_result["content_validation"]
                        print(f"   Files: {content.get('valid_files', 0)}/{content.get('total_files', 0)}")
                else:
                    print(f"   Files: {dir_result.get('valid_files', 0)}/{dir_result.get('total_files', 0)}")
                    if dir_result.get('summary', {}).get('format_distribution'):
                        print(f"   Formats: {dir_result['summary']['format_distribution']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 