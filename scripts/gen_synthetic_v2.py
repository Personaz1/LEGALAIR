#!/usr/bin/env python3
"""
Legal ASI - Synthetic Dataset v2 Generator
Enhanced document generation with PDF/PNG output, noise, and handwritten signatures
"""

import os
import sys
import json
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Core libraries
from jinja2 import Environment, BaseLoader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyntheticDataGeneratorV2:
    """Enhanced synthetic legal document generator"""
    
    def __init__(self, output_dir: str = "data/synthetic_v2"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "pdf").mkdir(exist_ok=True)
        (self.output_dir / "png").mkdir(exist_ok=True)
        (self.output_dir / "txt").mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Initialize data pools
        self._init_data_pools()
        
        # Document templates
        self._init_templates()
        
        logger.info(f"Synthetic generator v2 initialized: {self.output_dir}")
    
    def _init_data_pools(self):
        """Initialize pools of realistic Russian data"""
        
        self.names = {
            "male_first": ["Александр", "Андрей", "Алексей", "Дмитрий", "Евгений", "Игорь", "Иван", "Максим", "Михаил", "Николай", "Олег", "Павел", "Петр", "Роман", "Сергей", "Станислав", "Владимир"],
            "female_first": ["Анна", "Елена", "Ирина", "Мария", "Наталья", "Ольга", "Светлана", "Татьяна", "Юлия"],
            "last": ["Иванов", "Петров", "Сидоров", "Козлов", "Новиков", "Морозов", "Петров", "Волков", "Соловьев", "Васильев", "Зайцев", "Павлов", "Семенов", "Голубев", "Виноградов", "Богданов", "Воробьев", "Федоров", "Михайлов", "Беляев", "Тарасов", "Белов", "Комаров"],
            "patronymic": ["Александрович", "Андреевич", "Алексеевич", "Дмитриевич", "Евгеньевич", "Игоревич", "Иванович", "Максимович", "Михайлович", "Николаевич", "Олегович", "Павлович", "Петрович", "Романович", "Сергеевич", "Станиславович", "Владимирович"]
        }
        
        self.organizations = [
            'ООО "Рога и Копыта"', 'ЗАО "Финанс Групп"', 'ПАО "Технологии будущего"',
            'ООО "Бизнес Решения"', 'ЗАО "Капитал Инвест"', 'ООО "Торговый Дом"',
            'ПАО "Промышленность"', 'ООО "Строй Комплекс"', 'ЗАО "Нефть Газ"',
            'ООО "Металл Сервис"', 'ПАО "Энерго Системы"', 'ООО "Авто Трейд"'
        ]
        
        self.addresses = [
            "г. Москва, ул. Ленина, д. {}",
            "г. Санкт-Петербург, Невский пр., д. {}",
            "г. Новосибирск, ул. Красный пр., д. {}",
            "г. Екатеринбург, ул. Малышева, д. {}",
            "г. Казань, ул. Баумана, д. {}",
            "г. Нижний Новгород, ул. Горького, д. {}",
            "г. Челябинск, ул. Кирова, д. {}",
            "г. Самара, ул. Молодогвардейская, д. {}",
            "г. Омск, ул. Ленинградская, д. {}",
            "г. Ростов-на-Дону, пр. Буденновский, д. {}"
        ]
        
        self.koap_articles = [
            "12.9", "12.15", "12.16", "12.24", "20.4", "20.20", "20.25",
            "15.25", "19.3", "19.5", "8.23", "6.3", "7.12"
        ]
        
        self.violation_types = [
            "превышение скорости", "проезд на красный свет", "неправильная парковка",
            "нарушение ПДД", "несоблюдение дистанции", "обгон в неположенном месте",
            "нарушение разметки", "превышение массы", "нарушение режима труда"
        ]
        
        self.inspector_ranks = [
            "Инспектор ГИБДД", "Старший инспектор", "Лейтенант полиции",
            "Капитан полиции", "Майор полиции"
        ]
    
    def _init_templates(self):
        """Initialize Jinja2 templates for each document type"""
        
        self.templates = {
            "bill_of_exchange": """ВЕКСЕЛЬ № {{ doc_number }} от {{ doc_date }}

Я, {{ debtor_name }}, проживающий по адресу: {{ debtor_address }},
паспорт {{ debtor_passport }}, обязуюсь выплатить {{ creditor_name }}
сумму в размере {{ amount }} рублей к {{ payment_date }}.

ОСНОВАНИЕ: {{ basis }}

ДОЛЖНИК:
Ф.И.О.: {{ debtor_name }}
Паспорт: {{ debtor_passport }}
Адрес: {{ debtor_address }}

КРЕДИТОР:
{{ creditor_name }}
ИНН: {{ creditor_inn }}

Подпись должника: {{ signature_line }}
Дата составления: {{ doc_date }}
Место составления: {{ place }}""",

            "fine_notice": """ПОСТАНОВЛЕНИЕ об административном правонарушении
№ {{ doc_number }} от {{ doc_date }}

Гражданин {{ violator_name }} совершил административное правонарушение,
предусмотренное статьей {{ article }} КоАП РФ ({{ violation_type }}).

МЕСТО НАРУШЕНИЯ: {{ violation_place }}
ВРЕМЯ НАРУШЕНИЯ: {{ violation_time }}

На основании изложенного, руководствуясь статьей {{ article }} КоАП РФ,

ПОСТАНОВЛЯЮ:

Назначить {{ violator_name }} административный штраф в размере {{ fine_amount }} рублей.

НАРУШИТЕЛЬ:
Ф.И.О.: {{ violator_name }}
Паспорт: {{ violator_passport }}
Адрес: {{ violator_address }}

{{ inspector_rank }}: {{ inspector_name }}

Дата составления: {{ doc_date }}
Место составления: {{ place }}""",

            "protocol": """ПРОТОКОЛ заседания № {{ doc_number }} от {{ doc_date }}

ОРГАНИЗАЦИЯ: {{ organization }}
ТИП ЗАСЕДАНИЯ: {{ meeting_type }}

ПРЕДСЕДАТЕЛЬ: {{ chairman_name }}
СЕКРЕТАРЬ: {{ secretary_name }}

ПРИСУТСТВОВАЛИ:
{{ participants }}

ПОВЕСТКА ДНЯ:
{{ agenda }}

РЕШЕНИЕ:
{{ decision }}

Председатель: {{ chairman_name }} {{ signature_line }}
Секретарь: {{ secretary_name }} {{ signature_line }}

Дата: {{ doc_date }}
Место: {{ place }}"""
        }
    
    def _generate_person_name(self, gender: str = None) -> Dict[str, str]:
        """Generate realistic Russian person name"""
        if gender is None:
            gender = random.choice(["male", "female"])
        
        if gender == "male":
            first = random.choice(self.names["male_first"])
        else:
            first = random.choice(self.names["female_first"])
        
        last = random.choice(self.names["last"])
        patronymic = random.choice(self.names["patronymic"])
        
        return {
            "full": f"{last} {first} {patronymic}",
            "short": f"{last} {first[0]}.{patronymic[0]}.",
            "first": first,
            "last": last,
            "patronymic": patronymic
        }
    
    def _generate_passport(self) -> str:
        """Generate realistic passport number"""
        series = random.randint(4500, 4599)
        number = random.randint(100000, 999999)
        return f"{series} {number}"
    
    def _generate_inn(self, is_individual: bool = True) -> str:
        """Generate realistic INN"""
        if is_individual:
            return str(random.randint(100000000000, 999999999999))  # 12 digits
        else:
            return str(random.randint(1000000000, 9999999999))  # 10 digits
    
    def _generate_date(self, start_days_ago: int = 365, end_days_ago: int = 0) -> str:
        """Generate date in Russian format
        Positive values = days ago, negative values = days in future
        """
        start = datetime.now() - timedelta(days=start_days_ago)
        end = datetime.now() - timedelta(days=end_days_ago)
        
        # Ensure start is before end
        if start > end:
            start, end = end, start
        
        random_date = start + timedelta(
            seconds=random.randint(0, int((end - start).total_seconds()))
        )
        
        return random_date.strftime("%d.%m.%Y")
    
    def _generate_amount(self, min_amount: int = 1000, max_amount: int = 500000) -> int:
        """Generate realistic monetary amount"""
        # Prefer round numbers
        base_amounts = [1000, 2000, 3000, 5000, 10000, 15000, 20000, 25000, 30000, 50000, 75000, 100000]
        
        if random.random() < 0.7:  # 70% chance for round number
            return random.choice([a for a in base_amounts if min_amount <= a <= max_amount])
        else:
            return random.randint(min_amount, max_amount)
    
    def generate_bill_of_exchange(self) -> Dict[str, Any]:
        """Generate bill of exchange document"""
        debtor = self._generate_person_name()
        creditor = random.choice(self.organizations)
        
        doc_date = self._generate_date(90, 1)
        payment_date = self._generate_date(-30, -1)  # Future date
        
        amount = self._generate_amount(5000, 500000)
        
        context = {
            "doc_number": random.randint(100000, 999999),
            "doc_date": doc_date,
            "debtor_name": debtor["full"],
            "debtor_address": random.choice(self.addresses).format(random.randint(1, 200)),
            "debtor_passport": self._generate_passport(),
            "creditor_name": creditor,
            "creditor_inn": self._generate_inn(False),
            "amount": f"{amount:,}".replace(",", " "),
            "payment_date": payment_date,
            "basis": f"Договор займа № {random.randint(100, 999)} от {self._generate_date(120, 30)}",
            "signature_line": "_" * 17,
            "place": random.choice(["г. Москва", "г. Санкт-Петербург", "г. Новосибирск"])
        }
        
        text = self.jinja_env.from_string(self.templates["bill_of_exchange"]).render(**context)
        
        return {
            "document_type": "bill_of_exchange",
            "text": text,
            "context": context,
            "metadata": {
                "amount": amount,
                "debtor": debtor["full"],
                "creditor": creditor,
                "doc_date": doc_date,
                "payment_date": payment_date
            }
        }
    
    def generate_fine_notice(self) -> Dict[str, Any]:
        """Generate fine notice document"""
        violator = self._generate_person_name()
        inspector = self._generate_person_name()
        
        doc_date = self._generate_date(60, 1)
        article = random.choice(self.koap_articles)
        violation = random.choice(self.violation_types)
        fine_amount = self._generate_amount(500, 30000)
        
        context = {
            "doc_number": f"АА-{random.randint(100000, 999999)}",
            "doc_date": doc_date,
            "violator_name": violator["full"],
            "violator_passport": self._generate_passport(),
            "violator_address": random.choice(self.addresses).format(random.randint(1, 200)),
            "article": article,
            "violation_type": violation,
            "violation_place": random.choice([
                "г. Москва, Садовое кольцо", "г. Москва, МКАД 15 км",
                "г. Санкт-Петербург, КАД", "г. Новосибирск, ул. Красный пр."
            ]),
            "violation_time": f"{random.randint(8, 22)}:{random.randint(10, 59):02d}",
            "fine_amount": f"{fine_amount:,}".replace(",", " "),
            "inspector_rank": random.choice(self.inspector_ranks),
            "inspector_name": inspector["short"],
            "place": random.choice(["г. Москва", "г. Санкт-Петербург", "г. Новосибирск"])
        }
        
        text = self.jinja_env.from_string(self.templates["fine_notice"]).render(**context)
        
        return {
            "document_type": "fine_notice",
            "text": text,
            "context": context,
            "metadata": {
                "fine_amount": fine_amount,
                "violator": violator["full"],
                "article": article,
                "violation_type": violation,
                "doc_date": doc_date
            }
        }
    
    def generate_protocol(self) -> Dict[str, Any]:
        """Generate meeting protocol document"""
        chairman = self._generate_person_name()
        secretary = self._generate_person_name()
        organization = random.choice(self.organizations)
        
        # Generate participants
        num_participants = random.randint(3, 7)
        participants = []
        for _ in range(num_participants):
            p = self._generate_person_name()
            participants.append(f"- {p['short']}")
        
        participants_text = "\n".join(participants)
        
        # Generate agenda items
        agenda_items = [
            "Утверждение финансового отчета за период",
            "Рассмотрение бюджета на следующий год", 
            "Выборы нового состава правления",
            "Вопросы развития организации",
            "Утверждение изменений в устав",
            "Разное"
        ]
        
        agenda = "\n".join([f"{i+1}. {item}" for i, item in enumerate(random.sample(agenda_items, random.randint(2, 4)))])
        
        decisions = [
            "Утвердить представленный финансовый отчет единогласно",
            "Принять бюджет на следующий год с поправками",
            "Избрать новый состав правления большинством голосов",
            "Утвердить план развития на 2024 год"
        ]
        
        context = {
            "doc_number": random.randint(100, 999),
            "doc_date": self._generate_date(30, 1),
            "organization": organization,
            "meeting_type": random.choice(["Совет директоров", "Общее собрание", "Правление"]),
            "chairman_name": chairman["full"],
            "secretary_name": secretary["full"],
            "participants": participants_text,
            "agenda": agenda,
            "decision": random.choice(decisions),
            "signature_line": "_" * 17,
            "place": random.choice(["г. Москва", "г. Санкт-Петербург", "г. Новосибирск"])
        }
        
        text = self.jinja_env.from_string(self.templates["protocol"]).render(**context)
        
        return {
            "document_type": "protocol",
            "text": text,
            "context": context,
            "metadata": {
                "organization": organization,
                "chairman": chairman["full"],
                "secretary": secretary["full"],
                "participants_count": num_participants,
                "doc_date": context["doc_date"]
            }
        }
    
    def create_pdf(self, document: Dict[str, Any], filename: str) -> str:
        """Create PDF document with realistic formatting"""
        pdf_path = self.output_dir / "pdf" / f"{filename}.pdf"
        
        # Create document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Times-Roman',
            leading=16
        )
        
        # Build document content
        content = []
        text_lines = document["text"].split('\n')
        
        for i, line in enumerate(text_lines):
            if i == 0:  # First line is usually title
                content.append(Paragraph(line, title_style))
            else:
                if line.strip():
                    content.append(Paragraph(line, normal_style))
                else:
                    content.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(content)
        
        return str(pdf_path)
    
    def add_signature_to_pdf(self, pdf_path: str) -> str:
        """Add handwritten signature overlay to PDF"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            # Create signature overlay
            signature_path = pdf_path.replace('.pdf', '_signed.pdf')
            
            # Create a simple signature overlay
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            
            # Add some signature-like lines (simple simulation)
            can.setStrokeColor(colors.blue)
            can.setLineWidth(2)
            
            # Signature area (bottom of page)
            x_start, y_start = 100, 100
            
            # Draw signature-like curves
            can.line(x_start, y_start, x_start + 80, y_start + 10)
            can.line(x_start + 20, y_start + 10, x_start + 100, y_start - 5)
            can.line(x_start + 40, y_start + 5, x_start + 120, y_start + 15)
            
            can.save()
            
            # For now, just return original path
            # In production, you'd merge the signature overlay with the original PDF
            return pdf_path
            
        except Exception as e:
            logger.warning(f"Could not add signature to PDF: {e}")
            return pdf_path
    
    def pdf_to_png(self, pdf_path: str, add_noise: bool = True) -> str:
        """Convert PDF to PNG with optional noise and artifacts"""
        try:
            # For now, create a simple PNG representation
            # In production, you'd use pdf2image library
            png_path = str(self.output_dir / "png" / f"{Path(pdf_path).stem}.png")
            
            # Create a white image representing a document
            img = Image.new('RGB', (1200, 1600), 'white')
            draw = ImageDraw.Draw(img)
            
            # Add some text-like rectangles to simulate document content
            y_pos = 100
            for _ in range(20):  # Simulate text lines
                width = random.randint(300, 1000)
                height = random.randint(15, 25)
                x_pos = random.randint(50, 100)
                
                # Draw text-like rectangle
                draw.rectangle([x_pos, y_pos, x_pos + width, y_pos + height], 
                              fill='black', outline='black')
                y_pos += random.randint(30, 50)
            
            if add_noise:
                # Add noise and artifacts
                img = self._add_document_noise(img)
            
            # Save PNG
            img.save(png_path, 'PNG', dpi=(300, 300))
            
            return png_path
            
        except Exception as e:
            logger.error(f"Could not convert PDF to PNG: {e}")
            return ""
    
    def _add_document_noise(self, img: Image.Image) -> Image.Image:
        """Add realistic document scanning artifacts"""
        # Apply slight rotation
        angle = random.uniform(-2, 2)
        img = img.rotate(angle, fillcolor='white', expand=False)
        
        # Apply slight blur
        if random.random() < 0.3:
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Add some noise spots
        draw = ImageDraw.Draw(img)
        for _ in range(random.randint(5, 15)):
            x = random.randint(0, img.width)
            y = random.randint(0, img.height)
            size = random.randint(1, 3)
            
            color = random.choice(['black', 'gray'])
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
        
        # Adjust brightness/contrast slightly
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))
        
        return img
    
    def save_metadata(self, documents: List[Dict[str, Any]], filename: str = "dataset_v2.json"):
        """Save dataset metadata"""
        metadata = {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "total_documents": len(documents),
            "document_types": {},
            "documents": []
        }
        
        # Count document types
        for doc in documents:
            doc_type = doc["document_type"]
            if doc_type not in metadata["document_types"]:
                metadata["document_types"][doc_type] = 0
            metadata["document_types"][doc_type] += 1
        
        # Add document info
        for i, doc in enumerate(documents):
            doc_info = {
                "id": i,
                "filename": f"doc_{i:03d}",
                "document_type": doc["document_type"],
                "metadata": doc["metadata"],
                "files": {
                    "txt": f"txt/doc_{i:03d}.txt",
                    "pdf": f"pdf/doc_{i:03d}.pdf",
                    "png": f"png/doc_{i:03d}.png"
                }
            }
            metadata["documents"].append(doc_info)
        
        # Save metadata
        metadata_path = self.output_dir / filename
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Metadata saved: {metadata_path}")
        return str(metadata_path)
    
    def generate_dataset(self, num_documents: int = 50) -> List[Dict[str, Any]]:
        """Generate complete synthetic dataset"""
        logger.info(f"Generating {num_documents} synthetic documents...")
        
        documents = []
        
        # Distribution of document types
        bill_count = int(num_documents * 0.4)  # 40% bills
        fine_count = int(num_documents * 0.35)  # 35% fines  
        protocol_count = num_documents - bill_count - fine_count  # Rest protocols
        
        # Generate documents
        for i in range(bill_count):
            documents.append(self.generate_bill_of_exchange())
        
        for i in range(fine_count):
            documents.append(self.generate_fine_notice())
        
        for i in range(protocol_count):
            documents.append(self.generate_protocol())
        
        # Shuffle documents
        random.shuffle(documents)
        
        logger.info(f"Generated: {bill_count} bills, {fine_count} fines, {protocol_count} protocols")
        
        # Save files
        for i, doc in enumerate(documents):
            filename = f"doc_{i:03d}"
            
            # Save text
            txt_path = self.output_dir / "txt" / f"{filename}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(doc["text"])
            
            # Create PDF
            pdf_path = self.create_pdf(doc, filename)
            
            # Create PNG with noise
            png_path = self.pdf_to_png(pdf_path, add_noise=True)
            
            if i % 10 == 0:
                logger.info(f"Generated {i+1}/{num_documents} documents...")
        
        # Save metadata
        self.save_metadata(documents)
        
        logger.info(f"✅ Synthetic dataset v2 complete: {len(documents)} documents")
        logger.info(f"📁 Output directory: {self.output_dir}")
        
        return documents

def main():
    """Main function to generate synthetic dataset"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic legal documents v2')
    parser.add_argument('--count', type=int, default=50, help='Number of documents to generate')
    parser.add_argument('--output', type=str, default='data/synthetic_v2', help='Output directory')
    parser.add_argument('--seed', type=int, help='Random seed for reproducible generation')
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
        logger.info(f"Using random seed: {args.seed}")
    
    # Create generator
    generator = SyntheticDataGeneratorV2(args.output)
    
    # Generate dataset
    try:
        documents = generator.generate_dataset(args.count)
        
        print(f"\n🎉 Synthetic Dataset v2 Generation Complete!")
        print(f"📊 Generated: {len(documents)} documents")
        print(f"📁 Location: {generator.output_dir}")
        print(f"📄 Files: TXT, PDF, PNG + metadata.json")
        
        # Show breakdown
        doc_types = {}
        for doc in documents:
            doc_type = doc["document_type"]
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"📈 Breakdown:")
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count} documents")
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 