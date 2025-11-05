from flask import Flask, request, jsonify
import os
import logging
import json
from dotenv import load_dotenv

# Import our custom modules
from whatsapp_handler import WhatsAppHandler
from translation_service import TranslationService
from user_preferences import UserPreferences
from config import Config

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize services
try:
    whatsapp_handler = WhatsAppHandler()
    translation_service = TranslationService()
    user_preferences = UserPreferences('user_prefs.json')
    logger.info("✅ All services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {e}")
    whatsapp_handler = None
    translation_service = None
    user_preferences = None

# Get verify token from environment or use default from config
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or Config.VERIFY_TOKEN
logger.info(f"🔐 Using VERIFY_TOKEN from environment")

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "WhatsApp Translation Bot is running!",
        "status": "active",
        "version": "2.0"
    }), 200

@app.route("/health", methods=["GET"])
def healthcheck():
    """Extended health check"""
    from datetime import datetime
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp_handler": whatsapp_handler is not None,
            "translation_service": translation_service is not None,
            "user_preferences": user_preferences is not None
        }
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Main webhook endpoint for WhatsApp messages
    GET: Webhook verification from Meta
    POST: Incoming messages/status updates
    """
    
    if request.method == "GET":
        return handle_webhook_verification()
    
    elif request.method == "POST":
        return handle_webhook_post()
    
    return jsonify({"error": "Invalid method"}), 405

def handle_webhook_verification():
    """Handle webhook verification GET request from Meta"""
    try:
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")
        
        logger.info(f"🔍 Webhook verification attempt - Mode: {mode}, Token: {verify_token[:10] if verify_token else 'None'}...")
        
        if mode == "subscribe" and verify_token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            logger.error(f"❌ Webhook verification failed - Mode: {mode}, Token match: {verify_token == VERIFY_TOKEN}")
            return "Invalid verify token", 403
    
    except Exception as e:
        logger.error(f"❌ Error during webhook verification: {e}")
        return jsonify({"error": str(e)}), 500

def handle_webhook_post():
    """Handle incoming messages and status updates from WhatsApp"""
    try:
        body = request.get_json()
        
        if not body:
            logger.warning("⚠️ Received empty JSON body")
            return jsonify({"status": "received"}), 200
        
        logger.info(f"📨 Received webhook POST: {json.dumps(body, indent=2)}")
        
        # Extract data from webhook payload
        try:
            entry = body.get("entry", [])
            if not entry:
                logger.warning("⚠️ No entry in webhook body")
                return jsonify({"status": "received"}), 200
            
            changes = entry[0].get("changes", [])
            if not changes:
                logger.warning("⚠️ No changes in entry")
                return jsonify({"status": "received"}), 200
            
            value = changes[0].get("value", {})
            
            # Handle incoming messages
            messages = value.get("messages", [])
            if messages:
                logger.info(f"📨 Processing {len(messages)} message(s)")
                for msg in messages:
                    process_incoming_message(msg, value)
            
            # Handle status updates (delivery receipts, read receipts, etc.)
            statuses = value.get("statuses", [])
            if statuses:
                logger.info(f"📊 Processing {len(statuses)} status update(s)")
                for status in statuses:
                    process_status_update(status)
            
            # Handle contacts (when WhatsApp provides contact info)
            contacts = value.get("contacts", [])
            if contacts:
                logger.info(f"👥 Processing {len(contacts)} contact(s)")
        
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"❌ Error parsing webhook payload: {e}")
            logger.error(f"   Payload structure: {json.dumps(body, indent=2)}")
            return jsonify({"status": "received"}), 200
        
        return jsonify({"status": "received"}), 200
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in handle_webhook_post: {e}")
        return jsonify({"error": str(e)}), 500

def process_incoming_message(msg, webhook_value):
    """
    Process incoming WhatsApp message
    Translate it to user's preferred languages and send responses
    """
    try:
        msg_id = msg.get("id")
        from_number = msg.get("from")
        timestamp = msg.get("timestamp")
        msg_type = msg.get("type", "text")
        
        logger.info(f"📱 Processing message from {from_number} (Type: {msg_type}, ID: {msg_id})")
        
        # Validate required fields
        if not from_number or not whatsapp_handler or not translation_service or not user_preferences:
            logger.error("❌ Missing required data or services")
            return False
        
        # Get message text based on type
        message_text = None
        if msg_type == "text":
            message_text = msg.get("text", {}).get("body", "")
        else:
            logger.info(f"⏭️ Skipping non-text message type: {msg_type}")
            return False
        
        if not message_text:
            logger.warning(f"⚠️ Empty message text from {from_number}")
            return False
        
        logger.info(f"💬 Message text: {message_text}")
        
        # Get user's language preferences
        user_langs = user_preferences.get_user_languages(from_number)
        
        if not user_langs:
            # User hasn't set preferences yet - send setup message
            logger.info(f"👤 User {from_number} has no language preferences set")
            send_language_selection_menu(from_number)
            return True
        
        logger.info(f"🌍 User {from_number} preferences: {user_langs}")
        
        # Process and send translations
        for target_lang in user_langs:
            try:
                # Translate message
                translated_text = translation_service.translate(
                    message_text,
                    target_language=target_lang,
                    source_language="en"
                )
                
                if translated_text:
                    logger.info(f"✅ Translated to {target_lang}: {translated_text}")
                    
                    # Send translated message
                    whatsapp_handler.send_message(
                        to=from_number,
                        message=f"🌐 *{target_lang.upper()}*:\n{translated_text}"
                    )
                else:
                    logger.warning(f"⚠️ Translation failed for {target_lang}")
                    whatsapp_handler.send_message(
                        to=from_number,
                        message=f"❌ Translation to {target_lang} failed. Please try again."
                    )
            
            except Exception as e:
                logger.error(f"❌ Error translating to {target_lang}: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error processing incoming message: {e}")
        return False

def process_status_update(status):
    """
    Process WhatsApp status updates (delivery, read, failed, etc.)
    """
    try:
        msg_id = status.get("id")
        to_number = status.get("recipient_id")
        status_type = status.get("status")
        timestamp = status.get("timestamp")
        
        logger.info(f"📊 Message {msg_id} status: {status_type} (to: {to_number})")
        
        # Log different status types
        if status_type == "delivered":
            logger.info(f"✅ Message {msg_id} delivered")
        elif status_type == "read":
            logger.info(f"👁️ Message {msg_id} read")
        elif status_type == "failed":
            logger.error(f"❌ Message {msg_id} failed to send")
            error = status.get("errors", [{}])[0]
            logger.error(f"   Error: {error}")
        elif status_type == "sent":
            logger.info(f"📤 Message {msg_id} sent")
    
    except Exception as e:
        logger.error(f"❌ Error processing status update: {e}")

def send_language_selection_menu(user_number):
    """Send initial language selection menu to new user"""
    try:
        logger.info(f"📋 Sending language selection menu to {user_number}")
        
        # Send initial greeting
        greeting = (
            "👋 Welcome to WhatsApp Translation Bot!\n\n"
            "I can translate your messages to multiple languages.\n\n"
            "Please reply with the language codes you'd like translations in:\n"
            "🇯🇵 ja (Japanese)\n"
            "🇮🇳 hi (Hindi)\n"
            "🇮🇳 te (Telugu)\n"
            "🇮🇳 ta (Tamil)\n"
            "🇮🇳 ml (Malayalam)\n"
            "🇮🇳 kn (Kannada)\n"
            "🇮🇳 mr (Marathi)\n"
            "🇮🇳 gu (Gujarati)\n"
            "🇮🇳 bn (Bengali)\n"
            "🇨🇳 zh-CN (Chinese)\n"
            "🇪🇬 ar (Arabic)\n"
            "\nExample reply: 'ja,hi,te' for Japanese, Hindi, and Telugu"
        )
        
        whatsapp_handler.send_message(user_number, greeting)
        logger.info(f"✅ Language menu sent to {user_number}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending language menu: {e}")
        return False

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"❌ Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Validate configuration
    if not Config.validate_config():
        logger.error("❌ Configuration validation failed. Please check your environment variables.")
    
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting WhatsApp Translation Bot on port {port}")
    logger.info(f"📱 Webhook URL: https://your-render-url/webhook")
    logger.info(f"🔐 Verify Token: {VERIFY_TOKEN[:10]}...")
    
    # Run the app
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,  # Set to False in production
        use_reloader=False
    )