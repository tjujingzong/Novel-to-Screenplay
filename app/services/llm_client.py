"""Async LLM client for DeepSeek API (OpenAI-compatible)."""

import asyncio
import json
import logging
from typing import Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class DeepSeekClient:
    """Async wrapper around the DeepSeek API with retry and structured output."""

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.llm_timeout,
        )
        self._model = settings.deepseek_model
        self._max_output_tokens = settings.max_output_tokens
        self._temperature = settings.llm_temperature

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T] | None = None,
        temperature: float | None = None,
        max_retries: int = 3,
    ) -> str | T:
        """Send a chat completion request to DeepSeek.

        Args:
            system_prompt: The system message establishing the LLM's role.
            user_prompt: The user message with the task.
            response_model: If provided, parse the response as this Pydantic model.
            temperature: Override the default temperature.
            max_retries: Number of retries on transient errors.

        Returns:
            Raw text response, or a parsed Pydantic model if response_model is given.
        """
        temp = temperature if temperature is not None else self._temperature
        use_json = response_model is not None

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": self._max_output_tokens,
        }
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""

                if use_json:
                    return self._parse_json_response(content, response_model)
                return content

            except Exception as e:
                last_error = e
                logger.warning("LLM call attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")

    def _parse_json_response(self, content: str, model: Type[T]) -> T:
        """Parse a JSON string response into a Pydantic model."""
        # Strip markdown code fences if present
        text = content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [line for line in lines if not line.startswith("```")]
            text = "\n".join(lines)

        data = json.loads(text)
        return model.model_validate(data)

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.close()
