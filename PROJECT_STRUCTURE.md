# Database AI - Структура проекта и конфигурация

## 📂 Структура файлов

```
database-ai/
│
├── 📄 .env.example              # Шаблон переменных окружения (ВСЕ настройки здесь!)
├── 📄 .gitignore                # Git ignore файл
├── 📄 docker-compose.yml        # Docker Compose конфигурация
├── 📄 README.md                 # Основная документация
├── 📄 DEPLOY.md                 # Инструкции по развертыванию
├── 📄 Makefile                  # Команды для управления проектом
│
├── 📁 back/                     # Backend приложение (FastAPI + Python)
│   ├── 📄 Dockerfile            # Docker образ для backend
│   ├── 📄 requirements.txt      # Python зависимости
│   ├── 📄 alembic.ini          # Конфигурация Alembic (миграции БД)
│   ├── 📄 init_extensions.sql  # Инициализация PostgreSQL расширений
│   │
│   ├── 📁 alembic/             # Миграции базы данных
│   │   ├── env.py              # Async миграции
│   │   ├── script.py.mako      # Шаблон миграций
│   │   └── versions/           # История миграций
│   │       └── 001_initial.py
│   │
│   ├── 📁 app/                 # Основное приложение
│   │   ├── __init__.py
│   │   ├── 📄 main.py          # FastAPI приложение (entry point)
│   │   ├── 📄 cli.py           # CLI команды (создание админа и т.д.)
│   │   │
│   │   ├── 📁 core/            # Ядро приложения
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Настройки из .env (Pydantic Settings)
│   │   │   ├── security.py     # JWT, bcrypt, шифрование
│   │   │   ├── database.py     # SQLAlchemy sessions, connection pooling
│   │   │   └── elasticsearch.py # ES клиент, индексация, поиск
│   │   │
│   │   ├── 📁 models/          # SQLAlchemy ORM модели
│   │   │   ├── __init__.py     # Экспорт всех моделей
│   │   │   ├── base.py         # BaseModel с id, created_at, updated_at
│   │   │   ├── user.py         # Пользователи (admin/manager)
│   │   │   ├── supplier.py     # Поставщики
│   │   │   ├── rating.py       # Рейтинги поставщиков
│   │   │   ├── email.py        # Email шаблоны, рассылки, треды
│   │   │   ├── product_import.py # Импорты прайс-листов
│   │   │   └── audit_log.py    # Журнал аудита
│   │   │
│   │   ├── 📁 schemas/         # Pydantic схемы (валидация API)
│   │   │   ├── __init__.py
│   │   │   ├── user.py         # User CRUD, Login, Token
│   │   │   ├── supplier.py     # Supplier CRUD, Search Response
│   │   │   └── search.py       # Search Request/Response
│   │   │
│   │   ├── 📁 api/             # API endpoints (роутеры)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # /api/auth/* - авторизация
│   │   │   ├── suppliers.py    # /api/suppliers/* - CRUD поставщиков
│   │   │   ├── search.py       # /api/search/* - поиск
│   │   │   ├── admin.py        # /api/admin/* - админ функции
│   │   │   └── campaigns.py    # /api/campaigns/* - email рассылки
│   │   │
│   │   ├── 📁 services/        # Бизнес-логика (TODO: будет расширена)
│   │   │   ├── __init__.py
│   │   │   ├── email_service.py    # IMAP/SMTP
│   │   │   ├── parser_service.py   # Парсинг прайсов
│   │   │   └── search_service.py   # Поиск через ES
│   │   │
│   │   ├── 📁 tasks/           # Celery задачи
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py   # Конфигурация Celery
│   │   │   ├── email_tasks.py  # IMAP проверка, отправка
│   │   │   ├── parsing_tasks.py # Парсинг файлов
│   │   │   ├── search_tasks.py # Реиндексация ES
│   │   │   └── cleanup_tasks.py # Очистка старых файлов
│   │   │
│   │   ├── 📁 middleware/      # HTTP Middleware
│   │   │   ├── __init__.py
│   │   │   ├── audit.py        # Логирование действий
│   │   │   └── rate_limit.py   # Rate limiting
│   │   │
│   │   └── 📁 utils/           # Утилиты (TODO)
│   │       └── __init__.py
│   │
│   └── 📁 redis/               # Redis конфигурации
│       └── sentinel.conf       # Redis Sentinel для HA
│
├── 📁 front/                   # Frontend (React/Next.js)
│   ├── 📄 Dockerfile
│   ├── 📄 package.json
│   └── (TODO: React компоненты)
│
└── 📁 nginx/                   # Nginx reverse proxy
    ├── 📄 nginx.conf           # Конфигурация nginx
    └── 📁 ssl/                 # SSL сертификаты (не в git)
        └── .gitkeep

```

## 🔧 Ключевые конфигурационные файлы

### 1. `.env` - ЦЕНТРАЛЬНАЯ КОНФИГУРАЦИЯ

**ВСЕ** настройки проекта вынесены в `.env` файл:

#### Группы настроек:

