import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]   # usato solo per Whisper (trascrizione vocale)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
SHOP_SECRET_KEY = os.getenv("SHOP_SECRET_KEY", "dev-secret-change-in-production")
ALLOWED_CHAT_ID = os.environ["ALLOWED_CHAT_ID"]

# Configurazione modello AI: "deepseek" | "lmstudio"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "qwen3.5-9b")
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
