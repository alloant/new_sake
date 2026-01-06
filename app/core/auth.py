from fastapi import Depends, HTTPException, Request
from fastapi.security import SecurityScopes
from authx import AuthX, AuthXConfig, RequestToken

from types import SimpleNamespace

from jose import JWTError, jwt

from app.models.user import User
from app.crud.user import get_user_by_email

# Authx
config = AuthXConfig(
    JWT_ALGORITHM = "HS256",
    JWT_SECRET_KEY = "SECRET_KEY",
    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_REFRESH_COOKIE_NAME="refresh_token",
    JWT_TOKEN_LOCATION = ["cookies"]
)

auth = AuthX(model=User,config=config)


async def get_current_user(token: str = Depends(auth.get_token_from_request)):
    if not token:
        raise HTTPException(401, "Missing token")
    
    try:
        claims = auth.verify_token(token=token)
    except Exception as e:
        raise HTTPException(401, str(e))
    """
    uid = claims.get("sub") or claims.get("uid") or claims.get("user_id")
    if not uid:
        raise HTTPException(401, "Invalid token payload")
    with Session(your_engine) as session:
        user = session.exec(select(User).where(User.id == uid)).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
    """

async def get_current_user_from_cookie(request: Request):
    """Get current user from cookie token (for HTMX endpoints)"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user_by_email(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user

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

async def check_permissions(
    security_scopes: SecurityScopes, 
    # Extracts the payload from the 'Authorization' header
    payload: dict = Depends(auth.access_token_required)
):
    # AuthX puts token data in the payload. 
    # We assume your token has a "scopes" claim (e.g., ["read", "write"])
    user_scopes = payload.scopes
    
    for scope in security_scopes.scopes:
        if scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
            )
    return payload
