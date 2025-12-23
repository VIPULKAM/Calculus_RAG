"""
Tests for the base LLM interface.

TDD: These tests define the expected interface before implementation.
"""

from abc import ABC
from typing import Iterator

import pytest


class TestBaseLLMInterface:
    """Test the abstract base LLM interface."""

    def test_base_llm_is_abstract(self) -> None:
        """BaseLLM should be an abstract class."""
        from calculus_rag.llm.base import BaseLLM

        assert issubclass(BaseLLM, ABC)

    def test_base_llm_cannot_be_instantiated(self) -> None:
        """BaseLLM should not be directly instantiable."""
        from calculus_rag.llm.base import BaseLLM

        with pytest.raises(TypeError):
            BaseLLM()  # type: ignore

    def test_base_llm_has_generate_method(self) -> None:
        """BaseLLM should define a generate method."""
        from calculus_rag.llm.base import BaseLLM

        assert hasattr(BaseLLM, "generate")
        assert callable(getattr(BaseLLM, "generate", None))

    def test_base_llm_has_generate_stream_method(self) -> None:
        """BaseLLM should define a generate_stream method."""
        from calculus_rag.llm.base import BaseLLM

        assert hasattr(BaseLLM, "generate_stream")
        assert callable(getattr(BaseLLM, "generate_stream", None))

    def test_base_llm_has_model_name_property(self) -> None:
        """BaseLLM should define a model_name property."""
        from calculus_rag.llm.base import BaseLLM

        assert hasattr(BaseLLM, "model_name")


class TestLLMMessage:
    """Test the LLMMessage data model."""

    def test_message_has_role_and_content(self) -> None:
        """LLMMessage should have role and content fields."""
        from calculus_rag.llm.base import LLMMessage

        msg = LLMMessage(role="user", content="What is a derivative?")

        assert msg.role == "user"
        assert msg.content == "What is a derivative?"

    def test_message_role_validation(self) -> None:
        """LLMMessage role should be one of system, user, assistant."""
        from calculus_rag.llm.base import LLMMessage

        # Valid roles
        LLMMessage(role="system", content="You are a tutor.")
        LLMMessage(role="user", content="Help me.")
        LLMMessage(role="assistant", content="Sure!")

        # Invalid role
        with pytest.raises(ValueError):
            LLMMessage(role="invalid", content="test")


class TestLLMResponse:
    """Test the LLMResponse data model."""

    def test_response_has_content(self) -> None:
        """LLMResponse should have content field."""
        from calculus_rag.llm.base import LLMResponse

        response = LLMResponse(content="The derivative is...")

        assert response.content == "The derivative is..."

    def test_response_has_optional_metadata(self) -> None:
        """LLMResponse should support optional metadata."""
        from calculus_rag.llm.base import LLMResponse

        response = LLMResponse(
            content="Answer",
            metadata={
                "tokens_used": 100,
                "model": "qwen2.5-math:7b",
            },
        )

        assert response.metadata["tokens_used"] == 100


class TestConcreteLLMImplementation:
    """Test that concrete implementations work correctly."""

    def test_concrete_llm_can_be_created(self) -> None:
        """A concrete LLM implementation should be instantiable."""
        from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse

        class MockLLM(BaseLLM):
            @property
            def model_name(self) -> str:
                return "mock-model"

            def generate(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> LLMResponse:
                return LLMResponse(content="Mock response")

            def generate_stream(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> Iterator[str]:
                yield "Mock "
                yield "response"

        llm = MockLLM()
        assert llm.model_name == "mock-model"

    def test_generate_returns_response(self) -> None:
        """generate() should return an LLMResponse."""
        from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse

        class MockLLM(BaseLLM):
            @property
            def model_name(self) -> str:
                return "mock-model"

            def generate(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> LLMResponse:
                return LLMResponse(content="The derivative of x^2 is 2x.")

            def generate_stream(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> Iterator[str]:
                yield "Test"

        llm = MockLLM()
        messages = [LLMMessage(role="user", content="What is the derivative of x^2?")]
        response = llm.generate(messages)

        assert isinstance(response, LLMResponse)
        assert "2x" in response.content

    def test_generate_stream_yields_strings(self) -> None:
        """generate_stream() should yield string chunks."""
        from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse

        class MockLLM(BaseLLM):
            @property
            def model_name(self) -> str:
                return "mock-model"

            def generate(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> LLMResponse:
                return LLMResponse(content="Test")

            def generate_stream(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> Iterator[str]:
                yield "The "
                yield "answer "
                yield "is..."

        llm = MockLLM()
        messages = [LLMMessage(role="user", content="Test")]
        chunks = list(llm.generate_stream(messages))

        assert chunks == ["The ", "answer ", "is..."]
        assert "".join(chunks) == "The answer is..."
