"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


class LLMBackend(str, Enum):
    openai_compatible = "openai_compatible"
    self_hosted = "self_hosted"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: Environment = Environment.development
    debug: bool = False
    secret_key: str = Field(..., description="JWT secret key")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    redis_url: str = "redis://localhost:6379/0"

    # Object storage
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "court-documents"

    # LLM
    llm_backend: LLMBackend = LLMBackend.openai_compatible
    llm_api_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = Field(default="", description="LLM API key (empty for self-hosted)")
    llm_model_name: str = "gpt-4o"
    llm_temperature: float = 0.0

    # Embedding
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_api_base_url: str = ""

    # OCR
    tesseract_languages: str = "hin+eng"
    ocr_confidence_threshold: float = 60.0

    # PII
    pii_masking_enabled: bool = True
    pii_encryption_key: str = Field(default="", description="Fernet key for PII reversible masking")

    # Pipeline
    max_pdf_pages: int = 500
    max_pdf_size_mb: int = 50
    pipeline_version: str = "1.0.0"

    # Features
    self_hosted_mode: bool = False

    # Security
    access_token_expire_minutes: int = 60
    session_timeout_minutes: int = 30


settings = Settings()  # type: ignore[call-arg]
