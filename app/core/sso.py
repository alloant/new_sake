import os
import time
from datetime import timedelta
import json
from urllib.parse import urlencode


from fastapi import FastAPI, Request, Response, Form, Depends, APIRouter, HTTPException, status, Header
from fastapi.responses import RedirectResponse, HTMLResponse
from itsdangerous import URLSafeSerializer, BadSignature
import httpx
from joserfc import jwk, jwt

from app.crud import get_actor_by_alias, get_actor_by_email
from app.core.auth import auth

# SSO Synology
DSM = os.getenv("SSO_SERVER")
PORT = os.getenv("SYNOLOGY_PORT")
DISCOVERY = f"https://{DSM}:{PORT}/webman/sso/.well-known/openid-configuration"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Google SSO
GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI") # e.g., /auth/callback/google

SESSION_SECRET = os.getenv("SESSION_SECRET")

serializer = URLSafeSerializer(SESSION_SECRET, salt="session")

# helper: fetch discovery once and cache
_discovery = None
_jwks = None

def get_session(request: Request):
    session_val = request.cookies.get("access_token")
    if not session_val:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = load_session_cookie(session_val)   # reuse serializer.loads function from your app
    #user['sid'] = request.cookies.get('id') or request.cookies.get('sid')
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user



def make_session_cookie(user_claims: dict) -> str:
    return serializer.dumps(user_claims)

def load_session_cookie(val: str):
    try:
        return serializer.loads(val)
    except BadSignature:
        return None

# Change from None to empty dicts
_discovery_cache = {}
_jwks_cache = {}



async def get_discovery(provider: str = "synology"):
    global _discovery_cache, _jwks_cache
    
    # Check if we already have this specific provider's data
    if provider not in _discovery_cache:
        url = GOOGLE_DISCOVERY if provider == "google" else DISCOVERY
        try: # DEBUG verify should be True
            async with httpx.AsyncClient(verify=True) as client:
                # Fetch OpenID Configuration
                print('url:',url)
                r = await client.get(url, timeout=10)
                r.raise_for_status()
                disc = r.json()
                _discovery_cache[provider] = disc
                print('disc',disc)
                
                # Fetch JWKS (Keys)
                jwks_uri = disc.get("jwks_uri")
                if jwks_uri:
                    r2 = await client.get(jwks_uri, timeout=10)
                    r2.raise_for_status()
                    _jwks_cache[provider] = r2.json()
        except httpx.HTTPError as exc:
            # LOG THE ERROR HERE
            print(f"SSO Discovery failed for {provider}: {exc}")
            # Return None or raise a custom Exception that your UI can catch
            return None, None

                
    return _discovery_cache[provider], _jwks_cache.get(provider)

async def login_by_sso(state: str, provider: str = "synology"):
    # Get the correct discovery data from our new dict cache
    disc, _ = await get_discovery(provider)
    if not disc:
        return None

    auth_ep = disc["authorization_endpoint"]
    
    # Select credentials based on provider
    if provider == "google":
        client_id = GOOGLE_CLIENT_ID
        redirect_uri = GOOGLE_REDIRECT_URI
        scope = "openid email profile https://www.googleapis.com/auth/drive"
    else:
        client_id = CLIENT_ID
        redirect_uri = REDIRECT_URI
        scope = "openid"
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state, # Good practice to make state unique
        "access_type": "offline",      # CRITICAL for background access
        "prompt": "consent",
    }
    
    return auth_ep + "?" + urlencode(params)

async def callback(request: Request, db: Session, code: str = None, state: str = None, provider: str = "synology"):
    # 0. Without code we cannot go forward
    if not code:
        return HTMLResponse("Missing code", status_code=400)

    # 1. Set variables based on provider
    if provider == "google":
        client_id, client_secret = GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
        redirect_uri = GOOGLE_REDIRECT_URI
    else:
        client_id, client_secret = CLIENT_ID, CLIENT_SECRET
        redirect_uri = REDIRECT_URI

    # 2. Exchange code (This logic remains exactly as you have it)
    disc, jwks = await get_discovery(provider)
    token_ep = disc["token_endpoint"]
    userinfo_ep = disc.get("userinfo_endpoint")
    
    async with httpx.AsyncClient(verify=True) as client:
        # exchange code for tokens
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
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
            jwk_set = jwk.import_key_set(_jwks)
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


    # 3. Extract Identity
    # Synology provides 'username', Google provides 'email'
    alias = claims.get('email') if provider == "google" else claims.get('username')
    
    if not alias:
         raise HTTPException(status_code=400, detail="Could not retrieve user identity")

    if provider == "google":
        actor = get_actor_by_email(db, alias)
        alias = actor.alias
    else:
        actor = get_actor_by_alias(db, alias)
    
    user_payload = {
        "uid": actor.id,
        "alias": alias,
        "provider": provider,
        "lang": actor.get_setting('lang'),
        "data": {"kind": actor.kind.value},
        "google_access_token": access_token if provider == "google" else None,
        "google_refresh_token": refresh_token if provider == "google" else None,
    }

    return create_cookie_response(user_payload=user_payload, provider=provider)

def create_cookie_response(user_payload: dict, provider: str):
    cookie_duration = 60 * 60 * 24 * 7 # 7 Days
    access_token = auth.create_access_token("sake",data=user_payload, expires_delta=timedelta(seconds=cookie_duration))
        
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/">
    </head>
    <body>
        <script>window.location.href = "/";</script>
    </body>
    </html>
    """
    response = HTMLResponse(content=html_content, status_code=200)
   
    if provider == 'synology':
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,   # Keep this True since you are using HTTPS!
            samesite="lax",
            max_age=cookie_duration,
            domain=DSM # Explicitly tell the browser to trust the whole domain
        )   
    else:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,   # Keep this True since you are using HTTPS!
            samesite="lax",
            max_age=cookie_duration
        )
    return response

async def logout():
    resp = RedirectResponse(url="/")
    resp.delete_cookie("access_token")
    return resp
