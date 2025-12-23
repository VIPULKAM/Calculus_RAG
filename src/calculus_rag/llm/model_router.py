"""
Intelligent model routing based on question complexity.

Routes simple questions to fast local models and complex questions to
more powerful models (cloud or larger local models).
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterator

from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse


class ComplexityLevel(Enum):
    """Question complexity levels."""

    SIMPLE = 1  # Basic definitions, simple calculations
    MODERATE = 2  # Standard problems, multi-step solutions
    COMPLEX = 3  # Advanced problems, proofs, complex reasoning


@dataclass
class ModelConfig:
    """Configuration for a model in the routing system."""

    llm: BaseLLM
    name: str
    max_complexity: ComplexityLevel
    is_fallback: bool = False


class ComplexityAnalyzer:
    """
    Analyzes question complexity using heuristics.

    This is a simple rule-based system. Can be enhanced with ML later.
    """

    # Keywords that suggest complexity
    COMPLEX_KEYWORDS = [
        "prove",
        "proof",
        "derive",
        "derivation",
        "why does",
        "explain why",
        "rigorous",
        "justify",
        "show that",
        "demonstrate",
        "integration by parts",
        "u-substitution",
        "chain rule",
        "implicit differentiation",
        "related rates",
        "optimization",
        "taylor series",
        "fourier",
    ]

    # Keywords that suggest simplicity
    SIMPLE_KEYWORDS = [
        "what is",
        "define",
        "definition",
        "basic",
        "simple",
        "calculate",
        "find the derivative of",
        "power rule",
        "constant rule",
    ]

    def analyze(self, question: str) -> ComplexityLevel:
        """
        Analyze question complexity.

        Args:
            question: The question to analyze.

        Returns:
            ComplexityLevel: Estimated complexity level.
        """
        question_lower = question.lower()

        # Check for complex indicators
        complex_score = 0
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in question_lower:
                complex_score += 2

        # Check for simple indicators
        simple_score = 0
        for keyword in self.SIMPLE_KEYWORDS:
            if keyword in question_lower:
                simple_score += 2

        # Check question length (longer = potentially more complex)
        word_count = len(question.split())
        if word_count > 30:
            complex_score += 1
        elif word_count < 10:
            simple_score += 1

        # Check for mathematical expressions (more = more complex)
        math_symbols = len(re.findall(r'[∫∑∏√±∞αβγθλπ]|\\frac|\\int|\\sum', question))
        if math_symbols > 3:
            complex_score += 2
        elif math_symbols > 1:
            complex_score += 1

        # Make decision
        if complex_score >= 3:
            return ComplexityLevel.COMPLEX
        elif simple_score >= 3 or (simple_score > complex_score):
            return ComplexityLevel.SIMPLE
        else:
            return ComplexityLevel.MODERATE


class ModelRouter(BaseLLM):
    """
    Routes questions to appropriate models based on complexity.

    Starts with the simplest/fastest model and falls back to more
    powerful models if needed.

    Example:
        >>> small_llm = OllamaLLM(model="qwen2-math:1.5b")
        >>> large_llm = OllamaLLM(model="deepseek-v3.1:671b-cloud")
        >>>
        >>> router = ModelRouter()
        >>> router.add_model(small_llm, "Small", ComplexityLevel.MODERATE)
        >>> router.add_model(large_llm, "Large", ComplexityLevel.COMPLEX, is_fallback=True)
        >>>
        >>> # Simple questions use small model, complex use large
        >>> response = router.generate(messages)
    """

    def __init__(self, enable_fallback: bool = True):
        """
        Initialize the model router.

        Args:
            enable_fallback: Whether to fall back to larger models on errors.
        """
        self.models: list[ModelConfig] = []
        self.complexity_analyzer = ComplexityAnalyzer()
        self.enable_fallback = enable_fallback
        self._last_model_used: str | None = None

    def add_model(
        self,
        llm: BaseLLM,
        name: str,
        max_complexity: ComplexityLevel,
        is_fallback: bool = False,
    ) -> None:
        """
        Add a model to the routing system.

        Args:
            llm: The LLM instance.
            name: Human-readable name for the model.
            max_complexity: Maximum complexity this model can handle.
            is_fallback: Whether this model is used as fallback.
        """
        config = ModelConfig(
            llm=llm,
            name=name,
            max_complexity=max_complexity,
            is_fallback=is_fallback,
        )
        self.models.append(config)

        # Sort by complexity (simple models first)
        self.models.sort(key=lambda m: m.max_complexity.value)

    @property
    def model_name(self) -> str:
        """Return the name of the last used model."""
        if self._last_model_used:
            return f"Router(last_used={self._last_model_used})"
        return "Router(no_models)"

    @property
    def last_model_used(self) -> str | None:
        """Return the name of the last model that was used."""
        return self._last_model_used

    def _extract_question(self, messages: list[LLMMessage]) -> str:
        """Extract the main question from messages."""
        # Get the last user message as the question
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content
        return ""

    def _select_model(self, question: str) -> ModelConfig:
        """
        Select appropriate model based on question complexity.

        Args:
            question: The question to analyze.

        Returns:
            ModelConfig: The selected model configuration.

        Raises:
            ValueError: If no models are configured.
        """
        if not self.models:
            raise ValueError("No models configured in router")

        # Analyze complexity
        complexity = self.complexity_analyzer.analyze(question)

        # Find the smallest model that can handle this complexity
        for model_config in self.models:
            if model_config.max_complexity.value >= complexity.value:
                if not model_config.is_fallback:
                    return model_config

        # If no suitable model found, use the most powerful one
        return self.models[-1]

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate response using appropriate model.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse: The generated response.

        Raises:
            RuntimeError: If all models fail.
        """
        # Extract question for complexity analysis
        question = self._extract_question(messages)

        # Select primary model
        primary_model = self._select_model(question)
        self._last_model_used = primary_model.name

        # Try primary model
        try:
            response = primary_model.llm.generate(messages, temperature, max_tokens)
            # Add routing info to metadata
            response.metadata["router_model"] = primary_model.name
            response.metadata["router_complexity"] = self.complexity_analyzer.analyze(
                question
            ).name
            return response

        except Exception as primary_error:
            # If fallback is disabled, raise immediately
            if not self.enable_fallback:
                raise RuntimeError(
                    f"Primary model '{primary_model.name}' failed: {primary_error}"
                ) from primary_error

            # Try fallback models
            fallback_models = [m for m in self.models if m.is_fallback]

            for fallback_model in fallback_models:
                try:
                    self._last_model_used = f"{primary_model.name}→{fallback_model.name}"
                    response = fallback_model.llm.generate(
                        messages, temperature, max_tokens
                    )
                    response.metadata["router_model"] = fallback_model.name
                    response.metadata["router_fallback_from"] = primary_model.name
                    response.metadata["router_primary_error"] = str(primary_error)
                    return response

                except Exception as fallback_error:
                    continue  # Try next fallback

            # All models failed
            raise RuntimeError(
                f"All models failed. Primary: {primary_error}"
            ) from primary_error

    def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Generate streaming response using appropriate model.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            str: Chunks of generated text.

        Raises:
            RuntimeError: If all models fail.
        """
        # Extract question for complexity analysis
        question = self._extract_question(messages)

        # Select model
        model_config = self._select_model(question)
        self._last_model_used = model_config.name

        # Stream from selected model
        try:
            yield from model_config.llm.generate_stream(
                messages, temperature, max_tokens
            )
        except Exception as e:
            # Note: Fallback for streaming is tricky - would need to buffer
            # For now, just raise
            raise RuntimeError(
                f"Model '{model_config.name}' streaming failed: {e}"
            ) from e

    def __repr__(self) -> str:
        model_names = [m.name for m in self.models]
        return f"ModelRouter(models={model_names})"
