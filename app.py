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

from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def webhook():
    VERIFY_TOKEN = "my_secret_verify_token_12345"  # Make sure this matches Facebook Webhook page
    mode = request.args.get("hub.mode")
    challenge = request.args.get("hub.challenge")
    verify_token = request.args.get("hub.verify_token")

    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

# Your other bot logic and routes (POST chatbot handling) stay as they are!
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
app = Flask(__name__)

translation_service = None
whatsapp_handler = None
user_prefs = None

try:
    logger.info("Initializing Translation Service...")
    translation_service = TranslationService()
    logger.info("Translation Service initialized")
except Exception as e:
    logger.error(f"Failed to initialize TranslationService: {str(e)}")
    logger.error(f"Make sure GOOGLE_APPLICATION_CREDENTIALS_JSON env var is set!")

try:
    logger.info("Initializing WhatsApp Handler...")
    whatsapp_handler = WhatsAppHandler()
    logger.info("WhatsApp Handler initialized")
except Exception as e:
    logger.error(f"Failed to initialize WhatsAppHandler: {str(e)}")
    logger.error(f"Check WhatsApp environment variables!")

try:
    logger.info("Initializing User Preferences...")
    user_prefs = UserPreferences()
    logger.info("User Preferences initialized")
except Exception as e:
    logger.error(f"Failed to initialize UserPreferences: {str(e)}")

logger.info("==========================================================")
logger.info("ALL SERVICES INITIALIZED SUCCESSFULLY!")
logger.info("==========================================================")

processed_message_ids = set()
user_translation_cache = {}


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "WhatsApp Translation Bot is running!",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'GET':
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            logger.info("Webhook verification attempt")
            
            if verify_token == os.getenv('VERIFY_TOKEN'):
                logger.info("Webhook verified successfully")
                return challenge
            else:
                logger.error("Invalid verify token")
                return 'Invalid verify token', 403

        elif request.method == 'POST':
            body = request.get_json()
            logger.info("Received webhook POST request")
            response = process_message(body)
            return jsonify(response)

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


def process_message(webhook_data):
    try:
        if not webhook_data.get('entry'):
            return {"status": "no_entry"}
        
        if not whatsapp_handler or not user_prefs or not translation_service:
            logger.error("Services not initialized - cannot process message")
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
                        
                        if message_id in processed_message_ids:
                            logger.info(f"Skip processed: {message_id}")
                            continue
                        
                        processed_message_ids.add(message_id)
                        
                        if len(processed_message_ids) > 1000:
                            processed_message_ids.pop()
                        
                        if message_type != 'text':
                            logger.info(f"Skip non-text: {message_type}")
                            continue
                        
                        message_body = message.get('text', {}).get('body', '')
                        
                        if not message_body or not message_body.strip():
                            logger.info("Skip empty message")
                            continue
                        
                        logger.info(f"From {sender_id}: '{message_body}'")
                        
                        user_langs = user_prefs.get_user_languages(sender_id)
                        
                        if not user_langs:
                            logger.info(f"New user")
                            continue
                        
                        logger.info(f"User langs: {user_langs}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Process message error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error"}


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "translation": "OK" if translation_service else "FAILED",
            "whatsapp": "OK" if whatsapp_handler else "FAILED",
            "user_prefs": "OK" if user_prefs else "FAILED"
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting Bot on port {port}")
    logger.info("All systems ready!")
    app.run(host='0.0.0.0', port=port, debug=debug)
    
    
