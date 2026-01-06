# app/routers/main.py
from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends, Form, Response, status, HTTPException

from app.core.auth import auth
from app.crud.user import create_user, get_user_by_email, verify_user_password

# Initialize the router and templates
router = APIRouter()
from app.routers.main import templates


@router.get('/logout')
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    
    return response

@router.get('/login')
def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post('/login')
def login(email: Annotated[str, Form()], password: Annotated[str, Form()]):
    user = get_user_by_email(email)
    if not user or verify_user_password(user,password):
        raise HTTPException(401, "Bad email/password")
    
    user_payload = {
        "uid": user.id,
        "alias": user.actor.alias,
        "data": {"role": user.role.value},
        "scopes": user.scopes
    }
    
    access_token = auth.create_access_token(email,data=user_payload)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=36000 
    )
    return response

@router.get('/register')
def register_form(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post('/register')
def register(email: Annotated[str, Form()], full_name: Annotated[str, Form()], password: Annotated[str, Form()]):
    user = get_user_by_email(email)
    
    if user:
        raise HTTPException(401, "Email already in system")

    create_user(email,full_name,password)
    
    RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

