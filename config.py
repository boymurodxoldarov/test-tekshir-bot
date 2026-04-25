import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL: str = os.getenv("DATABASE_URL", "test_bot.db")

RATE_LIMIT_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_ATTEMPTS", "5"))
RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
