"""
Ollama LLM integration.

Provides integration with Ollama for running local LLMs like Qwen 2.5-Math.
Supports both local models and cloud models with API key authentication.
"""

from typing import Iterator

import httpx
import ollama

from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse


class OllamaLLM(BaseLLM):
    """
    LLM integration using Ollama.

    Ollama provides a simple API for running local LLMs. This implementation
    is optimized for mathematical reasoning with models like Qwen 2.5-Math.
    Also supports cloud models with API key authentication.

    Example:
        >>> # Local model
        >>> llm = OllamaLLM(
        ...     model="qwen2.5-math:7b",
        ...     base_url="http://localhost:11434"
        ... )
        >>> # Cloud model with API key
        >>> llm = OllamaLLM(
        ...     model="deepseek-v3.1:671b-cloud",
        ...     base_url="http://localhost:11434",
        ...     api_key="your-api-key"
        ... )
        >>> messages = [LLMMessage(role="user", content="What is a derivative?")]
        >>> response = llm.generate(messages)
        >>> print(response.content)
    """

    def __init__(
        self,
        model: str = "qwen2.5-math:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        api_key: str | None = None,
    ) -> None:
        """
        Initialize the Ollama LLM.

        Args:
            model: The model name to use (e.g., "qwen2.5-math:7b").
            base_url: The base URL for the Ollama API.
            timeout: Request timeout in seconds.
            api_key: Optional API key for cloud models.
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._api_key = api_key

        # Use httpx for authenticated requests, ollama client for local
        if api_key:
            self._use_httpx = True
            self._http_client = httpx.Client(timeout=timeout)
        else:
            self._use_httpx = False
            self._client = ollama.Client(host=base_url, timeout=timeout)

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model

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
            temperature: Sampling temperature (0-1, lower = more deterministic).
            max_tokens: Maximum tokens to generate (None for model default).

        Returns:
            LLMResponse: The generated response with metadata.

        Raises:
            RuntimeError: If the Ollama API call fails.
        """
        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Build options
        options = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        try:
            if self._use_httpx:
                # Use httpx for authenticated cloud requests
                response = self._http_client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": ollama_messages,
                        "options": options,
                        "stream": False,
                    },
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data["message"]["content"]
                metadata = {
                    "model": data.get("model", self._model),
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                }
            else:
                # Use ollama client for local requests
                response = self._client.chat(
                    model=self._model,
                    messages=ollama_messages,
                    options=options,
                )

                content = response["message"]["content"]
                metadata = {
                    "model": response.get("model", self._model),
                    "total_duration": response.get("total_duration"),
                    "load_duration": response.get("load_duration"),
                    "prompt_eval_count": response.get("prompt_eval_count"),
                    "eval_count": response.get("eval_count"),
                }

            return LLMResponse(content=content, metadata=metadata)

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API call failed: {e.response.text}") from e
        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {e}") from e

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
            temperature: Sampling temperature (0-1, lower = more deterministic).
            max_tokens: Maximum tokens to generate (None for model default).

        Yields:
            str: Chunks of the generated response.

        Raises:
            RuntimeError: If the Ollama API call fails.
        """
        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Build options
        options = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        try:
            # Stream response from Ollama
            stream = self._client.chat(
                model=self._model,
                messages=ollama_messages,
                options=options,
                stream=True,
            )

            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            raise RuntimeError(f"Ollama API streaming failed: {e}") from e

    def __repr__(self) -> str:
        return f"OllamaLLM(model={self._model}, base_url={self._base_url})"
