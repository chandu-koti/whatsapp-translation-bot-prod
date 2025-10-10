import os
import logging
from typing import Dict, Optional
from google.cloud import translate_v2 as translate
from google.api_core import exceptions

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        """Initialize Google Cloud Translation client"""
        self.client = None
        self.supported_languages = ['ja', 'hi', 'te', 'en']

        try:
            # Check if credentials are available
            credentials_path = os.path.join(os.path.dirname(__file__), 'service-account-key.json')

            if not credentials_path:
                logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
                return

            if not os.path.exists(credentials_path):
                logger.error(f"❌ Credentials file not found: {credentials_path}")
                return

            # Initialize client
            self.client = translate.Client()
            logger.info("✅ Google Cloud Translation client initialized successfully")

            # Test the connection
            self._test_connection()

        except Exception as e:
            logger.error(f"❌ Failed to initialize translation client: {str(e)}")
            self.client = None

    def _test_connection(self):
        """Test the translation service connection"""
        try:
            result = self.client.translate("Hello", target_language='ja')
            logger.info("✅ Translation service connection test successful")
        except Exception as e:
            logger.warning(f"⚠️ Translation service connection test failed: {str(e)}")

    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of input text"""
        if not self.client:
            logger.error("❌ Translation client not available")
            return None

        try:
            result = self.client.detect_language(text)
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

    def translate_text(self, text: str, target_language: str, source_language: str = None) -> Optional[str]:
        """Translate text to target language"""
        if not self.client:
            logger.error("❌ Translation client not available")
            return None

        try:
            result = self.client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )

            translated_text = result['translatedText']

            # Clean up HTML entities that sometimes appear
            import html
            translated_text = html.unescape(translated_text)

            logger.info(f"🔄 Translated to {target_language}: '{translated_text[:30]}...'")
            return translated_text

        except exceptions.GoogleAPIError as e:
            logger.error(f"❌ Google API error in translation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Translation error: {str(e)}")
            return None

    def translate_message(self, message: str) -> Dict[str, str]:
        """Translate message to all supported languages except source"""
        translations = {}

        if not self.client:
            logger.error("❌ Translation client not available")
            return translations

        if not message or not message.strip():
            logger.warning("⚠️ Empty message provided for translation")
            return translations

        try:
            # Detect source language
            detected_lang = self.detect_language(message)

            if not detected_lang:
                logger.warning("⚠️ Could not detect source language, defaulting to English")
                detected_lang = 'en'

            logger.info(f"🎯 Translating from {detected_lang} to supported languages")

            # Translate to all supported languages except the detected one
            for target_lang in self.supported_languages:
                if detected_lang == target_lang:
                    logger.info(f"⏭️ Skipping translation to same language: {target_lang}")
                    continue

                translated = self.translate_text(message, target_lang, detected_lang)

                if translated and translated.strip():
                    translations[target_lang] = translated
                    logger.info(f"✅ Translation to {target_lang} successful")
                else:
                    logger.warning(f"⚠️ Empty translation result for {target_lang}")

            logger.info(f"🎉 Generated {len(translations)} translations")
            return translations

        except Exception as e:
            logger.error(f"❌ Message translation error: {str(e)}")
            return translations

    def is_healthy(self) -> bool:
        """Check if the translation service is healthy"""
        return self.client is not None