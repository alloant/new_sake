# app/routers/main.py
from fastapi import APIRouter, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from authx import TokenPayload
from sqlmodel import Session

from app.core.database import get_db
from app.core.auth import auth, get_payload_from_cookie, get_current_user_from_cookie

from app.crud import get_user_by_email

from app.models.user import Role
from app.views.sidebar import get_sections, get_panel, get_sidebar
from app.views.settings import get_settings_form

def is_true(obj,condition,text=""):
    if obj:
        if getattr(obj,condition):
            return text if text else getattr(obj,condition)
    return ""

def is_false(obj,condition,text=""):
    if obj:
        if not getattr(obj,condition):
            return ""
    return text


class AppTemplates(Jinja2Templates):
    def TemplateResponse(self, name: str, context: Dict[str, Any], status_code: int = 200):
        context.setdefault("is_true", is_true)
        context.setdefault("is_false", is_false)
        return super().TemplateResponse(name, context, status_code=status_code)

# Initialize the router and templates
router = APIRouter()

#templates = Jinja2Templates(directory="templates")
templates = AppTemplates(directory="templates")

@router.get("/", name="homepage")
async def home(request: Request, section: str | None = "board", panel: str | None = None, search: str = "", db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    if not panel:
        match section:
            case 'board':
                panel = 'inbox'
            case 'register':
                panel = 'cg-in'
            case 'sccr':
                panel = 'mail'

    sidebar = get_sidebar(payload,section,panel)
    current_user = get_user_by_email(payload.sub, db)
    theme = current_user.get_setting('theme') 
    
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "sidebar": sidebar, "section": section, "panel": panel, "search": search})

# Here is only for all_search. It will always have a section and panel
@router.post("/", name="homepage_search")
async def home_search(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    sidebar = get_sidebar(payload,section,panel)
    current_user = get_user_by_email(payload.sub, db)
    theme = current_user.get_setting('theme') 
    
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    #return RedirectResponse(url=f"/?section={section}&panel={panel}&search={search}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "sidebar": sidebar, "section": section, "panel": panel, "search": search})


## Settings/profile part
@router.get("/settings", name="settings")
async def settings(request: Request, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    sidebar = get_sidebar(payload,'settings','')
    current_user = get_user_by_email(payload.sub, db)
    theme = current_user.get_setting('theme') 
    return templates.TemplateResponse("settings.html", {"request": request, "theme": theme, "sidebar": sidebar,"user": current_user,"settings": get_settings_form(current_user)})

@router.post("/settings", name="settings")
async def settings_post(request: Request, db: Session = Depends(get_db), payload = Depends(get_payload_from_cookie)):
    sidebar = get_sidebar(payload,'settings','')
    current_user = get_user_by_email(payload.sub, db)
    theme = current_user.get_setting('theme') 
    
    form = await request.form()
    data = dict(form)
    
    scopes = []
    settings = {}
    for setting in data:
        kind, key = setting.split('_', 1)
        if kind == 'user':
            if key == 'role':
                current_user.role = Role(data[setting])

        elif kind == 'register':
            if data[setting]:
                scopes.append(f'{key}:{data[setting]}')

        elif kind == 'setting': 
            settings[key] = int(data[setting]) if data[setting].isdigit() else data[setting]

        elif kind == 'perm':
            if data[setting] == 'on':
                scopes.append(key)

    current_user.scopes = scopes
    current_user.settings = settings

    db.add(current_user)
    db.commit()

    user_payload = {
        "uid": current_user.id,
        "alias": current_user.actor.alias,
        "data": {"role": data['user_role']}
    }
    
    access_token = auth.create_access_token(current_user.email,data=user_payload,scopes=scopes)
    response = RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=36000 
    )
    auth.set_access_cookies(access_token, response)
    return response