1. **Application Settings** - Базовые настройки приложения
2. **PostgreSQL Settings** - БД (master + replica)
3. **Elasticsearch Settings** - Поиск (точность vs скорость)
4. **Redis Settings** - Кэш и Celery broker
5. **Celery Settings** - Воркеры (количество, очереди)
6. **MinIO/S3 Storage** - Хранение файлов (стратегия хранения)
7. **Email IMAP/SMTP** - Входящие/исходящие письма
8. **AI/LLM Settings** - OpenAI (включение/выключение)
9. **Parsing Settings** - Стратегия парсинга
10. **Search & Indexing** - Режим поиска, индексация
11. **Audit & Logging** - Журналирование
12. **Feature Flags** - Включение/выключение функций

#### Критичные параметры для настройки:

```bash
# Производительность поиска
ES_SEARCH_STRATEGY=precise      # precise | fast | balanced
ES_SEARCH_FUZZINESS=AUTO        # Нечеткий поиск

# Хранение данных
STORAGE_KEEP_ORIGINAL_FILES=true    # Хранить оригиналы прайсов?
STORAGE_KEEP_PARSED_FILES=true      # Хранить распарсенные?
STORAGE_FILE_RETENTION_DAYS=365     # Срок хранения

# Воркеры Celery (масштабирование)
CELERY_EMAIL_CONCURRENCY=4          # Воркеров email
CELERY_PARSING_CONCURRENCY=2        # Воркеров парсинга
CELERY_SEARCH_CONCURRENCY=4         # Воркеров поиска

# AI парсинг (по умолчанию выключен)
AI_ENABLED=false                    # true/false
PARSING_STRATEGY=hybrid             # hybrid | ai | rule_based

# Поиск
SEARCH_MODE=elasticsearch           # elasticsearch | postgres
SEARCH_FALLBACK_TO_POSTGRES=true    # Фоллбэк
```

### 2. `docker-compose.yml` - Оркестрация сервисов

#### Сервисы:

- **postgres_master** - Основная БД (read/write)
- **postgres_replica** - Реплика БД (read-only для поиска) [profile: replica]
- **elasticsearch** - Поисковый движок
- **redis_master** - Кэш и Celery broker
- **redis_sentinel** - HA для Redis [profile: ha]
- **minio** - S3-совместимое хранилище файлов
- **api** - FastAPI приложение
- **celery_worker_email** - Воркер для email задач
- **celery_worker_parsing** - Воркер для парсинга
- **celery_worker_search** - Воркер для поиска
- **celery_beat** - Планировщик задач
- **flower** - Мониторинг Celery [profile: monitoring]
- **nginx** - Reverse proxy
- **frontend** - React приложение

#### Profiles для гибкого запуска:

```bash
# Минимальная конфигурация
docker-compose up -d

# С репликой PostgreSQL
docker-compose --profile replica up -d

# С мониторингом
docker-compose --profile monitoring up -d

# Полная (production)
docker-compose --profile replica --profile ha --profile monitoring up -d
```

### 3. `requirements.txt` - Python зависимости

Основные библиотеки:
- FastAPI + Uvicorn - API
- SQLAlchemy + Asyncpg - ORM
- Elasticsearch - Поиск
- Celery - Задачи
- MinIO + Boto3 - Хранилище
- OpenAI + LangChain - AI (опционально)
- Email библиотеки - IMAP/SMTP
- Pandas, PyPDF2, Tesseract - Парсинг

## 🚀 Быстрый старт

```bash
# 1. Распаковать
tar -xzf database-ai.tar.gz
cd database-ai

# 2. Настроить
cp .env.example .env
# Отредактировать .env

# 3. Запустить
make init
make build
make up

# 4. Миграции
make migrate

# 5. Создать админа
make create-admin

# 6. Проверить
curl http://localhost:8000/health
```

## 📊 Архитектурные решения

### Двухуровневое хранение данных

1. **PostgreSQL** - мета-данные (поставщики, пользователи, рейтинги)
2. **Elasticsearch** - товары (миллионы записей, полнотекстовый поиск)

### Масштабируемость

- **Read Replica** - отдельная БД для поисковых запросов
- **Celery Queues** - раздельные очереди для разных типов задач
- **Nginx Load Balancing** - несколько инстансов API
- **ES Sharding** - данные распределены по шардам

### Отказоустойчивость

- **Redis Sentinel** - автоматический failover
- **PostgreSQL Replication** - streaming replication
- **Health Checks** - автоматический рестарт контейнеров
- **Retry механизмы** - в Celery tasks и ES запросах

## 🔐 Безопасность

- JWT токены (access + refresh)
- Bcrypt хеширование паролей
- Fernet шифрование чувствительных данных
- Rate limiting
- CORS настройки
- Audit log всех действий

## 📝 TODO (для дальнейшей разработки)

1. Полная реализация email парсинга (services/email_service.py)
2. AI парсинг прайсов (services/parser_service.py)
3. Frontend компоненты (React)
4. Расширенные тесты (pytest)
5. CI/CD pipeline (GitHub Actions)
6. Prometheus + Grafana метрики
7. Полная реализация Admin UI (pending imports)

## 🐛 Известные ограничения

1. Frontend - только базовая структура
2. AI парсинг - stub, требует доработки
3. Email reply parsing - базовая реализация
4. Без backup автоматизации (нужен отдельный скрипт)

## 📞 Поддержка

См. README.md и DEPLOY.md для детальной документации.
