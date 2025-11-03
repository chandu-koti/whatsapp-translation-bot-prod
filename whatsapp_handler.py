import os
import requests
import json
import logging
from typing import Optional, List, Dict
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
        self.media_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/media"
        
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
            logger.info("✅ WhatsApp credentials validated")
    
    def send_message(self, to: str, message: str) -> bool:
        """Send a text message"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to {to}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error sending message: {str(e)}")
            return False
    
    def send_interactive_buttons(self, to: str, body_text: str, buttons: List[Dict]) -> bool:
        """
        Send interactive reply buttons
        
        Args:
            to: Recipient phone number
            body_text: Main message text
            buttons: List of button dicts with 'id' and 'title'
                     Max 3 buttons, title max 20 chars
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Format buttons for WhatsApp API
        formatted_buttons = []
        for btn in buttons[:3]:  # Max 3 buttons
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn['id'],
                    "title": btn['title'][:20]  # Max 20 chars
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Interactive buttons sent to {to}")
                return True
            else:
                logger.error(f"❌ Failed to send buttons: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error sending buttons: {str(e)}")
            return False
    
    def send_interactive_list(self, to: str, body_text: str, button_text: str, sections: List[Dict]) -> bool:
        """
        Send interactive list message
        
        Args:
            to: Recipient phone number
            body_text: Main message text
            button_text: Text on the list button
            sections: List of section dicts with 'title' and 'rows'
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": body_text
                },
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Interactive list sent to {to}")
                return True
            else:
                logger.error(f"❌ Failed to send list: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error sending list: {str(e)}")
            return False
    
    def upload_media(self, file_path: str) -> Optional[str]:
        """Upload media file and return media ID"""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'audio/mpeg'),
                    'messaging_product': (None, 'whatsapp'),
                    'type': (None, 'audio/mpeg')
                }
                
                response = requests.post(self.media_url, headers=headers, files=files)
                
                if response.status_code == 200:
                    media_id = response.json().get('id')
                    logger.info(f"✅ Media uploaded successfully: {media_id}")
                    return media_id
                else:
                    logger.error(f"❌ Failed to upload media: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"❌ Error uploading media: {str(e)}")
            return None
    
    def send_voice_message(self, to: str, media_id: str) -> bool:
        """Send voice message using media ID"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": {
                "id": media_id
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Voice message sent to {to}")
                return True
            else:
                logger.error(f"❌ Failed to send voice: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error sending voice: {str(e)}")
            return False