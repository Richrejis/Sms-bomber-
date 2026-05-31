import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-to-a-random-secret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bomber.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SMS Gateway configs
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
    
    TEXTLBOT_API_KEY = os.getenv('TEXTLBOT_API_KEY', '')
    
    # Call configs
    TWILIO_VOICE_URL = os.getenv('TWILIO_VOICE_URL', '')
    
    # Rate limiting defaults
    DEFAULT_DELAY_SECONDS = 2
    MAX_BURST = 100
