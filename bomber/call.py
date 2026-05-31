import requests
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from config import Config

logger = logging.getLogger(__name__)

class CallBomber:
    def __init__(self):
        self.services = []
        self._init_services()
    
    def _init_services(self):
        self.services = []
        
        if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            self.services.append({
                'name': 'twilio',
                'func': self._call_via_twilio
            })
        
        # Add more call providers here as needed
    
    def _call_via_twilio(self, number, message=None):
        """Initiate a call via Twilio"""
        try:
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            
            # Create TwiML for the call
            response = VoiceResponse()
            if message:
                response.say(message, voice='alice')
            else:
                # Play a tone/silence for "bombing" effect
                response.play(digits='wwwwwwwwww')
            
            call = client.calls.create(
                twiml=str(response),
                to=number,
                from_=Config.TWILIO_PHONE_NUMBER
            )
            return {'success': True, 'sid': call.sid, 'service': 'twilio'}
        except Exception as e:
            logger.error(f"Twilio call error: {e}")
            return {'success': False, 'error': str(e), 'service': 'twilio'}
    
    def call(self, number, message=None, service='all'):
        """Initiate call via specified service(s)"""
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
        return [s['name'] for s in self.services]
