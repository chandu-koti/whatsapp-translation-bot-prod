import os

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

            # Check credentials file exists

            credentials_path = os.path.join(os.path.dirname(__file__), 'service-account-key.json')

            if not os.path.exists(credentials_path):

                logger.error(f"❌ Credentials file not found: {credentials_path}")

                return

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

            self.translate_client = None

            self.tts_client = None

    def _test_connection(self):

        """Test the translation service connection"""

        try:

            result = self.translate_client.translate("Hello", target_language='ja')

            logger.info("✅ Translation service connection test successful")

        except Exception as e:

            logger.warning(f"⚠️ Translation service connection test failed: {str(e)}")

    def detect_language(self, text: str) -> Optional[str]:

        """Detect the language of input text"""

        if not self.translate_client:

            logger.error("❌ Translation client not available")

            return None

        try:

            result = self.translate_client.detect_language(text)

            detected_lang = result['language']

            confidence = result['confidence']

            logger.info(f"🔍 Detected language: {detected_lang} (confidence: {confidence:.2f})")

            return detected_lang

        except exceptions.GoogleAPIError as e:

            logger.error(f"❌ Google API error in language detection: {str(e)}")

            return None

        except Exception as e:

            logger.error(f"❌ Language detection error: {str(e)}")

            return None

    def normalize_detected_language_code(self, detected_lang: str) -> str:

        """

        Normalize detected language code to avoid 'Bad language pair' errors.

        """

        if not detected_lang:

            return 'en'

        # If language ends with '-Latn' (Romanized script), treat as English

        if detected_lang.endswith('-Latn'):

            logger.info(f"🔄 Normalized {detected_lang} → en (Romanized script)")

            return 'en'

        # Extract base language code (e.g., 'zh' from 'zh-CN')

        if '-' in detected_lang:

            base_lang = detected_lang.split('-')[0]

            # Special handling for Chinese

            if base_lang == 'zh':

                # Keep the full code for Chinese (zh-CN or zh-TW)

                if detected_lang in ['zh-CN', 'zh-TW']:

                    return detected_lang

                else:

                    # Default to Simplified Chinese

                    return 'zh-CN'

            # For other languages, use base code

            detected_lang = base_lang

        # Return the detected language if it's in our supported list

        if detected_lang in self.supported_languages:

            return detected_lang

        # If unknown, default to English

        logger.warning(f"⚠️ Unknown language code: {detected_lang}, defaulting to 'en'")

        return 'en'

    def translate_text(self, text: str, target_language: str, source_language: str = None) -> Optional[str]:

        """Translate text to target language"""

        if not self.translate_client:

            logger.error("❌ Translation client not available")

            return None

        try:

            # ✅ FIXED: Handle Chinese language codes properly

            translate_target = target_language

            translate_source = source_language

            # Google Translate uses 'zh-CN' and 'zh-TW', which is correct

            # No need to change anything for Chinese

            logger.info(f"🔄 Translating from '{translate_source}' to '{translate_target}'")

            result = self.translate_client.translate(

                text,

                target_language=translate_target,

                source_language=translate_source

            )

            translated_text = result['translatedText']

            # Clean up HTML entities

            import html

            translated_text = html.unescape(translated_text)

            logger.info(f"✅ Translated to {target_language}: '{translated_text[:50]}...'")

            return translated_text

        except exceptions.GoogleAPIError as e:

            logger.error(f"❌ Google API error in translation to {target_language}: {str(e)}")

            return None

        except Exception as e:

            logger.error(f"❌ Translation error to {target_language}: {str(e)}")

            return None

    def translate_message(self, message: str, target_languages: List[str] = None) -> Dict[str, str]:

        """Translate message to specified target languages"""

        translations = {}

        if not self.translate_client:

            logger.error("❌ Translation client not available")

            return translations

        if not message or not message.strip():

            logger.warning("⚠️ Empty message provided for translation")

            return translations

        try:

            # ✅ FIXED: Use provided target languages or default to original 4 (including Punjabi now!)

            if target_languages is None:

                target_languages = ['ja', 'hi', 'te', 'pa']

            # ✅ FIXED: Validate languages against our supported list

            valid_target_languages = []

            for lang in target_languages:

                if Config.is_language_supported(lang):

                    valid_target_languages.append(lang)

                else:

                    logger.warning(f"⚠️ Skipping unsupported language: {lang}")

            if not valid_target_languages:

                logger.error("❌ No valid target languages provided")

                return translations

            logger.info(f"🎯 Valid target languages: {valid_target_languages}")

            # Detect source language

            detected_lang = self.detect_language(message)

            if not detected_lang:

                logger.warning("⚠️ Could not detect source language, defaulting to English")

                detected_lang = 'en'

            # Normalize detected language

            normalized_lang = self.normalize_detected_language_code(detected_lang)

            logger.info(f"🎯 Source language: {normalized_lang}")

            # Translate to all target languages except the source language

            for target_lang in valid_target_languages:

                if normalized_lang == target_lang:

                    logger.info(f"⏭️ Skipping translation to same language: {target_lang}")

                    continue

                logger.info(f"🔄 Translating to {target_lang}...")

                translated = self.translate_text(message, target_lang, normalized_lang)

                if translated and translated.strip():

                    translations[target_lang] = translated

                    logger.info(f"✅ Translation to {target_lang} successful")

                else:

                    logger.warning(f"⚠️ Empty translation result for {target_lang}")

            logger.info(f"🎉 Generated {len(translations)} translations")

            return translations

        except Exception as e:

            logger.error(f"❌ Message translation error: {str(e)}")

            import traceback

            logger.error(traceback.format_exc())

            return translations

    def convert_to_romaji(self, japanese_text: str) -> Optional[str]:

        """Convert Japanese text to Romaji"""

        try:

            result = self.kakasi.convert(japanese_text)

            romaji_text = ''.join([item['hepburn'] for item in result])

            logger.info(f"📝 Romaji conversion successful")

            return romaji_text

        except Exception as e:

            logger.error(f"❌ Romaji conversion error: {str(e)}")

            return None

    def text_to_speech(self, text: str, filename: str = 'output.mp3', lang_code: str = 'hi-IN') -> Optional[str]:

        """Convert text to speech MP3 file"""

        if not self.tts_client:

            logger.error("❌ TTS client not initialized")

            return None

        try:

            logger.info(f"🎤 Generating voice for language: {lang_code}")

            synthesis_input = texttospeech.SynthesisInput(text=text)

            # ✅ FIXED: Use the exact voice code from config

            voice = texttospeech.VoiceSelectionParams(

                language_code=lang_code,

                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL

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

            with open(filename, "wb") as out:

                out.write(response.audio_content)

            logger.info(f"✅ Voice file created: {filename} ({len(response.audio_content)} bytes)")

            return filename

        except Exception as e:

            logger.error(f"❌ Text-to-speech error for {lang_code}: {str(e)}")

            import traceback

            logger.error(traceback.format_exc())

            return None

    def is_healthy(self) -> bool:

        """Check if the translation service is healthy"""

        return self.translate_client is not None and self.tts_client is not None
