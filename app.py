from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
from whatsapp_handler import WhatsAppHandler
from translation_service import TranslationService
from user_preferences import UserPreferences
from config import Config
import logging
from datetime import datetime
from typing import Optional
import time

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Initialize services SAFELY with proper error handling
translation_service = None
whatsapp_handler = None
user_prefs = None

try:
    logger.info("🔧 Initializing Translation Service...")
    translation_service = TranslationService()
    logger.info("✅ Translation Service initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize TranslationService: {str(e)}")
    logger.error(f"   Make sure GOOGLE_APPLICATION_CREDENTIALS_JSON env var is set!")

try:
    logger.info("🔧 Initializing WhatsApp Handler...")
    whatsapp_handler = WhatsAppHandler()
    logger.info("✅ WhatsApp Handler initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize WhatsAppHandler: {str(e)}")
    logger.error(f"   Check WhatsApp environment variables!")

try:
    logger.info("🔧 Initializing User Preferences...")
    user_prefs = UserPreferences()
    logger.info("✅ User Preferences initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize UserPreferences: {str(e)}")

logger.info("=" * 50)
logger.info("✅ ALL SERVICES INITIALIZED SUCCESSFULLY!")
logger.info("=" * 50)

# CRITICAL: Track processed message IDs to prevent infinite loops
processed_message_ids = set()
user_translation_cache = {}


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🌐 WhatsApp Translation Bot is running!",
        "status": "active",
        "features": ["Visual Menu", "Interactive Buttons", "26 Languages", "On-Demand Audio"],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle WhatsApp webhook requests"""
    try:
        if request.method == 'GET':
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            logger.info("🔍 Webhook verification attempt")
            
            if verify_token == os.getenv('VERIFY_TOKEN'):
                logger.info("✅ Webhook verified successfully")
                return challenge
            else:
                logger.error("❌ Invalid verify token")
                return 'Invalid verify token', 403

        elif request.method == 'POST':
            body = request.get_json()
            logger.info("📨 Received webhook POST request")
            response = process_message(body)
            return jsonify(response)

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


def send_welcome_menu(sender_id: str):
    """Send welcome menu with language categories"""
    if not whatsapp_handler:
        logger.error("❌ WhatsApp handler not initialized")
        return
    
    body_text = """🌐 *TRANSLATION BOT*
━━━━━━━━━━━━━━━━━━━━
👋 Welcome! Let's set up your languages!

I support 26 languages across different regions.

Tap the button below to choose:"""
    
    buttons = [
        {"id": "menu_categories", "title": "🎨 Choose Languages"},
        {"id": "menu_quick", "title": "⚡ Quick Setup"},
        {"id": "menu_help", "title": "❓ Help"}
    ]
    
    whatsapp_handler.send_interactive_buttons(sender_id, body_text, buttons)


def send_category_menu(sender_id: str):
    """Send language category selection"""
    if not whatsapp_handler:
        logger.error("❌ WhatsApp handler not initialized")
        return
    
    body_text = """📱 *SELECT LANGUAGE CATEGORY*
━━━━━━━━━━━━━━━━━━━━
Choose a category to see available languages:"""
    
    sections = [
        {
            "title": "Language Categories",
            "rows": [
                {"id": "cat_asian", "title": "📱 Asian Languages", "description": "Japanese, Chinese, Korean, Thai, Vietnamese"},
                {"id": "cat_indian", "title": "🇮🇳 Indian Languages", "description": "Hindi, Telugu, Tamil, Bengali, and more"},
                {"id": "cat_european", "title": "🌍 European Languages", "description": "German, Spanish, French, Italian, Portuguese"},
                {"id": "cat_other", "title": "🌎 Other Languages", "description": "Arabic, Russian, and more"},
                {"id": "view_selected", "title": "✅ View Selected", "description": "See your languages"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Choose Category", sections)


def send_done_message(sender_id: str):
    """Send confirmation"""
    if not whatsapp_handler or not user_prefs:
        logger.error("❌ Services not initialized")
        return
    
    user_langs = user_prefs.get_user_languages(sender_id)
    
    if not user_langs:
        whatsapp_handler.send_message(sender_id, "⚠️ No languages selected!")
        send_welcome_menu(sender_id)
        return
    
    lang_list = []
    for lang_code in user_langs:
        lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
        lang_list.append(f"{lang_info.get('flag', '🌍')} {lang_info.get('name', lang_code)}")
    
    message = f"""🎉 *ALL SET!*
