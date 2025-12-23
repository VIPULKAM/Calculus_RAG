"""
Base abstract class for LLM integrations.

All LLM implementations should inherit from BaseLLM.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, Literal

from pydantic import BaseModel, field_validator


class LLMMessage(BaseModel):
    """
    Represents a message in the LLM conversation.

    Attributes:
        role: The role of the message sender (system, user, or assistant).
        content: The text content of the message.
    """

    role: Literal["system", "user", "assistant"]
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is one of the allowed values."""
        allowed = {"system", "user", "assistant"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}, got '{v}'")
        return v


@dataclass
class LLMResponse:
    """
    Represents a response from the LLM.

    Attributes:
        content: The generated text content.
        metadata: Optional metadata (tokens used, model info, etc.).
    """

    content: str
    metadata: dict = field(default_factory=dict)


class BaseLLM(ABC):
    """
    Abstract base class for LLM integrations.

    Provides a consistent interface for different LLM backends
    (e.g., Ollama, OpenAI-compatible APIs, local models).
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Return the name of the model being used.

        Returns:
            str: The model identifier.
        """
        ...

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate a response for the given messages.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse: The generated response.
        """
        ...

    @abstractmethod
    def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Generate a streaming response for the given messages.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens to generate.

        Yields:
            str: Chunks of the generated response.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"
