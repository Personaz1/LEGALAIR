#!/usr/bin/env python3
"""
Legal ASI - Synthetic Test Data Generator
Generates synthetic legal documents for testing OCR and ML pipeline
"""

import os
import json
from datetime import datetime, timedelta
import random
from PIL import Image, ImageDraw, ImageFont
import uuid

# Russian legal document templates
BILL_OF_EXCHANGE_TEMPLATE = """
ВЕКСЕЛЬ № {doc_number}

Дата: {date}

Обязательство: {debtor_name} обязуется выплатить {creditor_org} 
сумму в размере {amount} рублей до {due_date}.

Основание: {legal_basis}

Должник: {debtor_name}
Паспорт: {passport_series} {passport_number}
Адрес: {address}

Кредитор: {creditor_org}
ИНН: {creditor_inn}

Подпись должника: _________________
Дата составления: {date}

Место составления: {location}
"""

FINE_NOTICE_TEMPLATE = """
ПОСТАНОВЛЕНИЕ об административном правонарушении
№ {doc_number} от {date}

Гражданин {violator_name} совершил административное правонарушение,
предусмотренное статьей {article} КоАП РФ ({violation_type}).

Место нарушения: {location}
Время нарушения: {violation_time}

Назначить административный штраф в размере {amount} рублей.

Нарушитель: {violator_name}
Паспорт: {passport_series} {passport_number}
Адрес: {address}

Инспектор: {inspector_name}
Должность: {inspector_position}

Дата составления: {date}
Место составления: {location}
"""

PROTOCOL_TEMPLATE = """
ПРОТОКОЛ заседания
№ {doc_number} от {date}

Организация: {organization}
Тип заседания: {meeting_type}

Председатель: {chairman_name}
Секретарь: {secretary_name}

Присутствовали:
{attendees}

ПОВЕСТКА ДНЯ:
{agenda_items}

РЕШЕНИЕ:
{decision}

Председатель: {chairman_name} _________________
Секретарь: {secretary_name} _________________

Дата: {date}
Место: {location}
"""

