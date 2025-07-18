#!/usr/bin/env python3
"""
Label Studio Bulk Import Script
Upload documents to Label Studio for annotation
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Any
import base64
from urllib.parse import urljoin

class LabelStudioImporter:
    def __init__(
        self, 
        url: str = "http://localhost:8080",
        api_key: str = None,
        project_id: int = None
    ):
        self.base_url = url.rstrip('/')
        self.api_key = api_key or os.getenv('LABEL_STUDIO_API_KEY')
        self.project_id = project_id
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Token {self.api_key}'
            })
    
    def create_project(self, name: str, description: str = "") -> int:
        """Create a new Label Studio project"""
        
        # Label config for legal document annotation
        label_config = """
        <View>
          <Text name="text" value="$text"/>
          <Choices name="document_type" toName="text" choice="single-radio">
            <Choice value="bill_of_exchange"/>
            <Choice value="fine_notice"/>
            <Choice value="protocol"/>
            <Choice value="other"/>
          </Choices>
          
          <Labels name="entities" toName="text" choice="multiple">
            <Label value="PERSON" background="red"/>
            <Label value="ORGANIZATION" background="blue"/>
            <Label value="DATE" background="green"/>
            <Label value="MONEY" background="orange"/>
            <Label value="DOCUMENT_NUMBER" background="purple"/>
            <Label value="LEGAL_ARTICLE" background="brown"/>
            <Label value="ADDRESS" background="yellow"/>
          </Labels>
        </View>
        """
        
        payload = {
            "title": name,
            "description": description,
            "label_config": label_config,
            "expert_instruction": "Аннотирование юридических документов:\n1. Выберите тип документа\n2. Выделите и пометьте именованные сущности\n3. Проверьте точность извлечения текста"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/projects/",
            json=payload
        )
        
        if response.status_code == 201:
            project = response.json()
            print(f"✅ Project created: {project['title']} (ID: {project['id']})")
            return project['id']
        else:
            print(f"❌ Failed to create project: {response.status_code}")
            print(response.text)
            return None
    
    def upload_tasks(self, tasks: List[Dict[str, Any]]) -> List[int]:
        """Upload tasks to Label Studio project"""
        
        if not self.project_id:
            raise ValueError("Project ID is required for uploading tasks")
        
        task_ids = []
        
        for i, task in enumerate(tasks):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/projects/{self.project_id}/import",
                    json=[task]
                )
                
                if response.status_code == 201:
                    result = response.json()
                    if result and len(result) > 0:
                        task_id = result[0]['id']
                        task_ids.append(task_id)
                        print(f"✅ Uploaded task {i+1}/{len(tasks)}: {task.get('data', {}).get('filename', 'N/A')}")
                    else:
                        print(f"⚠️  Task {i+1} uploaded but no ID returned")
                else:
                    print(f"❌ Failed to upload task {i+1}: {response.status_code}")
                    print(response.text)
            
            except Exception as e:
                print(f"❌ Error uploading task {i+1}: {str(e)}")
        
        return task_ids
    
    def process_directory(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Process directory with text and image files"""
        
        tasks = []
        
        # Look for paired files (text + image)
        text_files = list(data_dir.glob("*.txt"))
        
        for text_file in text_files:
            try:
                # Read text content
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                
                if not text_content:
                    print(f"⚠️  Skipping empty file: {text_file.name}")
                    continue
                
                # Look for corresponding image
                image_file = None
                base_name = text_file.stem
                
                for ext in ['.png', '.jpg', '.jpeg']:
                    potential_image = data_dir / f"{base_name}{ext}"
                    if potential_image.exists():
                        image_file = potential_image
                        break
                
                # Create task
                task_data = {
                    "text": text_content,
                    "filename": text_file.name,
                    "source": str(text_file.parent.name)
                }
                
                # Add image if available
                if image_file:
                    try:
                        with open(image_file, 'rb') as f:
                            image_data = base64.b64encode(f.read()).decode('utf-8')
                        
                        task_data["image"] = f"data:image/{image_file.suffix[1:]};base64,{image_data}"
                        task_data["image_filename"] = image_file.name
                    except Exception as e:
                        print(f"⚠️  Failed to encode image {image_file.name}: {str(e)}")
                
                task = {
                    "data": task_data,
                    "meta": {
                        "source_file": str(text_file),
                        "has_image": image_file is not None,
                        "char_count": len(text_content),
                        "processing_date": "2024-07-18"
                    }
                }
                
                tasks.append(task)
                
            except Exception as e:
                print(f"❌ Error processing {text_file.name}: {str(e)}")
        
        return tasks

def main():
    parser = argparse.ArgumentParser(description="Bulk import data to Label Studio")
    parser.add_argument("data_dir", help="Directory containing text and image files")
    parser.add_argument("--url", default="http://localhost:8080", help="Label Studio URL")
    parser.add_argument("--api-key", help="Label Studio API key (or set LABEL_STUDIO_API_KEY env var)")
    parser.add_argument("--project-id", type=int, help="Existing project ID (or create new)")
    parser.add_argument("--project-name", default="Legal AI Annotation", help="Project name for new project")
    parser.add_argument("--dry-run", action="store_true", help="Show tasks without uploading")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        sys.exit(1)
    
    print(f"🚀 Label Studio Bulk Import")
    print(f"📁 Data directory: {data_dir}")
    print(f"🌐 Label Studio URL: {args.url}")
    
    # Initialize importer
    importer = LabelStudioImporter(
        url=args.url,
        api_key=args.api_key,
        project_id=args.project_id
    )
    
    # Create project if needed
    if not args.project_id:
        project_id = importer.create_project(
            name=args.project_name,
            description=f"Legal document annotation from {data_dir.name}"
        )
        if not project_id:
            print("❌ Failed to create project")
            sys.exit(1)
        importer.project_id = project_id
    
    # Process files
    print(f"\n📋 Processing files in {data_dir}...")
    tasks = importer.process_directory(data_dir)
    
    if not tasks:
        print("❌ No valid tasks found")
        sys.exit(1)
    
    print(f"✅ Prepared {len(tasks)} tasks")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Tasks that would be uploaded:")
        for i, task in enumerate(tasks[:5]):  # Show first 5
            print(f"  {i+1}. {task['data'].get('filename', 'N/A')} ({task['meta']['char_count']} chars)")
        if len(tasks) > 5:
            print(f"  ... and {len(tasks) - 5} more")
        return
    
    # Upload tasks
    print(f"\n⬆️  Uploading {len(tasks)} tasks to project {importer.project_id}...")
    task_ids = importer.upload_tasks(tasks)
    
    print(f"\n✅ Upload complete!")
    print(f"📊 Successfully uploaded: {len(task_ids)}/{len(tasks)} tasks")
    print(f"🌐 Project URL: {args.url}/projects/{importer.project_id}/")

if __name__ == "__main__":
    main() 