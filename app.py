from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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
        body = request.get_json()
        logging.info(f"Received POST request from WhatsApp: {body}")
        return jsonify(status="received"), 200

@app.route("/health", methods=["GET"])
def healthcheck():
    from datetime import datetime
    return jsonify(status="healthy", timestamp=datetime.now().isoformat())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting WhatsApp Translation Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
