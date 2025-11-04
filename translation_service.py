import os
import json
import base64
import logging
from typing import Dict, Optional, List
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
import pykakasi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        credentials_json_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not credentials_json_b64:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set!")
            self.translate_client = None
            self.tts_client = None
            return
        try:
            credentials_json_str = base64.b64decode(credentials_json_b64).decode("utf-8")
            credentials_dict = json.loads(credentials_json_str)
            credential_path = "/tmp/google-credentials.json"
            with open(credential_path, "w") as f:
                json.dump(credentials_dict, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
            logger.info("Google Cloud credentials loaded successfully")
        except Exception as e:
            logger.error(f"Failed to decode BASE64 credentials: {e}")
            self.translate_client = None
            self.tts_client = None
            return

        try:
            self.translate_client = translate.Client()
            self.tts_client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud clients: {e}")
            self.translate_client = None
            self.tts_client = None

        self.kakasi = pykakasi.kakasi()

    def translate(self, text: str, target_language: str, source_language: str = "en") -> Optional[str]:
        if not self.translate_client:
            logger.error("Translation client not initialized")
            return None
        try:
            result = self.translate_client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            return result['translatedText']
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return None

    def text_to_speech(self, text: str, language_code: str, output_path: str) -> bool:
        if not self.tts_client:
            logger.error("TTS client not initialized")
            return False
        try:
            voice_name = {
                "hi": "hi-IN-Standard-A",
                "ta": "ta-IN-Standard-A",
                "te": "te-IN-Standard-A",
                "kn": "kn-IN-Standard-A",
                "gu": "gu-IN-Standard-A",
                "pt": "pt-BR-Standard-A",
                "de": "de-DE-Standard-A",
                "vi": "vi-VN-Standard-A",
            }.get(language_code, "en-US-Standard-A")
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code, name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            logger.info(f"Text-to-speech generated: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Text-to-Speech failed: {e}")
            return False

    def convert_to_romaji(self, text: str) -> str:
        try:
            result = self.kakasi.convert(text)
            romaji = " ".join([item['hepburn'] for item in result])
            return romaji
        except Exception as e:
            logger.error(f"Romaji conversion failed: {e}")
            return text
