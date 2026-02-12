import os
import time
import json
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Response, Form, Depends, APIRouter, HTTPException, status, Header
from fastapi.responses import RedirectResponse, HTMLResponse
from itsdangerous import URLSafeSerializer, BadSignature
import httpx
from authlib.jose import JsonWebKey, jwt

from app.crud import get_actor_by_alias
from app.core.auth import auth

# CONFIG - replace these with your values
DSM = os.getenv("SSO_SERVER")
PORT = os.getenv("SYNOLOGY_PORT")
DISCOVERY = f"https://{DSM}:{PORT}/webman/sso/.well-known/openid-configuration"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SESSION_SECRET = os.getenv("SESSION_SECRET")


serializer = URLSafeSerializer(SESSION_SECRET, salt="session")

# helper: fetch discovery once and cache
_discovery = None
_jwks = None

def get_session(request: Request):
    session_val = request.cookies.get("session")
    if not session_val:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = load_session_cookie(session_val)   # reuse serializer.loads function from your app
    #user['sid'] = request.cookies.get('id') or request.cookies.get('sid')
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


async def get_discovery():
    global _discovery, _jwks
    if _discovery is None:
        async with httpx.AsyncClient(verify=False) as client:
            r = await client.get(DISCOVERY, timeout=10)
            r.raise_for_status()
            _discovery = r.json()
            jwks_uri = _discovery.get("jwks_uri")
            if jwks_uri:
                r2 = await client.get(jwks_uri, timeout=10)
                r2.raise_for_status()
                _jwks = r2.json()
    return _discovery

def make_session_cookie(user_claims: dict) -> str:
    return serializer.dumps(user_claims)

def load_session_cookie(val: str):
    try:
        return serializer.loads(val)
    except BadSignature:
        return None

async def login_by_sso():
    disc = await get_discovery()
    auth_ep = disc["authorization_endpoint"]
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
        "state": "state123",  # simple static state for demo; in prod generate/verifiy per session
    }
    auth_url = auth_ep + "?" + urlencode(params)
    return auth_url

async def callback(request: Request, db: Session, code: str = None, state: str = None):
    if not code:
        return HTMLResponse("Missing code", status_code=400)

    disc = await get_discovery()
    token_ep = disc["token_endpoint"]
    userinfo_ep = disc.get("userinfo_endpoint")
    
    async with httpx.AsyncClient(verify=False) as client:
        # exchange code for tokens
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        r = await client.post(token_ep, data=data, timeout=10)
        r.raise_for_status()
        token_resp = r.json()
        id_token = token_resp.get("id_token")
        access_token = token_resp.get("access_token")
        refresh_token = token_resp.get("refresh_token")
        expires_in = token_resp.get("expires_in")  # seconds

        claims = {}
        if id_token and _jwks:
            # verify id_token signature and basic claims (simplified)
            jwk_set = JsonWebKey.import_key_set(_jwks)
            try:
                claims = jwt.decode(id_token, jwk_set)
                claims.validate_exp()
            except Exception:
                claims = {}
        # fallback: fetch userinfo if available
        if not claims and userinfo_ep and access_token:
            r2 = await client.get(userinfo_ep, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
            r2.raise_for_status()
            claims = r2.json()
    
    # build session payload
    session_claims = claims.copy() if claims else {}
    if access_token:
        session_claims["access_token"] = access_token
    if refresh_token:
        session_claims["refresh_token"] = refresh_token
    if expires_in:
        session_claims["expires_at"] = int(time.time()) + int(expires_in)
  
    alias = claims['username']
    actor = get_actor_by_alias(alias, db)
    user_payload = {
        "uid": actor.id,
        "alias": alias,
        "data": {"kind": actor.kind.value},
    }
    
    access_token = auth.create_access_token("sake",data=user_payload, scopes=actor.scopes)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=session_claims["expires_at"] if expires_in else 36000 
    )
    return response


async def logout():
    resp = RedirectResponse(url="/")
    resp.delete_cookie("session")
    return resp
