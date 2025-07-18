"""
Legal ASI - Document Parser Tests
Unit tests for document structure parsing and field extraction
"""

import pytest
from ml.preprocess import DocumentSectionParser, split_sections, analyze_document_structure
from ml.extract_fields import FieldExtractor, extract_fields_from_sections

class TestDocumentSectionParser:
    """Test document section parsing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = DocumentSectionParser()
    
    def test_bill_of_exchange_parsing(self):
        """Test parsing of bill of exchange document"""
        bill_text = """ВЕКСЕЛЬ № 123456 от 15.12.2023

Обязательство: Иванов Иван Иванович обязуется выплатить 
ООО "Рога и Копыта" сумму в размере 50000 рублей до 15.01.2024.

Основание: Договор займа № 157 от 01.12.2023

Должник: Иванов Иван Иванович
Паспорт: 4510 123456
Адрес: г. Москва, ул. Ленина, д. 10

Кредитор: ООО "Рога и Копыта"
ИНН: 7701234567

Подпись должника: _________________
Дата составления: 15.12.2023
Место составления: г. Москва"""
        
        sections = self.parser.split_sections(bill_text)
        
        assert "header" in sections
        assert "body" in sections
        assert "footer" in sections
        
        # Header should contain document title and number
        assert "ВЕКСЕЛЬ" in sections["header"]
        assert "123456" in sections["header"]
        
        # Body should contain main obligation details
        assert "Обязательство" in sections["body"]
        assert "50000 рублей" in sections["body"]
        
        # Footer should contain signatures and dates
        assert "Подпись" in sections["footer"]
        assert "_________________" in sections["footer"]
    
    def test_fine_notice_parsing(self):
        """Test parsing of administrative fine notice"""
        fine_text = """ПОСТАНОВЛЕНИЕ об административном правонарушении
№ АА-001234 от 10.11.2023

Гражданин Петров Петр Петрович совершил административное правонарушение,
предусмотренное статьей 12.9 КоАП РФ (превышение скорости).

Место нарушения: г. Москва, Садовое кольцо
Время нарушения: 14:30

Назначить административный штраф в размере 5000 рублей.

Нарушитель: Петров Петр Петрович
Паспорт: 4511 654321
Адрес: г. Москва, ул. Пушкина, д. 5

Инспектор: Сидоров С.С.
Должность: Инспектор ГИБДД

Дата составления: 10.11.2023
Место составления: г. Москва"""
        
        sections = self.parser.split_sections(fine_text)
        
        # Header should contain document type and number
        assert "ПОСТАНОВЛЕНИЕ" in sections["header"]
        assert "АА-001234" in sections["header"]
        
        # Body should contain violation details
        assert "Гражданин" in sections["body"]
        assert "правонарушение" in sections["body"]
        assert "5000 рублей" in sections["body"]
        
        # Footer should contain official information
        assert "Инспектор" in sections["footer"] or "Дата составления" in sections["footer"]
    
    def test_protocol_parsing(self):
        """Test parsing of meeting protocol"""
        protocol_text = """ПРОТОКОЛ заседания № 789 от 20.11.2023

Организация: ООО "Технологии будущего"
Тип заседания: Совет директоров

Председатель: Новиков Алексей Сергеевич
Секретарь: Морозова Елена Викторовна

Присутствовали:
- Иванов И.И.
- Петров П.П.
- Сидоров С.С.

ПОВЕСТКА ДНЯ:
1. Утверждение финансового отчета
2. Рассмотрение бюджета на следующий год

РЕШЕНИЕ:
Утвердить представленный финансовый отчет единогласно.

Председатель: Новиков А.С. _________________
Секретарь: Морозова Е.В. _________________

Дата: 20.11.2023
Место: г. Москва"""
        
        sections = self.parser.split_sections(protocol_text)
        
        # Header should contain protocol info
        assert "ПРОТОКОЛ" in sections["header"]
        assert "789" in sections["header"]
        
        # Body should contain meeting details
        assert "ПОВЕСТКА" in sections["body"] or "Присутствовали" in sections["body"]
        assert "РЕШЕНИЕ" in sections["body"]
        
        # Footer should contain signatures
        assert "Председатель" in sections["footer"]
        assert "_________________" in sections["footer"]
    
    def test_empty_and_invalid_input(self):
        """Test handling of empty and invalid input"""
        # Empty text
        sections = self.parser.split_sections("")
        assert sections["header"] == ""
        assert sections["body"] == ""
        assert sections["footer"] == ""
        
        # Very short text
        sections = self.parser.split_sections("test")
        assert sections["body"] == "test"
        
        # None input
        sections = self.parser.split_sections(None)
        assert all(v == "" for v in sections.values())
    
    def test_document_structure_analysis(self):
        """Test document structure analysis"""
        test_text = """ВЕКСЕЛЬ № 123456

