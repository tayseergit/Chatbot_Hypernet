# منظومة المساعد الذكي ولوحة التحكم لشركات مزودي خدمة الإنترنت (AI ISP Chatbot & Dashboard)

منصة متكاملة متعددة الطبقات (Multi-Tier Architecture) مصممة لأتمتة خدمة العملاء والدعم الفني لشركات تزويد خدمة الإنترنت (ISP). يجمع المشروع بين **بوت تيليجرام تفاعلي** مدعوم بنماذج اللغة الكبيرة (LLMs) وتقنية الاسترجاع المعزز بالتوليد (RAG)، مع **ربط مباشر بنظام إدارة المشتركين (HyperCRM)**، و**لوحة تحكم إدارية حديثة (React + FastAPI)** لإدارة الجلسات، الصلاحيات، قاعدة المعرفة، والإشعارات.

---

## المحتويات

1. [المميزات الرئيسية](#المميزات-الرئيسية)
2. [معمارية النظام وبنية المشروع](#معمارية-النظام-وبنية-المشروع)
3. [المتطلبات الأساسية](#المتطلبات-الأساسية)
4. [الإعداد والتكوين (Configuration)](#الإعداد-والتكوين-configuration)
5. [طريقة التثبيت والتشغيل](#طريقة-التثبيت-والتشغيل)
6. [واجهات الاستخدام وأوضاع التشغيل](#واجهات-الاستخدام-وأوضاع-التشغيل)
7. [نقاط وملاحظات تحتاج إلى توضيح أو مراجعة](#نقاط-وملاحظات-تحتاج-إلى-توضيح-أو-مراجعة)

---

## المميزات الرئيسية

- **بوت تيليجرام ذكي ومتعدد الوسائط (`presentation/telegram_bot.py`):**
  - دعم المحادثات النصية مع البث التدريجي للردود (Streaming).
  - استقبال الصور وتحليلها بصرياً (مثل تشخيص مؤشرات الراوتر أو قيم خط الـ DSL).
  - استقبال الرسائل الصوتية وتحويلها إلى نص باستخدام نموذج Whisper المحلي (`application/shared/utils/transcriber.py`).
  - مصادقة المشتركين عبر مشاركة رقم الهاتف الموثق في تيليجرام أو عبر اسم المستخدم وكلمة المرور الخاصة بالاشتراك.
  - أزرار تفاعلية (Inline Keyboards) لتنفيذ العمليات مثل تمديد الفاتورة، فصل الجلسة النشطة، وتفعيل الباقات الإضافية.
- **تكامل مباشر مع نظام CRM (`backend_service/crm/`):**
  - استعلام فوري ومتوازٍ (Concurrent Fetching) عن بيانات المشترك، الرصيد، الباقة الحالية، السرعة الحية، الفواتير، الجلسات، وصلاحية IPTV.
  - تخزين مؤقت ذكي (`TTLCache`) لتقليل الضغط على خادم الـ CRM، مع تنقيح تلقائي للبيانات الحساسة (PII Redaction) قبل تمريرها للنموذج اللغوي.
- **محرك استرجاع معزز بالتوليد RAG (`application/rag/`):**
  - يعتمد على `ChromaDB` و`SentenceTransformers` (`paraphrase-multilingual-MiniLM-L12-v2`).
  - يدمج الأسئلة الشائعة من ملف `chatbot.xls` وبيانات الباقات والأسعار من `resources/company_info.json` مع إعادة التحميل التلقائي عند التعديل (Hot-Reload).
- **دعم متعدد لمزودي النماذج اللغوية (`application/llm/`):**
  - يدعم كلاً من **Google Gemini** (`gemini_provider.py`)، و**Ollama** (`ollama_provider.py`)، و**LM Studio** (`lmstudio_provider.py`).
- **نظام أمان وصلاحيات متعدد الطبقات:**
  - بوابة صلاحيات (`PermissionGate` و`PermissionService`) للتحكم الفوري بتفعيل أو تعطيل أي أداة من أدوات الوكيل الذكي، بالإضافة إلى مفتاح إيقاف طوارئ شامل (Emergency Kill Switch).
  - حماية من الإغراق والرسائل المزعجة (`RateLimitMiddleware`) وتحديد حصص شهرية للرسائل والصور والمقاطع الصوتية لكل مستخدم.
- **لوحة تحكم إدارية شاملة (`dashboard_frontend/` + `presentation/api_server.py`):**
  - مبنية باستخدام React 19 وVite 8، وتوفر نظام صلاحيات للمشرفين (RBAC) ومصادقة JWT، ومراقبة حية للجلسات، والرد اليدوي المباشر عبر تيليجرام، وبث الإشعارات الجماعية، وإدارة قاعدة المعرفة وكتيبات إرشادات الراوتر (PDFs)، وبيئة اختبار تفاعلية (Playground).

---

## معمارية النظام وبنية المشروع

يتبع المشروع معمارية ثلاثية الطبقات (Presentation Tier, Application Tier, Backend/Data Tier) مع فصل الاهتمامات عبر البرمجة الموجهة بالجوانب (AOP) وناقل رسائل داخلي (Message Bus):

```text
Chatbot_Hypernet/
├── application/                        # طبقة منطق الأعمال والذكاء الاصطناعي (Application Tier)
│   ├── app.py                          # نقطة الدخول الرئيسية للتطبيق (Console / Telegram / API)
│   ├── agent/                          # تصنيف النوايا (Intents) وإدارة قرارات الوكيل والخدمة الصوتية
│   ├── analytics/                      # جمع وتحليل مقاييس الاستخدام والأداء
│   ├── aspects/                        # مزخرفات AOP (التسجيل، المقاييس، التتبع، معالجة الاستثناءات)
│   ├── facade/                         # الواجهة الموحدة (ChatbotFacade) ومنسق سير العمل (WorkflowCoordinator)
│   ├── llm/                            # محرك الاستدلال وموفرو النماذج (Gemini, Ollama, LM Studio) وبناء المحفزات
│   ├── message_bus/                    # ناقل الأوامر والأحداث الداخلي (Broker, Commands, Events)
│   ├── middlewares/                    # خط أنابيب البرمجيات الوسيطة (المصادقة، تحديد معدل الطلبات)
│   ├── monitoring/                     # إدارة السجلات (Logger)، المقاييس، والتتبع (Trace Manager)
│   ├── permissions/                    # بوابة التحقق من صلاحيات الوكيل الذكي (PermissionGate)
│   ├── rag/                            # خدمة RAG، مسترجع الوثائق، إعادة الترتيب (Reranker)، وبناء السياق
│   ├── response_generation/            # بناء وتنسيق الردود النهائية للمستخدم
│   └── shared/                         # الإعدادات المركزية (app_config.py)، كائنات نقل البيانات (DTOs)، والأدوات المساعدة
│
├── backend_service/                    # طبقة البيانات، الأمان، والتكامل مع الـ CRM (Backend Tier)
│   ├── main.py                         # تهيئة قاعدة البيانات وحاوية الخدمات الخلفية
│   ├── container.py                    # حاوية حقن الاعتماديات (BackendContainer)
│   ├── core/
│   │   ├── database.py                 # إعدادات اتصال SQLAlchemy بـ MySQL والإنشاء التلقائي للجداول
│   │   ├── security.py                 # تشفير كلمات المرور (Bcrypt) وإدارة رموز JWT
│   │   ├── models/                     # نماذج قاعدة البيانات (Session, Message, Admin, AdminRole, ActionLog, CRMLog...)
│   │   └── services/                   # خدمات الجلسات، الرسائل، مصادقة المشتركين والمشرفين، السجلات، والصلاحيات
│   ├── crm/                            # عميل HyperCRM (crm_client.py) ومدير مصادقة الـ CRM (crm_auth_manager.py)
│   └── tools/                          # منفذ أدوات الوكيل الذكي (tool_executor.py)
│
├── presentation/                       # طبقة العرض وواجهات البرمجة (Presentation Tier)
│   ├── api_server.py                   # خادم FastAPI لواجهة لوحة التحكم ونقاط نهاية المحادثة
│   └── telegram_bot.py                 # تطبيق بوت تيليجرام ومعالجة الرسائل والأزرار التفاعلية
│
├── dashboard_frontend/                 # واجهة لوحة التحكم الأمامية (React 19 + Vite 8)
│   ├── src/
│   │   ├── components/                 # تبويبات اللوحة (Overview, Analytics, Sessions, CRM, Broadcast, RAG, Permissions, Admins, Playground)
│   │   └── context/                    # سياق مصادقة المشرفين (AuthContext.jsx)
│   ├── package.json
│   └── vite.config.js                  # إعدادات Vite وتوجيه طلبات /api إلى المنفذ 8000
│
├── resources/                          # الموارد الثابتة وقاعدة المعرفة
│   ├── company_info.json               # بيانات الباقات، الأسعار، الخدمات، وأرقام التواصل
│   └── pdfs/                           # كتيبات إعداد أجهزة الراوتر (PDFs) لإرسالها للمشتركين
│
├── chatbot.xls                         # ملف الأسئلة الشائعة والإجابات (مصدر أساسي لخدمة RAG)
├── config.example.json                 # نموذج ملف إعدادات الشركة والرسائل النصية (يُنسخ إلى config.json)
├── .env.example                        # نموذج متغيرات البيئة والبيانات السرية (يُنسخ إلى .env)
├── seed_permissions.py                 # سكربت لزرع الصلاحيات الافتراضية للوكيل الذكي في قاعدة البيانات
├── dashboard.py                        # لوحة سجلات مبسطة (Legacy) مبنية بـ Flask تعمل على المنفذ 5000
├── templates/index.html                # قالب HTML الخاص بلوحة Flask القديمة
├── start_all.bat                       # سكربت تشغيل الخدمات على نظام Windows
├── start_bot.bat                       # سكربت تشغيل البوت على نظام Windows
└── requirements.txt                    # الحزم والاعتماديات البرمجية للغة Python
```

---

## المتطلبات الأساسية

1. **Python 3.10+**.
2. **MySQL Server** (يعمل محلياً أو على خادم خارجي، بترميز `utf8mb4`).
3. **Node.js (v18+) & npm** (لتشغيل واجهة لوحة التحكم `dashboard_frontend`).
4. **FFmpeg** مثبت على النظام ومضاف إلى متغير المسار `PATH` (ضروري لمعالجة المقاطع الصوتية عبر مكتبة `openai-whisper` في `application/shared/utils/transcriber.py`).
5. **مزود نموذج لغوي (LLM Provider):**
   - مفتاح API من **Google Gemini** (الخيار الافتراضي في الإعدادات)، أو
   - خادم **Ollama** محلي، أو
   - خادم **LM Studio** محلي.
6. **حساب بوت تيليجرام (Bot Token)** عبر `@BotFather`.

---

## الإعداد والتكوين (Configuration)

يعتمد المشروع على ملفين أساسيين للإعدادات (كلاهما مستثنى من الرفع إلى Git عبر `.gitignore` لحماية البيانات السرية والخاصة):

### 1. إعداد ملف متغيرات البيئة (`.env`)

قم بنسخ الملف النموذجي `.env.example` إلى `.env` في المجلد الرئيسي للمشروع:

```bash
cp .env.example .env
```

ثم عدّل القيم داخل `.env` بما يناسب بيئة العمل الخاصة بك:

| المتغير | الوصف | القيمة الافتراضية في الكود |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | رمز بوت تيليجرام الخاص بالمشروع | `""` (إلزامي لتشغيل البوت) |
| `DB_HOST` / `DB_PORT` | عنوان ومنفذ خادم قاعدة بيانات MySQL | `localhost` / `3306` |
| `DB_USER` / `DB_PASSWORD` | اسم المستخدم وكلمة المرور لقاعدة البيانات | `root` / `""` |
| `DB_NAME` | اسم قاعدة البيانات (يتم إنشاؤها تلقائياً إن لم تكن موجودة) | `isp_chatbot` |
| `DASHBOARD_JWT_SECRET` | المفتاح السري لتوقيع رموز جلسات المشرفين (JWT) | قيمة افتراضية للتطوير (يجب تغييرها في الإنتاج) |
| `LLM_PROVIDER` | مزود النموذج اللغوي (`gemini` أو `ollama` أو `lmstudio`) | `gemini` |
| `GEMINI_API_KEY` | مفتاح واجهة Google Gemini API | `""` |
| `GEMINI_MODEL` | اسم نموذج Gemini المستخدم | `gemini-3.1-flash-lite` |
| `OLLAMA_URL` / `OLLAMA_MODEL` | رابط واسم نموذج Ollama المحلي | `http://localhost:11434/api/generate` |
| `LMSTUDIO_URL` / `LMSTUDIO_MODEL` | رابط واسم نموذج LM Studio المحلي | `http://127.0.0.1:1234/v1/chat/completions` |
| `CRM_BASE_URL` | الرابط الأساسي لواجهة HyperCRM API | `http://localhost:8090/api/crm` |
| `CRM_USERNAME` / `CRM_PASSWORD` | بيانات دخول حساب المدير في نظام CRM لجلب رمز المصادقة | غير معرّف (إلزامي للاتصال بالـ CRM) |
| `CRM_USER_LOGIN_ENDPOINT` | رابط التحقق من بيانات دخول المشتركين | `{CRM_BASE_URL}/login-user` |
| `RAG_KNOWLEDGE_FILE` | مسار ملف الأسئلة الشائعة لخدمة RAG | `chatbot.xls` |
| `CHATBOT_DEBUG` / `LOG_LEVEL` | تفعيل وضع التصحيح ومستوى السجلات | `false` / `INFO` |
| `ENABLE_TRACING` / `ENABLE_CRM_LOGS` | تفعيل تتبع الطلبات وتسجيل طلبات الـ CRM | `true` / `true` |

### 2. إعداد ملف تكوين الشركة والرسائل (`config.json`)

يقرأ الملف `application/shared/configuration/app_config.py` إعدادات اسم الشركة، رقم مركز الاتصال، رابط واتساب، وقوالب رسائل المصادقة والأخطاء من ملف `config.json`.

قم بنسخ الملف النموذجي `config.example.json` إلى `config.json`:

```bash
cp config.example.json config.json
```

وعدّل القيم (`company_name`، `call_center_number`، `whatsapp_link`، ونصوص `messages`) مع الحفاظ على المتغيرات النصية مثل `{attempt}` و`{call_center_number}` و`{whatsapp_link}`.

---

## طريقة التثبيت والتشغيل

### الخطوة 1: إنشاء البيئة الافتراضية وتثبيت حزم Python

```bash
# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# أو على أنظمة Linux / macOS
source venv/bin/activate

# تثبيت المتطلبات الأساسية
pip install -r requirements.txt

# تثبيت الحزم الإضافية المستخدمة في طبقة الأمان والتخزين المؤقت
pip install bcrypt cachetools
```

> **ملاحظة حول نموذج الصوت (Whisper):** عند استقبال أول رسالة صوتية، يبحث النظام عن النموذج المحلي في المسار `models/small.pt`، وفي حال عدم وجوده يقوم بتحميل نموذج `small` تلقائياً عبر مكتبة `openai-whisper`.

### الخطوة 2: تهيئة قاعدة البيانات والصلاحيات

يتولى النظام (`backend_service/core/database.py` و`backend_service/container.py`) عند بدء التشغيل ما يلي تلقائياً:
1. إنشاء قاعدة البيانات المحددة في `DB_NAME` (افتراضياً `isp_chatbot`) إذا لم تكن موجودة.
2. إنشاء جميع الجداول عبر SQLAlchemy.
3. زرع الصلاحيات الافتراضية لأدوات الوكيل الذكي (`seed_defaults`).
4. إنشاء دور `Super Admin` وحساب المشرف الأول تلقائياً إذا كان جدول المشرفين فارغاً.

كما يمكنك تشغيل سكربت زرع الصلاحيات يدوياً عند الحاجة:

```bash
python seed_permissions.py
```

### الخطوة 3: تشغيل الخادم الخلفي وبوت تيليجرام

نقطة الدخول الموحدة للتطبيق هي `application/app.py`، وتدعم ثلاثة أوضاع تشغيل:

#### أ) وضع الخادم المتكامل (FastAPI + Telegram Bot معاً) — **موصى به**
يشغّل خادم الـ API على المنفذ `8000` (لربط لوحة التحكم) ويطلق بوت تيليجرام تلقائياً في خيط خلفي (Background Thread) في حال توفر `TELEGRAM_BOT_TOKEN`:

```bash
python application/app.py --mode api
```
- توثيق الواجهة البرمجية (Swagger UI): `http://localhost:8000/docs`
- فحص حالة الخادم: `http://localhost:8000/health`

#### ب) وضع بوت تيليجرام فقط
لتشغيل بوت تيليجرام بمفرده دون خادم FastAPI:

```bash
python application/app.py --mode telegram
```

#### ج) وضع طرفية الاختبار التفاعلية (Console Mode)
لاختبار المحادثة والـ RAG مباشرة من سطر الأوامر:

```bash
python application/app.py --mode console
```

### الخطوة 4: تشغيل واجهة لوحة التحكم الأمامية (React Dashboard)

في نافذة طرفية جديدة، انتقل إلى مجلد `dashboard_frontend` وقم بتثبيت الحزم وتشغيل خادم التطوير:

```bash
cd dashboard_frontend
npm install
npm run dev
```

- ستعمل لوحة التحكم على الرابط: `http://localhost:5173` (ويقوم Vite بتوجيه جميع طلبات `/api` تلقائياً إلى `http://127.0.0.1:8000`).

---

## واجهات الاستخدام وأوضاع التشغيل

- **أوامر بوت تيليجرام المتاحة للمشتركين:**
  - `/start` — بدء المحادثة وعرض رسالة الترحيب.
  - `/new` — مسح سياق المحادثة السابق وبدء موضوع جديد.
  - `/id` — عرض المعرّف الخاص بالمستخدم لمشاركته مع فريق الدعم الفني.
  - `/logout` — تسجيل الخروج من حساب المشترك المرتبط بالجلسة.
- **تبويبات لوحة التحكم الإدارية (`dashboard_frontend`):**
  - **نظرة عامة (Overview):** إحصائيات الجلسات وحالة الاتصال الفورية (Bot, LLM, CRM).
  - **التحليلات (Analytics):** أكثر النوايا (Intents) والأدوات استخداماً ومتوسط زمن الاستجابة.
  - **جلسات المحادثة (Sessions & Chat):** استعراض محادثات المشتركين وإرسال ردود يدوية مباشرة إلى تيليجرام.
  - **سجل عمليات الوكيل (Agent Action Logs):** تتبع تفصيلي لجميع العمليات والأدوات المنفذة.
  - **بيانات المشتركين (CRM Lookup):** عرض حالة ارتباط جلسات المشتركين واستعراض ملخص حساب المشترك من الـ CRM.
  - **بث الإشعارات (Broadcast):** إرسال تعميمات أو تنبيهات جماعية عبر تيليجرام (للجميع، للموثقين، لغير الموثقين، أو لقائمة مخصصة).
  - **قاعدة المعرفة (Knowledge Base):** إضافة وتعديل وحذف الأسئلة الشائعة (`chatbot.xls`)، تعديل باقات وأسعار الشركة (`company_info.json`)، ورفع أو حذف كتيبات إعداد الراوتر (`resources/pdfs/`).
  - **الصلاحيات والطوارئ (Permissions):** تفعيل/تعطيل أدوات الوكيل الذكي أو تفعيل الإيقاف الطارئ الشامل.
  - **إدارة المشرفين والأدوار (Admins Management):** إدارة حسابات مشرفي اللوحة والأدوار والصلاحيات (RBAC).
  - **بيئة الاختبار (Test Playground):** محاكاة محادثة مباشرة مع البوت من داخل لوحة التحكم.

---

## نقاط وملاحظات تحتاج إلى توضيح أو مراجعة

بناءً على فحص ملفات المستودع الحالية دون تخمين، توجد النقاط التالية التي يُنصح الفريق بمراجعتها أو توضيحها:

1. **تعارض مسار تشغيل الـ API في `start_all.bat`:**
   - السطر الخاص بتشغيل الـ Backend في ملف `start_all.bat` يستدعي:
     `uvicorn backend_service.api:app --host 0.0.0.0 --port 8000 --reload`
   - بينما لا يوجد ملف باسم `backend_service/api.py` في المستودع، وإنما يتم إنشاء تطبيق FastAPI داخل `presentation/api_server.py` ويتم تشغيله عبر `python application/app.py --mode api`. كما أن تشغيل `--mode api` يقوم بالفعل بتشغيل بوت تيليجرام في الخلفية، لذا فإن تشغيل `presentation/telegram_bot.py` بشكل منفصل في الخطوة الثالثة من `start_all.bat` (وهو ملف يحتوي على الصنف `TelegramBot` فقط دون دالة `main`) لن يعمل بشكل مستقل.
2. **ملف مفقود مشار إليه في `start_bot.bat`:**
   - يحاول ملف `start_bot.bat` تشغيل `python mock_crm_server.py` قبل تشغيل البوت، ولكن ملف `mock_crm_server.py` غير موجود في الفرع الحالي (تمت إزالته في تحديثات سابقة).
3. **حزم مستخدمة في الكود وغير مدرجة في `requirements.txt`:**
   - المكتبتان `bcrypt` (في `backend_service/core/security.py`) و`cachetools` (في `backend_service/crm/crm_client.py`) مستخدمتان بشكل أساسي في المشروع ولكن غير مذكورتين في `requirements.txt`.
   - ملف `dashboard.py` (لوحة السجلات القديمة) يستورد مكتبة `flask` وهي غير مضافة في `requirements.txt`.
4. **ازدواجية في خدمات تحويل الصوت إلى نص:**
   - يوجد ملف `application/shared/utils/transcriber.py` الذي يستخدم مكتبة `openai-whisper` محلياً (وهو المستخدم فعلياً في `presentation/telegram_bot.py`)، ويوجد أيضاً ملف `application/agent/voice_service.py` الذي يعتمد على واجهة OpenAI السحابية (`OPENAI_API_KEY`). يُنصح بتوضيح ما إذا كان `voice_service.py` لا يزال مستخدماً أم أنه كود قديم.
5. **طريقة تعامل خدمة RAG مع ملفات الـ PDF:**
   - وفقاً للتعليق التوضيحي والكود في `application/rag/rag_service.py`، تقوم خدمة RAG بفهرسة ملف `chatbot.xls` وملف `resources/company_info.json` فقط، ولا تقوم بفهرسة النصوص داخل ملفات `resources/pdfs/`، بل تُستخدم ملفات الـ PDF لإرسالها كملفات إرشادية جاهزة للمشتركين عند طلب إعدادات الراوتر.
6. **تنبيهات أمنية خاصة ببيئة الإنتاج:**
   - عند تشغيل النظام لأول مرة على قاعدة بيانات فارغة، يقوم `AdminAuthService.seed_default_admin_if_empty()` في `backend_service/core/services/admin_auth_service.py` بإنشاء حساب مشرف افتراضي وتطبعه في الطرفية. **يجب تغيير كلمة المرور الافتراضية فوراً بعد أول تسجيل دخول.**
   - يجب التأكد من تعيين قيمة عشوائية قوية للمتغير `DASHBOARD_JWT_SECRET` في ملف `.env` وعدم الاعتماد على القيمة الاحتياطية الموجودة في `backend_service/core/security.py`.
   - في ملف `presentation/api_server.py`، تم تعريف نقاط النهاية `GET /api/permissions` و`PUT /api/permissions/{tool_name}` مرتين (المرة الأولى محمية بـ `Depends(get_current_admin)` والمرة الثانية بدون مصادقة)، مما يستدعي مراجعة الفريق لإزالة التعريف المكرر.
   - توجد بعض الملفات الفارغة في المستودع (`backend_service/config.py`، `backend_service/crm/exceptions.py`، `backend_service/crm/interfaces.py`، `backend_service/crm/README.md`) والتي قد تكون محجوزة لتطوير مستقبلي.
