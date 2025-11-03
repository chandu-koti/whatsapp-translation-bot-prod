import os
import json
import base64
import logging
from typing import Dict, Optional, List
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from google.api_core import exceptions
import pykakasi
from config import Config

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        """Initialize Google Cloud Translation and TTS clients"""
        self.translate_client = None
        self.tts_client = None
        
        # ✅ FIXED: Get supported languages dynamically from Config
        self.supported_languages = Config.get_supported_language_codes()
        logger.info(f"✅ Loaded {len(self.supported_languages)} supported languages")
        
        try:
            # ✅ NEW: Load credentials from environment variable instead of file
            credentials_json_b64 = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            
            if not credentials_json_b64:
                logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")
                logger.error("Make sure to set this in Render environment variables!")
                return
            
            # Decode BASE64 to JSON string
            try:
                credentials_json_str = base64.b64decode(credentials_json_b64).decode('utf-8')
                credentials_dict = json.loads(credentials_json_str)
                logger.info("✅ Successfully decoded BASE64 credentials")
            except Exception as e:
                logger.error(f"❌ Failed to decode BASE64 credentials: {str(e)}")
                return
            
            # Write credentials to temporary location for Google Cloud SDK
            # This is required by google-cloud-translate
            credentials_path = '/tmp/google-credentials.json'
            with open(credentials_path, 'w') as f:
                json.dump(credentials_dict, f)
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            logger.info("✅ Google Cloud credentials loaded from environment variable")
            
            # Initialize Translation client
            self.translate_client = translate.Client()
            logger.info("✅ Google Cloud Translation client initialized")
            
            # Initialize Text-to-Speech client
            self.tts_client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google Cloud Text-to-Speech client initialized")
            
            # Initialize Romaji converter for Japanese
            self.kakasi = pykakasi.kakasi()
            logger.info("✅ Romaji converter initialized")
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize clients: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.translate_client = None
            self.tts_client = None

    def _test_connection(self):
        """Test translation service connection"""
        try:
            if self.translate_client:
                # Simple test translation
                test_result = self.translate_client.translate_text(
                    source_language='en',
                    target_language='hi',
                    source_text='Hello'
                )
                logger.info("✅ Translation service connection successful")
        except Exception as e:
            logger.warning(f"⚠️ Translation test failed: {str(e)}")

    def translate(self, text: str, target_language: str, source_language: str = 'en') -> Optional[str]:
        """Translate text using Google Cloud Translation API"""
        if not self.translate_client:
            logger.error("❌ Translation client not initialized")
            return None
        
        try:
            if target_language not in self.supported_languages:
                logger.warning(f"⚠️ Language {target_language} not supported, skipping translation")
                return text
            
            result = self.translate_client.translate_text(
                source_language=source_language,
                target_language=target_language,
                source_text=text
            )
            
            return result['translatedText']
        except Exception as e:
            logger.error(f"❌ Translation failed: {str(e)}")
            return None

    def text_to_speech(self, text: str, language_code: str, output_path: str) -> bool:
        """Convert text to speech using Google Cloud TTS"""
        if not self.tts_client:
            logger.error("❌ TTS client not initialized")
            return False
        
        try:
            # Determine voice for language
            if language_code == 'hi':
                voice_name = 'hi-IN-Standard-A'
            elif language_code == 'ta':
                voice_name = 'ta-IN-Standard-A'
            elif language_code == 'te':
                voice_name = 'te-IN-Standard-A'
            elif language_code == 'kn':
                voice_name = 'kn-IN-Standard-A'
            elif language_code == 'gu':
                voice_name = 'gu-IN-Standard-A'
            elif language_code == 'pt':
                voice_name = 'pt-BR-Standard-A'
            elif language_code == 'de':
                voice_name = 'de-DE-Standard-A'
            elif language_code == 'vi':
                voice_name = 'vi-VN-Standard-A'
            else:
                voice_name = 'en-US-Standard-A'
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Write audio to file
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            logger.info(f"✅ Text-to-Speech generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Text-to-Speech failed: {str(e)}")
            return False

    def convert_to_romaji(self, text: str) -> str:
        """Convert Japanese text to Romaji"""
        try:
            result = self.kakasi.convert(text)
            romaji = ''.join([item['hepburn'] for item in result])
            return romaji
        except Exception as e:
            logger.error(f"❌ Romaji conversion failed: {str(e)}")
            return text

    def get_supported_languages(self) -> Dict[str, str]:
        """Return supported languages"""
        return self.supported_languages
