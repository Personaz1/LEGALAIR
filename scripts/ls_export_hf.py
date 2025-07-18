#!/usr/bin/env python3
"""
Label Studio Export to HuggingFace Dataset
Export annotated data for model training
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from datasets import Dataset, DatasetDict
    from datasets.features import Features, Value, Sequence, ClassLabel
except ImportError:
    print("❌ HuggingFace datasets not installed. Run: pip install datasets")
    sys.exit(1)

class LabelStudioExporter:
    def __init__(
        self, 
        url: str = "http://localhost:8080",
        api_key: str = None
    ):
        self.base_url = url.rstrip('/')
        self.api_key = api_key or os.getenv('LABEL_STUDIO_API_KEY')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Token {self.api_key}'
            })
    
    def get_project_info(self, project_id: int) -> Dict[str, Any]:
        """Get project information"""
        response = self.session.get(f"{self.base_url}/api/projects/{project_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get project info: {response.status_code}")
    
    def export_annotations(self, project_id: int, export_type: str = "JSON") -> List[Dict[str, Any]]:
        """Export annotations from Label Studio project"""
        
        # Get export snapshot
        response = self.session.get(
            f"{self.base_url}/api/projects/{project_id}/export",
            params={"exportType": export_type}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to export annotations: {response.status_code}")
    
    def transform_for_classification(self, annotations: List[Dict[str, Any]]) -> Dict[str, List]:
        """Transform annotations for document classification task"""
        
        texts = []
        labels = []
        metadata = []
        
        for annotation in annotations:
            if not annotation.get('annotations'):
                continue  # Skip unannotated tasks
            
            text = annotation.get('data', {}).get('text', '')
            if not text:
                continue
            
            # Get the first annotation (assuming single annotator)
            ann = annotation['annotations'][0]
            
            # Extract document type
            document_type = None
            for result in ann.get('result', []):
                if result.get('from_name') == 'document_type':
                    document_type = result.get('value', {}).get('choices', [None])[0]
                    break
            
            if document_type:
                texts.append(text)
                labels.append(document_type)
                metadata.append({
                    'task_id': annotation.get('id'),
                    'filename': annotation.get('data', {}).get('filename', ''),
                    'source': annotation.get('data', {}).get('source', ''),
                    'annotation_id': ann.get('id'),
                    'annotator': ann.get('completed_by'),
                    'created_at': ann.get('created_at'),
                    'char_count': len(text)
                })
        
        return {
            'text': texts,
            'label': labels,
            'metadata': metadata
        }
    
    def transform_for_ner(self, annotations: List[Dict[str, Any]]) -> Dict[str, List]:
        """Transform annotations for Named Entity Recognition task"""
        
        texts = []
        entities = []
        metadata = []
        
        for annotation in annotations:
            if not annotation.get('annotations'):
                continue
            
            text = annotation.get('data', {}).get('text', '')
            if not text:
                continue
            
            ann = annotation['annotations'][0]
            
            # Extract entities
            task_entities = []
            for result in ann.get('result', []):
                if result.get('from_name') == 'entities' and result.get('type') == 'labels':
                    entity = {
                        'start': result['value']['start'],
                        'end': result['value']['end'],
                        'label': result['value']['labels'][0],
                        'text': result['value']['text']
                    }
                    task_entities.append(entity)
            
            texts.append(text)
            entities.append(task_entities)
            metadata.append({
                'task_id': annotation.get('id'),
                'filename': annotation.get('data', {}).get('filename', ''),
                'entity_count': len(task_entities)
            })
        
        return {
            'text': texts,
            'entities': entities,
            'metadata': metadata
        }
    
    def create_classification_dataset(self, data: Dict[str, List]) -> Dataset:
        """Create HuggingFace dataset for classification"""
        
        # Define features
        features = Features({
            'text': Value('string'),
            'label': ClassLabel(names=['bill_of_exchange', 'fine_notice', 'protocol', 'other']),
            'metadata': {
                'task_id': Value('int64'),
                'filename': Value('string'),
                'source': Value('string'),
                'char_count': Value('int64')
            }
        })
        
        # Prepare dataset
        dataset_dict = {
            'text': data['text'],
            'label': data['label'],
            'metadata': data['metadata']
        }
        
        return Dataset.from_dict(dataset_dict, features=features)
    
    def create_ner_dataset(self, data: Dict[str, List]) -> Dataset:
        """Create HuggingFace dataset for NER"""
        
        # Define features
        features = Features({
            'text': Value('string'),
            'entities': Sequence({
                'start': Value('int64'),
                'end': Value('int64'),
                'label': ClassLabel(names=['PERSON', 'ORGANIZATION', 'DATE', 'MONEY', 'DOCUMENT_NUMBER', 'LEGAL_ARTICLE', 'ADDRESS']),
                'text': Value('string')
            }),
            'metadata': {
                'task_id': Value('int64'),
                'filename': Value('string'),
                'entity_count': Value('int64')
            }
        })
        
        return Dataset.from_dict({
            'text': data['text'],
            'entities': data['entities'],
            'metadata': data['metadata']
        }, features=features)
    
    def split_dataset(self, dataset: Dataset, train_ratio: float = 0.8) -> DatasetDict:
        """Split dataset into train/validation sets"""
        
        # Shuffle and split
        dataset = dataset.shuffle(seed=42)
        train_size = int(len(dataset) * train_ratio)
        
        train_dataset = dataset.select(range(train_size))
        val_dataset = dataset.select(range(train_size, len(dataset)))
        
        return DatasetDict({
            'train': train_dataset,
            'validation': val_dataset
        })

def main():
    parser = argparse.ArgumentParser(description="Export Label Studio annotations to HuggingFace Dataset")
    parser.add_argument("project_id", type=int, help="Label Studio project ID")
    parser.add_argument("--url", default="http://localhost:8080", help="Label Studio URL")
    parser.add_argument("--api-key", help="Label Studio API key")
    parser.add_argument("--output-dir", default="./hf_dataset", help="Output directory for dataset")
    parser.add_argument("--task-type", choices=["classification", "ner", "both"], default="both", help="Task type to export")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train/validation split ratio")
    parser.add_argument("--min-annotations", type=int, default=1, help="Minimum annotations per task")
    
    args = parser.parse_args()
    
    print(f"🚀 Label Studio → HuggingFace Dataset Export")
    print(f"📊 Project ID: {args.project_id}")
    print(f"🌐 Label Studio URL: {args.url}")
    print(f"📁 Output directory: {args.output_dir}")
    
    # Initialize exporter
    exporter = LabelStudioExporter(
        url=args.url,
        api_key=args.api_key
    )
    
    try:
        # Get project info
        project_info = exporter.get_project_info(args.project_id)
        print(f"📋 Project: {project_info['title']}")
        
        # Export annotations
        print(f"\n⬇️  Exporting annotations...")
        annotations = exporter.export_annotations(args.project_id)
        
        # Filter completed annotations
        completed_annotations = [
            ann for ann in annotations 
            if ann.get('annotations') and len(ann['annotations']) >= args.min_annotations
        ]
        
        print(f"✅ Found {len(completed_annotations)}/{len(annotations)} completed tasks")
        
        if len(completed_annotations) == 0:
            print("❌ No completed annotations found")
            sys.exit(1)
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Export classification dataset
        if args.task_type in ["classification", "both"]:
            print(f"\n📚 Creating classification dataset...")
            
            class_data = exporter.transform_for_classification(completed_annotations)
            if class_data['text']:
                class_dataset = exporter.create_classification_dataset(class_data)
                class_split = exporter.split_dataset(class_dataset, args.train_ratio)
                
                class_dir = output_dir / "classification"
                class_split.save_to_disk(str(class_dir))
                
                print(f"✅ Classification dataset saved to {class_dir}")
                print(f"   📊 Train: {len(class_split['train'])} samples")
                print(f"   📊 Validation: {len(class_split['validation'])} samples")
                
                # Save label distribution
                label_counts = {}
                for label in class_data['label']:
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                with open(class_dir / "label_distribution.json", 'w', encoding='utf-8') as f:
                    json.dump(label_counts, f, indent=2, ensure_ascii=False)
            else:
                print("⚠️  No classification annotations found")
        
        # Export NER dataset
        if args.task_type in ["ner", "both"]:
            print(f"\n🏷️  Creating NER dataset...")
            
            ner_data = exporter.transform_for_ner(completed_annotations)
            if ner_data['text']:
                ner_dataset = exporter.create_ner_dataset(ner_data)
                ner_split = exporter.split_dataset(ner_dataset, args.train_ratio)
                
                ner_dir = output_dir / "ner"
                ner_split.save_to_disk(str(ner_dir))
                
                print(f"✅ NER dataset saved to {ner_dir}")
                print(f"   📊 Train: {len(ner_split['train'])} samples")
                print(f"   📊 Validation: {len(ner_split['validation'])} samples")
                
                # Save entity statistics
                entity_counts = {}
                total_entities = 0
                for entities_list in ner_data['entities']:
                    for entity in entities_list:
                        label = entity['label']
                        entity_counts[label] = entity_counts.get(label, 0) + 1
                        total_entities += 1
                
                stats = {
                    'total_entities': total_entities,
                    'entity_counts': entity_counts,
                    'avg_entities_per_doc': total_entities / len(ner_data['text']) if ner_data['text'] else 0
                }
                
                with open(ner_dir / "entity_statistics.json", 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
            else:
                print("⚠️  No NER annotations found")
        
        # Save export metadata
        export_metadata = {
            'export_date': datetime.now().isoformat(),
            'project_id': args.project_id,
            'project_title': project_info['title'],
            'total_tasks': len(annotations),
            'completed_tasks': len(completed_annotations),
            'task_type': args.task_type,
            'train_ratio': args.train_ratio,
            'min_annotations': args.min_annotations
        }
        
        with open(output_dir / "export_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(export_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Export complete!")
        print(f"📊 Exported {len(completed_annotations)} annotated tasks")
        print(f"📁 Dataset saved to: {output_dir}")
        print(f"📄 Load with: `from datasets import load_from_disk; dataset = load_from_disk('{output_dir}/classification')`")
        
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 