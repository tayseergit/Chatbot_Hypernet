"""Inference engine — manages the LLM inference pipeline."""

from typing import Any, Dict, Optional
from application.llm.ollama_provider import OllamaProvider
from application.llm.gemini_provider import GeminiProvider
from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import LLMConfig


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
class InferenceEngine:
    """Manages LLM inference with model selection and parameter tuning."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("inference_engine")
        if config.provider.lower() == "gemini":
            self._provider = GeminiProvider(config)
            self._logger.info("Selected LLM provider: Gemini")
        else:
            self._provider = OllamaProvider(config)
            self._logger.info("Selected LLM provider: Ollama")

    def infer(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """Run inference on a prompt and return raw LLM output."""
        self._logger.debug(f"Running inference ({len(prompt)} chars prompt)")
        result = self._provider.generate(prompt, options)
        self._logger.debug(f"Inference complete ({len(result)} chars output)")
        return result

    def health_check(self) -> bool:
        """Check if the LLM backend is available."""
        return self._provider.health_check()