Основное содержание документа с обязательствами
и суммами к выплате.

Подпись: _________________"""
        
        result = analyze_document_structure(test_text)
        
        assert "sections" in result
        assert "analysis" in result
        assert "section_lengths" in result["analysis"]
        assert "document_type_indicators" in result["analysis"]
        assert "completeness_score" in result["analysis"]
        
        # Check completeness score is reasonable
        assert 0.0 <= result["analysis"]["completeness_score"] <= 1.0

class TestFieldExtractor:
    """Test field extraction functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = FieldExtractor()
        
        # Sample sections for testing
        self.bill_sections = {
            "header": "ВЕКСЕЛЬ № 123456 от 15.12.2023",
            "body": """Обязательство: Иванов Иван Иванович обязуется выплатить 
ООО "Рога и Копыта" сумму в размере 50000 рублей до 15.01.2024.

Должник: Иванов Иван Иванович
Паспорт: 4510 123456
Кредитор: ООО "Рога и Копыта"
ИНН: 7701234567""",
            "footer": "Подпись должника: _________________"
        }
    
    def test_money_extraction(self):
        """Test money amount extraction"""
        amounts = self.extractor.extract_money_amounts(self.bill_sections)
        
        assert len(amounts) > 0
        assert any(a["amount"] == 50000 for a in amounts)
        assert any("руб" in a["currency"] for a in amounts)
        
        # Check structure
        for amount in amounts:
            assert "amount" in amount
            assert "currency" in amount
            assert "formatted" in amount
            assert "section" in amount
    
    def test_date_extraction(self):
        """Test date extraction"""
        dates = self.extractor.extract_dates(self.bill_sections)
        
        assert len(dates) > 0
        
        # Check for expected dates
        date_strings = [d["formatted"] for d in dates]
        assert any("15.12.2023" in ds for ds in date_strings)
        assert any("15.01.2024" in ds for ds in date_strings)
        
        # Check structure
        for date in dates:
            assert "formatted" in date
            assert "section" in date
    
    def test_person_extraction(self):
        """Test person name extraction"""
        persons = self.extractor.extract_persons(self.bill_sections)
        
        assert len(persons) > 0
        
        # Check for expected person
        person_names = [p["name"] for p in persons]
        assert any("Иванов Иван Иванович" in name for name in person_names)
        
        # Check roles
        person_roles = [p["role"] for p in persons]
        assert any(role in ["debtor", "person"] for role in person_roles)
    
    def test_organization_extraction(self):
        """Test organization extraction"""
        orgs = self.extractor.extract_organizations(self.bill_sections)
        
        assert len(orgs) > 0
        
        # Check for expected organization
        org_names = [o["name"] for o in orgs]
        assert any("ООО \"Рога и Копыта\"" in name for name in org_names)
        
        # Check types
        for org in orgs:
            assert "type" in org
            assert "name" in org
    
    def test_document_number_extraction(self):
        """Test document number extraction"""
        numbers = self.extractor.extract_document_numbers(self.bill_sections)
        
        assert len(numbers) > 0
        
        # Check for expected number
        number_values = [n["number"] for n in numbers]
        assert any("123456" in num for num in number_values)
    
    def test_passport_extraction(self):
        """Test passport data extraction"""
        passports = self.extractor.extract_passports(self.bill_sections)
        
        assert len(passports) > 0
        
        # Check for expected passport
        passport = passports[0]
        assert passport["series"] == "4510"
        assert passport["number"] == "123456"
        assert passport["formatted"] == "4510 123456"
    
    def test_inn_extraction(self):
        """Test INN code extraction"""
        inn_codes = self.extractor.extract_inn_codes(self.bill_sections)
        
        assert len(inn_codes) > 0
        
        # Check for expected INN
        inn = inn_codes[0]
        assert inn["inn"] == "7701234567"
        assert inn["type"] == "organization"
    
    def test_complete_field_extraction(self):
        """Test complete field extraction"""
        fields = self.extractor.extract_all_fields(self.bill_sections)
        
        # Check all field types are present
        expected_fields = [
            "amounts", "dates", "persons", "organizations", 
            "document_numbers", "passports", "inn_codes", 
            "legal_articles", "extraction_summary"
        ]
        
        for field in expected_fields:
            assert field in fields
        
        # Check extraction summary
        summary = fields["extraction_summary"]
        assert "total_characters" in summary
        assert "sections_processed" in summary
        assert summary["total_characters"] > 0
    
    def test_fine_notice_extraction(self):
        """Test extraction from fine notice"""
        fine_sections = {
            "header": "ПОСТАНОВЛЕНИЕ об административном правонарушении № АА-001234",
            "body": """Гражданин Петров Петр Петрович совершил правонарушение,
предусмотренное статьей 12.9 КоАП РФ.
Назначить штраф в размере 5000 рублей.""",
            "footer": "Инспектор: Сидоров С.С."
        }
        
        fields = self.extractor.extract_all_fields(fine_sections)
        
        # Check specific fine notice fields
        assert len(fields["amounts"]) > 0
        assert any(a["amount"] == 5000 for a in fields["amounts"])
        
        assert len(fields["legal_articles"]) > 0
        assert any("12.9" in a["article"] for a in fields["legal_articles"])
        
        assert len(fields["persons"]) > 0
        person_names = [p["name"] for p in fields["persons"]]
        assert any("Петров Петр Петрович" in name for name in person_names)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty sections
        empty_sections = {"header": "", "body": "", "footer": ""}
        fields = self.extractor.extract_all_fields(empty_sections)
        
        # Should not crash and return empty results
        assert all(isinstance(fields[key], list) for key in fields if key != "extraction_summary")
        
        # Invalid data
        invalid_sections = {"header": "###", "body": "123", "footer": "..."}
        fields = self.extractor.extract_all_fields(invalid_sections)
        
        # Should handle gracefully
        assert "extraction_summary" in fields

