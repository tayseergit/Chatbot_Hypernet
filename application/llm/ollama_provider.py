"""Ollama provider — HTTP client for local Ollama LLM API."""

from typing import Any, Dict, Optional
import requests

from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import LLMConfig
from application.shared.exceptions.app_exceptions import LLMInferenceError


class OllamaProvider:
    """HTTP client for Ollama local LLM API."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("ollama_provider")

    def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Send a prompt to Ollama and return the response text.

        Raises LLMInferenceError on failure.
        """
        opts = {
            "temperature": self._config.temperature,
            "top_p": self._config.top_p,
            "top_k": self._config.top_k,
            "num_ctx": self._config.num_ctx,
        }
        if options:
            opts.update(options)

        payload = {
            "model": self._config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": opts,
        }

        try:
            response = requests.post(
                self._config.ollama_url, json=payload,
                timeout=self._config.request_timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

        except requests.exceptions.ConnectionError as e:
            self._logger.error(f"Cannot connect to Ollama: {e}")
            raise LLMInferenceError(f"Ollama connection failed: {e}")
        except requests.exceptions.Timeout as e:
            self._logger.error(f"Ollama request timed out: {e}")
            raise LLMInferenceError(f"Ollama timeout: {e}")
        except Exception as e:
            self._logger.error(f"Ollama error: {e}")
            raise LLMInferenceError(f"Ollama error: {e}")

    def health_check(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            base_url = self._config.ollama_url.replace("/api/generate", "")
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
