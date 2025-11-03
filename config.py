# config.py
# 100% RELIABLE Configuration - Fixed indentation

import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for WhatsApp Translation Bot"""
    
    # WhatsApp Business API Settings
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_BOT_PHONE_NUMBER = os.getenv('WHATSAPP_BOT_PHONE_NUMBER')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'whatsapp_translation_bot_verify')
    
    # Google Cloud Translation API Settings
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # SUPPORTED LANGUAGES - 100% Working
    SUPPORTED_LANGUAGES = {
        # European Languages
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
        
        # Asian Languages (FIXED TTS codes!)
        'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵', 'translate': 'ja', 'tts': 'ja-JP'},
        'ko': {'name': 'Korean', 'native': '한국어', 'flag': '🇰🇷', 'translate': 'ko', 'tts': 'ko-KR'},
        'zh-CN': {'name': 'Chinese (Simplified)', 'native': '简体中文', 'flag': '🇨🇳', 'translate': 'zh-CN', 'tts': 'cmn-CN'},
        'zh-TW': {'name': 'Chinese (Traditional)', 'native': '繁體中文', 'flag': '🇹🇼', 'translate': 'zh-TW', 'tts': 'cmn-TW'},
        'th': {'name': 'Thai', 'native': 'ไทย', 'flag': '🇹🇭', 'translate': 'th', 'tts': 'th-TH'},
        'vi': {'name': 'Vietnamese', 'native': 'Tiếng Việt', 'flag': '🇻🇳', 'translate': 'vi', 'tts': 'vi-VN'},
        'id': {'name': 'Indonesian', 'native': 'Bahasa Indonesia', 'flag': '🇮🇩', 'translate': 'id', 'tts': 'id-ID'},
        
        # Indian Languages
        'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳', 'translate': 'hi', 'tts': 'hi-IN'},
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳', 'translate': 'te', 'tts': 'te-IN'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳', 'translate': 'ta', 'tts': 'ta-IN'},
        'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': '🇧🇩', 'translate': 'bn', 'tts': 'bn-IN'},
        'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'flag': '🇮🇳', 'translate': 'ml', 'tts': 'ml-IN'},
        'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'flag': '🇮🇳', 'translate': 'kn', 'tts': 'kn-IN'},
        'mr': {'name': 'Marathi', 'native': 'मराठी', 'flag': '🇮🇳', 'translate': 'mr', 'tts': 'mr-IN'},
        'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'flag': 'IN', 'translate': 'pa', 'tts': 'pa-IN'},
        'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'flag': '🇮🇳', 'translate': 'gu', 'tts': 'gu-IN'},
        
        # Other Languages
        'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦', 'translate': 'ar', 'tts': 'ar-XA'},
    }
    
    # Default language preferences for new users
    DEFAULT_TARGET_LANGUAGES = ['ja', 'hi', 'te']
    
    # Flask Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
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
            logger.error(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False
        
        # Check if credentials file exists
        if not os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            logger.error(f"❌ Google credentials file not found: {cls.GOOGLE_APPLICATION_CREDENTIALS}")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True
    
    @classmethod
    def get_language_display_name(cls, lang_code: str) -> str:
        """Get the display name of a language"""
        if lang_code in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[lang_code]['name']
        return lang_code.upper()
    
    @classmethod
    def get_supported_language_codes(cls) -> list:
        """Get list of all supported language codes"""
        return list(cls.SUPPORTED_LANGUAGES.keys())
    
    @classmethod
    def get_tts_code(cls, lang_code: str) -> str:
        """Get the TTS language code for a given language"""
        if lang_code in cls.SUPPORTED_LANGUAGES:
            return cls.SUPPORTED_LANGUAGES[lang_code]['tts']
        return 'en-US'
    
    @classmethod
    def is_language_supported(cls, lang_code: str) -> bool:
        """Check if a language is supported"""
        return lang_code in cls.SUPPORTED_LANGUAGES