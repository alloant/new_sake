# app/routers/main.py
from fastapi import APIRouter, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from authx import TokenPayload
from sqlmodel import Session

from app.core.database import get_db
from app.core.auth import auth, get_payload_from_cookie, get_current_actor_alias_from_cookie

from app.crud import get_actor_by_id

from app.models.actor import Kind
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
    def TemplateResponse(self, name: str, context: dict[str, Any], status_code: int = 200):
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

    sidebar = get_sidebar(payload,section,panel,db)
    current_actor = get_actor_by_id(payload.uid, db)
    theme = current_actor.get_setting('theme') 
    
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "sidebar": sidebar, "section": section, "panel": panel, "search": search})

# Here is only for all_search. It will always have a section and panel
@router.post("/", name="homepage_search")
async def home_search(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    sidebar = get_sidebar(payload,section,panel, db)
    current_actor = get_actor_by_id(payload.uid, db)
    theme = current_actor.get_setting('theme') 
    
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    #return RedirectResponse(url=f"/?section={section}&panel={panel}&search={search}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "sidebar": sidebar, "section": section, "panel": panel, "search": search})


## Settings/profile part
@router.get("/settings", name="settings")
async def settings(request: Request, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    sidebar = get_sidebar(payload,'settings','', db)
    current_actor = get_actor_by_id(payload.uid, db)
    theme = current_actor.get_setting('theme') 
    return templates.TemplateResponse("settings.html", {"request": request, "theme": theme, "sidebar": sidebar,"actor": current_actor,"settings": get_settings_form(current_actor, db)})

@router.post("/settings", name="settings")
async def settings_post(request: Request, db: Session = Depends(get_db), payload = Depends(get_payload_from_cookie)):
    sidebar = get_sidebar(payload,'settings','', db)
    current_actor = get_actor_by_id(payload.uid, db)
    theme = current_actor.get_setting('theme') 
    
    form = await request.form()
    data = dict(form)
    
    scopes = []
    settings = {}
    for setting in data:
        kind, key = setting.split('_', 1)
        if kind == 'actor':
            if key == 'kind':
                if data[setting] == 'dr':
                    scopes.append(f'cg:editor')
                    scopes.append(f'asr:editor')
                    scopes.append(f'r:editor')
                    scopes.append(f'ctr:editor')
                elif data[setting] == 'of':
                    scopes.append(f'cg:viewer')
                    scopes.append(f'asr:viewer')
                    scopes.append(f'r:viewer')
                    scopes.append(f'ctr:viewer')
        elif kind == 'register':
            if data[setting]:
                scopes.append(f'{key}:{data[setting]}')
        elif kind == 'ctr':
            print('ctr',key)
            scopes.append(f'ctr_{key}:editor')
        elif kind == 'setting': 
            settings[key] = int(data[setting]) if data[setting].isdigit() else data[setting]

        elif kind == 'perm':
            if data[setting] == 'on':
                scopes.append(key)

    current_actor.scopes = scopes
    current_actor.settings = settings

    db.add(current_actor)
    db.commit()
    
    user_payload = {
        "uid": current_actor.id,
        "alias": current_actor.alias,
        "data": {"kind": "user"},
    }
    
    access_token = auth.create_access_token("sake",data=user_payload, scopes=current_actor.scopes)
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
