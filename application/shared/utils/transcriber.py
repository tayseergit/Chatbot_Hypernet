import os
import logging
import whisper
from application.shared.exceptions.app_exceptions import ChatbotBaseException

import sys

# أضفنا مسار venv/Scripts إلى النظام مؤقتاً لكي يتعرف Whisper على ffmpeg
venv_scripts = os.path.abspath(os.path.join(os.getcwd(), "venv", "Scripts"))
if venv_scripts not in os.environ.get("PATH", ""):
    os.environ["PATH"] = venv_scripts + os.pathsep + os.environ.get("PATH", "")

logger = logging.getLogger("audio_transcriber")

class AudioTranscriber:
    """
    Service for converting voice messages into text using local Whisper.
    Uses a Singleton pattern for the model to prevent massive RAM usage on concurrent requests.
    """
    _model_instance = None

    def __init__(self):
        # We load the model from the local file if it exists, otherwise it will try to download
        model_path = os.path.join(os.getcwd(), "models", "small.pt")
        try:
            if AudioTranscriber._model_instance is None:
                if os.path.exists(model_path):
                    AudioTranscriber._model_instance = whisper.load_model(model_path)
                else:
                    logger.warning("Local model not found at models/small.pt. It will try to download automatically without resume support.")
                    AudioTranscriber._model_instance = whisper.load_model("small")
            
            self.model = AudioTranscriber._model_instance
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes the given audio file using local Whisper.
        Args:
            audio_file_path (str): The absolute path to the audio file (.ogg, .mp3, etc.)
        Returns:
            str: The transcribed text.
        """
        if self.model is None:
            raise ChatbotBaseException("Whisper model is not loaded. Please download the model first.")

        if not os.path.exists(audio_file_path):
            raise ChatbotBaseException(f"Audio file not found at: {audio_file_path}")

        try:
            # Local whisper model inference
            result = self.model.transcribe(audio_file_path, language="ar", fp16=False)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Failed to transcribe audio file {audio_file_path}: {e}")
            raise ChatbotBaseException(f"حدث خطأ أثناء معالجة المقطع الصوتي: تأكد من تثبيت ffmpeg على جهازك. ({str(e)})")
