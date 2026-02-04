# app/routers/main.py
from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends, Form, Response, status, HTTPException
from sqlmodel import Session

from app.core.auth import auth
from app.core.sso import login_by_sso, callback
from app.core.database import get_db
from app.crud.user import create_user, get_user_by_id, verify_user_password

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
    print('Here getting the login')
    auth_url =  await login_by_sso()
    return templates.TemplateResponse("auth/sso.html", {"request": request, "auth_url": auth_url})


@router.post('/login')
def login(email: Annotated[str, Form()], password: Annotated[str, Form()], db: Session = Depends(get_db)):
    user = get_user_by_email(email, db)
    if not user or verify_user_password(user,password):
        raise HTTPException(401, "Bad email/password")
    
    user_payload = {
        "uid": user.id,
        "alias": user.actor.alias,
        "data": {"role": user.role.value},
    }
    
    access_token = auth.create_access_token(email,data=user_payload, scopes=user.scopes)
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


@router.get("/auth/callback")
async def callback_route(request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)):
    return await callback(request,db,code,state)

@router.get('/register')
def register_form(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post('/register')
def register(email: Annotated[str, Form()], full_name: Annotated[str, Form()], password: Annotated[str, Form()], db: Session = Depends(get_db)):
    user = get_user_by_email(email,db)
    
    if user:
        raise HTTPException(401, "Email already in system")

    create_user(email,full_name,password)
    
    RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

