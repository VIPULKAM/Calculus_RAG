"""
Configuration management for Calculus RAG.

Uses pydantic-settings for environment variable loading and validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # General Settings
    # ==========================================================================

    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Application environment",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # ==========================================================================
    # Embedding Settings
    # ==========================================================================

    embedding_model_name: str = Field(
        default="BAAI/bge-base-en-v1.5",
        description="Embedding model name (BGE or Ollama model)",
    )

    embedding_device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Device to run embedding model on",
    )

    embedding_type: Literal["sentence-transformers", "ollama"] = Field(
        default="sentence-transformers",
        description="Type of embedder to use (sentence-transformers for BGE, ollama for mxbai)",
    )

    # ==========================================================================
    # Vector Store Settings (PostgreSQL + pgvector)
    # ==========================================================================

    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host",
    )

    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
        gt=0,
        lt=65536,
    )

    postgres_db: str = Field(
        default="calculus_rag",
        description="PostgreSQL database name",
    )

    postgres_user: str = Field(
        default="postgres",
        description="PostgreSQL username",
    )

    postgres_password: str = Field(
        default="postgres",
        description="PostgreSQL password",
    )

    vector_dimension: int = Field(
        default=768,
        description="Vector embedding dimension (must match embedding model)",
        ge=128,
        le=2048,
    )

    # ==========================================================================
    # LLM Settings (Ollama)
    # ==========================================================================

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API",
    )

    ollama_model: str = Field(
        default="qwen2.5-math:7b",
        description="Ollama model to use for generation",
    )

    ollama_request_timeout: int = Field(
        default=120,
        description="Request timeout in seconds for Ollama",
        gt=0,
    )

    ollama_api_key: str | None = Field(
        default=None,
        description="API key for Ollama cloud models (optional)",
    )

    # ==========================================================================
    # Cloud LLM Settings (for complex queries)
    # ==========================================================================

    cloud_llm_enabled: bool = Field(
        default=False,
        description="Enable cloud LLM for complex queries (avoids local 7B)",
    )

    cloud_llm_provider: Literal["openrouter", "deepseek", "ollama-cloud"] = Field(
        default="openrouter",
        description="Cloud LLM provider (openrouter, deepseek, or ollama-cloud)",
    )

    cloud_llm_api_key: str = Field(
        default="",
        description="API key for cloud LLM provider",
    )

    cloud_llm_model: str = Field(
        default="deepseek/deepseek-chat",
        description="Cloud model to use (e.g., deepseek/deepseek-chat for OpenRouter)",
    )

    cloud_llm_timeout: int = Field(
        default=180,
        description="Request timeout for cloud LLM (in seconds)",
        gt=0,
    )

    # ==========================================================================
    # Knowledge Base Settings
    # ==========================================================================

    knowledge_base_path: Path = Field(
        default=Path("./knowledge_content"),
        description="Path to knowledge base content",
    )

    chunk_size: int = Field(
        default=512,
        description="Size of text chunks for embedding",
        gt=0,
    )

    chunk_overlap: int = Field(
        default=50,
        description="Overlap between consecutive chunks",
        ge=0,
    )

    # ==========================================================================
    # Connection Settings
    # ==========================================================================

    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_async_dsn(self) -> str:
        """Build async PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ==========================================================================
    # API Settings
    # ==========================================================================

    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind API server",
    )

    api_port: int = Field(
        default=8000,
        description="Port for API server",
        gt=0,
        lt=65536,
    )

    # ==========================================================================
    # Validators
    # ==========================================================================

    @field_validator("knowledge_base_path", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        """Ensure chunk overlap is less than chunk size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure we only load settings once.

    Returns:
        Settings: Application settings
    """
    return Settings()
