"""LM Studio provider — OpenAI-compatible HTTP client for local LM Studio API."""

from typing import Any, Dict, Optional
import requests

from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import LLMConfig
from application.shared.exceptions.app_exceptions import LLMInferenceError


class LMStudioProvider:
    """HTTP client for local LM Studio OpenAI-compatible API."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("lmstudio_provider")

    def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Send a prompt to LM Studio (v1/chat/completions) and return the response text.

        Raises LLMInferenceError on failure.
        """
        temp = self._config.temperature
        if options:
            temp = options.get("temperature", temp)

        url = self._config.lmstudio_url.rstrip("/")
        if not url.endswith("/v1/chat/completions"):
            if url.endswith("/v1"):
                url += "/chat/completions"
            else:
                url += "/v1/chat/completions"

        payload = {
            "model": self._config.lmstudio_model or "local-model",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temp,
        }

        try:
            response = requests.post(
                url, json=payload,
                timeout=self._config.request_timeout,
            )
            response.raise_for_status()
            result = response.json()
            choices = result.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("content", "").strip()
            return ""

        except requests.exceptions.ConnectionError as e:
            self._logger.error(f"Cannot connect to LM Studio at {url}: {e}")
            raise LLMInferenceError(f"LM Studio connection failed: {e}")
        except requests.exceptions.Timeout as e:
            self._logger.error(f"LM Studio request timed out: {e}")
            raise LLMInferenceError(f"LM Studio timeout: {e}")
        except Exception as e:
            self._logger.error(f"LM Studio error: {e}")
            raise LLMInferenceError(f"LM Studio error: {e}")

    def health_check(self) -> bool:
        """Check if LM Studio API server is running."""
        try:
            base_url = self._config.lmstudio_url.split("/v1")[0]
            resp = requests.get(f"{base_url}/v1/models", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False
