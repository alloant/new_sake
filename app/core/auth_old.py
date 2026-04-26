from datetime import timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import SecurityScopes
from authx import AuthX, AuthXConfig, RequestToken

from types import SimpleNamespace

from joserfc import jwt

from app.core.config import settings
from app.models.actor import Actor
from app.crud import get_actor_by_id

# Authx
config = AuthXConfig(
    JWT_ALGORITHM = "HS256",
    JWT_SECRET_KEY = settings.SECRET_KEY.encode('utf-8'),
    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_REFRESH_COOKIE_NAME="refresh_token",
    JWT_TOKEN_LOCATION = ["cookies"],
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
)

auth = AuthX(model=Actor,config=config)

async def get_current_actor_alias_from_cookie(request: Request):
    """Get current actor from cookie token (for HTMX endpoints)"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"], options={"leeway": 30})
        alias= payload.get("uid")
        if alias is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return alias

async def get_current_actor_lang_from_cookie(request: Request):
    """Get current actor from cookie token (for HTMX endpoints)"""
    token = request.cookies.get("access_token")
    
    if not token:
        return "en"
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"], options={"leeway": 30})
        lang = payload.get("lang")

        if lang is None:
            lang = "en"
    except:
        #raise HTTPException(status_code=401, detail="Invalid token")
        lang = "en"
    
    return lang

async def get_payload_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        raw_payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"], options={"leeway": 30})
        payload = SimpleNamespace(**raw_payload)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload
