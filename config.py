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

    # Supported Languages
    SUPPORTED_LANGUAGES = {
        'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
        'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳'}, 
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳'},
        'en': {'name': 'English', 'native': 'English', 'flag': '🇺🇸'}
    }

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