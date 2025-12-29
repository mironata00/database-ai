from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DatabaseAI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENCRYPTION_KEY: str

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_EXTERNAL_REGISTRATION: int = 10

    # PostgreSQL
    POSTGRES_HOST: str = "postgres_master"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_REPLICA_ENABLED: bool = False
    POSTGRES_REPLICA_HOST: Optional[str] = None
    POSTGRES_REPLICA_PORT: int = 5432
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 40
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_POOL_RECYCLE: int = 3600

    # Elasticsearch
    ES_HOST: str = "elasticsearch"
    ES_PORT: int = 9200
    ES_SCHEME: str = "http"
    ES_SECURITY_ENABLED: bool = False
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None
    ES_INDEX_PRODUCTS: str = "products"
    ES_INDEX_SHARDS: int = 3
    ES_INDEX_REPLICAS: int = 1
    ES_REFRESH_INTERVAL: str = "1s"

    # Search Configuration
    ES_SEARCH_STRATEGY: str = "precise"
    ES_SEARCH_FUZZINESS: str = "AUTO"
    ES_SEARCH_MIN_SCORE: float = 0.5
    ES_SEARCH_BOOST_EXACT_SKU: float = 10.0
    ES_SEARCH_BOOST_BRAND: float = 8.0
    ES_SEARCH_BOOST_SKU_PARTIAL: float = 5.0
    ES_SEARCH_BOOST_TAGS: float = 4.0
    ES_SEARCH_BOOST_NAME: float = 3.0
    ES_SEARCH_MAX_RESULTS: int = 1000
    ES_SEARCH_AGGREGATION_SIZE: int = 1000
    ES_BULK_SIZE: int = 500
    ES_BULK_TIMEOUT: int = 30
    ES_REQUEST_TIMEOUT: int = 30
    ES_MAX_RETRIES: int = 3

    # Redis
    REDIS_HOST: str = "redis_master"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_MAX_MEMORY: str = "512mb"
    REDIS_CACHE_TTL_SHORT: int = 300
    REDIS_CACHE_TTL_MEDIUM: int = 1800
    REDIS_CACHE_TTL_LONG: int = 3600
    REDIS_CACHE_ENABLED: bool = True

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_EMAIL_CONCURRENCY: int = 4
    CELERY_PARSING_CONCURRENCY: int = 2
    CELERY_SEARCH_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 600
    CELERY_TASK_HARD_TIME_LIMIT: int = 900
    CELERY_BEAT_IMAP_CHECK_INTERVAL: int = 300
    CELERY_BEAT_ES_REINDEX_INTERVAL: int = 86400
    CELERY_BEAT_CLEANUP_OLD_FILES_INTERVAL: int = 43200

    # MinIO / S3
    MINIO_ENABLED: bool = True
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_PRICELISTS: str = "pricelists"
    MINIO_BUCKET_EMAIL_ATTACHMENTS: str = "email-attachments"
    MINIO_BUCKET_EXPORTS: str = "exports"

    # Storage Strategy
    STORAGE_KEEP_ORIGINAL_FILES: bool = True
    STORAGE_KEEP_PARSED_FILES: bool = True
    STORAGE_FILE_RETENTION_DAYS: int = 365
    STORAGE_AUTO_CLEANUP_ENABLED: bool = True
    STORAGE_MAX_FILE_SIZE: int = 104857600
    STORAGE_MAX_EMAIL_ATTACHMENT_SIZE: int = 52428800

    # Email IMAP
    EMAIL_IMAP_ENABLED: bool = True
    EMAIL_IMAP_HOST: str
    EMAIL_IMAP_PORT: int = 993
    EMAIL_IMAP_USER: str
    EMAIL_IMAP_PASSWORD: str
    EMAIL_IMAP_USE_SSL: bool = True
    EMAIL_IMAP_FOLDER: str = "INBOX"
    EMAIL_IMAP_FORWARDING_ADDRESS: str
    EMAIL_IMAP_CHECK_INTERVAL: int = 300
    EMAIL_IMAP_BATCH_SIZE: int = 50
    EMAIL_IMAP_MARK_AS_READ: bool = True

    # Email SMTP - Carousel Configuration
    EMAIL_SMTP_ENABLED: bool = True
    EMAIL_SMTP_CAROUSEL_ENABLED: bool = True
    EMAIL_SMTP_CAROUSEL_SWITCH_ON_LIMIT: bool = True

    # SMTP Account #1
    EMAIL_SMTP_1_HOST: str
    EMAIL_SMTP_1_PORT: int = 587
    EMAIL_SMTP_1_USER: str
    EMAIL_SMTP_1_PASSWORD: str
    EMAIL_SMTP_1_USE_TLS: bool = True
    EMAIL_SMTP_1_FROM_NAME: str
    EMAIL_SMTP_1_FROM_EMAIL: str
    EMAIL_SMTP_1_DAILY_LIMIT: int = 500
    EMAIL_SMTP_1_HOURLY_LIMIT: int = 50

    # SMTP Account #2
    EMAIL_SMTP_2_HOST: Optional[str] = None
    EMAIL_SMTP_2_PORT: int = 587
    EMAIL_SMTP_2_USER: Optional[str] = None
    EMAIL_SMTP_2_PASSWORD: Optional[str] = None
    EMAIL_SMTP_2_USE_TLS: bool = True
    EMAIL_SMTP_2_FROM_NAME: Optional[str] = None
    EMAIL_SMTP_2_FROM_EMAIL: Optional[str] = None
    EMAIL_SMTP_2_DAILY_LIMIT: int = 500
    EMAIL_SMTP_2_HOURLY_LIMIT: int = 50

    # SMTP Account #3
    EMAIL_SMTP_3_HOST: Optional[str] = None
    EMAIL_SMTP_3_PORT: int = 587
    EMAIL_SMTP_3_USER: Optional[str] = None
    EMAIL_SMTP_3_PASSWORD: Optional[str] = None
    EMAIL_SMTP_3_USE_TLS: bool = True
    EMAIL_SMTP_3_FROM_NAME: Optional[str] = None
    EMAIL_SMTP_3_FROM_EMAIL: Optional[str] = None
    EMAIL_SMTP_3_DAILY_LIMIT: int = 500
    EMAIL_SMTP_3_HOURLY_LIMIT: int = 50

    # SMTP Account #4
    EMAIL_SMTP_4_HOST: Optional[str] = None
    EMAIL_SMTP_4_PORT: int = 587
    EMAIL_SMTP_4_USER: Optional[str] = None
    EMAIL_SMTP_4_PASSWORD: Optional[str] = None
    EMAIL_SMTP_4_USE_TLS: bool = True
    EMAIL_SMTP_4_FROM_NAME: Optional[str] = None
    EMAIL_SMTP_4_FROM_EMAIL: Optional[str] = None
    EMAIL_SMTP_4_DAILY_LIMIT: int = 500
    EMAIL_SMTP_4_HOURLY_LIMIT: int = 50

    # SMTP Account #5
    EMAIL_SMTP_5_HOST: Optional[str] = None
    EMAIL_SMTP_5_PORT: int = 587
    EMAIL_SMTP_5_USER: Optional[str] = None
    EMAIL_SMTP_5_PASSWORD: Optional[str] = None
    EMAIL_SMTP_5_USE_TLS: bool = True
    EMAIL_SMTP_5_FROM_NAME: Optional[str] = None
    EMAIL_SMTP_5_FROM_EMAIL: Optional[str] = None
    EMAIL_SMTP_5_DAILY_LIMIT: int = 500
    EMAIL_SMTP_5_HOURLY_LIMIT: int = 50

    # Global SMTP Settings
    EMAIL_SMTP_RATE_LIMIT_PER_MINUTE: int = 30
    EMAIL_SMTP_MAX_RECIPIENTS_PER_EMAIL: int = 1
    EMAIL_SMTP_RETRY_ATTEMPTS: int = 3
    EMAIL_SMTP_RETRY_DELAY: int = 300
    EMAIL_TRACKING_ENABLED: bool = False

    # Telegram Bot
    TELEGRAM_ENABLED: bool = True
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_IDS: str = ""
    TELEGRAM_NOTIFICATION_ON_NEW_REQUEST: bool = True
    TELEGRAM_NOTIFICATION_ON_REQUEST_APPROVED: bool = True
    TELEGRAM_NOTIFICATION_ON_REQUEST_REJECTED: bool = True
    TELEGRAM_RATE_LIMIT_PER_SECOND: int = 30
    TELEGRAM_RATE_LIMIT_PER_MINUTE: int = 20

    # Notifications
    NOTIFICATION_ADMIN_EMAILS: str = ""
    NOTIFICATION_NEW_REQUEST_TO_ADMINS: bool = True
    NOTIFICATION_NEW_SUPPLIER_TO_ADMINS: bool = True
    NOTIFICATION_REQUEST_STATUS_TO_USER: bool = True
    NOTIFICATION_SEND_VIA_EMAIL: bool = True
    NOTIFICATION_SEND_VIA_TELEGRAM: bool = True

    # AI / LLM
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "openai"
    AI_MODEL: str = "gpt-4o"
    AI_API_KEY: Optional[str] = None
    AI_API_BASE_URL: str = "https://api.openai.com/v1"
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.1
    AI_TIMEOUT: int = 60
    AI_AUTO_PARSE_ENABLED: bool = False
    AI_FALLBACK_ON_PARSING_ERROR: bool = True
    AI_MAX_REQUESTS_PER_DAY: int = 1000
    AI_DAILY_COST_LIMIT_USD: float = 50.0

    # Parsing
    PARSING_STRATEGY: str = "hybrid"
    PARSING_ENABLED_FORMATS: str = "xlsx,xls,csv,pdf,txt,zip"
    PARSING_MAX_ROWS_PER_FILE: int = 100000
    PARSING_AUTO_DETECT_ENCODING: bool = True
    PARSING_DEFAULT_ENCODING: str = "utf-8"
    PARSING_PDF_USE_OCR: bool = True
    PARSING_PDF_OCR_LANGUAGE: str = "rus+eng"
    PARSING_COLUMN_DETECTION_MODE: str = "auto"
    PARSING_REQUIRED_COLUMNS: str = "sku,name"
    PARSING_NORMALIZE_BRANDS: bool = True
    PARSING_NORMALIZE_CATEGORIES: bool = True
    PARSING_GENERATE_TAGS_AUTO: bool = True
    PARSING_MAX_TAGS_PER_SUPPLIER: int = 100000

    # Column Synonyms
    PARSING_COLUMN_SKU_SYNONYMS: str = "sku|артикул|код|article|арт|код товара|артикул товара|vendor code|item code|part number|партномер|каталожный номер"
    PARSING_COLUMN_NAME_SYNONYMS: str = "name|наименование|название|товар|продукт|описание|product|item|description|номенклатура|материал"
    PARSING_COLUMN_PRICE_SYNONYMS: str = "price|цена|стоимость|прайс|cost|розница|опт|розничная цена|оптовая цена|price rub|цена руб"
    PARSING_COLUMN_BRAND_SYNONYMS: str = "brand|бренд|производитель|марка|manufacturer|vendor|поставщик|завод"
    PARSING_COLUMN_CATEGORY_SYNONYMS: str = "category|категория|группа|раздел|тип|вид|class|group|подгруппа"
    PARSING_COLUMN_UNIT_SYNONYMS: str = "unit|ед|единица|единица измерения|ед.изм|measure|uom"
    PARSING_COLUMN_STOCK_SYNONYMS: str = "stock|остаток|наличие|количество|qty|available|в наличии|склад"

    PARSING_COLUMN_FUZZY_MATCHING: bool = True
    PARSING_COLUMN_MIN_CONFIDENCE: float = 0.7
    PARSING_COLUMN_USE_POSITION_HINTS: bool = True

    # Search & Indexing
    SEARCH_MODE: str = "elasticsearch"
    SEARCH_ELASTICSEARCH_ENABLED: bool = True
    SEARCH_FALLBACK_TO_POSTGRES: bool = True
    SEARCH_CACHE_RESULTS: bool = True
    SEARCH_CACHE_TTL: int = 1800
    INDEX_STRATEGY: str = "incremental"
    INDEX_BATCH_SIZE: int = 1000
    INDEX_ON_SUPPLIER_CREATE: bool = True
    INDEX_ON_PRODUCT_UPDATE: bool = True
    INDEX_FULL_REINDEX_ENABLED: bool = False

    # Audit & Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_ACTIONS: str = "create,update,delete,login,export"
    AUDIT_LOG_RETENTION_DAYS: int = 365
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: str = "/app/logs/app.log"

    # Sentry
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"

    # Business Logic
    SUPPLIER_DEFAULT_STATUS: str = "pending"
    SUPPLIER_AUTO_APPROVE: bool = False
    RATING_MIN_VALUE: int = 1
    RATING_MAX_VALUE: int = 5
    RATING_REQUIRED_COMMENT_ON_LOW: bool = True
    RATING_LOW_THRESHOLD: int = 3
    EXTERNAL_REGISTRATION_ENABLED: bool = True

    # Company Info
    COMPANY_NAME: str = "Ваша Компания"
    COMPANY_INN: str = ""
    COMPANY_EMAIL: str = "info@yourcompany.ru"
    COMPANY_PHONE: str = "+7 (xxx) xxx-xx-xx"

    # Feature Flags
    FEATURE_EMAIL_TEMPLATES: bool = True
    FEATURE_EMAIL_CAMPAIGNS: bool = True
    FEATURE_EMAIL_REPLY_PARSING: bool = True
    FEATURE_ADVANCED_SEARCH: bool = True
    FEATURE_SUPPLIER_RATINGS: bool = True
    FEATURE_AUDIT_LOG: bool = True
    FEATURE_EXPORT_EXCEL: bool = True
    FEATURE_IMAP_AUTO_IMPORT: bool = True
    FEATURE_AI_PARSING: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_REPLICA(self) -> Optional[str]:
        if self.POSTGRES_REPLICA_ENABLED and self.POSTGRES_REPLICA_HOST:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_REPLICA_HOST}:{self.POSTGRES_REPLICA_PORT}/{self.POSTGRES_DB}"
        return None

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def ELASTICSEARCH_URL(self) -> str:
        auth = ""
        if self.ES_SECURITY_ENABLED and self.ES_USERNAME and self.ES_PASSWORD:
            auth = f"{self.ES_USERNAME}:{self.ES_PASSWORD}@"
        return f"{self.ES_SCHEME}://{auth}{self.ES_HOST}:{self.ES_PORT}"

    @property
    def MINIO_ENDPOINT(self) -> str:
        return f"{self.MINIO_HOST}:{self.MINIO_PORT}"

    @property
    def PARSING_ENABLED_FORMATS_LIST(self) -> List[str]:
        return [fmt.strip() for fmt in self.PARSING_ENABLED_FORMATS.split(",")]

    @property
    def PARSING_REQUIRED_COLUMNS_LIST(self) -> List[str]:
        return [col.strip() for col in self.PARSING_REQUIRED_COLUMNS.split(",")]

    @property
    def AUDIT_LOG_ACTIONS_LIST(self) -> List[str]:
        return [action.strip() for action in self.AUDIT_LOG_ACTIONS.split(",")]

    @property
    def COLUMN_SYNONYMS_MAP(self) -> dict:
        """Returns mapping of column types to their synonyms."""
        return {
            "sku": [s.strip().lower() for s in self.PARSING_COLUMN_SKU_SYNONYMS.split("|")],
            "name": [s.strip().lower() for s in self.PARSING_COLUMN_NAME_SYNONYMS.split("|")],
            "price": [s.strip().lower() for s in self.PARSING_COLUMN_PRICE_SYNONYMS.split("|")],
            "brand": [s.strip().lower() for s in self.PARSING_COLUMN_BRAND_SYNONYMS.split("|")],
            "category": [s.strip().lower() for s in self.PARSING_COLUMN_CATEGORY_SYNONYMS.split("|")],
            "unit": [s.strip().lower() for s in self.PARSING_COLUMN_UNIT_SYNONYMS.split("|")],
            "stock": [s.strip().lower() for s in self.PARSING_COLUMN_STOCK_SYNONYMS.split("|")],
        }

    @property
    def SMTP_ACCOUNTS(self) -> List[dict]:
        """Returns list of available SMTP accounts for carousel."""
        accounts = []
        for i in range(1, 6):
            host = getattr(self, f"EMAIL_SMTP_{i}_HOST", None)
            user = getattr(self, f"EMAIL_SMTP_{i}_USER", None)
            password = getattr(self, f"EMAIL_SMTP_{i}_PASSWORD", None)

            if host and user and password:
                accounts.append({
                    "id": i,
                    "host": host,
                    "port": getattr(self, f"EMAIL_SMTP_{i}_PORT"),
                    "user": user,
                    "password": password,
                    "use_tls": getattr(self, f"EMAIL_SMTP_{i}_USE_TLS"),
                    "from_name": getattr(self, f"EMAIL_SMTP_{i}_FROM_NAME"),
                    "from_email": getattr(self, f"EMAIL_SMTP_{i}_FROM_EMAIL"),
                    "daily_limit": getattr(self, f"EMAIL_SMTP_{i}_DAILY_LIMIT"),
                    "hourly_limit": getattr(self, f"EMAIL_SMTP_{i}_HOURLY_LIMIT"),
                })
        return accounts

    @property
    def TELEGRAM_ADMIN_IDS_LIST(self) -> List[int]:
        """Returns list of Telegram admin IDs."""
        if not self.TELEGRAM_ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.TELEGRAM_ADMIN_IDS.split(",") if id.strip()]

    @property
    def NOTIFICATION_ADMIN_EMAILS_LIST(self) -> List[str]:
        """Returns list of admin emails for notifications."""
        if not self.NOTIFICATION_ADMIN_EMAILS:
            return []
        return [email.strip() for email in self.NOTIFICATION_ADMIN_EMAILS.split(",") if email.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
