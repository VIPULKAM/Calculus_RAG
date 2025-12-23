"""
Tests for the configuration module.

TDD: These tests are written FIRST, before the implementation.
"""

import os
from pathlib import Path

import pytest


class TestSettings:
    """Test the Settings configuration class."""

    def test_settings_loads_defaults(self) -> None:
        """Settings should have sensible defaults when no env vars are set."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert settings.environment == "development"
        assert settings.log_level == "INFO"

    def test_settings_loads_from_env(self, test_env_vars: dict[str, str]) -> None:
        """Settings should load values from environment variables."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert settings.environment == "testing"
        assert settings.embedding_model_name == "BAAI/bge-base-en-v1.5"
        assert settings.embedding_device == "cpu"
        assert settings.ollama_model == "qwen2.5-math:7b"
        assert settings.log_level == "DEBUG"

    def test_settings_postgres_connection_string(
        self, test_env_vars: dict[str, str]
    ) -> None:
        """Should build PostgreSQL connection string."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert "postgresql://" in settings.postgres_dsn
        assert settings.postgres_host in settings.postgres_dsn

    def test_settings_knowledge_base_path_is_path(
        self, test_env_vars: dict[str, str]
    ) -> None:
        """Knowledge base path should be converted to Path."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert isinstance(settings.knowledge_base_path, Path)

    def test_settings_validates_environment(self) -> None:
        """Settings should only accept valid environment values."""
        from calculus_rag.config import Settings

        os.environ["ENVIRONMENT"] = "invalid_env"

        with pytest.raises(ValueError):
            Settings()

        # Clean up
        os.environ.pop("ENVIRONMENT", None)

    def test_settings_validates_log_level(self) -> None:
        """Settings should only accept valid log levels."""
        from calculus_rag.config import Settings

        os.environ["LOG_LEVEL"] = "INVALID"

        with pytest.raises(ValueError):
            Settings()

        # Clean up
        os.environ.pop("LOG_LEVEL", None)

    def test_settings_chunk_size_positive(self) -> None:
        """Chunk size must be a positive integer."""
        from calculus_rag.config import Settings

        os.environ["CHUNK_SIZE"] = "-100"

        with pytest.raises(ValueError):
            Settings()

        os.environ.pop("CHUNK_SIZE", None)

    def test_settings_chunk_overlap_less_than_size(self) -> None:
        """Chunk overlap must be less than chunk size."""
        from calculus_rag.config import Settings

        os.environ["CHUNK_SIZE"] = "100"
        os.environ["CHUNK_OVERLAP"] = "150"

        with pytest.raises(ValueError):
            Settings()

        os.environ.pop("CHUNK_SIZE", None)
        os.environ.pop("CHUNK_OVERLAP", None)


class TestGetSettings:
    """Test the get_settings singleton function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """get_settings should return a Settings instance."""
        from calculus_rag.config import Settings, get_settings

        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings should return the same cached instance."""
        from calculus_rag.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


class TestEmbeddingSettings:
    """Test embedding-specific settings."""

    def test_embedding_settings_defaults(self) -> None:
        """Embedding settings should have proper defaults."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert settings.embedding_model_name == "BAAI/bge-base-en-v1.5"
        assert settings.embedding_device in ("cpu", "cuda", "mps")

    def test_embedding_device_validation(self) -> None:
        """Embedding device should be validated."""
        from calculus_rag.config import Settings

        os.environ["EMBEDDING_DEVICE"] = "invalid_device"

        with pytest.raises(ValueError):
            Settings()

        os.environ.pop("EMBEDDING_DEVICE", None)


class TestLLMSettings:
    """Test LLM-specific settings."""

    def test_llm_settings_defaults(self) -> None:
        """LLM settings should have proper defaults."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_request_timeout == 120

    def test_ollama_timeout_positive(self) -> None:
        """Ollama timeout must be positive."""
        from calculus_rag.config import Settings

        os.environ["OLLAMA_REQUEST_TIMEOUT"] = "0"

        with pytest.raises(ValueError):
            Settings()

        os.environ.pop("OLLAMA_REQUEST_TIMEOUT", None)


class TestAPISettings:
    """Test API-specific settings."""

    def test_api_settings_defaults(self) -> None:
        """API settings should have proper defaults."""
        from calculus_rag.config import Settings

        settings = Settings()

        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_api_port_valid_range(self) -> None:
        """API port must be in valid range."""
        from calculus_rag.config import Settings

        os.environ["API_PORT"] = "99999"

        with pytest.raises(ValueError):
            Settings()

        os.environ.pop("API_PORT", None)
