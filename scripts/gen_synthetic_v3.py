#!/usr/bin/env python3
"""
Enhanced Synthetic Document Generator v3
Generates realistic "dirty" documents with noise, blur, perspective, watermarks
for stress testing and robustness validation
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

class AdvancedDocumentGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "txt").mkdir(exist_ok=True)
        (self.output_dir / "pdf").mkdir(exist_ok=True)
        (self.output_dir / "png").mkdir(exist_ok=True)
        (self.output_dir / "dirty_png").mkdir(exist_ok=True)
        
        # Enhanced data pools
        self.russian_names = [
            "Иванов Иван Иванович", "Петров Петр Петрович", "Сидоров Сергей Сергеевич",
            "Козлова Мария Александровна", "Смирнов Алексей Викторович", "Морозова Елена Дмитриевна",
            "Волков Михаил Андреевич", "Соколова Анна Игоревна", "Лебедев Дмитрий Олегович",
            "Орлова Ольга Владимировна", "Медведев Владимир Николаевич", "Зайцева Татьяна Сергеевна",
            "Белов Игорь Анатольевич", "Чернова Светлана Викторовна", "Серов Андрей Михайлович",
            "Рыжова Наталья Александровна", "Быков Роман Дмитриевич", "Щукина Ирина Олеговна",
            "Баранов Евгений Игоревич", "Крылова Юлия Андреевна", "Фролов Максим Владимирович"
        ]
        
        self.organizations = [
            'ООО "Альфа-Строй"', 'ЗАО "БетаТех"', 'ПАО "ГаммаИнвест"', 'ООО "ДельтаСервис"',
            'АО "ОмегаГрупп"', 'ООО "СигмаТранс"', 'ЗАО "ТетаКонсалт"', 'ПАО "ЛямбдаБанк"',
            'ООО "КаппаЛогистик"', 'АО "МюТрейд"', 'ООО "НюКомпани"', 'ЗАО "КсиИнжиниринг"',
            'ООО "ОмикронДевелопмент"', 'ПАО "ПиИнтернешнл"', 'АО "РоТехнологии"',
            'ГИБДД г. Москвы', 'Росреестр Московской области', 'ФНС России № 15',
            'Арбитражный суд г. Москвы', 'Нотариальная палата', 'Банк "Сбербанк России"'
        ]
        
        self.cities = [
            "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
            "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
            "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград", "Краснодар"
        ]
        
        self.streets = [
            "ул. Ленина", "пр. Мира", "ул. Советская", "пл. Революции", "ул. Пушкина",
            "пр. Победы", "ул. Гагарина", "ул. Комсомольская", "пр. Ленинский", "ул. Центральная"
        ]
        
        self.legal_articles = [
            "ст. 12.1 КоАП РФ", "ст. 12.8 КоАП РФ", "ст. 20.4 КоАП РФ", "ст. 7.17 КоАП РФ",
            "ст. 14.1 КоАП РФ", "ст. 15.25 КоАП РФ", "ст. 18.8 КоАП РФ", "ст. 19.3 КоАП РФ",
            "ст. 6.4 КоАП РФ", "ст. 8.6 КоАП РФ", "ст. 11.1 КоАП РФ", "ст. 13.11 КоАП РФ",
            "ст. 16.2 КоАП РФ", "ч. 1 ст. 159 УК РФ", "п. 2 ст. 421 ГК РФ"
        ]
        
        # Watermark texts
        self.watermarks = [
            "КОПИЯ", "ОБРАЗЕЦ", "НЕ ДЕЙСТВИТЕЛЕН", "АРХИВНАЯ КОПИЯ",
            "КОНФИДЕНЦИАЛЬНО", "ЧЕРНОВИК", "ПРЕДВАРИТЕЛЬНЫЙ", "COPY"
        ]
    
    def generate_bill_content(self) -> str:
        """Generate bill of exchange content with random variations"""
        debtor = random.choice(self.russian_names)
        creditor = random.choice(self.russian_names)
        amount = random.choice([1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000])
        amount_text = self._number_to_words(amount)
        
        due_date = datetime.now() + timedelta(days=random.randint(30, 365))
        doc_number = f"{random.randint(100000, 999999)}"
        
        # Add random formatting variations
        variations = [
            f"""
ПРОСТОЙ ВЕКСЕЛЬ № {doc_number}

