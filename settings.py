import os
from pathlib import Path

# Load environment variables from .env if present
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env located at project root
load_dotenv(dotenv_path=BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_TTL_SECONDS = 300
