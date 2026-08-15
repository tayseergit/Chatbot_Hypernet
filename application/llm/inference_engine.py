"""Inference engine — manages the LLM inference pipeline."""

from typing import Any, Dict, Optional
from application.llm.ollama_provider import OllamaProvider
from application.llm.gemini_provider import GeminiProvider
from application.llm.lmstudio_provider import LMStudioProvider
from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import LLMConfig


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
class InferenceEngine:
    """Manages LLM inference with model selection and parameter tuning."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("inference_engine")
        prov = config.provider.lower()
        if prov == "gemini":
            self._provider = GeminiProvider(config)
            self._logger.info("Selected LLM provider: Gemini")
        elif prov in ["lmstudio", "lm_studio", "lm-studio"]:
            self._provider = LMStudioProvider(config)
            self._logger.info("Selected LLM provider: LM Studio")
        else:
            self._provider = OllamaProvider(config)
            self._logger.info("Selected LLM provider: Ollama")

    def infer(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """Run inference on a prompt and return raw LLM output."""
        self._logger.debug(f"Running inference ({len(prompt)} chars prompt)")
        result = self._provider.generate(prompt, options)
        self._logger.debug(f"Inference complete ({len(result)} chars output)")
        return result

    def infer_stream(self, prompt: str, options: Dict[str, Any] = None):
        """Run streaming inference on a prompt and yield raw LLM output chunks."""
        self._logger.debug(f"Running stream inference ({len(prompt)} chars prompt)")
        if hasattr(self._provider, 'generate_stream'):
            for chunk in self._provider.generate_stream(prompt, options):
                yield chunk
        else:
            # Fallback for providers that don't support streaming yet
            result = self._provider.generate(prompt, options)
            yield result

    def health_check(self) -> bool:
        """Check if the LLM backend is available."""
        return self._provider.health_check()