г. {random.choice(self.cities)}                                           {due_date.strftime('%d.%m.%Y')}

Я, {debtor}, обязуюсь безусловно выплатить по этому векселю 
{creditor} или его приказу сумму {amount:,} ({amount_text}) рублей
не позднее {due_date.strftime('%d.%m.%Y')} года.

Место платежа: {random.choice(self.cities)}
Адрес должника: {self._generate_address()}

_____________________                                  _____________________
      (подпись)                                           (дата)

М.П.
            """,
            f"""
ПЕРЕВОДНОЙ ВЕКСЕЛЬ № {doc_number}

Сумма: {amount:,} руб. ({amount_text} рублей)
Место составления: г. {random.choice(self.cities)}
Дата составления: {(datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%d.%m.%Y')}

ПРЕДЛАГАЮ {random.choice(self.organizations)} выплатить в срок до {due_date.strftime('%d.%m.%Y')}
векселедержателю {creditor} сумму {amount:,} рублей.

Трассант: {debtor}
Адрес: {self._generate_address()}

Аваль: _______________

Подпись трассанта: _____________________
            """
        ]
        
        return random.choice(variations).strip()
    
    def generate_fine_content(self) -> str:
        """Generate fine notice content"""
        violator = random.choice(self.russian_names)
        inspector = random.choice(self.russian_names)
        article = random.choice(self.legal_articles)
        fine_amount = random.choice([500, 1000, 1500, 2000, 3000, 5000, 10000, 15000])
        
        case_number = f"{random.randint(1000000, 9999999)}"
        violation_date = datetime.now() - timedelta(days=random.randint(1, 60))
        
        content = f"""
ПОСТАНОВЛЕНИЕ
по делу об административном правонарушении № {case_number}

г. {random.choice(self.cities)}                                           {datetime.now().strftime('%d.%m.%Y')}

Рассмотрев материалы дела об административном правонарушении в отношении 
{violator}, {violation_date.strftime('%d.%m.%Y')} в {violation_date.strftime('%H:%M')} 
по адресу: {self._generate_address()}

УСТАНОВИЛ:

{violation_date.strftime('%d.%m.%Y')} в {violation_date.strftime('%H:%M')} {violator} совершил административное 
правонарушение, предусмотренное {article}, а именно: 
{self._generate_violation_description()}

На основании изложенного и руководствуясь {article} КоАП РФ,

ПОСТАНОВЛЯЮ:

Признать {violator} виновным в совершении административного правонарушения,
предусмотренного {article} КоАП РФ, и назначить ему административное наказание
в виде административного штрафа в размере {fine_amount:,} рублей.

Штраф подлежит уплате не позднее 60 дней со дня вступления постановления в законную силу.

Постановление может быть обжаловано в течение 10 суток.

Должностное лицо: {inspector}
Подпись: _____________________

М.П.
        """.strip()
        
        return content
    
    def generate_protocol_content(self) -> str:
        """Generate meeting protocol content"""
        participants = random.sample(self.russian_names, random.randint(3, 7))
        chairman = participants[0]
        secretary = participants[1] if len(participants) > 1 else chairman
        
        meeting_date = datetime.now() - timedelta(days=random.randint(1, 30))
        protocol_number = random.randint(1, 50)
        
        agenda_items = [
            "О финансовом состоянии компании",
            "Об утверждении годового отчета",
            "О распределении прибыли",
            "О выборе аудиторской организации",
            "О внесении изменений в устав",
            "О реорганизации общества",
            "Об увеличении уставного капитала",
            "О выплате дивидендов",
            "О принятии бюджета на следующий год"
        ]
        
        selected_agenda = random.sample(agenda_items, random.randint(2, 4))
        
        content = f"""
ПРОТОКОЛ № {protocol_number}
заседания Совета директоров {random.choice(self.organizations)}

г. {random.choice(self.cities)}                                           {meeting_date.strftime('%d.%m.%Y')}

Время проведения: {meeting_date.strftime('%H:%M')}
Место проведения: {self._generate_address()}

Председатель: {chairman}
Секретарь: {secretary}

ПРИСУТСТВОВАЛИ:
""" + "\n".join([f"- {name}" for name in participants]) + f"""

ПОВЕСТКА ДНЯ:
""" + "\n".join([f"{i+1}. {item}" for i, item in enumerate(selected_agenda)]) + f"""

ПО ПЕРВОМУ ВОПРОСУ ПОВЕСТКИ ДНЯ:
СЛУШАЛИ: {chairman} - {selected_agenda[0].lower()}
РЕШИЛИ: Принять к сведению представленную информацию.
ГОЛОСОВАЛИ: ЗА - {len(participants)}, ПРОТИВ - 0, ВОЗДЕРЖАЛИСЬ - 0

ПО ВТОРОМУ ВОПРОСУ ПОВЕСТКИ ДНЯ:
СЛУШАЛИ: {participants[-1]} - {selected_agenda[1].lower()}
РЕШИЛИ: Утвердить предложенные изменения.
ГОЛОСОВАЛИ: ЗА - {len(participants)-1}, ПРОТИВ - 0, ВОЗДЕРЖАЛИСЬ - 1

Заседание объявлено закрытым в {(meeting_date + timedelta(hours=2)).strftime('%H:%M')}.

Председатель: _____________________  {chairman}
Секретарь:   _____________________  {secretary}
        """.strip()
        
        return content
    
    def _generate_address(self) -> str:
        """Generate random Russian address"""
        city = random.choice(self.cities)
        street = random.choice(self.streets)
        house = random.randint(1, 200)
        apt = random.randint(1, 150) if random.random() > 0.3 else None
        
        address = f"г. {city}, {street}, д. {house}"
        if apt:
            address += f", кв. {apt}"
        
        return address
    
    def _number_to_words(self, number: int) -> str:
        """Convert number to Russian words (simplified)"""
        words_map = {
            1000: "одна тысяча", 5000: "пять тысяч", 10000: "десять тысяч",
            25000: "двадцать пять тысяч", 50000: "пятьдесят тысяч",
            100000: "сто тысяч", 250000: "двести пятьдесят тысяч",
            500000: "пятьсот тысяч"
        }
        return words_map.get(number, f"{number//1000} тысяч")
    
    def _generate_violation_description(self) -> str:
        """Generate violation description"""
        violations = [
            "нарушение правил дорожного движения",
            "неисполнение требований должностного лица",
            "нарушение общественного порядка",
            "незаконная торговля",
            "нарушение санитарных норм",
            "неуплата административного штрафа",
            "нарушение правил благоустройства"
        ]
        return random.choice(violations)
    
    def create_multi_page_pdf(self, content: str, doc_type: str, filename: str) -> str:
        """Create multi-page PDF with appendices"""
        pdf_path = self.output_dir / "pdf" / f"{filename}.pdf"
        
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Add main content
        for line in content.split('\n'):
            if line.strip():
                if any(word in line.upper() for word in ['ВЕКСЕЛЬ', 'ПОСТАНОВЛЕНИЕ', 'ПРОТОКОЛ']):
                    story.append(Paragraph(line, title_style))
                else:
                    story.append(Paragraph(line, styles['Normal']))
            else:
                story.append(Spacer(1, 12))
        
        # Add page break and appendix
        story.append(PageBreak())
        story.append(Paragraph("ПРИЛОЖЕНИЕ 1", title_style))
        story.append(Spacer(1, 20))
        
        # Add a table for appendix
        if doc_type == "bill_of_exchange":
            table_data = [
                ['Дата', 'Сумма', 'Описание'],
                ['01.01.2024', '10,000 руб.', 'Первоначальный взнос'],
                ['15.01.2024', '15,000 руб.', 'Дополнительный платеж'],
                ['01.02.2024', '25,000 руб.', 'Окончательный расчет']
            ]
        elif doc_type == "fine_notice":
            table_data = [
                ['Статья', 'Описание', 'Штраф'],
                ['12.8 КоАП РФ', 'Управление в нетрезвом виде', '30,000 руб.'],
                ['12.26 КоАП РФ', 'Отказ от медосвидетельствования', '30,000 руб.']
            ]
        else:
            table_data = [
                ['Участник', 'Должность', 'Подпись'],
                ['Иванов И.И.', 'Директор', 'И.Иванов'],
                ['Петров П.П.', 'Бухгалтер', 'П.Петров']
            ]
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Add another page with signatures
        story.append(PageBreak())
        story.append(Paragraph("ПОДПИСИ И ПЕЧАТИ", title_style))
        story.append(Spacer(1, 40))
        story.append(Paragraph("Руководитель: _____________________", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("М.П.", styles['Normal']))
        
        doc.build(story)
        return str(pdf_path)
    
    def apply_image_distortions(self, image: Image.Image, noise_types: List[str]) -> Image.Image:
        """Apply various realistic distortions to image"""
        img_array = np.array(image)
        
        # Convert to OpenCV format
        if len(img_array.shape) == 3:
            cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            cv_image = img_array
        
        # Apply perspective transformation
        if 'perspective' in noise_types:
            h, w = cv_image.shape[:2]
            
            # Random perspective points
            pts1 = np.float32([
                [random.randint(0, 20), random.randint(0, 20)],
                [w - random.randint(0, 20), random.randint(0, 20)],
                [random.randint(0, 20), h - random.randint(0, 20)],
                [w - random.randint(0, 20), h - random.randint(0, 20)]
            ])
            pts2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            
            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            cv_image = cv2.warpPerspective(cv_image, matrix, (w, h))
        
        # Add rotation
        if 'rotation' in noise_types:
            angle = random.uniform(-3, 3)
            h, w = cv_image.shape[:2]
            center = (w//2, h//2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            cv_image = cv2.warpAffine(cv_image, rotation_matrix, (w, h), 
                                    borderMode=cv2.BORDER_CONSTANT, 
                                    borderValue=(255, 255, 255))
        
        # Convert back to PIL
        if len(cv_image.shape) == 3:
            result_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        else:
            result_image = Image.fromarray(cv_image)
        
        # Apply PIL-based effects
        if 'blur' in noise_types:
            blur_radius = random.uniform(0.5, 2.0)
            result_image = result_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        if 'noise' in noise_types:
            enhancer = ImageEnhance.Brightness(result_image)
            result_image = enhancer.enhance(random.uniform(0.8, 1.2))
            
            enhancer = ImageEnhance.Contrast(result_image)
            result_image = enhancer.enhance(random.uniform(0.8, 1.2))
        
        if 'jpeg_compression' in noise_types:
            # Simulate JPEG compression artifacts
            temp_buffer = io.BytesIO()
            result_image.save(temp_buffer, format='JPEG', quality=random.randint(60, 85))
            temp_buffer.seek(0)
            result_image = Image.open(temp_buffer)
        
        return result_image
    
    def add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to image"""
        if random.random() > 0.3:  # 30% chance of watermark
            return image
        
        watermark_text = random.choice(self.watermarks)
        
        # Create watermark overlay
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2
        
        # Draw watermark with transparency
        draw.text((x, y), watermark_text, font=font, fill=(128, 128, 128, 128))
        
        # Rotate watermark
        overlay = overlay.rotate(random.randint(-30, 30), expand=False)
        
        # Composite with original image
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        result = Image.alpha_composite(image, overlay)
        return result.convert('RGB')
    
    def generate_document(self, doc_type: str, index: int, noise_types: List[str] = None) -> Dict[str, Any]:
        """Generate a single document with specified noise types"""
        if noise_types is None:
            noise_types = ['blur', 'noise']
        
        filename = f"doc_{index:03d}"
        
        # Generate content based on type
        if doc_type == "bill_of_exchange":
            content = self.generate_bill_content()
        elif doc_type == "fine_notice":
            content = self.generate_fine_content()
        elif doc_type == "protocol":
            content = self.generate_protocol_content()
        else:
            content = random.choice([
                self.generate_bill_content(),
                self.generate_fine_content(),
                self.generate_protocol_content()
            ])
            doc_type = random.choice(["bill_of_exchange", "fine_notice", "protocol"])
        
        # Save text file
        txt_path = self.output_dir / "txt" / f"{filename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create multi-page PDF
        pdf_path = self.create_multi_page_pdf(content, doc_type, filename)
        
        # Convert PDF to clean PNG
        try:
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            page = pdf_doc[0]  # First page only for PNG
            
            mat = fitz.Matrix(2.0, 2.0)  # High resolution
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            clean_image = Image.open(io.BytesIO(img_data))
            png_path = self.output_dir / "png" / f"{filename}.png"
            clean_image.save(png_path)
            
            pdf_doc.close()
        except ImportError:
            print("⚠️  PyMuPDF not available, using alternative PDF to PNG conversion")
            # Fallback method using reportlab canvas
            clean_image = self._create_image_from_text(content)
            png_path = self.output_dir / "png" / f"{filename}.png"
            clean_image.save(png_path)
        
        # Create dirty version with distortions
        dirty_image = self.apply_image_distortions(clean_image, noise_types)
        dirty_image = self.add_watermark(dirty_image)
        
        dirty_png_path = self.output_dir / "dirty_png" / f"{filename}.png"
        dirty_image.save(dirty_png_path)
        
        return {
            "filename": filename,
            "document_type": doc_type,
            "text_file": str(txt_path),
            "pdf_file": str(pdf_path),
            "clean_png": str(png_path),
            "dirty_png": str(dirty_png_path),
            "noise_types": noise_types,
            "char_count": len(content),
            "pages": 3,  # Multi-page PDF
            "has_watermark": random.random() <= 0.3
        }
    
    def _create_image_from_text(self, content: str) -> Image.Image:
        """Fallback method to create image from text"""
        # Create a large image
        img_width, img_height = 800, 1000
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Split content into lines and draw
        lines = content.split('\n')
        y_offset = 20
        line_height = 15
        
        for line in lines:
            if y_offset > img_height - 30:
                break
            draw.text((20, y_offset), line, font=font, fill='black')
            y_offset += line_height
        
        return image

def main():
    parser = argparse.ArgumentParser(description="Generate enhanced synthetic documents v3 with realistic noise")
    parser.add_argument("--count", type=int, default=40, help="Number of documents to generate")
    parser.add_argument("--output-dir", default="./data/synthetic_v3", help="Output directory")
    parser.add_argument("--noise", default="blur,perspective,noise,rotation", help="Comma-separated noise types")
    parser.add_argument("--doc-types", default="bill_of_exchange,fine_notice,protocol", help="Document types to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Parse noise types
    noise_types = [noise.strip() for noise in args.noise.split(',')]
    doc_types = [dtype.strip() for dtype in args.doc_types.split(',')]
    
    print(f"🚀 Enhanced Synthetic Document Generator v3")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"📊 Document count: {args.count}")
    print(f"🎭 Noise types: {noise_types}")
    print(f"📄 Document types: {doc_types}")
    
    # Initialize generator
    generator = AdvancedDocumentGenerator(Path(args.output_dir))
    
    # Generate documents
    documents = []
    start_time = datetime.now()
    
    for i in range(args.count):
        try:
            doc_type = random.choice(doc_types)
            
            # Randomly select subset of noise types for each document
            doc_noise_types = random.sample(noise_types, random.randint(1, len(noise_types)))
            
            doc_info = generator.generate_document(doc_type, i, doc_noise_types)
            documents.append(doc_info)
            
            print(f"✅ Generated {i+1}/{args.count}: {doc_info['filename']} ({doc_type})")
            
        except Exception as e:
            print(f"❌ Error generating document {i}: {str(e)}")
    
    # Save metadata
    metadata = {
        "generation_date": datetime.now().isoformat(),
        "document_count": len(documents),
        "noise_types": noise_types,
        "document_types": doc_types,
        "generation_time_seconds": (datetime.now() - start_time).total_seconds(),
        "documents": documents
    }
    
    metadata_path = Path(args.output_dir) / "metadata_v3.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Generate summary statistics
    type_counts = {}
    noise_stats = {}
    
    for doc in documents:
        doc_type = doc['document_type']
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        for noise in doc['noise_types']:
            noise_stats[noise] = noise_stats.get(noise, 0) + 1
    
    print(f"\n✅ Generation complete!")
    print(f"📊 Generated {len(documents)} documents in {(datetime.now() - start_time).total_seconds():.1f}s")
    print(f"📄 Document type distribution: {type_counts}")
    print(f"🎭 Noise type usage: {noise_stats}")
    print(f"📁 Files saved to: {args.output_dir}")
    print(f"📋 Metadata: {metadata_path}")
    
    print(f"\n🔥 Ready for stress testing:")
    print(f"- Clean images: {args.output_dir}/png/")
    print(f"- Dirty images: {args.output_dir}/dirty_png/")
    print(f"- Multi-page PDFs: {args.output_dir}/pdf/")
    print(f"- Text files: {args.output_dir}/txt/")

if __name__ == "__main__":
    main() 