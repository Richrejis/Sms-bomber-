import requests
import logging
from twilio.rest import Client
from config import Config

logger = logging.getLogger(__name__)

class SMSBomber:
    def __init__(self):
        self.services = []
        self._init_services()
    
    def _init_services(self):
        """Initialize available SMS gateways"""
        self.services = []
        
        # Twilio (if configured)
        if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            self.services.append({
                'name': 'twilio',
                'func': self._send_via_twilio
            })
        
        # Textbelt (if configured)
        if Config.TEXTLBOT_API_KEY:
            self.services.append({
                'name': 'textbelt',
                'func': self._send_via_textbelt
            })
        
        # Public free SMS gateways (rate-limited, no API key needed)
        self.services.append({
            'name': 'free-gateway-1',
            'func': self._send_via_fast2sms
        })
    
    def _send_via_twilio(self, number, message):
        """Send via Twilio API"""
        try:
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                body=message,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=number
            )
            return {'success': True, 'sid': msg.sid, 'service': 'twilio'}
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            return {'success': False, 'error': str(e), 'service': 'twilio'}
    
    def _send_via_textbelt(self, number, message):
        """Send via Textbelt API"""
        try:
            resp = requests.post('https://textbelt.com/text', {
                'phone': number,
                'message': message,
                'key': Config.TEXTLBOT_API_KEY
            }, timeout=10)
            data = resp.json()
            return {'success': data.get('success', False), 'service': 'textbelt'}
        except Exception as e:
            logger.error(f"Textbelt error: {e}")
            return {'success': False, 'error': str(e), 'service': 'textbelt'}
    
    def _send_via_fast2sms(self, number, message):
        """Send via free public gateway"""
        # This is a placeholder — replace with actual free SMS API if available
        # In real deployment, you'd use a legitimate provider
        return {'success': False, 'error': 'No free gateway configured', 'service': 'free-gateway'}
    
    def send(self, number, message, service='all'):
        """Send SMS via specified service(s)"""
        results = []
        
        if service == 'all':
            for svc in self.services:
                results.append(svc['func'](number, message))
        else:
            for svc in self.services:
                if svc['name'] == service:
                    results.append(svc['func'](number, message))
                    break
        
        return results
    
    def get_available_services(self):
        """Return list of active SMS services"""
        return [s['name'] for s in self.services]
