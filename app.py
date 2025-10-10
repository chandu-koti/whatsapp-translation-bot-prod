from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
from whatsapp_handler import WhatsAppHandler
from translation_service import TranslationService
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging with timestamp
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
    logger.info("✅ Services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {str(e)}")

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🌐 WhatsApp Translation Bot is running!",
        "status": "active",
        "supported_languages": {
            "ja": "Japanese (日本語)",
            "hi": "Hindi (हिन्दी)", 
            "te": "Telugu (తెలుగు)",
            "en": "English"
        },
        "purpose": "Japanese-Indian business communication bridge",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle WhatsApp webhook requests"""
    try:
        if request.method == 'GET':
            # Webhook verification
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')

            logger.info(f"🔍 Webhook verification attempt")

            if verify_token == os.getenv('VERIFY_TOKEN'):
                logger.info("✅ Webhook verified successfully")
                return challenge
            else:
                logger.error("❌ Invalid verify token")
                return 'Invalid verify token', 403

        elif request.method == 'POST':
            # Handle incoming messages
            body = request.get_json()
            logger.info(f"📨 Received webhook message")

            # Process the message
            response = process_message(body)
            return jsonify(response)

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def process_message(webhook_data):
    """Process incoming WhatsApp message and send translation"""
    try:
        if not webhook_data.get('entry'):
            return {"status": "no_entry"}

        for entry in webhook_data['entry']:
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    value = change.get('value', {})
                    messages = value.get('messages', [])

                    for message in messages:
                        # Only process text messages
                        if message.get('type') != 'text':
                            logger.info(f"⏭️ Skipping non-text message")
                            continue

                        message_body = message.get('text', {}).get('body', '')
                        sender_id = message.get('from')

                        # Skip empty messages or bot commands
                        if not message_body or message_body.startswith('/'):
                            logger.info(f"⏭️ Skipping empty/command message")
                            continue

                        # Prevent bot from responding to itself
                        if sender_id == os.getenv('WHATSAPP_BOT_PHONE_NUMBER'):
                            logger.info("⏭️ Skipping message from bot itself")
                            continue

                        logger.info(f"🔤 Processing message: '{message_body[:50]}...' from {sender_id}")

                        # Translate the message
                        translations = translation_service.translate_message(message_body)

                        if translations:
                            # Format and send response
                            formatted_response = format_translation_response(message_body, translations)
                            success = whatsapp_handler.send_message(sender_id, formatted_response)

                            if success:
                                logger.info(f"✅ Translation sent successfully")
                            else:
                                logger.error(f"❌ Failed to send translation")
                        else:
                            logger.warning(f"⚠️ No translations generated")

        return {"status": "success", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"❌ Message processing error: {str(e)}")
        return {"status": "error", "message": str(e)}

def format_translation_response(original_text, translations):
    """Format the translation response message"""
    response = "🌐 *Translation Service*\n"
    response += "=" * 30 + "\n\n"
    response += f"📝 *Original:* {original_text}\n\n"

    language_info = {
        'ja': {'name': 'Japanese', 'flag': '🇯🇵'},
        'hi': {'name': 'Hindi', 'flag': '🇮🇳'}, 
        'te': {'name': 'Telugu', 'flag': '🇮🇳'},
        'en': {'name': 'English', 'flag': '🇺🇸'}
    }

    for lang_code, translated_text in translations.items():
        if translated_text and translated_text.strip() != original_text.strip():
            lang_info_item = language_info.get(lang_code, {'name': lang_code.upper(), 'flag': '🌍'})
            response += f"{lang_info_item['flag']} *{lang_info_item['name']}:*\n"
            response += f"   {translated_text}\n\n"

    response += "─" * 30 + "\n"
    response += "🤖 _WhatsApp Translation Bot_\n"
    response += "_Bridging Japanese-Indian Communication_"

    return response

@app.route('/test', methods=['POST'])
def test_translation():
    """Test endpoint for translation functionality"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        translations = translation_service.translate_message(text)
        return jsonify({
            "original": text,
            "translations": translations,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        translation_status = translation_service.client is not None
        whatsapp_status = whatsapp_handler.access_token is not None

        return jsonify({
            "status": "healthy" if translation_status and whatsapp_status else "degraded",
            "services": {
                "translation": "up" if translation_status else "down",
                "whatsapp": "up" if whatsapp_status else "down"
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting WhatsApp Translation Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)