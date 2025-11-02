import os
from dotenv import load_dotenv

load_dotenv()

MARZBAN_API_URL = os.getenv("MARZBAN_API_URL")
MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME")
MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")