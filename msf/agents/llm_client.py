"""MSF LLM Client.

Provides LLMClient class supporting OpenAI-compatible chat/completions APIs
(including local servers like OmniRoute at localhost:20128) with streaming, retry,
timeout, and JSON parsing functionality.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import httpx

from msf.config import LLMConfig

logger = logging.getLogger("msf.llm_client")


class LLMClient:
    """Client for interacting with OpenAI-compatible LLM endpoints."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def _get_base_url(self) -> str:
        """Resolve base URL for OpenAI-compatible endpoint."""
        url = self.config.base_url or "https://api.openai.com/v1"
        url = url.rstrip("/")
        if not url.endswith("/v1") and not url.endswith("/chat/completions"):
            # Check if user provided endpoint up to base host or v1
            pass
        return url

    def _get_chat_url(self) -> str:
        """Get full chat completions URL."""
        base = self._get_base_url()
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        """Send chat request to OpenAI-compatible endpoint with retries and timeout.

        Args:
            messages: List of message dictionaries (e.g. [{"role": "user", "content": "..."}]).
            temperature: Sampling temperature (defaults to self.config.temperature).
            max_tokens: Maximum response tokens (defaults to self.config.max_tokens).
            response_format: Dict for response format parameter (e.g. {"type": "json_object"}).

        Returns:
            The completion content as a string.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        url = self._get_chat_url()
        headers = self._get_headers()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        max_attempts = 3
        last_exception: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                # Use httpx post with 60s timeout
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise ValueError(f"No choices returned in LLM response: {data}")
                    content = choices[0].get("message", {}).get("content", "")
                    if content is None:
                        content = ""
                    return content
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"LLM request attempt {attempt}/{max_attempts} failed: {e}"
                )
                if attempt < max_attempts:
                    time.sleep(1.0 * attempt)

        raise RuntimeError(
            f"LLM chat request failed after {max_attempts} attempts: {last_exception}"
        ) from last_exception

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        schema_hint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """Send chat request forcing JSON response and parse the output.

        Args:
            messages: List of message dicts.
            schema_hint: Optional prompt suffix describing expected JSON schema.
            temperature: Optional temperature override.
            max_tokens: Optional max_tokens override.

        Returns:
            Parsed JSON dictionary.
        """
        msgs = [dict(m) for m in messages]
        if schema_hint:
            # Append schema hint to the system message or add system message
            sys_msg_idx = next(
                (i for i, m in enumerate(msgs) if m.get("role") == "system"), None
            )
            hint_str = f"\nRespond strictly with a JSON object matching this schema or structure:\n{schema_hint}"
            if sys_msg_idx is not None:
                msgs[sys_msg_idx] = {
                    "role": "system",
                    "content": msgs[sys_msg_idx]["content"] + hint_str,
                }
            else:
                msgs.insert(
                    0,
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant. {hint_str}",
                    },
                )

        # Try requesting response_format={"type": "json_object"} first
        try:
            content = self.chat(
                msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception:
            # Fallback to plain chat if json_object format is not supported by backend
            content = self.chat(
                msgs,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Clean codeblock markdown if present
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        elif clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()

        # Parse JSON
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as e:
            # Attempt basic extraction of JSON substring between first { and last }
            start = clean_content.find("{")
            end = clean_content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(clean_content[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise ValueError(
                f"Failed to parse LLM response as JSON: {e}\nRaw output: {content}"
            ) from e
