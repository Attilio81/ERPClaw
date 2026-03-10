import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]   # usato solo per Whisper (trascrizione vocale)
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
SHOP_SECRET_KEY = os.getenv("SHOP_SECRET_KEY", "dev-secret-change-in-production")
