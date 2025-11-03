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
    logger.info("✅ Services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {str(e)}")

# CRITICAL: Track processed message IDs to prevent infinite loops
processed_message_ids = set()
# Store translations temporarily for audio playback
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


def send_asian_languages(sender_id: str):
    """Send Asian language selection"""
    body_text = """📱 *ASIAN LANGUAGES*
━━━━━━━━━━━━━━━━━━━━

Select languages to add:"""
    
    sections = [
        {
            "title": "East Asia",
            "rows": [
                {"id": "add_ja", "title": "🇯🇵 Japanese", "description": "日本語"},
                {"id": "add_zh-CN", "title": "🇨🇳 Chinese (Simplified)", "description": "简体中文"},
                {"id": "add_zh-TW", "title": "🇹🇼 Chinese (Traditional)", "description": "繁體中文"},
                {"id": "add_ko", "title": "🇰🇷 Korean", "description": "한국어"}
            ]
        },
        {
            "title": "Southeast Asia",
            "rows": [
                {"id": "add_th", "title": "🇹🇭 Thai", "description": "ไทย"},
                {"id": "add_vi", "title": "🇻🇳 Vietnamese", "description": "Tiếng Việt"},
                {"id": "add_id", "title": "🇮🇩 Indonesian", "description": "Bahasa Indonesia"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "menu_categories", "title": "⬅️ Back", "description": "Return to categories"},
                {"id": "done_selecting", "title": "✅ Done", "description": "Finish"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Select Language", sections)


def send_indian_languages(sender_id: str):
    """Send Indian language selection"""
    body_text = """🇮🇳 *INDIAN LANGUAGES*
━━━━━━━━━━━━━━━━━━━━

Select languages to add:"""
    
    sections = [
        {
            "title": "Indian Languages",
            "rows": [
                {"id": "add_hi", "title": "🇮🇳 Hindi", "description": "हिन्दी"},
                {"id": "add_te", "title": "🇮🇳 Telugu", "description": "తెలుగు"},
                {"id": "add_ta", "title": "🇮🇳 Tamil", "description": "தமிழ்"},
                {"id": "add_bn", "title": "🇮🇳 Bengali", "description": "বাংলা"},
                {"id": "add_mr", "title": "🇮🇳 Marathi", "description": "मराठी"},
                {"id": "add_gu", "title": "🇮🇳 Gujarati", "description": "ગુજરાતી"},
                {"id": "add_kn", "title": "🇮🇳 Kannada", "description": "ಕನ್ನಡ"},
                {"id": "add_ml", "title": "🇮🇳 Malayalam", "description": "മലയാളം"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "menu_categories", "title": "⬅️ Back", "description": "Return"},
                {"id": "done_selecting", "title": "✅ Done", "description": "Finish"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Select Language", sections)


def send_european_languages(sender_id: str):
    """Send European language selection - PAGE 1 (MAX 10 ROWS)"""
    body_text = """🌍 *EUROPEAN LANGUAGES (Page 1)*
━━━━━━━━━━━━━━━━━━━━

Select languages to add:"""
    
    sections = [
        {
            "title": "European Languages",
            "rows": [
                {"id": "add_en", "title": "🇬🇧 English", "description": "English"},
                {"id": "add_de", "title": "🇩🇪 German", "description": "Deutsch"},
                {"id": "add_es", "title": "🇪🇸 Spanish", "description": "Español"},
                {"id": "add_fr", "title": "🇫🇷 French", "description": "Français"},
                {"id": "add_it", "title": "🇮🇹 Italian", "description": "Italiano"},
                {"id": "add_pt", "title": "🇵🇹 Portuguese", "description": "Português"},
                {"id": "add_ru", "title": "🇷🇺 Russian", "description": "Русский"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "cat_european_2", "title": "➡️ More European", "description": "See more languages"},
                {"id": "menu_categories", "title": "⬅️ Back", "description": "Return"},
                {"id": "done_selecting", "title": "✅ Done", "description": "Finish"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Select Language", sections)


def send_european_languages_page2(sender_id: str):
    """Send European language selection - PAGE 2"""
    body_text = """🌍 *EUROPEAN LANGUAGES (Page 2)*
━━━━━━━━━━━━━━━━━━━━

Select more languages:"""
    
    sections = [
        {
            "title": "More European",
            "rows": [
                {"id": "add_nl", "title": "🇳🇱 Dutch", "description": "Nederlands"},
                {"id": "add_pl", "title": "🇵🇱 Polish", "description": "Polski"},
                {"id": "add_tr", "title": "🇹🇷 Turkish", "description": "Türkçe"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "cat_european", "title": "⬅️ Page 1", "description": "Go back to page 1"},
                {"id": "menu_categories", "title": "⬅️ Categories", "description": "Main menu"},
                {"id": "done_selecting", "title": "✅ Done", "description": "Finish"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Select Language", sections)


def send_other_languages(sender_id: str):
    """Send other languages selection"""
    body_text = """🌎 *OTHER LANGUAGES*
━━━━━━━━━━━━━━━━━━━━

Select languages to add:"""
    
    sections = [
        {
            "title": "Other Languages",
            "rows": [
                {"id": "add_ar", "title": "🇸🇦 Arabic", "description": "العربية"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "menu_categories", "title": "⬅️ Back", "description": "Return"},
                {"id": "done_selecting", "title": "✅ Done", "description": "Finish"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Select Language", sections)


def send_quick_setup(sender_id: str):
    """Send quick setup presets"""
    body_text = """⚡ *QUICK SETUP*
━━━━━━━━━━━━━━━━━━━━

Choose a preset:"""
    
    sections = [
        {
            "title": "Quick Combinations",
            "rows": [
                {"id": "preset_japan", "title": "🇯🇵 Japan Travel", "description": "Japanese + English"},
                {"id": "preset_india", "title": "🇮🇳 India Full", "description": "Hindi + Telugu + Tamil + English"},
                {"id": "preset_asia", "title": "🌏 East Asia", "description": "Japanese + Chinese + Korean"},
                {"id": "preset_europe", "title": "🌍 Europe", "description": "German + French + Spanish"},
                {"id": "preset_default", "title": "🎯 Default", "description": "Japanese + Hindi + Telugu"}
            ]
        },
        {
            "title": "Navigation",
            "rows": [
                {"id": "menu_categories", "title": "⬅️ Custom", "description": "Choose manually"}
            ]
        }
    ]
    
    whatsapp_handler.send_interactive_list(sender_id, body_text, "Choose Preset", sections)


def show_selected_languages(sender_id: str):
    """Show currently selected languages"""
    user_langs = user_prefs.get_user_languages(sender_id)
    
    if not user_langs:
        lang_list = "None selected yet"
    else:
        lang_names = []
        for lang_code in user_langs:
            lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
            flag = lang_info.get('flag', '🌍')
            name = lang_info.get('name', lang_code)
            lang_names.append(f"{flag} {name}")
        lang_list = "\n".join(lang_names)
    
    body_text = f"""✅ *YOUR LANGUAGES*
━━━━━━━━━━━━━━━━━━━━

{lang_list}

What next?"""
    
    buttons = [
        {"id": "menu_categories", "title": "➕ Add More"},
        {"id": "clear_all", "title": "❌ Clear All"},
        {"id": "done_selecting", "title": "✅ Start"}
    ]
    
    whatsapp_handler.send_interactive_buttons(sender_id, body_text, buttons)


def handle_button_response(sender_id: str, button_id: str):
    """Handle button/list responses"""
    logger.info(f"🎯 Button: {button_id} by {sender_id}")
    
    # Navigation
    if button_id == "menu_categories":
        send_category_menu(sender_id)
    elif button_id == "menu_quick":
        send_quick_setup(sender_id)
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
    elif button_id == "cat_asian":
        send_asian_languages(sender_id)
    elif button_id == "cat_indian":
        send_indian_languages(sender_id)
    elif button_id == "cat_european":
        send_european_languages(sender_id)
    elif button_id == "cat_european_2":
        send_european_languages_page2(sender_id)
    elif button_id == "cat_other":
        send_other_languages(sender_id)
    elif button_id == "view_selected":
        show_selected_languages(sender_id)
    
    # Add language
    elif button_id.startswith("add_"):
        lang_code = button_id.replace("add_", "")
        current_langs = user_prefs.get_user_languages(sender_id)
        if lang_code not in current_langs:
            current_langs.append(lang_code)
            user_prefs.set_user_languages(sender_id, current_langs)
            lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
            lang_name = f"{lang_info.get('flag', '🌍')} {lang_info.get('name', lang_code)}"
            whatsapp_handler.send_message(sender_id, f"✅ Added {lang_name}!")
        else:
            whatsapp_handler.send_message(sender_id, f"ℹ️ Already added!")
        
        buttons = [
            {"id": "menu_categories", "title": "➕ Add More"},
            {"id": "view_selected", "title": "👀 View"},
            {"id": "done_selecting", "title": "✅ Done"}
        ]
        whatsapp_handler.send_interactive_buttons(sender_id, "What next?", buttons)
    
    # Presets
    elif button_id == "preset_japan":
        user_prefs.set_user_languages(sender_id, ['ja', 'en'])
        whatsapp_handler.send_message(sender_id, "✅ Japan Travel!\n🇯🇵 Japanese + 🇬🇧 English")
        send_done_message(sender_id)
    elif button_id == "preset_india":
        user_prefs.set_user_languages(sender_id, ['hi', 'te', 'ta', 'en'])
        whatsapp_handler.send_message(sender_id, "✅ India Full!\n🇮🇳 Hindi + Telugu + Tamil + English")
        send_done_message(sender_id)
    elif button_id == "preset_asia":
        user_prefs.set_user_languages(sender_id, ['ja', 'zh-CN', 'ko'])
        whatsapp_handler.send_message(sender_id, "✅ East Asia!\n🇯🇵 Japanese + 🇨🇳 Chinese + 🇰🇷 Korean")
        send_done_message(sender_id)
    elif button_id == "preset_europe":
        user_prefs.set_user_languages(sender_id, ['de', 'fr', 'es'])
        whatsapp_handler.send_message(sender_id, "✅ Europe!\n🇩🇪 German + 🇫🇷 French + 🇪🇸 Spanish")
        send_done_message(sender_id)
    elif button_id == "preset_default":
        user_prefs.set_user_languages(sender_id, ['ja', 'hi', 'te'])
        whatsapp_handler.send_message(sender_id, "✅ Default!\n🇯🇵 Japanese + 🇮🇳 Hindi + Telugu")
        send_done_message(sender_id)
    
    # Clear
    elif button_id == "clear_all":
        user_prefs.set_user_languages(sender_id, [])
        whatsapp_handler.send_message(sender_id, "🗑️ Cleared!")
        send_welcome_menu(sender_id)
    
    # Done
    elif button_id == "done_selecting":
        send_done_message(sender_id)
    
    # Settings
    elif button_id == "settings_menu":
        send_category_menu(sender_id)
    
    # AUDIO PLAYBACK BUTTONS
    elif button_id.startswith("play_audio_"):
        lang_code = button_id.replace("play_audio_", "")
        play_audio_for_language(sender_id, lang_code)


def send_done_message(sender_id: str):
    """Send confirmation"""
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


def play_audio_for_language(sender_id: str, lang_code: str):
    """Play audio for specific language"""
    # Get cached translation
    if sender_id not in user_translation_cache or lang_code not in user_translation_cache[sender_id]:
        whatsapp_handler.send_message(sender_id, "⚠️ Audio expired. Please translate again.")
        return
    
    translated_text = user_translation_cache[sender_id][lang_code]
    lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
    tts_code = lang_info.get('tts')
    lang_name = f"{lang_info.get('flag', '🌍')} {lang_info.get('name', lang_code)}"
    
    if not tts_code:
        whatsapp_handler.send_message(sender_id, f"⚠️ Audio not available for {lang_name}")
        return
    
    try:
        # Send "Playing" message
        whatsapp_handler.send_message(sender_id, f"▶️ Playing: {lang_name}")
        
        # Generate voice
        voice_filename = f"voice_{lang_code}_{sender_id}_{datetime.now().timestamp()}.mp3"
        voice_file = translation_service.text_to_speech(
            text=translated_text,
            filename=voice_filename,
            lang_code=tts_code
        )
        
        if voice_file and os.path.exists(voice_file):
            media_id = whatsapp_handler.upload_media(voice_file)
            if media_id:
                whatsapp_handler.send_voice_message(sender_id, media_id)
                logger.info(f"✅ Played audio: {lang_name}")
            
            if os.path.exists(voice_file):
                os.remove(voice_file)
    
    except Exception as e:
        logger.error(f"❌ Audio error {lang_code}: {str(e)}")
        whatsapp_handler.send_message(sender_id, f"❌ Failed to play audio")


def process_message(webhook_data):
    """Process incoming WhatsApp messages - 100% LOOP FREE WITH STRICTEST PROTECTION"""
    try:
        if not webhook_data.get('entry'):
            return {"status": "no_entry"}
        
        for entry in webhook_data['entry']:
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    value = change.get('value', {})
                    
                    # LOOP PROTECTION 1: Skip if no messages
                    if 'messages' not in value:
                        continue
                    
                    messages = value.get('messages', [])
                    
                    for message in messages:
                        message_id = message.get('id')
                        message_type = message.get('type')
                        sender_id = message.get('from')
                        
                        # LOOP PROTECTION 2: Skip if already processed
                        if message_id in processed_message_ids:
                            logger.info(f"⏭️ Skip processed: {message_id}")
                            continue
                        
                        # Add to processed immediately
                        processed_message_ids.add(message_id)
                        
                        # LOOP PROTECTION 3: Clean up (keep last 1000)
                        if len(processed_message_ids) > 1000:
                            processed_message_ids.pop()
                        
                        # LOOP PROTECTION 4: Skip bot's own messages
                        bot_phone = os.getenv('WHATSAPP_BOT_PHONE_NUMBER', '').replace('+', '').replace('-', '').replace(' ', '')
                        sender_phone = sender_id.replace('+', '').replace('-', '').replace(' ', '')
                        
                        if bot_phone and sender_phone == bot_phone:
                            logger.info(f"⏭️ Skip bot message")
                            continue
                        
                        # LOOP PROTECTION 5: Skip status/system messages
                        if message_type in ['status', 'reaction', 'delivery', 'read', 'system']:
                            logger.info(f"⏭️ Skip status: {message_type}")
                            continue
                        
                        # LOOP PROTECTION 6: Skip if message timestamp is old (older than 5 minutes)
                        message_timestamp = message.get('timestamp', 0)
                        current_timestamp = int(datetime.now().timestamp())
                        if message_timestamp and (current_timestamp - int(message_timestamp)) > 300:
                            logger.info(f"⏭️ Skip old message (>5min)")
                            continue
                        
                        logger.info(f"📋 Process {message_type} from {sender_id}")
                        
                        # Handle interactive
                        if message_type == 'interactive':
                            interactive = message.get('interactive', {})
                            
                            if interactive.get('type') == 'button_reply':
                                button_id = interactive.get('button_reply', {}).get('id')
                                handle_button_response(sender_id, button_id)
                            elif interactive.get('type') == 'list_reply':
                                button_id = interactive.get('list_reply', {}).get('id')
                                handle_button_response(sender_id, button_id)
                            
                            continue
                        
                        # Handle text
                        if message_type != 'text':
                            logger.info(f"⏭️ Skip non-text")
                            continue
                        
                        message_body = message.get('text', {}).get('body', '')
                        
                        # LOOP PROTECTION 7: Skip empty messages
                        if not message_body or not message_body.strip():
                            logger.info("⏭️ Skip empty")
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
                        translations = translation_service.translate_message(message_body, target_languages=user_langs)
                        
                        if translations:
                            # Cache translations for audio playback
                            user_translation_cache[sender_id] = translations
                            
                            # Send text with audio buttons
                            formatted_response = format_translation_with_audio_buttons(message_body, translations, sender_id)
                            success = whatsapp_handler.send_message(sender_id, formatted_response)
                            
                            if success:
                                logger.info("✅ Translation sent")
                                
                                # Send audio buttons
                                send_audio_buttons(sender_id, list(translations.keys()))
                                
                                # Settings button
                                time.sleep(0.5)
                                settings_text = "━━━━━━━━━━━━━━━━━━━━\n💡 Change languages?"
                                buttons = [{"id": "settings_menu", "title": "⚙️ Settings"}]
                                whatsapp_handler.send_interactive_buttons(sender_id, settings_text, buttons)
                            else:
                                logger.error("❌ Failed send")
                        else:
                            logger.warning("⚠️ No translations")
                            whatsapp_handler.send_message(sender_id, "Sorry, couldn't translate.")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error"}


def format_translation_with_audio_buttons(original_text, translations, sender_id):
    """Format translation response"""
    response = "🌐 *Translation Service*\n"
    response += "=" * 30 + "\n\n"
    response += f"📝 *Original:* {original_text}\n\n"
    
    for lang_code, translated_text in translations.items():
        if translated_text and translated_text.strip() != original_text.strip():
            lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
            response += f"{lang_info.get('flag', '🌍')} *{lang_info.get('name', lang_code)}:*\n"
            response += f"  {translated_text}\n\n"
    
    response += "=" * 30 + "\n"
    response += "🔊 _Tap buttons below for audio!_"
    
    return response


def send_audio_buttons(sender_id: str, lang_codes: list):
    """Send interactive audio playback buttons"""
    if not lang_codes:
        return
    
    # WhatsApp allows max 3 buttons, so send in batches
    max_buttons = 3
    
    for i in range(0, len(lang_codes), max_buttons):
        batch = lang_codes[i:i+max_buttons]
        buttons = []
        
        for lang_code in batch:
            lang_info = Config.SUPPORTED_LANGUAGES.get(lang_code, {})
            button_text = f"▶️ {lang_info.get('flag', '🌍')} {lang_info.get('name', lang_code)}"
            if len(button_text) > 20:
                button_text = f"▶️ {lang_info.get('flag', '🌍')} {lang_info.get('name', lang_code)[:15]}"
            
            buttons.append({
                "id": f"play_audio_{lang_code}",
                "title": button_text[:20]
            })
        
        body_text = "🎵 *SELECT AUDIO:*" if i == 0 else "🎵 *MORE AUDIO:*"
        whatsapp_handler.send_interactive_buttons(sender_id, body_text, buttons)
        time.sleep(0.3)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Bot - ON-DEMAND AUDIO + 100% LOOP FREE + MAX 10 ROWS FIX!")
    app.run(host='0.0.0.0', port=port, debug=True)