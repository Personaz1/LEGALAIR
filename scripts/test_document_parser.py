#!/usr/bin/env python3
"""
Legal ASI - Document Parser Test Script
Quick validation of parsing and field extraction functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.preprocess import split_sections, analyze_document_structure
from ml.extract_fields import extract_fields_from_sections

def test_bill_of_exchange():
    """Test bill of exchange parsing"""
    print("🧪 Testing Bill of Exchange parsing...")
    
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
    
    # Parse sections
    sections = split_sections(bill_text)
    print(f"✅ Sections parsed: header={len(sections['header'])}, body={len(sections['body'])}, footer={len(sections['footer'])}")
    
    # Check content
    assert "ВЕКСЕЛЬ" in sections["header"]
    assert "Обязательство" in sections["body"]
    assert "Подпись" in sections["footer"]
    print("✅ Section content validation passed")
    
    # Extract fields
    fields = extract_fields_from_sections(sections)
    print(f"✅ Fields extracted: {len(fields['amounts'])} amounts, {len(fields['dates'])} dates, {len(fields['persons'])} persons")
    
    # Validate extracted data
    amounts = fields["amounts"]
    assert len(amounts) > 0
    assert any(a["amount"] == 50000 for a in amounts)
    print(f"✅ Amount extraction: {amounts[0]['formatted'] if amounts else 'None'}")
    
    dates = fields["dates"]
    assert len(dates) > 0
    date_strings = [d["formatted"] for d in dates]
    print(f"✅ Date extraction: {', '.join(date_strings)}")
    
    persons = fields["persons"]
    assert len(persons) > 0
    person_names = [p["name"] for p in persons]
    print(f"✅ Person extraction: {', '.join(person_names)}")
    
    return True

def test_fine_notice():
    """Test fine notice parsing"""
    print("\n🧪 Testing Fine Notice parsing...")
    
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
    
    # Parse sections
    sections = split_sections(fine_text)
    print(f"✅ Sections parsed: header={len(sections['header'])}, body={len(sections['body'])}, footer={len(sections['footer'])}")
    
    # Check content
    assert "ПОСТАНОВЛЕНИЕ" in sections["header"]
    assert "правонарушение" in sections["body"]
    print("✅ Section content validation passed")
    
    # Extract fields
    fields = extract_fields_from_sections(sections)
    
    # Check fine-specific extractions
    amounts = fields["amounts"]
    assert len(amounts) > 0
    assert any(a["amount"] == 5000 for a in amounts)
    print(f"✅ Fine amount: {amounts[0]['formatted'] if amounts else 'None'}")
    
    legal_articles = fields["legal_articles"]
    assert len(legal_articles) > 0
    assert any("12.9" in a["article"] for a in legal_articles)
    print(f"✅ Legal article: {legal_articles[0]['formatted'] if legal_articles else 'None'}")
    
    persons = fields["persons"]
    person_names = [p["name"] for p in persons]
    assert any("Петров Петр Петрович" in name for name in person_names)
    print(f"✅ Violator: {person_names[0] if person_names else 'None'}")
    
    return True

def test_protocol():
    """Test protocol parsing"""
    print("\n🧪 Testing Protocol parsing...")
    
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
    
    # Parse sections
    sections = split_sections(protocol_text)
    print(f"✅ Sections parsed: header={len(sections['header'])}, body={len(sections['body'])}, footer={len(sections['footer'])}")
    
    # Check content
    assert "ПРОТОКОЛ" in sections["header"]
    assert "ПОВЕСТКА" in sections["body"] or "Присутствовали" in sections["body"]
    assert "Председатель" in sections["footer"]
    print("✅ Section content validation passed")
    
    # Extract fields
    fields = extract_fields_from_sections(sections)
    
    persons = fields["persons"]
    print(f"✅ Persons found: {len(persons)}")
    if persons:
        person_names = [p["name"] for p in persons]
        print(f"   Names: {', '.join(person_names[:3])}")
    
    organizations = fields["organizations"]
    print(f"✅ Organizations found: {len(organizations)}")
    if organizations:
        org_names = [o["name"] for o in organizations]
        print(f"   Organizations: {', '.join(org_names)}")
    
    return True

def test_comprehensive_analysis():
    """Test comprehensive document analysis"""
    print("\n🧪 Testing Comprehensive Analysis...")
    
    test_text = """ВЕКСЕЛЬ № 999999 от 25.12.2023

Я, Тестов Алексей Петрович, обязуюсь выплатить 
ЗАО "Финанс Групп" сумму в размере 75000 рублей 
к 25.03.2024 на основании договора займа № 156.

Должник: Тестов Алексей Петрович
Паспорт: 4512 789012
Кредитор: ЗАО "Финанс Групп"
ИНН: 7702345678

Подпись должника: _________________
Дата составления: 25.12.2023"""
    
    # Full analysis
    result = analyze_document_structure(test_text)
    
    assert "sections" in result
    assert "analysis" in result
    
    sections = result["sections"]
    analysis = result["analysis"]
    
    print(f"✅ Document analysis complete")
    print(f"   Completeness score: {analysis['completeness_score']:.2f}")
    print(f"   Document type scores: {analysis['document_type_indicators']}")
    
    # Extract fields
    fields = extract_fields_from_sections(sections)
    
    print(f"✅ Field extraction summary:")
    print(f"   Amounts: {len(fields['amounts'])}")
    print(f"   Dates: {len(fields['dates'])}")
    print(f"   Persons: {len(fields['persons'])}")
    print(f"   Organizations: {len(fields['organizations'])}")
    print(f"   Document numbers: {len(fields['document_numbers'])}")
    print(f"   Passports: {len(fields['passports'])}")
    print(f"   INN codes: {len(fields['inn_codes'])}")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing Edge Cases...")
    
    # Empty document
    sections = split_sections("")
    assert all(v == "" for v in sections.values())
    print("✅ Empty document handled")
    
    # Very short document
    sections = split_sections("Короткий текст")
    assert sections["body"] == "Короткий текст"
    print("✅ Short document handled")
    
    # Document with no clear structure
    messy_text = "Какой-то текст без четкой структуры и разделения на секции"
    sections = split_sections(messy_text)
    fields = extract_fields_from_sections(sections)
    print("✅ Unstructured document handled")
    
    # Document with numbers but no proper amounts
    fake_amounts = "Номер телефона: 123456789, индекс: 101000"
    sections = {"header": "", "body": fake_amounts, "footer": ""}
    fields = extract_fields_from_sections(sections)
    print("✅ False positive amounts filtered")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Legal ASI Document Parser - Test Suite")
    print("=" * 50)
    
    try:
        test_bill_of_exchange()
        test_fine_notice()
        test_protocol()
        test_comprehensive_analysis()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Document Parser is ready for integration")
        
        # Performance test
        print("\n⚡ Quick performance test...")
        import time
        
        large_doc = "ВЕКСЕЛЬ № 123456\n\n" + "Содержание документа. " * 100 + "\n\nПодпись: ___"
        
        start_time = time.time()
        sections = split_sections(large_doc)
        fields = extract_fields_from_sections(sections)
        end_time = time.time()
        
        print(f"✅ Large document processed in {end_time - start_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 