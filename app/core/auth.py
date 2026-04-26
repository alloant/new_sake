from datetime import timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import SecurityScopes
from authx import AuthX, AuthXConfig
from types import SimpleNamespace

# Import joserfc AND its specific key object handler
from joserfc import jwt
from joserfc.jwk import OctKey

from app.core.config import settings
from app.models.actor import Actor
from app.crud import get_actor_by_id

# 1. AuthX gets the standard string
config = AuthXConfig(
    JWT_ALGORITHM="HS256",
    JWT_SECRET_KEY=settings.SECRET_KEY, 
    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_REFRESH_COOKIE_NAME="refresh_token",
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=7)
)

auth = AuthX(model=Actor, config=config)

# 2. joserfc gets a properly formatted OctKey object!
JOSERFC_SECRET = OctKey.import_key(settings.SECRET_KEY)


async def get_current_actor_alias_from_cookie(request: Request):
    """Get current actor from cookie token (for HTMX endpoints)"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Decode using the OctKey object (removed the algorithms kwarg)
        token_obj = jwt.decode(token, JOSERFC_SECRET)
        
        alias = token_obj.claims.get("uid") 
        if alias is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return alias

    except Exception as e:
        print(f"Alias decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_actor_lang_from_cookie(request: Request):
    """Get current actor lang from cookie token"""
    token = request.cookies.get("access_token")
    
    if not token:
        return "en"
        
    try:
        token_obj = jwt.decode(token, JOSERFC_SECRET)
        lang = token_obj.claims.get("lang", "en")
        return lang

    except Exception as e:
        print(f"Lang decode failed: {e}")
        return "en"


async def get_payload_from_cookie(request: Request):
    """Get full payload from cookie token"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token_obj = jwt.decode(token, JOSERFC_SECRET)
        
        # Unpack the .claims dictionary
        payload = SimpleNamespace(**token_obj.claims)
        return payload
        
    except Exception as e:
        print(f"Payload decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
