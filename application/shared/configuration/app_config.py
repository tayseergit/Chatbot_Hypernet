"""
Application configuration — centralized config for all modules.
Loads from environment variables with sensible defaults.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_FILE_PATH = BASE_DIR / "config.json"

def load_config():
    if CONFIG_FILE_PATH.exists():
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

_config_data = load_config()

try:
    from dotenv import load_dotenv
    load_dotenv()
    env_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
except ImportError:
    pass

import urllib.parse

def get_whatsapp_link(user_id: Optional[str] = None) -> str:
    base_link = _config_data.get("whatsapp_link", "https://wa.me/963932274222")
    if user_id:
        text = f"ارسل الرسالة كما هي ليستطيع الموظف التعرف على محادثتك:\n{user_id}"
        encoded_text = urllib.parse.quote(text)
        return f"{base_link}?text={encoded_text}"
    return base_link

_call_center = _config_data.get("call_center_number", "963932274222")

def get_support_fallback_message(user_id: Optional[str] = None) -> str:
    template = _config_data.get("messages", {}).get("fallback_error", "حدث خطأ غير متوقع. يرجى المتابعة مع الدعم عبر واتساب: {whatsapp_link}")
    return template.format(whatsapp_link=get_whatsapp_link(user_id), call_center_number=_call_center)

# Provide fallback for older imports that might still look for a static string
SUPPORT_FALLBACK_MESSAGE = get_support_fallback_message()

def get_message(key: str, user_id: Optional[str] = None, **kwargs) -> str:
    msg = _config_data.get("messages", {}).get(key, "")
    kwargs.setdefault("whatsapp_link", get_whatsapp_link(user_id))
    kwargs.setdefault("call_center_number", _call_center)
    return msg.format(**kwargs)


@dataclass
class RAGConfig:
 
    # knowledge_file: str = "chatbot_knowledge_base.md"
    knowledge_file: str = "chatbot.xls"
    chunk_size: int = 350
    overlap: int = 50
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    collection_name: str = "isp_knowledge"
    n_results: int = 10
    distance_threshold: float = 25.0


@dataclass
class LLMConfig:

    # provider: str = "lmstudio"  
    provider: str = "gemini"  
    # provider: str = "ollama"  
    use_for_intent: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "dagbs/qwen2.5-coder-7b-instruct-abliterated:latest"
    lmstudio_url: str = "http://127.0.0.1:1234/v1/chat/completions"
    lmstudio_model: str = "local-model"
    temperature: float = 0.1
    top_p: float = 0.8
    top_k: int = 5
    num_ctx: int = 500
    request_timeout: int = 120


@dataclass
class CRMConfig:
 
    base_url: str = "http://localhost:8090/api/crm"
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    renewal_day: int = 3


@dataclass
class DatabaseConfig:
 
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""
    pool_size: int = 5
    charset: str = "utf8mb4"

    @property
    def connection_string(self) -> str:
        """Build MySQL connection string."""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}"
        )


@dataclass
class SessionConfig:
    """Session management configuration."""

    ttl_minutes: int = 60
    max_history: int = 20
    cleanup_interval_minutes: int = 10


@dataclass
class SecurityConfig:
    spam_max_calls_per_window: int = 10
    spam_time_window_seconds: int = 20
    spam_block_duration_minutes: int = 5
    pres_max_calls_per_window: int = 10
    pres_time_window_seconds: int = 60
    max_images_per_month: int = 15
    max_voices_per_month: int = 50
    max_messages_per_month: int = 200


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""

    bot_token: str = ""
    webhook_url: Optional[str] = None
    polling_interval: float = 1.0


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration."""

    log_level: str = "INFO"
    log_format: str = "json"
    enable_tracing: bool = True
    enable_metrics: bool = True
    metrics_flush_interval: int = 60


