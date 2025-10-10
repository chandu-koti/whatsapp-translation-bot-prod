# WhatsApp Translation Bot

🌐 A real-time translation bot that bridges communication between Japanese business travelers and Indian local personnel via WhatsApp.

## Features

- **Multi-language Support**: Japanese (日本語), Hindi (हिन्दी), Telugu (తెలుగు), and English
- **Real-time Translation**: Automatic language detection and translation
- **WhatsApp Integration**: Works directly within WhatsApp conversations
- **Production Ready**: Complete error handling, logging, and monitoring

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd whatsapp_translation_bot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Credentials**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Run the Bot**
   ```bash
   python run_bot.py
   ```

## API Setup

### Google Cloud Translation
1. Create project at https://console.cloud.google.com/
2. Enable Translation API
3. Create service account with "Translation API User" role
4. Download JSON key as `service-account-key.json`

### WhatsApp Business API
1. Create app at https://developers.facebook.com/
2. Add WhatsApp product
3. Get access token, phone number ID, and test number

## Usage Example

**Input**: "空港まで行ってください" (Please take me to the airport)

**Bot Response**:
```
🌐 Translation Service
==============================

📝 Original: 空港まで行ってください

🇮🇳 Hindi: कृपया मुझे हवाई अड्डे पर ले जाएं
🇮🇳 Telugu: దయచేసి నన్ను విమానాశ్రయానికి తీసుకెళ్లండి  
🇺🇸 English: Please take me to the airport

🤖 WhatsApp Translation Bot
```

## Deployment

### Heroku
```bash
heroku create your-app-name
heroku config:set WHATSAPP_ACCESS_TOKEN=your_token
# ... set other env vars
git push heroku main
```

### Local Development with ngrok
```bash
ngrok http 5000
# Use the HTTPS URL for webhook in Meta Developer Console
```

## Project Structure

```
whatsapp_translation_bot/
├── app.py                    # Main Flask application
├── translation_service.py    # Google Cloud Translation service  
├── whatsapp_handler.py      # WhatsApp Business API handler
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── run_bot.py              # Easy startup script
├── Procfile                # Heroku deployment
└── README.md               # This file
```

## Support

For issues and questions, please check:
1. Logs for specific error messages
2. API credentials are correctly configured
3. Webhook URL is properly set in Meta Developer Console

---
Built to enable seamless communication between Japanese business travelers and Indian local personnel.