"""
Tests for Ollama LLM integration.

TDD: These tests define the expected behavior before full integration.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestOllamaLLMInitialization:
    """Test OllamaLLM initialization."""

    def test_create_ollama_llm(self) -> None:
        """Should create an OllamaLLM instance."""
        from calculus_rag.llm.ollama_llm import OllamaLLM

        llm = OllamaLLM(
            model="qwen2.5-math:7b",
            base_url="http://localhost:11434",
        )

        assert llm is not None
        assert llm.model_name == "qwen2.5-math:7b"

    def test_ollama_llm_default_model(self) -> None:
        """Should use default model if not specified."""
        from calculus_rag.llm.ollama_llm import OllamaLLM

        llm = OllamaLLM()
        assert llm.model_name == "qwen2.5-math:7b"

    def test_ollama_llm_custom_timeout(self) -> None:
        """Should accept custom timeout."""
        from calculus_rag.llm.ollama_llm import OllamaLLM

        llm = OllamaLLM(timeout=60)
        assert llm._timeout == 60


class TestOllamaLLMGenerate:
    """Test OllamaLLM text generation."""

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_basic(self, mock_client_class: MagicMock) -> None:
        """Should generate a response for user message."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        # Mock the Ollama client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": "A derivative measures the rate of change."},
            "model": "qwen2.5-math:7b",
            "total_duration": 1000000,
            "eval_count": 10,
        }

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="What is a derivative?")]
        response = llm.generate(messages)

        assert response.content == "A derivative measures the rate of change."
        assert "model" in response.metadata
        assert response.metadata["model"] == "qwen2.5-math:7b"

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_with_system_message(self, mock_client_class: MagicMock) -> None:
        """Should handle system messages."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": "Test response"},
            "model": "qwen2.5-math:7b",
        }

        llm = OllamaLLM()
        messages = [
            LLMMessage(role="system", content="You are a calculus tutor."),
            LLMMessage(role="user", content="Explain limits."),
        ]
        response = llm.generate(messages)

        # Verify client was called with correct messages
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        assert len(call_args.kwargs["messages"]) == 2
        assert call_args.kwargs["messages"][0]["role"] == "system"
        assert call_args.kwargs["messages"][1]["role"] == "user"

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_with_temperature(self, mock_client_class: MagicMock) -> None:
        """Should respect temperature parameter."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": "Test"},
            "model": "qwen2.5-math:7b",
        }

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="Test")]
        llm.generate(messages, temperature=0.2)

        call_args = mock_client.chat.call_args
        assert call_args.kwargs["options"]["temperature"] == 0.2

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_with_max_tokens(self, mock_client_class: MagicMock) -> None:
        """Should respect max_tokens parameter."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {"content": "Test"},
            "model": "qwen2.5-math:7b",
        }

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="Test")]
        llm.generate(messages, max_tokens=100)

        call_args = mock_client.chat.call_args
        assert call_args.kwargs["options"]["num_predict"] == 100

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_handles_errors(self, mock_client_class: MagicMock) -> None:
        """Should handle API errors gracefully."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = Exception("Connection failed")

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(RuntimeError, match="Ollama API call failed"):
            llm.generate(messages)


class TestOllamaLLMStream:
    """Test OllamaLLM streaming generation."""

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_stream_basic(self, mock_client_class: MagicMock) -> None:
        """Should stream response chunks."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock streaming response
        mock_client.chat.return_value = iter(
            [
                {"message": {"content": "A "}},
                {"message": {"content": "derivative "}},
                {"message": {"content": "is..."}},
            ]
        )

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="What is a derivative?")]
        chunks = list(llm.generate_stream(messages))

        assert chunks == ["A ", "derivative ", "is..."]

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_stream_with_options(self, mock_client_class: MagicMock) -> None:
        """Should pass options to streaming call."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = iter([{"message": {"content": "Test"}}])

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="Test")]
        list(llm.generate_stream(messages, temperature=0.1, max_tokens=50))

        call_args = mock_client.chat.call_args
        assert call_args.kwargs["options"]["temperature"] == 0.1
        assert call_args.kwargs["options"]["num_predict"] == 50
        assert call_args.kwargs["stream"] is True

    @patch("calculus_rag.llm.ollama_llm.ollama.Client")
    def test_generate_stream_handles_errors(self, mock_client_class: MagicMock) -> None:
        """Should handle streaming errors gracefully."""
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.side_effect = Exception("Streaming failed")

        llm = OllamaLLM()
        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(RuntimeError, match="Ollama API streaming failed"):
            list(llm.generate_stream(messages))


class TestOllamaLLMIntegration:
    """Integration tests requiring actual Ollama instance."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_real_ollama_connection(self) -> None:
        """
        Test connection to real Ollama instance.

        Note: This test requires Ollama to be running locally.
        Skip if Ollama is not available.
        """
        from calculus_rag.llm.base import LLMMessage
        from calculus_rag.llm.ollama_llm import OllamaLLM

        try:
            llm = OllamaLLM(model="qwen2.5-math:7b")
            messages = [
                LLMMessage(role="user", content="What is 2+2? Answer briefly.")
            ]
            response = llm.generate(messages, temperature=0.1, max_tokens=50)

            # Should get a response
            assert response.content is not None
            assert len(response.content) > 0
            assert "model" in response.metadata

        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
