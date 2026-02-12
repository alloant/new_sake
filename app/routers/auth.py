# app/routers/main.py
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
    auth_url =  await login_by_sso()
    # 1. Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # 2. Tell HTMX to redirect the entire window to the SSO page
        return Response(
            headers={"HX-Redirect": "/login"} 
        )

    return templates.TemplateResponse("auth/sso.html", {"request": request, "auth_url": auth_url})

@router.get("/auth/callback")
async def callback_route(request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)):
    return await callback(request,db,code,state)
