"""
Enterprise Security Module for Hypernet Dashboard.
Provides Bcrypt Password Hashing, JWT Token Generation & Verification, and Session Expiry.
"""
import os
import uuid
import datetime
import bcrypt
import jwt
from typing import Optional, Dict, Any

# JWT Configuration
JWT_SECRET = os.getenv("DASHBOARD_JWT_SECRET", "hypernet-corp-enterprise-ai-secret-key-2026-secure-jwt-token")
JWT_ALGORITHM = "HS256"
DEFAULT_SESSION_DURATION_MINUTES = 60  # 1 Hour


def hash_password(plain_password: str) -> str:
    """Hash a password securely using bcrypt with auto salt."""
    if isinstance(plain_password, str):
        plain_password_bytes = plain_password.encode('utf-8')
    else:
        plain_password_bytes = bytes(plain_password)
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash in constant time."""
    try:
        if isinstance(plain_password, str):
            plain_password_bytes = plain_password.encode('utf-8')
        else:
            plain_password_bytes = bytes(plain_password)
            
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode('utf-8')
        else:
            hashed_password_bytes = bytes(hashed_password)

        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception:
        return False


def create_access_token(
    admin_id: int,
    username: str,
    role: str = "super_admin",
    expires_minutes: int = DEFAULT_SESSION_DURATION_MINUTES,
    custom_jti: Optional[str] = None,
) -> tuple[str, str, datetime.datetime]:
    """
    Create a cryptographically signed JWT access token.
    Returns:
        (token_string, jti, expire_datetime_utc)
    """
    jti = custom_jti or str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(admin_id),
        "username": username,
        "role": role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # Return naive UTC datetime for MySQL storage
    return token, jti, expire.replace(tzinfo=None)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    Returns payload dictionary if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None
    except Exception:
        return None
