#!/usr/bin/env python3
"""
WhatsApp Translation Bot - Easy Startup Script
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import flask
        import google.cloud.translate_v2
        import requests
        import dotenv
        logger.info("✅ All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False

def check_credentials():
    """Check if all credentials are properly configured"""
    logger.info("🔍 Checking credentials...")

    required_vars = [
        'WHATSAPP_ACCESS_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID', 
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CLOUD_PROJECT'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        return False

    # Check if credentials file exists
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not os.path.exists(creds_file):
        logger.error(f"❌ Google credentials file not found: {creds_file}")
        return False

    logger.info("✅ All credentials validated")
    return True

def start_bot():
    """Start the WhatsApp Translation Bot"""
    logger.info("🚀 Starting WhatsApp Translation Bot...")

    # Check requirements
    if not check_requirements():
        logger.error("❌ Please install requirements first")
        return False

    # Check credentials
    if not check_credentials():
        logger.error("❌ Please configure credentials first")
        return False

    # Start the Flask app
    try:
        from app import app
        port = int(os.getenv('PORT', 5000))
        logger.info(f"🌟 Bot starting on port {port}")
        logger.info("📱 Ready to translate messages!")
        logger.info("🔗 Remember to set up your webhook URL in Meta Developer Console")

        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.getenv('DEBUG', 'True').lower() == 'true'
        )
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    start_bot()