import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings


def create_token(user_id: int, empresa_id: int, email: str, rol: str) -> str:
    payload = {
        "sub": user_id,
        "empresa_id": empresa_id,
        "email": email,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
