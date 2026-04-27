# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = "claude-haiku-4-5-20251001"  # Cheapest, fastest

# Auth
JWT_SECRET      = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM   = "HS256"
JWT_EXPIRY_HRS  = 24

# Data paths — /data in production (Fly.io volume), ./data locally
APP_ENV     = os.getenv("APP_ENV", "development")
DATA_DIR    = "/data" if APP_ENV == "production" else "./data"
CHROMA_PATH = os.path.join(DATA_DIR, "chromadb")
SQLITE_PATH = os.path.join(DATA_DIR, "users.db")

# Tiers
FREE_SESSION_LIMIT    = 50   # messages per month
PREMIUM_MONTHLY_PRICE = 49   # USD

# Coaching config
MEMORY_CONTEXT_K = 3    # how many past turns to retrieve
MAX_TOKENS       = 800  # per Haiku response

# Cohorts
COHORTS = {
    "FreshGraduate":     "Age 20–35 · Fresh Builder",
    "AgeAbove35Less50":  "Age 35–50 · Bridge Builder",
    "AgeAbove50":        "Age 50+  · Navigator",
}

# Target roles
TARGET_ROLES = [
    "Director of AI",
    "VP of AI",
    "Director of AI Strategy",
    "Director of AI Programs",
    "Head of AI / ML",
    "Director of AI Governance",
    "VP of Engineering (AI)",
]