class SyntheticDataGenerator:
    """Generates synthetic legal documents for testing"""
    
    def __init__(self, output_dir="data/synthetic"):
        self.output_dir = output_dir
        self.ensure_output_dir()
        
        # Sample data pools
        self.names = [
            "Иванов Иван Иванович", "Петров Петр Петрович", "Сидоров Сидор Сидорович",
            "Смирнова Анна Ивановна", "Козлова Мария Петровна", "Новиков Алексей Сергеевич",
            "Морозов Дмитрий Александрович", "Федорова Елена Викторовна"
        ]
        
        self.organizations = [
            'ООО "Рога и Копыта"', 'ЗАО "Спектр"', 'ОАО "Газпром"',
            'ИП Иванов И.И.', 'ООО "Технологии будущего"', 'ЗАО "Финанс Групп"'
        ]
        
        self.locations = [
            "г. Москва", "г. Санкт-Петербург", "г. Новосибирск",
            "г. Екатеринбург", "г. Казань", "г. Челябинск"
        ]
        
        self.violation_types = [
            "превышение скорости", "нарушение правил парковки",
            "проезд на красный свет", "нарушение правил остановки"
        ]
        
        self.legal_articles = ["12.9", "12.16", "12.6", "12.19"]
        
    def ensure_output_dir(self):
        """Create output directories"""
        for subdir in ["bills", "fines", "protocols", "images", "metadata"]:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
    
    def generate_random_data(self):
        """Generate random data for document fields"""
        return {
            "doc_number": f"{random.randint(100000, 999999)}",
            "date": self.random_date().strftime("%d.%m.%Y"),
            "due_date": (self.random_date() + timedelta(days=random.randint(30, 365))).strftime("%d.%m.%Y"),
            "amount": f"{random.randint(5000, 500000):,}".replace(",", " "),
            "debtor_name": random.choice(self.names),
            "creditor_org": random.choice(self.organizations),
            "violator_name": random.choice(self.names),
            "inspector_name": random.choice(self.names),
            "chairman_name": random.choice(self.names),
            "secretary_name": random.choice(self.names),
            "organization": random.choice(self.organizations),
            "location": random.choice(self.locations),
            "passport_series": f"{random.randint(10, 99)}{random.randint(10, 99)}",
            "passport_number": f"{random.randint(100000, 999999)}",
            "creditor_inn": f"{random.randint(1000000000, 9999999999)}",
            "legal_basis": f"Договор № {random.randint(1, 999)} от {self.random_date().strftime('%d.%m.%Y')}",
            "article": random.choice(self.legal_articles),
            "violation_type": random.choice(self.violation_types),
            "violation_time": f"{random.randint(8, 22)}:{random.randint(10, 59):02d}",
            "inspector_position": "Инспектор ГИБДД",
            "meeting_type": "Совет директоров",
            "address": f"г. {random.choice(self.locations).split('. ')[1]}, ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина'])}, д. {random.randint(1, 200)}"
        }
    
    def random_date(self):
        """Generate random date within last 2 years"""
        start_date = datetime.now() - timedelta(days=730)
        random_days = random.randint(0, 730)
        return start_date + timedelta(days=random_days)
    
    def generate_attendees(self, count=3):
        """Generate attendees list for protocol"""
        attendees = random.sample(self.names, min(count, len(self.names)))
        return "\n".join([f"- {name}" for name in attendees])
    
    def generate_agenda_items(self, count=3):
        """Generate agenda items for protocol"""
        items = [
            "Утверждение финансового отчета",
            "Рассмотрение бюджета на следующий год",
            "Обсуждение кадровых вопросов",
            "Принятие решения о распределении прибыли",
            "Вопросы развития бизнеса"
        ]
        selected = random.sample(items, min(count, len(items)))
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(selected)])
    
    def generate_decision(self):
        """Generate decision text for protocol"""
        decisions = [
            "Утвердить представленный финансовый отчет единогласно.",
            "Принять бюджет на следующий год с учетом внесенных поправок.",
            "Одобрить предложенные кадровые изменения.",
            "Утвердить распределение прибыли согласно представленному плану."
        ]
        return random.choice(decisions)
    
    def create_bill_of_exchange(self, doc_id):
        """Generate bill of exchange document"""
        data = self.generate_random_data()
        text = BILL_OF_EXCHANGE_TEMPLATE.format(**data)
        
        metadata = {
            "document_id": doc_id,
            "document_type": "bill_of_exchange",
            "generated_at": datetime.now().isoformat(),
            "entities": {
                "PERSON": [data["debtor_name"]],
                "ORGANIZATION": [data["creditor_org"]],
                "DATE": [data["date"], data["due_date"]],
                "MONEY": [f"{data['amount']} рублей"],
                "DOCUMENT_NUMBER": [data["doc_number"]],
                "LOCATION": [data["location"]]
            }
        }
        
        return text, metadata
    
    def create_fine_notice(self, doc_id):
        """Generate fine notice document"""
        data = self.generate_random_data()
        text = FINE_NOTICE_TEMPLATE.format(**data)
        
        metadata = {
            "document_id": doc_id,
            "document_type": "fine_notice", 
            "generated_at": datetime.now().isoformat(),
            "entities": {
                "PERSON": [data["violator_name"], data["inspector_name"]],
                "DATE": [data["date"]],
                "MONEY": [f"{data['amount']} рублей"],
                "DOCUMENT_NUMBER": [data["doc_number"]],
                "LOCATION": [data["location"]],
                "LEGAL_BASIS": [f"статья {data['article']} КоАП РФ"]
            }
        }
        
        return text, metadata
    
    def create_protocol(self, doc_id):
        """Generate protocol document"""
        data = self.generate_random_data()
        data["attendees"] = self.generate_attendees()
        data["agenda_items"] = self.generate_agenda_items()
        data["decision"] = self.generate_decision()
        
        text = PROTOCOL_TEMPLATE.format(**data)
        
        metadata = {
            "document_id": doc_id,
            "document_type": "protocol",
            "generated_at": datetime.now().isoformat(),
            "entities": {
                "PERSON": [data["chairman_name"], data["secretary_name"]],
                "ORGANIZATION": [data["organization"]],
                "DATE": [data["date"]],
                "DOCUMENT_NUMBER": [data["doc_number"]],
                "LOCATION": [data["location"]]
            }
        }
        
        return text, metadata
    
    def text_to_image(self, text, filename):
        """Convert text to image for OCR testing"""
        # Create image with white background
        img_width, img_height = 800, 1200
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Add some margin
        margin = 50
        y_offset = margin
        line_height = 25
        
        # Split text into lines and draw
        lines = text.split('\n')
        for line in lines:
            # Word wrap for long lines
            if len(line) > 80:
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) <= 80:
                        current_line += " " + word if current_line else word
                    else:
                        if current_line:
                            draw.text((margin, y_offset), current_line, fill='black', font=font)
                            y_offset += line_height
                        current_line = word
                if current_line:
                    draw.text((margin, y_offset), current_line, fill='black', font=font)
                    y_offset += line_height
            else:
                draw.text((margin, y_offset), line, fill='black', font=font)
                y_offset += line_height
            
            # Check if we're running out of space
            if y_offset > img_height - 100:
                break
        
        # Save image
        image_path = os.path.join(self.output_dir, "images", filename)
        image.save(image_path, "PNG")
        return image_path
    
    def generate_documents(self, count_per_type=5):
        """Generate specified number of documents per type"""
        print(f"🏗️ Generating {count_per_type * 3} synthetic legal documents...")
        
        all_metadata = []
        
        # Generate bills of exchange
        for i in range(count_per_type):
            doc_id = f"bill_{i+1:03d}"
            text, metadata = self.create_bill_of_exchange(doc_id)
            
            # Save text file
            text_path = os.path.join(self.output_dir, "bills", f"{doc_id}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Create image
            image_path = self.text_to_image(text, f"{doc_id}.png")
            metadata["text_path"] = text_path
            metadata["image_path"] = image_path
            
            all_metadata.append(metadata)
            print(f"✅ Generated bill of exchange: {doc_id}")
        
        # Generate fine notices  
        for i in range(count_per_type):
            doc_id = f"fine_{i+1:03d}"
            text, metadata = self.create_fine_notice(doc_id)
            
            # Save text file
            text_path = os.path.join(self.output_dir, "fines", f"{doc_id}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Create image
            image_path = self.text_to_image(text, f"{doc_id}.png")
            metadata["text_path"] = text_path
            metadata["image_path"] = image_path
            
            all_metadata.append(metadata)
            print(f"✅ Generated fine notice: {doc_id}")
        
        # Generate protocols
        for i in range(count_per_type):
            doc_id = f"protocol_{i+1:03d}"
            text, metadata = self.create_protocol(doc_id)
            
            # Save text file
            text_path = os.path.join(self.output_dir, "protocols", f"{doc_id}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Create image
            image_path = self.text_to_image(text, f"{doc_id}.png")
            metadata["text_path"] = text_path
            metadata["image_path"] = image_path
            
            all_metadata.append(metadata)
            print(f"✅ Generated protocol: {doc_id}")
        
        # Save combined metadata
        metadata_path = os.path.join(self.output_dir, "metadata", "all_documents.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Generation complete:")
        print(f"   📄 {count_per_type * 3} text documents")
        print(f"   🖼️ {count_per_type * 3} synthetic images")
        print(f"   📋 Metadata saved to: {metadata_path}")
        
        return all_metadata

if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    
    # Generate documents (5 per type = 15 total)
    metadata = generator.generate_documents(count_per_type=5)
    
    print(f"\n🎯 Ready for testing with {len(metadata)} synthetic documents")
    print("📁 Files saved to: data/synthetic/")
    print("🔄 Use these for API testing and Label Studio workflow validation") 