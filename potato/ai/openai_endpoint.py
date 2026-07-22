"""
OpenAI AI endpoint implementation.

This module provides integration with OpenAI's API for LLM inference.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

from .ai_endpoint import BaseAIEndpoint, AIEndpointRequestError, ModelCapabilities

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class OfficialOpenAI:
    """The OpenAI-hosted Chat Completions API."""


@dataclass(frozen=True)
class CompatibleOpenAI:
    """An OpenAI-compatible server with its own request compatibility."""

    base_url: str


OpenAITarget = Union[OfficialOpenAI, CompatibleOpenAI]


def build_chat_completion_request(
    target: OpenAITarget,
    model: str,
    messages: List[Dict[str, str]],
    max_output_tokens: int,
    temperature: float,
    response_format: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Serialize a provider-neutral output limit for the selected target."""
    request = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if isinstance(target, OfficialOpenAI):
        request["max_completion_tokens"] = max_output_tokens
    else:
        request["max_tokens"] = max_output_tokens
    if response_format is not None:
        request["response_format"] = response_format
    return request


class OpenAIEndpoint(BaseAIEndpoint):
    """OpenAI endpoint for cloud-based LLM inference."""

    # Capabilities declaration for text-based OpenAI models
    CAPABILITIES = ModelCapabilities(
        text_generation=True,
        vision_input=False,
        bounding_box_output=False,
        text_classification=True,
        image_classification=False,
        rationale_generation=True,
        keyword_extraction=True,
    )

    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        # OpenAI-compatible servers (vLLM, llama.cpp, etc.) ignore the key
        # but the SDK rejects an empty string, so accept a placeholder.
        api_key = self.ai_config.get("api_key") or os.environ.get(
            "OPENAI_API_KEY", ""
        )
        base_url = self.ai_config.get("base_url")
        self.target: OpenAITarget = (
            CompatibleOpenAI(base_url) if base_url else OfficialOpenAI()
        )
        if not api_key:
            if base_url:
                api_key = "EMPTY"  # non-empty placeholder for local servers
            else:
                raise AIEndpointRequestError("OpenAI API key is required")

        # Default timeout of 30 seconds, configurable via ai_config
        timeout = self.ai_config.get("timeout", 30)
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        # Honor a custom base_url so this endpoint can target any
        # OpenAI-compatible server (previously ignored -> always hit
        # api.openai.com even when a local base_url was configured).
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    def _get_default_model(self) -> str:
        """Get the default OpenAI model."""
        return DEFAULT_MODEL

    def query(self, prompt: str, output_format: dict) -> str:
        """
        Send a query to OpenAI and return the response.

        Args:
            prompt: The prompt to send to the model

        Returns:
            The model's response as a string

        Raises:
            AIEndpointRequestError: If the request fails
        """
        try:
            # Free-text when no schema is requested (e.g. the model arena);
            # structured JSON output only when an output_format is supplied.
            response_format = None
            if output_format is not None and hasattr(output_format, "model_json_schema"):
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": getattr(output_format, "__name__", "output"),
                        "schema": output_format.model_json_schema(),
                    },
                }
            kwargs = build_chat_completion_request(
                target=self.target,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format=response_format,
            )
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise AIEndpointRequestError(f"OpenAI request failed: {e}")

    def chat_query(self, messages: List[Dict[str, str]]) -> str:
        """Send a multi-turn chat to OpenAI using native messages API."""
        try:
            kwargs = build_chat_completion_request(
                target=self.target,
                model=self.model,
                messages=messages,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise AIEndpointRequestError(f"OpenAI chat request failed: {e}")