class TestIntegration:
    """Test integration between parsing and extraction"""
    
    def test_full_pipeline(self):
        """Test complete parsing and extraction pipeline"""
        document_text = """ВЕКСЕЛЬ № 789012 от 20.12.2023

Я, Сидоров Алексей Петрович, обязуюсь выплатить 
ЗАО "Финанс Групп" сумму в размере 75000 рублей 
к 20.03.2024 на основании договора займа № 156.

Должник: Сидоров Алексей Петрович
Паспорт: 4512 789012
Кредитор: ЗАО "Финанс Групп"
ИНН: 7702345678

Подпись должника: _________________
Дата составления: 20.12.2023"""
        
        # Parse sections
        sections = split_sections(document_text)
        
        # Extract fields
        fields = extract_fields_from_sections(sections)
        
        # Verify integration
        assert len(fields["amounts"]) > 0
        assert len(fields["dates"]) > 0
        assert len(fields["persons"]) > 0
        assert len(fields["organizations"]) > 0
        
        # Check specific values
        assert any(a["amount"] == 75000 for a in fields["amounts"])
        assert any("Сидоров Алексей Петрович" in p["name"] for p in fields["persons"])
        assert any("ЗАО \"Финанс Групп\"" in o["name"] for o in fields["organizations"])
    
    def test_section_based_extraction(self):
        """Test that extraction properly uses section information"""
        document_text = """ПРОТОКОЛ № 555

В заседании приняли участие директора.

Председатель: Иванов И.И. _________"""
        
        sections = split_sections(document_text)
        fields = extract_fields_from_sections(sections)
        
        # Check that persons are found with correct sections
        persons = fields["persons"]
        if persons:
            person = persons[0]
            assert person["section"] in ["header", "body", "footer"]
    
    def test_performance(self):
        """Test performance with larger documents"""
        # Create a larger document
        large_doc = """ВЕКСЕЛЬ № 123456 от 01.01.2023

""" + "Содержание документа. " * 100 + """

Сумма: 100000 рублей
Должник: Тестов Тест Тестович
Кредитор: ООО "Тест"

Подпись: _________________"""
        
        import time
        start_time = time.time()
        
        sections = split_sections(large_doc)
        fields = extract_fields_from_sections(sections)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process reasonably quickly (under 1 second)
        assert processing_time < 1.0
        
        # Should still extract correctly
        assert len(fields["amounts"]) > 0
        assert len(fields["persons"]) > 0

# Test fixtures and helpers
@pytest.fixture
def sample_bill_text():
    """Sample bill of exchange text for testing"""
    return """ВЕКСЕЛЬ № 123456 от 15.12.2023

Обязательство: Иванов Иван Иванович обязуется выплатить 
ООО "Рога и Копыта" сумму в размере 50000 рублей до 15.01.2024.

Должник: Иванов Иван Иванович
Паспорт: 4510 123456

Подпись должника: _________________"""

@pytest.fixture  
def sample_fine_text():
    """Sample fine notice text for testing"""
    return """ПОСТАНОВЛЕНИЕ об административном правонарушении № АА-001234

Гражданин Петров Петр Петрович совершил правонарушение
по статье 12.9 КоАП РФ. Штраф 5000 рублей.

Инспектор: Сидоров С.С."""

# Integration tests using fixtures
def test_bill_with_fixture(sample_bill_text):
    """Test bill parsing using fixture"""
    sections = split_sections(sample_bill_text)
    assert "ВЕКСЕЛЬ" in sections["header"]
    assert "Обязательство" in sections["body"]

def test_fine_with_fixture(sample_fine_text):
    """Test fine parsing using fixture"""
    sections = split_sections(sample_fine_text)
    fields = extract_fields_from_sections(sections)
    assert len(fields["amounts"]) > 0
    assert any("5000" in str(a["amount"]) for a in fields["amounts"]) 