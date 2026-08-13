"""Gemini provider — HTTP client for Google Gemini REST API."""

from typing import Any, Dict, Optional
import requests

from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import LLMConfig
from application.shared.exceptions.app_exceptions import LLMInferenceError


class GeminiProvider:
    """HTTP client for Google Gemini REST API."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("gemini_provider")

    def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Send a prompt to Gemini API and return the response text.

        Raises LLMInferenceError on failure.
        """
        temp = self._config.temperature
        top_p = self._config.top_p
        top_k = self._config.top_k
        if options:
            temp = options.get("temperature", temp)
            top_p = options.get("top_p", top_p)
            top_k = options.get("top_k", top_k)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._config.gemini_model}:generateContent?key={self._config.gemini_api_key}"

        parts = [{"text": prompt}]
        if options and "image_bytes" in options and options["image_bytes"]:
            import base64
            img_b64 = base64.b64encode(options["image_bytes"]).decode("utf-8")
            parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": img_b64
                }
            })

        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "temperature": temp,
                "topP": top_p,
                "topK": top_k,
            }
        }

        try:
            response = requests.post(
                url, json=payload,
                timeout=self._config.request_timeout,
            )
            response.raise_for_status()
            result = response.json()
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""

        except requests.exceptions.ConnectionError as e:
            self._logger.error(f"Cannot connect to Gemini API: {e}")
            raise LLMInferenceError(f"Gemini connection failed: {e}")
        except requests.exceptions.Timeout as e:
            self._logger.error(f"Gemini request timed out: {e}")
            raise LLMInferenceError(f"Gemini timeout: {e}")
        except Exception as e:
            self._logger.error(f"Gemini API error: {e}")
            raise LLMInferenceError(f"Gemini error: {e}")

    def health_check(self) -> bool:
        """Check if Gemini API is accessible with the provided API key."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._config.gemini_model}?key={self._config.gemini_api_key}"
            resp = requests.get(url, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
