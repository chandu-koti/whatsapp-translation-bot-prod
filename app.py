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

# Initialize services
try:
    translation_service = TranslationService()
    whatsapp_handler = WhatsAppHandler()
    user_prefs = UserPreferences()
    logger.info("✅ All services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())

# Track processed message IDs
processed_message_ids = set()
user_translation_cache = {}

# ============ WEBHOOK ROUTES ============

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "WhatsApp Translation Bot is running!",
        "status": "active"
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle WhatsApp webhook - BOTH verification and incoming messages"""
    try:
        if request.method == 'GET':
            # Webhook verification from Meta/Facebook
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            logger.info(f"🔐 Verification attempt with token: {verify_token}")
            
            if verify_token == os.getenv('VERIFY_TOKEN', 'whatsapp-translation-bot-verify'):
                logger.info("✅ Webhook verified successfully")
                return challenge, 200
            else:
                logger.error("❌ Invalid verify token")
                return "Invalid verify token", 403

        elif request.method == 'POST':
            # Incoming message from WhatsApp
            logger.info("📨 Received POST request from WhatsApp")
            body = request.get_json()
            
            if not body:
                logger.warning("⚠️ Empty POST body")
                return jsonify({"status": "received"}), 200
            
            logger.info(f"📦 Webhook body: {json.dumps(body, indent=2)}")
            
            # Process the message
            response = process_message(body)
            return jsonify(response), 200

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "status": "error"}), 500

def process_message(webhook_data):
    """Process incoming WhatsApp messages - MAIN MESSAGE HANDLER"""
    try:
        if 'entry' not in webhook_data:
            logger.warning("⚠️ No 'entry' in webhook data")
            return {"status": "no_entry"}
        
        for entry in webhook_data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') != 'messages':
                    continue
                
                value = change.get('value', {})
                messages = value.get('messages', [])
                
                if not messages:
                    logger.info("ℹ️ No messages in value")
                    continue
                
                for message in messages:
                    message_id = message.get('id')
                    message_type = message.get('type')
                    sender_id = message.get('from')
                    
                    logger.info(f"📩 Message from {sender_id}, Type: {message_type}, ID: {message_id}")
                    
                    # === LOOP PROTECTION 1: Skip if already processed ===
                    if message_id in processed_message_ids:
                        logger.info(f"⏭️ Skipping already processed message: {message_id}")
                        continue
                    
                    processed_message_ids.add(message_id)
                    if len(processed_message_ids) > 1000:
                        processed_message_ids.pop()
                    
                    # === SKIP STATUS/REACTION MESSAGES ===
                    if message_type in ['status', 'reaction', 'delivery', 'read', 'system']:
                        logger.info(f"⏭️ Skipping {message_type} message")
                        continue
                    
                    # === HANDLE TEXT MESSAGES ===
                    if message_type == 'text':
                        message_body = message.get('text', {}).get('body', '').strip()
                        
                        if not message_body:
                            logger.warning("⚠️ Empty message body")
                            continue
                        
                        logger.info(f"💬 Text from {sender_id}: {message_body}")
                        
                        # === GET USER LANGUAGES ===
                        user_languages = user_prefs.get_user_languages(sender_id)
                        
                        if not user_languages:
                            logger.info(f"🆕 New user: {sender_id} - sending welcome menu")
                            send_welcome_menu(sender_id)
                            continue
                        
                        logger.info(f"👤 User {sender_id} has languages: {user_languages}")
                        
                        # === TRANSLATE THE MESSAGE ===
                        try:
                            translations = translation_service.translate_message(
                                message_body,
                                target_languages=user_languages
                            )
                            
                            if translations:
                                logger.info(f"✅ Translations received: {list(translations.keys())}")
                                
                                # Cache translations for audio
                                user_translation_cache[sender_id] = translations
                                
                                # Format and send response
                                formatted_response = format_translation_response(message_body, translations)
                                
                                logger.info(f"📤 Sending translation response to {sender_id}")
                                success = whatsapp_handler.send_message(sender_id, formatted_response)
                                
                                if success:
                                    logger.info("✅ Translation message sent successfully")
                                    send_audio_buttons(sender_id, list(translations.keys()))
                                else:
                                    logger.error("❌ Failed to send translation message")
                            else:
                                logger.warning("⚠️ No translations received")
                                whatsapp_handler.send_message(sender_id, "Sorry, couldn't translate. Please try again.")
                        
                        except Exception as e:
                            logger.error(f"❌ Translation error: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                            whatsapp_handler.send_message(sender_id, f"Error: {str(e)}")
                    
                    elif message_type == 'interactive':
                        # Handle interactive button/list responses
                        interactive = message.get('interactive', {})
                        if interactive.get('type') == 'button_reply':
                            button_id = interactive.get('button_reply', {}).get('id')
                            logger.info(f"🔘 Button pressed: {button_id}")
                            handle_button_response(sender_id, button_id)
                        elif interactive.get('type') == 'list_reply':
                            button_id = interactive.get('list_reply', {}).get('id')
                            logger.info(f"📋 List selected: {button_id}")
                            handle_button_response(sender_id, button_id)
                    
                    else:
                        logger.info(f"⏭️ Skipping message type: {message_type}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"❌ Error in process_message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

def format_translation_response(original_text, translations):
    """Format translations with language names"""
    response = f"🌍 *TRANSLATIONS FOR:* {original_text[:30]}\n\n"
    
    for lang_code, translated_text in translations.items():
        try:
            if translated_text and translated_text.strip() != original_text.strip():
                lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
                flag = lang_info.get('flag', '🌐')
                name = lang_info.get('name', lang_code)
                response += f"{flag} *{name}:*\n{translated_text}\n\n"
        except Exception as e:
            logger.error(f"Error formatting {lang_code}: {e}")
    
    response += "👆 Tap buttons below for audio!\n"
    return response

def send_audio_buttons(sender_id, lang_codes):
    """Send audio playback buttons"""
    if not lang_codes:
        return
    
    try:
        max_buttons = 3
        for i in range(0, len(lang_codes), max_buttons):
            batch = lang_codes[i:i + max_buttons]
            buttons = []
            
            for lang_code in batch:
                lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
                button_text = f"{lang_info.get('flag', '')} {lang_info.get('name', lang_code)}"
                
                if len(button_text) > 20:
                    button_text = f"{lang_info.get('flag', '')} {lang_info.get('name', lang_code)[:15]}"
                
                buttons.append({
                    "id": f"play_audio_{lang_code}",
                    "title": button_text[:20]
                })
            
            body_text = "🎵 *SELECT AUDIO*" if i == 0 else "🎵 *MORE AUDIO*"
            whatsapp_handler.send_interactive_buttons(sender_id, body_text, buttons)
            time.sleep(0.3)
        
        logger.info(f"✅ Audio buttons sent to {sender_id}")
    
    except Exception as e:
        logger.error(f"❌ Error sending audio buttons: {e}")

def send_welcome_menu(sender_id):
    """Send welcome menu to new users"""
    try:
        message = "👋 *Welcome to WhatsApp Translation Bot!*\n\n"
        message += "🌐 Translate messages to multiple languages instantly!\n"
        message += "🎵 Listen to pronunciations\n\n"
        message += "Just send a message and I'll translate it for you!\n\n"
        message += "Tap 'Start' to begin:"
        
        buttons = [
            {"id": "start", "title": "Start Translating"}
        ]
        
        whatsapp_handler.send_interactive_buttons(sender_id, message, buttons)
        logger.info(f"✅ Welcome menu sent to {sender_id}")
    
    except Exception as e:
        logger.error(f"❌ Error sending welcome menu: {e}")
        whatsapp_handler.send_message(sender_id, "👋 Welcome! Just send me a message to translate!")

def handle_button_response(sender_id, button_id):
    """Handle button responses"""
    try:
        if button_id == "start":
            message = "✅ You're all set! Send any message and I'll translate it to popular languages."
            whatsapp_handler.send_message(sender_id, message)
    except Exception as e:
        logger.error(f"❌ Error in button response: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting WhatsApp Translation Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
