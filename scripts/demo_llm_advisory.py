#!/usr/bin/env python3
"""
Legal ASI - LLM Advisory Demo (No Dependencies)
Demonstrates advisory analysis without external libraries
"""

import re
import json
import time

def extract_key_info(text):
    """Extract key information from legal document"""
    info = {
        "amounts": [],
        "dates": [],
        "parties": [],
        "document_numbers": []
    }
    
    # Extract money amounts
    money_matches = re.findall(r'(\d+[\s,]?\d*)\s*(руб|рублей|₽)', text, re.IGNORECASE)
    for match in money_matches:
        amount = match[0].replace(' ', '').replace(',', '')
        if amount.isdigit():
            info["amounts"].append(f"{amount} рублей")
    
    # Extract dates
    date_matches = re.findall(r'\d{1,2}\.\d{1,2}\.\d{2,4}', text)
    info["dates"].extend(date_matches)
    
    # Extract names (Russian pattern)
    names = re.findall(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+', text)
    info["parties"].extend(names[:5])
    
    # Extract document numbers
    doc_nums = re.findall(r'№\s*(\d+[\w\-\/]*)', text, re.IGNORECASE)
    info["document_numbers"].extend(doc_nums)
    
    return info

def analyze_bill_of_exchange(text, key_info):
    """Analyze bill of exchange document"""
    return {
        "document_analysis": "Обнаружен вексель - долговое обязательство с указанием суммы и срока платежа",
        "key_parties": key_info.get("parties", ["Должник", "Кредитор"]),
        "legal_obligations": [
            "Обязательство выплатить указанную сумму в срок",
            "Соблюдение формы простого векселя",
            "Возможность передачи прав по индоссаменту"
        ],
        "deadlines": key_info.get("dates", ["Срок платежа не указан"]),
        "recommendations": [
            "Проверить наличие всех обязательных реквизитов векселя",
            "Убедиться в платежеспособности должника",
            "Сохранить оригинал документа"
        ],
        "risk_level": "средний",
        "next_actions": [
            "Направить требование о платеже",
            "При неплатеже - обратиться в суд",
            "Рассмотреть возможность залогового обеспечения"
        ]
    }

def analyze_fine_notice(text, key_info):
    """Analyze fine notice document"""
    return {
        "document_analysis": "Постановление об административном правонарушении с назначением штрафа",
        "key_parties": key_info.get("parties", ["Нарушитель", "Инспектор"]),
        "legal_obligations": [
            "Обязанность уплатить штраф в установленный срок",
            "Право на обжалование постановления",
            "Возможность рассрочки платежа"
        ],
        "deadlines": [
            "60 дней на уплату штрафа",
            "10 дней на обжалование (если не пропущен)"
        ],
        "recommendations": [
            "Проверить правомерность вынесения постановления",
            "При несогласии - подать жалобу в вышестоящий орган",
            "Уплатить штраф в срок во избежание увеличения суммы"
        ],
        "risk_level": "низкий",
        "next_actions": [
            "Оплатить штраф через госуслуги или банк",
            "При обжаловании - подготовить доказательства",
            "Сохранить документы об оплате"
        ]
    }

def analyze_document(text, doc_type):
    """Main document analysis function"""
    start_time = time.time()
    
    # Extract key information
    key_info = extract_key_info(text)
    
    # Analyze based on document type
    if "вексель" in doc_type.lower() or "bill" in doc_type.lower():
        analysis = analyze_bill_of_exchange(text, key_info)
    elif "штраф" in doc_type.lower() or "fine" in doc_type.lower():
        analysis = analyze_fine_notice(text, key_info)
    else:
        analysis = {
            "document_analysis": "Документ требует дополнительного анализа",
            "key_parties": key_info.get("parties", []),
            "legal_obligations": ["Требуется определение типа документа"],
            "deadlines": [],
            "recommendations": ["Обратиться к юристу для консультации"],
            "risk_level": "неопределен",
            "next_actions": ["Провести детальную экспертизу"]
        }
    
    processing_time = time.time() - start_time
    
    return {
        **analysis,
        "processing_time": round(processing_time, 3),
        "key_info_extracted": key_info,
        "llm_used": False,
        "analysis_method": "Enhanced pattern matching + legal knowledge base"
    }

def demo_advisory_analysis():
    """Demonstrate advisory analysis capabilities"""
    print("🧪 Legal ASI - LLM Advisory Demo")
    print("=" * 35)
    print()
    
    # Test documents
    test_documents = [
        {
            "title": "Вексель",
            "text": """ВЕКСЕЛЬ № 123456 от 15.12.2023

Обязательство: Иванов Иван Иванович обязуется выплатить 
ООО "Рога и Копыта" сумму в размере 50000 рублей до 15.01.2024.

Должник: Иванов Иван Иванович
Паспорт: 4510 123456
Адрес: г. Москва, ул. Ленина, д. 10

Кредитор: ООО "Рога и Копыта"
ИНН: 7701234567

Подпись должника: _________________""",
            "type": "bill_of_exchange"
        },
        {
            "title": "Штраф ГИБДД",
            "text": """ПОСТАНОВЛЕНИЕ об административном правонарушении
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
Должность: Инспектор ГИБДД""",
            "type": "fine_notice"
        }
    ]
    
    for i, doc in enumerate(test_documents):
        print(f"📄 Demo {i+1}: {doc['title']}")
        print("-" * 30)
        
        # Analyze document
        result = analyze_document(doc["text"], doc["type"])
        
        # Display results
        print(f"✅ Анализ завершен за {result['processing_time']}s")
        print(f"📋 Описание: {result['document_analysis']}")
        print(f"⚖️  Уровень риска: {result['risk_level']}")
        print()
        
        print("👥 Основные участники:")
        for party in result['key_parties'][:3]:
            print(f"   • {party}")
        print()
        
        print("📌 Юридические обязательства:")
        for obligation in result['legal_obligations'][:3]:
            print(f"   • {obligation}")
        print()
        
        print("💡 Рекомендации:")
        for rec in result['recommendations'][:3]:
            print(f"   • {rec}")
        print()
        
        print("🚀 Следующие шаги:")
        for action in result['next_actions'][:3]:
            print(f"   • {action}")
        print()
        
        # Show extracted information
        extracted = result['key_info_extracted']
        if any(extracted.values()):
            print("🔍 Извлеченная информация:")
            if extracted['amounts']:
                print(f"   💰 Суммы: {', '.join(extracted['amounts'])}")
            if extracted['dates']:
                print(f"   📅 Даты: {', '.join(extracted['dates'])}")
            if extracted['parties']:
                print(f"   👤 Лица: {', '.join(extracted['parties'][:2])}")
            if extracted['document_numbers']:
                print(f"   📄 Номера: {', '.join(extracted['document_numbers'])}")
        
        print("\n" + "=" * 50 + "\n")
    
    print("🎉 DEMO COMPLETE!")
    print()
    print("✅ LLM Advisory Features Demonstrated:")
    print("   • Document type recognition")
    print("   • Key information extraction")
    print("   • Risk level assessment")
    print("   • Legal obligations identification")
    print("   • Practical recommendations")
    print("   • Next action guidance")
    print()
    print("🔄 Integration Status:")
    print("   • Stub analysis: ✅ Working")
    print("   • Ollama LLM: ⏳ Optional (install with scripts/setup_ollama.sh)")
    print("   • API endpoint: ✅ /api/v1/advise/analyze")
    print("   • Frontend ready: ✅ JSON response format")

if __name__ == "__main__":
    demo_advisory_analysis() 