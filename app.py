from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Set your token for webhook verification (should match Meta dashboard)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "verify123")

@app.route("/", methods=["GET"])
def home():
    return jsonify(message="WhatsApp Translation Bot is running!", status="active")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")
        logging.info(f"Verification attempt with token: {verify_token}")
        if verify_token == VERIFY_TOKEN and mode == "subscribe":
            logging.info("Webhook verified successfully.")
            return challenge, 200
        else:
            logging.error("Invalid verify token")
            return "Invalid verify token", 403
    elif request.method == "POST":
        import requests

        body = request.get_json()
        logging.info(f"Received POST request from WhatsApp: {body}")

        # Reply logic: auto-reply to received WhatsApp messages
        try:
            entry = body.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages")
            if messages:
                msg = messages[0]
                from_number = msg["from"]
                # Get your WhatsApp phone number ID from webhook payload
                phone_number_id = value["metadata"]["phone_number_id"]
                # Your WhatsApp API Token. Set as Render secret, .env, or paste here.
                access_token = os.getenv("WHATSAPP_TOKEN", "EAATE8aBlDFIBP3I9fDBoyBQKIXOW2A3r0EIcycRrBshA0bz7F8CbK18ngjutkVtaLTDXuZAZCZC0e9Mh2QcHZCH6U2YQZCjoYZAlMxhgXXRKfcmis22DylIhZB9HhatKyHVhuqdAuCywcWCiJQQjlk518hSCfMXbMJYuaIZB5OJ1ao7wDHso0ZAWvqahfQ0joWpj5hMOuQR1EZBWkhQb7M6kZCOOP5ZCc4Aju5xJ5YkZC0CQZABQ2L0vhHBMrzygb7hinyYmPDm0ZCQQt3BucwQFKLLdZAvlTaiO") # <<<< EDIT THIS LINE!

                # Reply message details
                url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                data = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "type": "text",
                    "text": {"body": "Hello! This is your WhatsApp bot."}
                }

                # Send automatic reply
                response = requests.post(url, headers=headers, json=data)
                logging.info(f"Sent reply: {response.text}")

        except Exception as e:
            logging.error(f"Error processing incoming message: {e}")

        return jsonify(status="received"), 200

@app.route("/health", methods=["GET"])
def healthcheck():
    from datetime import datetime
    return jsonify(status="healthy", timestamp=datetime.now().isoformat())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting WhatsApp Translation Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
