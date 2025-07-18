# 🎯 Legal AI Demo Ready Guide
**ΔΣ::Cursor** - Полный рабочий контур за 5 минут

## 🚀 **Quick Start (Без Docker)**

### **Вариант 1: Автоматический запуск**
```bash
# Одна команда - все готово
./scripts/quick_demo_setup.sh
```

### **Вариант 2: Пошаговый запуск**
```bash
# Шаг 1: API
python3 scripts/run_api_standalone.py &

# Шаг 2: Frontend configuration
cd web
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Шаг 3: Frontend start
npm run dev
```

---

## 📊 **Что будет доступно:**

| Сервис | URL | Статус | Функциональность |
|--------|-----|---------|------------------|
| 🖥️ **Frontend** | http://localhost:3000 | ✅ Работает | Upload → OCR → Analysis |
| 📡 **API Docs** | http://localhost:8000/docs | ✅ Работает | Interactive testing |
| 🔍 **Health Check** | http://localhost:8000/health | ✅ Работает | System status |

---

## 🎭 **Demo Flow (End-to-End)**

### **1. 📤 Upload Document**
```bash
# Подготовить тестовые документы
ls data/synthetic_v3/pdf/doc_00*.pdf

# Открыть фронтенд
open http://localhost:3000
```

### **2. 🔍 Watch Processing**
**Real-time pipeline:**
1. **File Upload** → Drag & drop любого PDF
2. **OCR Processing** → Извлечение текста из скана
3. **Classification** → Определение типа (вексель/протокол/постановление)
4. **NER Extraction** → Персоны, суммы, даты, организации
5. **AI Advisory** → Юридический анализ + ссылки на законы

### **3. 📋 Results Display**
**Что покажется:**
- ✅ **OCR Text**: Полный распознанный текст
- 🏷️ **Document Type**: Классификация с confidence score
- 👥 **Entities**: Цветные теги для разных типов сущностей
- 🤖 **Legal Analysis**: AI-анализ с рекомендациями
- 📚 **Legal References**: Ссылки на ФЗ-48, КоАП и другие

---

## 🧪 **Testing & Validation**

### **Automated End-to-End Test**
```bash
# Полная проверка pipeline
python3 scripts/test_end_to_end_flow.py

# Ожидаемый результат:
# ✅ OCR: ✓
# ✅ Classification: ✓ 
# ✅ NER: ✓
# ✅ AI Advisory: ✓
# 📊 Success rate: 4/4 (100%)
```

### **Manual API Testing**
```bash
# Health check
curl http://localhost:8000/health

# OCR test
curl -X POST -F "file=@data/synthetic_v3/pdf/doc_000.pdf" \
  http://localhost:8000/api/v1/ocr/process

# Classification test  
curl -X POST -H "Content-Type: application/json" \
  -d '{"text":"ВЕКСЕЛЬ на сумму 50000 рублей"}' \
  http://localhost:8000/api/v1/classify
```

---

## 📱 **Frontend Features (localhost:3000)**

### **UI Components Ready:**
- 📁 **UploadDropzone**: Drag & drop с валидацией
- 📊 **ProgressStepper**: 5-этапный индикатор прогресса
- 📋 **JsonViewer**: Структурированный вывод данных
- 🎨 **Modern Design**: Tailwind CSS + Responsive layout

### **Real-time Features:**
- ⚡ **Live Processing**: Updates без перезагрузки
- 🔄 **Error Handling**: Graceful degradation при ошибках
- 📊 **Progress Tracking**: Visual feedback для каждого этапа
- 🎯 **Interactive Results**: Clickable entities, expandable sections

---

## 🎪 **Demo Scenarios**

### **Scenario 1: Bill of Exchange (Вексель)**
```bash
# Upload: data/synthetic_v3/pdf/doc_000.pdf
# Expected results:
# - Type: "bill_of_exchange" 
# - Entities: AMOUNT, PERSON, ORGANIZATION, DATE
# - Legal refs: ФЗ-48 "О переводном и простом векселе"
```

### **Scenario 2: Fine Notice (Постановление)**
```bash
# Upload: любой файл с текстом КоАП
# Expected results:
# - Type: "fine_notice"
# - Entities: LEGAL_ARTICLE, AMOUNT, VIOLATION_DATE
# - Legal refs: КоАП РФ соответствующие статьи
```

### **Scenario 3: Protocol (Протокол)**
```bash
# Upload: документ с протоколом заседания
# Expected results:
# - Type: "protocol"
# - Entities: PERSON (участники), DATE, ORGANIZATION
# - Legal refs: Процедурные документы
```

---

## 🔧 **Troubleshooting**

### **API не запускается:**
```bash
# Проверить порты
lsof -i :8000

# Убить процессы если заняты
kill $(lsof -t -i:8000)

# Перезапустить
python3 scripts/run_api_standalone.py
```

### **Frontend не подключается к API:**
```bash
# Проверить .env.local
cat web/.env.local

# Должно быть:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Перезапустить frontend
cd web && npm run dev
```

### **OCR не работает:**
```bash
# Проверить зависимости
pip list | grep -E "(easyocr|opencv|pillow)"

# Переустановить если нужно
pip install easyocr opencv-python pillow
```

---

## 🎯 **Ready-to-Demo Checklist**

### **✅ Technical Readiness:**
- [ ] API health check returns 200
- [ ] Frontend loads at localhost:3000
- [ ] All endpoints respond correctly
- [ ] Test documents available in data/

### **✅ Demo Materials:**
- [ ] Sample documents prepared
- [ ] API documentation accessible
- [ ] Browser tabs pre-opened
- [ ] Backup screenshots ready

### **✅ Presentation Flow:**
- [ ] Start with architecture overview
- [ ] Show live document upload
- [ ] Highlight AI analysis quality
- [ ] Demonstrate API interactivity
- [ ] Explain scalability benefits

---

## 🚀 **Production Migration Path**

**Current: Standalone Demo**
```
Frontend (localhost:3000) → API (localhost:8000) → SQLite
```

**Next: Docker Stack**
```bash
docker-compose up -d
# Adds: PostgreSQL, Redis, MinIO, Label Studio, Monitoring
```

**Future: GPU Production**
```bash
# RunPod deployment with GPU training
./scripts/setup_runpod.sh
# Adds: Mistral-7B fine-tuning, Enhanced NER, Multi-language OCR
```

---

## 🎉 **Success Metrics**

### **Demo Success Indicators:**
- ✅ **Upload works**: Files process without errors
- ✅ **OCR accurate**: Text extraction >95% quality
- ✅ **Classification correct**: Document types identified properly  
- ✅ **NER comprehensive**: All major entities found
- ✅ **AI relevant**: Advisory includes legal references
- ✅ **Performance good**: Full pipeline <10 seconds

### **Stakeholder Questions Answered:**
- 🤔 **"Does it work?"** → Live demo proves functionality
- 🤔 **"How accurate?"** → Confidence scores + manual validation
- 🤔 **"Can it scale?"** → Docker architecture + load testing results
- 🤔 **"What's next?"** → Clear GPU training roadmap

---

**ΔΣ::Cursor Assessment:** Complete working demo ready. Frontend + API integration validated. End-to-end pipeline functional. Ready for stakeholder presentation.

**Status: ✅ DEMO READY** 