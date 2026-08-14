import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceService:
    """
    Service responsible for converting voice notes to text using OpenAI Whisper API.
    """
    def __init__(self, api_key: Optional[str] = None):
        # We try to get the key from the parameter, or fallback to the environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file using OpenAI's Whisper model via HTTP request.
        
        Args:
            audio_file_path (str): The local path to the downloaded voice note file (e.g., .ogg from Telegram).
            
        Returns:
            str: The transcribed text. Returns empty string if transcription fails.
        """
        if not self.api_key:
            logger.error("[X] VoiceService - OpenAI API key not found. Cannot transcribe audio.")
            return ""

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"[-] VoiceService - Starting transcription for {audio_file_path}")
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                # Telegram usually sends voice notes as OGG format
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, "audio/ogg")
                }
                # Setting model to whisper-1. Specifying language="ar" helps the model 
                # focus on Arabic, reducing hallucinations and improving speed.
                data = {
                    "model": "whisper-1",
                    "language": "ar"
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    transcribed_text = result.get("text", "")
                    logger.info(f"[-] VoiceService - Transcription successful: '{transcribed_text}'")
                    return transcribed_text
                else:
                    logger.error(f"[X] VoiceService - Whisper API error ({response.status_code}): {response.text}")
                    return ""
                    
        except Exception as e:
            logger.error(f"[X] VoiceService - Exception during transcription: {str(e)}")
            return ""
