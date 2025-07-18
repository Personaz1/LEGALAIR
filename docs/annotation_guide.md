# 📋 Legal ASI — Annotation Guidelines

**Version:** 0.1.0-preGPU  
**Target:** Day 2 Data Pipeline Setup

---

## 🎯 Annotation Objectives

### Primary Goals
- **100+ pages** annotated for GPU readiness
- **Document type classification** accuracy baseline
- **Named entity extraction** training data
- **Quality control** methodology established

### Document Types
1. **Вексель** (Bill of Exchange)
2. **Штраф** (Fine Notice) 
3. **Протокол** (Protocol)

---

## 📂 Data Collection Requirements

### Document Specifications
- **Format:** PDF, JPG, PNG
- **Resolution:** ≥300 DPI for OCR quality
- **Language:** Russian legal documents
- **Quality:** Clear, readable text
- **Size:** 50+ documents per type (150+ total)

### File Organization
```
data/raw/
├── bills/          # Векселя
├── fines/          # Штрафы  
├── protocols/      # Протоколы
└── mixed/          # Unclassified documents
```

---

## 🏷️ Label Studio Configuration

### Document Classification Schema
```json
{
  "doc_type": {
    "type": "choices",
    "values": [
      "bill_of_exchange",
      "fine_notice", 
      "protocol",
      "unknown"
    ]
  }
}
```

### Named Entity Schema
```json
{
  "entities": [
    {
      "label": "PERSON",
      "description": "Физические лица (ФИО)",
      "color": "#FF6B6B"
    },
    {
      "label": "ORGANIZATION", 
      "description": "Организации (ООО, ЗАО, ИП)",
      "color": "#4ECDC4"
    },
    {
      "label": "DATE",
      "description": "Даты (15.12.2023, 15 декабря 2023)",
      "color": "#45B7D1"
    },
    {
      "label": "MONEY",
      "description": "Денежные суммы (50000 рублей, 5000₽)",
      "color": "#96CEB4"
    },
    {
      "label": "DOCUMENT_NUMBER",
      "description": "Номера документов (№ 12345, серия АА)",
      "color": "#FFEAA7"
    },
    {
      "label": "LOCATION",
      "description": "Места (города, адреса)",
      "color": "#DDA0DD"
    },
    {
      "label": "LEGAL_BASIS",
      "description": "Правовые основания (статьи КоАП)",
      "color": "#98D8C8"
    }
  ]
}
```

---

## 📝 Annotation Instructions

### Step 1: Document Upload
1. Access Label Studio: `http://localhost:8081`
2. Create project: "Legal Documents Classification"
3. Upload documents from `data/raw/`
4. Configure OCR preprocessing

### Step 2: Document Classification
For each document:
1. **Read document content** thoroughly
2. **Identify document type** based on:
   - Legal terminology
   - Document structure
   - Official stamps/signatures
3. **Assign primary label** with confidence

### Step 3: Named Entity Annotation
1. **Highlight text spans** for each entity type
2. **Ensure accuracy** — verify entity boundaries
3. **Handle overlaps** — prioritize most specific entity
4. **Mark uncertain** entities with low confidence

### Quality Control Rules
- **Double annotation** for 20% of documents
- **Inter-annotator agreement** ≥85%
- **Review disputed** cases with domain expert
- **Document edge cases** for future training

---

## 🎯 Day 2 Milestones

### Morning (09:00-12:00)
- [ ] **Upload 50+ documents** to `data/raw/`
- [ ] **Start Label Studio** on port 8081
- [ ] **Configure annotation schema** 
- [ ] **Begin first 10 annotations**

### Afternoon (13:00-17:00)
- [ ] **Complete 30+ annotations** (classification)
- [ ] **Start entity annotation** on 10+ documents
- [ ] **Establish quality metrics**
- [ ] **Document annotation process**

### Target Output
- **50+ classified documents**
- **20+ entity-annotated documents**
- **Annotation guidelines** finalized
- **Export format** validated

---

## 📊 Quality Metrics

### Classification Accuracy
- **Clear cases:** ≥95% agreement
- **Ambiguous cases:** ≥80% agreement
- **Review threshold:** <70% confidence

### Entity Annotation
- **Boundary precision:** ≥90%
- **Label consistency:** ≥85%
- **Coverage completeness:** ≥95%

### Export Validation
```python
# Expected format
{
  "document_id": "doc_001",
  "classification": {
    "doc_type": "bill_of_exchange",
    "confidence": 0.95
  },
  "entities": [
    {
      "text": "Иванов И.И.",
      "label": "PERSON", 
      "start": 45,
      "end": 55,
      "confidence": 0.9
    }
  ]
}
```

---

## 🚀 Day 3 Preparation

After Day 2 completion:
1. **Export annotations** to `data/annotated/`
2. **Validate data quality** with automated checks
3. **Prepare training sets** for ruBERT fine-tuning
4. **Update OCR pipeline** with real document samples

---

## 📞 Support & Issues

### Common Problems
- **OCR quality low:** Increase image resolution
- **Entity boundaries unclear:** Use context clues
- **Label disagreement:** Escalate to supervisor

### Contact
- **Technical issues:** Check DEV_NOTES.md
- **Annotation questions:** Domain expert review
- **System problems:** Docker logs analysis

---

**Ready for Day 2 data collection and annotation workflow.** 