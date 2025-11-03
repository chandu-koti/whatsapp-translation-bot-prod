from flask import Flask, request, jsonify
from whatsapp_handler import WhatsAppHandler  # Import your handler

app = Flask(__name__)

VERIFY_TOKEN = "my_secret_verify_token_12345"
whatsapp_handler = WhatsAppHandler()  # Initialize your handler

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Verification GET request (from Facebook/WhatsApp)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        challenge = request.args.get('hub.challenge')
        verify_token = request.args.get('hub.verify_token')
        if mode == 'subscribe' and verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    # Incoming message POST request (from WhatsApp)
    if request.method == 'POST':
        data = request.get_json()
        # Facebook sends entry->changes->value->messages for each incoming message
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for message in messages:
                        sender_id = message['from']
                        msg_body = message.get('text', {}).get('body', '')
                        # Actual reply logic: send reply back to WhatsApp
                        reply_text = "Hello from your WhatsApp bot!"  # Replace with your actual logic
                        whatsapp_handler.send_message(sender_id, reply_text)
        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