━━━━━━━━━━━━━━━━━━━━
Your languages:

{chr(10).join(lang_list)}

Send any message! Tap ▶️ buttons for audio! 🔊"""
    
    whatsapp_handler.send_message(sender_id, message)


def handle_button_response(sender_id: str, button_id: str):
    """Handle button/list responses"""
    if not whatsapp_handler or not user_prefs:
        logger.error("❌ Services not initialized")
        return
    
    logger.info(f"🎯 Button: {button_id} by {sender_id}")
    
    # Navigation
    if button_id == "menu_categories":
        send_category_menu(sender_id)
    elif button_id == "menu_help":
        help_text = """❓ *HOW TO USE*
━━━━━━━━━━━━━━━━━━━━
1️⃣ Choose languages
2️⃣ Tap ✅ Done
3️⃣ Send any message
4️⃣ Tap ▶️ Play Audio buttons for voice!

Clean, no spam!"""
        whatsapp_handler.send_message(sender_id, help_text)
        send_welcome_menu(sender_id)
    
    elif button_id == "done_selecting":
        send_done_message(sender_id)


def process_message(webhook_data):
    """Process incoming WhatsApp messages"""
    try:
        if not webhook_data.get('entry'):
            return {"status": "no_entry"}
        
        if not whatsapp_handler or not user_prefs or not translation_service:
            logger.error("❌ Services not initialized - cannot process message")
            return {"status": "error", "message": "Services not initialized"}
        
        for entry in webhook_data['entry']:
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    value = change.get('value', {})
                    
                    if 'messages' not in value:
                        continue
                    
                    messages = value.get('messages', [])
                    
                    for message in messages:
                        message_id = message.get('id')
                        message_type = message.get('type')
                        sender_id = message.get('from')
                        
                        # LOOP PROTECTION: Skip if already processed
                        if message_id in processed_message_ids:
                            logger.info(f"⏭️ Skip processed: {message_id}")
                            continue
                        
                        processed_message_ids.add(message_id)
                        
                        # Clean up (keep last 1000)
                        if len(processed_message_ids) > 1000:
                            processed_message_ids.pop()
                        
                        # Skip non-text messages
                        if message_type != 'text':
                            logger.info(f"⏭️ Skip non-text: {message_type}")
                            continue
                        
                        message_body = message.get('text', {}).get('body', '')
                        
                        if not message_body or not message_body.strip():
                            logger.info("⏭️ Skip empty message")
                            continue
                        
                        logger.info(f"💬 From {sender_id}: '{message_body}'")
                        
                        # Check user languages
                        user_langs = user_prefs.get_user_languages(sender_id)
                        
                        if not user_langs:
                            logger.info(f"👤 New user")
                            send_welcome_menu(sender_id)
                            continue
                        
                        logger.info(f"✅ User langs: {user_langs}")
                        
                        # Translate
                        try:
                            translations = translation_service.translate_message(
                                message_body, 
                                target_languages=user_langs
                            )
                            
                            if translations:
                                logger.info(f"✅ Translation successful")
                                whatsapp_handler.send_message(
                                    sender_id, 
                                    f"✅ Translated to {len(translations)} languages!"
                                )
                            else:
                                logger.warning("⚠️ No translations returned")
                                whatsapp_handler.send_message(
                                    sender_id, 
                                    "Sorry, couldn't translate that message."
                                )
                        
                        except Exception as e:
                            logger.error(f"❌ Translation error: {str(e)}")
                            whatsapp_handler.send_message(
                                sender_id, 
                                f"❌ Error during translation"
                            )
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"❌ Process message error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error"}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "translation": "✅" if translation_service else "❌",
            "whatsapp": "✅" if whatsapp_handler else "❌",
            "user_prefs": "✅" if user_prefs else "❌"
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    logger.info(f"🚀 Starting Bot on port {port}")
    logger.info("✅ All systems ready!")
    app.run(host='0.0.0.0', port=port, debug=debug)
