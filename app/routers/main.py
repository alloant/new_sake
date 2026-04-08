# app/routers/main.py
from datetime import timedelta

from fastapi import APIRouter, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from fastapi_babel import _

from authx import TokenPayload
from sqlmodel import Session

from app.core.database import get_db
from app.core.auth import auth, get_payload_from_cookie, get_current_actor_alias_from_cookie

from app.crud import get_actor_by_id, get_record_by_id

from app.models.actor import Kind
from app.views.sidebar import get_sections, get_panel, get_sidebar

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
templates.env.globals.update(_=_)

@router.get("/", name="homepage")
async def home(request: Request, section: str | None = "board", panel: str | None = None, search: str = "", db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    if not panel:
        match section:
            case 'board':
                panel = 'inbox'
            case 'register':
                panel = 'cg-in'
            case 'sccr':
                panel = 'new_mail'
            
    sidebar = get_sidebar(db,payload,section,panel)
    current_actor = get_actor_by_id(db,payload.uid)
    theme = current_actor.get_setting('theme') 
    font_size = f"1.{int(current_actor.get_setting('font_size'))-1}"
    
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "font_size": font_size, "actor_role": current_actor.role, "sidebar": sidebar, "section": section, "panel": panel, "search": search})

# Here is only for all_search. It will always have a section and panel
@router.post("/", name="homepage_search")
async def home_search(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    sidebar = get_sidebar(db,payload,section,panel)
    current_actor = get_actor_by_id(db,payload.uid)
    theme = current_actor.get_setting('theme') 
    font_size = f"1.{int(current_actor.get_setting('font_size'))-1}"
    
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    return templates.TemplateResponse("index.html", {"request": request, "theme": theme, "font_size": font_size, "actor_role": current_actor.role, "sidebar": sidebar, "section": section, "panel": panel, "search": search})



