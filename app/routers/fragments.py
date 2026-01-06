import json

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
#from fastapi.templating import Jinja2Templates

from sqlmodel import Session

from authx import TokenPayload

from app.core.auth import auth, get_current_user_from_cookie
from app.core.database import get_db
from app.core.htmx import add_hx_trigger_header_on_success

from app.crud import get_user_by_email, get_records, get_register_by_alias, update_user
from app.views.records import records_view, records_table_view
from app.views.sidebar import get_sidebar

# Initialize the router and templates
router = APIRouter()

#templates = Jinja2Templates(directory="templates")
#templates = AppTemplates(directory="templates")
from .main import templates

## SIDEBAR
@router.get("/sidebar", response_class=HTMLResponse)
def sidebar_fragment(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    #current_user = get_user_by_email(payload.sub, db)
    sidebar = get_sidebar(payload,section,panel)
    
    return templates.TemplateResponse("sidebar/main.html", {"request": request, "sidebar": sidebar, "section": section, "panel": panel})

@router.get("/sidebar-top", response_class=HTMLResponse)
def sidebar_top_fragment(request: Request, new_sidebar = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    print('Updating sidebar-top',new_sidebar)
    #current_user = get_user_by_email(payload.sub, db)
    section = 'register'
    panel = 'all'
    sidebar = get_sidebar(payload,section,panel)
    
    return templates.TemplateResponse("sidebar/sidebar-top.html", {"request": request, "sidebar": sidebar, "section": section, "panel": panel})

# RECORDS
@router.get("/records", response_class=HTMLResponse)
async def records(request: Request, search:str = None, page: int = None, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_user = get_user_by_email(payload.sub, db)
    #update_user(current_user,'settings',{'kind': 'cr'},db)
    
    template, rst = await records_view(page, search, section, panel, db, current_user)
   
    return templates.TemplateResponse(template,{'request': request, 'last_search': None, 'section': section, 'panel': panel} | rst)


@router.post("/records/table", response_class=HTMLResponse)
async def records_table(request: Request, page: int = None, last_search = None, section: str = None, panel: str = None, db: Session = Depends(get_db), current_user: str = Depends(get_current_user_from_cookie)):
    form = await request.form()
    data = dict(form)
    search = last_search if last_search else data.get("search")
    
    template, rst = await records_table_view(page, search, section, panel, db, current_user)
    return templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel} | rst)


@router.post("/global_search", response_class=HTMLResponse)
#@add_hx_trigger_header_on_success('global_search_changed')
async def records_global_search(request: Request, db: Session = Depends(get_db), current_user: str = Depends(get_current_user_from_cookie)):
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    page = 1
    section = 'register'
    panel = 'all'
    
    template, rst = await records_table_view(page, search, section, panel, db, current_user)
    response = templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel} | rst)

    payload_trigger = {
        "global_search_changed": "patata"
    }
    response.headers['HX-Trigger'] = json.dumps(payload_trigger)

    return response

# USERS
@router.get("/users/list", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db)):
    users = get_users(db)
    return templates.TemplateResponse("user/list.html", {"request": request, "users": users})
