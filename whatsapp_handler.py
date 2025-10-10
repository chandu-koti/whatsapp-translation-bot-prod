import os
import requests
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    def __init__(self):
        """Initialize WhatsApp Business API handler"""
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.bot_phone_number = os.getenv('WHATSAPP_BOT_PHONE_NUMBER')

        # WhatsApp API endpoint
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"

        # Validate credentials
        self._validate_credentials()

    def _validate_credentials(self):
        """Validate WhatsApp API credentials"""
        missing_credentials = []

        if not self.access_token:
            missing_credentials.append('WHATSAPP_ACCESS_TOKEN')

        if not self.phone_number_id:
            missing_credentials.append('WHATSAPP_PHONE_NUMBER_ID')

        if not self.bot_phone_number:
            missing_credentials.append('WHATSAPP_BOT_PHONE_NUMBER')

        if missing_credentials:
            logger.error(f"❌ Missing WhatsApp credentials: {', '.join(missing_credentials)}")
        else:
            logger.info("✅ WhatsApp credentials validated successfully")
            logger.info(f"📱 Bot phone number: {self.bot_phone_number}")

    def send_message(self, to_number: str, message: str) -> bool:
        """Send text message via WhatsApp Business API"""
        if not self._check_credentials():
            return False

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }

        try:
            logger.info(f"📤 Sending message to {to_number}")

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                logger.info(f"✅ Message sent successfully, ID: {message_id}")
                return True
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"❌ Failed to send message: {response.status_code} - {error_message}")
                return False

        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout while sending message")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error while sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error while sending message: {str(e)}")
            return False

    def _check_credentials(self) -> bool:
        """Check if all required credentials are available"""
        if not self.access_token or not self.phone_number_id:
            logger.error("❌ WhatsApp credentials not configured properly")
            return False
        return True

    def is_healthy(self) -> bool:
        """Check if WhatsApp handler is healthy"""
        return self._check_credentials()