@dataclass
class AppConfig:
    """
    Master application configuration.

    Aggregates all module-specific configs.
    Loads from environment variables with sensible defaults.
    """

    app_name: str = "ISP Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False

    rag: RAGConfig = field(default_factory=RAGConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    crm: CRMConfig = field(default_factory=CRMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        config = cls()

        # App-level
        config.debug = os.getenv("CHATBOT_DEBUG", "false").lower() == "true"

        # RAG
        config.rag.knowledge_file = os.getenv(
            "RAG_KNOWLEDGE_FILE", config.rag.knowledge_file
        )
        config.rag.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", config.rag.chunk_size))
        config.rag.overlap = int(os.getenv("RAG_OVERLAP", config.rag.overlap))
        config.rag.n_results = int(os.getenv("RAG_N_RESULTS", config.rag.n_results))

        # LLM
        config.llm.provider = os.getenv("LLM_PROVIDER", config.llm.provider)
        config.llm.use_for_intent = os.getenv("LLM_USE_FOR_INTENT", "true").lower() == "true"
        config.llm.gemini_api_key = os.getenv("GEMINI_API_KEY", config.llm.gemini_api_key)
        config.llm.gemini_model = os.getenv("GEMINI_MODEL", config.llm.gemini_model)
        config.llm.ollama_url = os.getenv("OLLAMA_URL", config.llm.ollama_url)
        config.llm.ollama_model = os.getenv("OLLAMA_MODEL", config.llm.ollama_model)
        config.llm.lmstudio_url = os.getenv("LMSTUDIO_URL", config.llm.lmstudio_url)
        config.llm.lmstudio_model = os.getenv("LMSTUDIO_MODEL", config.llm.lmstudio_model)
        config.llm.temperature = float(
            os.getenv("LLM_TEMPERATURE", config.llm.temperature)
        )
        config.llm.num_ctx = int(os.getenv("LLM_NUM_CTX", config.llm.num_ctx))

        # CRM
        config.crm.base_url = os.getenv("CRM_BASE_URL", config.crm.base_url)
        config.crm.api_key = os.getenv("CRM_API_KEY", config.crm.api_key)
        config.crm.timeout = int(os.getenv("CRM_TIMEOUT", config.crm.timeout))
        config.crm.renewal_day = int(os.getenv("ISP_RENEWAL_DAY", config.crm.renewal_day))

        # Database (MySQL)
        config.database.host = os.getenv("DB_HOST", config.database.host)
        config.database.port = int(os.getenv("DB_PORT", config.database.port))
        config.database.user = os.getenv("DB_USER", config.database.user)
        config.database.password = os.getenv("DB_PASSWORD", config.database.password)
        config.database.database = os.getenv("DB_NAME", config.database.database)

        # Session
        config.session.ttl_minutes = int(
            os.getenv("SESSION_TTL_MINUTES", config.session.ttl_minutes)
        )

        # Telegram
        config.telegram.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

        # Monitoring
        config.monitoring.log_level = os.getenv(
            "LOG_LEVEL", config.monitoring.log_level
        )
        config.monitoring.enable_tracing = (
            os.getenv("ENABLE_TRACING", "true").lower() == "true"
        )

        # Security & Spam Limits
        config.security.spam_max_calls_per_window = int(os.getenv("SPAM_MAX_CALLS", config.security.spam_max_calls_per_window))
        config.security.spam_time_window_seconds = int(os.getenv("SPAM_WINDOW_SECONDS", config.security.spam_time_window_seconds))
        config.security.spam_block_duration_minutes = int(os.getenv("SPAM_BLOCK_MINUTES", config.security.spam_block_duration_minutes))
        config.security.pres_max_calls_per_window = int(os.getenv("PRES_MAX_CALLS", config.security.pres_max_calls_per_window))
        config.security.pres_time_window_seconds = int(os.getenv("PRES_WINDOW_SECONDS", config.security.pres_time_window_seconds))
        config.security.max_images_per_month = int(os.getenv("MAX_IMAGES_PER_MONTH", config.security.max_images_per_month))
        config.security.max_voices_per_month = int(os.getenv("MAX_VOICES_PER_MONTH", config.security.max_voices_per_month))
        config.security.max_messages_per_month = int(os.getenv("MAX_MESSAGES_PER_MONTH", config.security.max_messages_per_month))

        return config
