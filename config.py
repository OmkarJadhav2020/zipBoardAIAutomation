import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://help.zipboard.co"
DB_NAME = "ai_automation.db"
# Rate limit: 2 requests per second = 0.5s interval
REQUEST_INTERVAL = 0.5 
AI_API_KEY = os.getenv("AI_API_KEY")
