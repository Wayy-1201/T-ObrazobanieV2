import os
from dotenv import load_dotenv
load_dotenv()

# --- API ключи ---
OPENROUTER_API_KEYS = [
    os.environ.get("OPENROUTER_KEY_1", ""),
    os.environ.get("OPENROUTER_KEY_2", ""),
    os.environ.get("OPENROUTER_KEY_3", ""),
]
OPENROUTER_API_KEYS = [k for k in OPENROUTER_API_KEYS if k]
OPENROUTER_API_KEY = OPENROUTER_API_KEYS[0] if OPENROUTER_API_KEYS else ""

# --- Основная модель ---
MODEL = "openai/gpt-oss-120b:free"

# --- БД ---
# На Render берётся из переменной окружения DB_PATH (persistent disk).
# Локально фолбэк на five_pigs.db рядом с кодом.
DB_PATH = os.environ.get("DB_PATH", "five_pigs.db")

# Сколько последних пар сообщений передавать в контекст
MAX_HISTORY_MESSAGES = 14
