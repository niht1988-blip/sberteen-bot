import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "sberteen2026")
ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

DB_PATH = os.getenv("DB_PATH", "sberteen.db")

# Стилистика проекта
COLORS = {
    "header": "🟡",
    "online": "🔵",
    "offline": "🟡",
    "approved": "✅",
    "pending": "⏳",
    "rejected": "❌",
    "coin": "💰",
}
