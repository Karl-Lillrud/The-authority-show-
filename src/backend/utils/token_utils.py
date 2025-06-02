# backend/utils/token_utils.py
import jwt
from datetime import datetime, timedelta
from flask import current_app

ALGORITHM = "HS256"

def create_token(data: dict, hours_valid: int = 24):
    secret = current_app.config.get("SECRET_KEY", "dev-secret-key")  # <-- flyttat hit
    expiration = datetime.utcnow() + timedelta(hours=hours_valid)
    payload = {
        **data,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")

def create_token_12h(data: dict):
    return create_token(data, hours_valid=12)

def create_token_24h(data: dict):
    return create_token(data, hours_valid=24)

def create_token_48h(data: dict):
    return create_token(data, hours_valid=48)

def decode_token(token: str):
    secret = current_app.config.get("SECRET_KEY", "dev-secret-key")  # <-- också flyttat hit
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
