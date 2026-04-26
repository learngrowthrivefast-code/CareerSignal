# core/auth.py
import bcrypt
import jwt
from datetime import datetime, timedelta
from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HRS

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, email: str, tier: str) -> str:
    payload = {
        "user_id": user_id,
        "email":   email,
        "tier":    tier,
        "exp":     datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HRS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict | None:
    """Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def require_login(session_state) -> dict | None:
    """
    Call at top of every page.
    Returns user payload or None (caller should st.stop() if None).
    """
    token = session_state.get("token")
    if not token:
        return None
    return decode_token(token)
