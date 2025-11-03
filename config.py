import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class Config:
    """Configuration settings for WhatsApp Translation Bot"""

    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_BOT_PHONE_NUMBER = os.getenv('WHATSAPP_BOT_PHONE_NUMBER')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'whatsapp_translation_bot_verify')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')

    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧', 'translate': 'en', 'tts': 'en-US'},
        'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪', 'translate': 'de', 'tts': 'de-DE'},
        'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸', 'translate': 'es', 'tts': 'es-ES'},
        'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷', 'translate': 'fr', 'tts': 'fr-FR'},
        'it': {'name': 'Italian', 'native': 'Italiano', 'flag': '🇮🇹', 'translate': 'it', 'tts': 'it-IT'},
        'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹', 'translate': 'pt', 'tts': 'pt-PT'},
        'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺', 'translate': 'ru', 'tts': 'ru-RU'},
        'nl': {'name': 'Dutch', 'native': 'Nederlands', 'flag': '🇳🇱', 'translate': 'nl', 'tts': 'nl-NL'},
        'pl': {'name': 'Polish', 'native': 'Polski', 'flag': '🇵🇱', 'translate': 'pl', 'tts': 'pl-PL'},
        'tr': {'name': 'Turkish', 'native': 'Türkçe', 'flag': '🇹🇷', 'translate': 'tr', 'tts': 'tr-TR'},
        'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵', 'translate': 'ja', 'tts': 'ja-JP'},
        'ko': {'name': 'Korean', 'native': '한국어', 'flag': '🇰🇷', 'translate': 'ko', 'tts': 'ko-KR'},
        'zh-CN': {'name': 'Chinese (Simplified)', 'native': '简体中文', 'flag': '🇨🇳', 'translate': 'zh-CN', 'tts': 'cmn-CN'},
        'zh-TW': {'name': 'Chinese (Traditional)', 'native': '繁體中文', 'flag': '🇹🇼', 'translate': 'zh-TW', 'tts': 'cmn-TW'},
        'th': {'name': 'Thai', 'native': 'ไทย', 'flag': '🇹🇭', 'translate': 'th', 'tts': 'th-TH'},
        'vi': {'name': 'Vietnamese', 'native': 'Tiếng Việt', 'flag': '🇻🇳', 'translate': 'vi', 'tts': 'vi-VN'},
        'id': {'name': 'Indonesian', 'native': 'Bahasa Indonesia', 'flag': '🇮🇩', 'translate': 'id', 'tts': 'id-ID'},
        'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳', 'translate': 'hi', 'tts': 'hi-IN'},
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳', 'translate': 'te', 'tts': 'te-IN'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳', 'translate': 'ta', 'tts': 'ta-IN'},
        'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': '🇧🇩', 'translate': 'bn', 'tts': 'bn-IN'},
        'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'flag': '🇮🇳', 'translate': 'ml', 'tts': 'ml-IN'},
        'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'flag': '🇮🇳', 'translate': 'kn', 'tts': 'kn-IN'},
        'mr': {'name': 'Marathi', 'native': 'मराठी', 'flag': '🇮🇳', 'translate': 'mr', 'tts': 'mr-IN'},
        'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'flag': '🇮🇳', 'translate': 'pa', 'tts': 'pa-IN'},
        'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'flag': '🇮🇳', 'translate': 'gu', 'tts': 'gu-IN'},
        'ur': {'name': 'Urdu', 'native': 'اردو', 'flag': '🇮🇳', 'translate': 'ur', 'tts': 'ur-IN'},
        'as': {'name': 'Assamese', 'native': 'অসমীয়া', 'flag': '🇮🇳', 'translate': 'as', 'tts': 'as-IN'},
        'or': {'name': 'Odia', 'native': 'ଓଡ଼ିଆ', 'flag': '🇮🇳', 'translate': 'or', 'tts': 'or-IN'},
        'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦', 'translate': 'ar', 'tts': 'ar-XA'},
    }

    DEFAULT_TARGET_LANGUAGES = ['ja', 'hi', 'te', 'ta', 'bn', 'ml', 'kn', 'mr', 'pa', 'gu', 'ur', 'as', 'or']
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))

    @classmethod
    def validate_config(cls) -> bool:
        required_vars = [
            ('WHATSAPP_ACCESS_TOKEN', cls.WHATSAPP_ACCESS_TOKEN),
            ('WHATSAPP_PHONE_NUMBER_ID', cls.WHATSAPP_PHONE_NUMBER_ID),
            ('GOOGLE_APPLICATION_CREDENTIALS', cls.GOOGLE_APPLICATION_CREDENTIALS),
            ('GOOGLE_CLOUD_PROJECT', cls.GOOGLE_CLOUD_PROJECT)
        ]
        missing = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing.append(var_name)
        if missing:
            logger.error(f"❌ Missing: {', '.join(missing)}")
            return False
        if not os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            logger.error(f"❌ Creds not found: {cls.GOOGLE_APPLICATION_CREDENTIALS}")
            return False
        logger.info("✅ Config valid")
        return True

    @classmethod
    def get_language_display_name(cls, lang_code: str) -> str:
        if lang_code in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[lang_code]['name']
        return lang_code.upper()

    @classmethod
    def get_supported_language_codes(cls) -> list:
        return list(cls.SUPPORTED_LANGUAGES.keys())

    @classmethod
    def get_tts_code(cls, lang_code: str) -> str:
        if lang_code in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[lang_code]['tts']
        return 'en-US'

    @classmethod
    def is_language_supported(cls, lang_code: str) -> bool:
        return lang_code in cls.SUPPORTED_LANGUAGES
