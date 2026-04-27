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

# Target roles — grouped by career stage
# Fresh Builder (20-35): Senior IC track
TARGET_ROLES_SENIOR_IC = [
    "Senior Software Engineer",
    "Senior ML Engineer",
    "Senior Data Scientist",
    "Staff Engineer",
    "Technical Lead",
    "Principal Engineer",
    "Senior AI / ML Engineer",
]

# Bridge Builder (35-50): Leadership track
TARGET_ROLES_LEADERSHIP = [
    "Engineering Manager",
    "Senior Manager of Engineering",
    "Solutions Architect",
    "Principal AI Engineer",
    "Head of Data Science",
    "Head of AI / ML",
    "Senior Manager, AI Platform",
]

# Navigator (50+): Executive track
TARGET_ROLES_EXECUTIVE = [
    "Director of AI",
    "Director of Engineering",
    "Director of AI Strategy",
    "Director of AI Programs",
    "Director of AI Governance",
    "VP of AI",
    "VP of Engineering (AI)",
    "VP of Engineering",
    "SVP of Engineering",
    "SVP of Technology",
    "CTO / Chief AI Officer",
    "Chief Data Officer",
]

TARGET_ROLES = TARGET_ROLES_SENIOR_IC + TARGET_ROLES_LEADERSHIP + TARGET_ROLES_EXECUTIVE
