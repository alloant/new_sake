# app/routers/main.py
import secrets
from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends, Form, Response, status, HTTPException
from sqlmodel import Session

from app.core.auth import auth
from app.core.sso import login_by_sso, callback
from app.core.database import get_db

# Initialize the router and templates
router = APIRouter()
from app.routers.main import templates


@router.get('/logout')
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sake")
    
    return response

@router.get('/login')
async def login_form(request: Request):
    # 1. Generate unique states for this specific visit
    state_syno = secrets.token_urlsafe(16)
    state_goog = secrets.token_urlsafe(16)

    # 2. Save them in the session immediately
    # This ensures that when the user clicks the button, the 'valid' state is already in their cookie
    #request.session["state_synology"] = state_syno
    #request.session["state_google"] = state_goog
    
    # 3. Generate the URLs using these states
    auth_url = await login_by_sso(state_syno,"synology")
    auth_url_google = await login_by_sso(state_goog,"google")

    # 1. Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # 2. Tell HTMX to redirect the entire window to the SSO page
        return Response(
            headers={"HX-Redirect": "/login"} 
        )
    
    return templates.TemplateResponse(
        request=request, 
        name="auth/sso.html", 
        context={"auth_url": auth_url, "auth_url_google": auth_url_google}
    )
    return templates.TemplateResponse("auth/sso.html", {"request": request, "auth_url": auth_url, "auth_url_google": auth_url_google})

@router.get("/auth/callback")
async def callback_route(request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)):
    return await callback(request,db,code,state)

@router.get("/auth/callback-google")
async def callback_route(request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)):
    return await callback(request,db,code,state,'google')
