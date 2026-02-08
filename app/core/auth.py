from fastapi import Depends, HTTPException, Request
from fastapi.security import SecurityScopes
from authx import AuthX, AuthXConfig, RequestToken

from types import SimpleNamespace

from jose import JWTError, jwt

from app.models.actor import Actor
from app.crud import get_actor_by_id

# Authx
config = AuthXConfig(
    JWT_ALGORITHM = "HS256",
    JWT_SECRET_KEY = "SECRET_KEY",
    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_REFRESH_COOKIE_NAME="refresh_token",
    JWT_TOKEN_LOCATION = ["cookies"]
)

auth = AuthX(model=Actor,config=config)

async def get_current_actor_alias_from_cookie(request: Request):
    """Get current actor from cookie token (for HTMX endpoints)"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        alias= payload.get("uid")
        if alias is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return alias

async def get_payload_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        raw_payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        payload = SimpleNamespace(**raw_payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload
