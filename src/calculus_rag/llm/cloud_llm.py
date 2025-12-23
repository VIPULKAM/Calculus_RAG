"""
Cloud LLM integration for powerful models without local resource usage.

Supports OpenRouter (unified API for DeepSeek, Claude, GPT-4, etc.)
and direct DeepSeek API.
"""

from typing import Iterator

import httpx

from calculus_rag.llm.base import BaseLLM, LLMMessage, LLMResponse


class CloudLLM(BaseLLM):
    """
    Cloud LLM integration using OpenRouter or DeepSeek API.

    This allows routing complex queries to powerful cloud models like:
    - DeepSeek V3 (671B parameters)
    - Claude Sonnet
    - GPT-4

    Without consuming local compute resources.

    Example:
        >>> # Using OpenRouter (recommended - supports many models)
        >>> llm = CloudLLM(
        ...     api_key="your-openrouter-api-key",
        ...     model="deepseek/deepseek-chat",
        ...     provider="openrouter"
        ... )
        >>>
        >>> # Using DeepSeek API directly
        >>> llm = CloudLLM(
        ...     api_key="your-deepseek-api-key",
        ...     model="deepseek-chat",
        ...     provider="deepseek"
        ... )
        >>>
        >>> messages = [LLMMessage(role="user", content="Prove the chain rule")]
        >>> response = llm.generate(messages)
    """

    # Provider API endpoints
    PROVIDER_URLS = {
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        "deepseek": "https://api.deepseek.com/v1/chat/completions",
        "ollama-cloud": "https://cloud.ollama.ai/v1/chat/completions",
    }

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek/deepseek-chat",
        provider: str = "openrouter",
        timeout: int = 180,
        base_url: str | None = None,
    ) -> None:
        """
        Initialize the Cloud LLM.

        Args:
            api_key: API key for the cloud provider.
            model: Model identifier (e.g., "deepseek/deepseek-chat" for OpenRouter,
                   "deepseek-chat" for DeepSeek API).
            provider: Cloud provider ("openrouter" or "deepseek").
            timeout: Request timeout in seconds.
            base_url: Optional custom base URL (overrides provider default).

        Raises:
            ValueError: If provider is not supported.
        """
        if provider not in self.PROVIDER_URLS and base_url is None:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {list(self.PROVIDER_URLS.keys())}"
            )

        self._api_key = api_key
        self._model = model
        self._provider = provider
        self._timeout = timeout
        self._base_url = base_url or self.PROVIDER_URLS.get(provider)

        # Create HTTP client
        self._client = httpx.Client(timeout=timeout)

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return f"Cloud-{self._model}"

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for API request."""
        headers = {
            "Content-Type": "application/json",
        }

        if self._provider == "openrouter":
            headers["Authorization"] = f"Bearer {self._api_key}"
            headers["HTTP-Referer"] = "https://github.com/calculus-rag"
            headers["X-Title"] = "Calculus RAG"
        elif self._provider == "deepseek":
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._provider == "ollama-cloud":
            # Ollama Cloud uses Bearer token authentication
            headers["Authorization"] = f"Bearer {self._api_key}"

        return headers

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate a response using the cloud model.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0-1, lower = more deterministic).
            max_tokens: Maximum tokens to generate (None for model default).

        Returns:
            LLMResponse: The generated response with metadata.

        Raises:
            RuntimeError: If the API call fails.
        """
        # Convert messages to OpenAI format (used by both providers)
        api_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Build request payload
        payload = {
            "model": self._model,
            "messages": api_messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            # Call API
            response = self._client.post(
                self._base_url,
                json=payload,
                headers=self._build_headers(),
            )
            response.raise_for_status()

            # Parse response
            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                raise RuntimeError(f"Invalid API response: {data}")

            content = data["choices"][0]["message"]["content"]

            # Extract metadata
            metadata = {
                "model": data.get("model", self._model),
                "provider": self._provider,
                "usage": data.get("usage", {}),
                "finish_reason": data["choices"][0].get("finish_reason"),
            }

            return LLMResponse(content=content, metadata=metadata)

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise RuntimeError(
                f"Cloud API call failed (HTTP {e.response.status_code}): {error_detail}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Cloud API call failed: {e}") from e

    def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Generate a streaming response using the cloud model.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0-1, lower = more deterministic).
            max_tokens: Maximum tokens to generate (None for model default).

        Yields:
            str: Chunks of the generated response.

        Raises:
            RuntimeError: If the API call fails.
        """
        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Build request payload with streaming
        payload = {
            "model": self._model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            # Stream response
            with self._client.stream(
                "POST",
                self._base_url,
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            import json
                            data = json.loads(data_str)

                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise RuntimeError(
                f"Cloud API streaming failed (HTTP {e.response.status_code}): {error_detail}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Cloud API streaming failed: {e}") from e

    def __repr__(self) -> str:
        return f"CloudLLM(model={self._model}, provider={self._provider})"
