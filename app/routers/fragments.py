import json

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
#from fastapi.templating import Jinja2Templates

from sqlmodel import Session

from authx import TokenPayload

from app.core.config import LAYOUT
from app.core.auth import auth, get_current_user_from_cookie, get_payload_from_cookie
from app.core.database import get_db
from app.core.htmx import add_hx_trigger_header_on_success

from app.crud import get_record, get_records, get_register_by_alias, update_user, get_user_by_id
from app.views.records import records_view, records_table_view, action_view
from app.views.sidebar import get_sidebar

# Initialize the router and templates
router = APIRouter()

#templates = Jinja2Templates(directory="templates")
#templates = AppTemplates(directory="templates")
from .main import templates

## SIDEBAR
@router.get("/sidebar", response_class=HTMLResponse)
def sidebar_fragment(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    sidebar = get_sidebar(payload,section,panel, db)
    
    return templates.TemplateResponse("sidebar/main.html", {"request": request, "sidebar": sidebar, "section": section, "panel": panel})

@router.get("/sidebar-top", response_class=HTMLResponse)
def sidebar_top_fragment(request: Request, new_sidebar = None, myData = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    section = 'register'
    panel = 'all'
    sidebar = get_sidebar(payload,section,panel, db)
    
    return templates.TemplateResponse("sidebar/sidebar-top.html", {"request": request, "sidebar": sidebar, "section": section, "panel": panel})

# RECORDS
@router.get("/records", response_class=HTMLResponse)
async def records(request: Request, search:str = None, page: int = None, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_user = get_user_by_id(payload.uid, db)
    #update_user(current_user,'settings',{'kind': 'cr'},db)
    template, rst = await records_view(page, search, section, panel, db, current_user)
   
    return templates.TemplateResponse(template,{'request': request, 'last_search': None, 'section': section, 'panel': panel} | rst)


@router.post("/records/table", response_class=HTMLResponse)
async def records_table(request: Request, page: int = None, last_search = None, section: str = None, panel: str = None, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_cookie)):
    current_user = get_user_by_id(current_user_id, db)
    form = await request.form()
    data = dict(form)
    search = last_search if last_search else data.get("search")
    
    template, rst = await records_table_view(page, search, section, panel, db, current_user)
    template = f"record/{LAYOUT}/table_pagination.html"
    
    return templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel, 'search': search} | rst)

@router.get("/records/number", response_class=HTMLResponse)
async def records_hidden_row(request: Request, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_user = get_user_by_id(payload.uid, db)
    num = get_records(db = db, user = current_user, section = section, panel = panel, just_number = True)
    if num == 0:
        return ''
    return f'<span class="tag is-danger is-rounded py-0" style="font-size: 0.65rem;">{num}</span>'


@router.get("/action", response_class=HTMLResponse)
async def action(request: Request, record_id: int, recorduser_id: str, action: str, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    current_user = get_user_by_id(payload.uid, db)
    if action == 'recursive_search':
        page = 1
        template, rst = await records_table_view(page, f'all_off:{record_id}', 'register', 'all', db, current_user)
        template = f"record/{LAYOUT}/table_sidebar.html"
        sidebar = get_sidebar(payload,'register','all',db)
        response = templates.TemplateResponse(template, {'request': request, 'section': 'register', 'panel': 'all', 'sidebar': sidebar, 'search':f'all_off:{record_id}'} | rst)

        return response
   
    template, rst = await action_view(record_id, recorduser_id, action, db, current_user)
    response = templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel, 'current_user': current_user} | rst)

    if action in ['mark_read','mark_unread']:
        response.headers['HX-Trigger'] = 'read_state_changed'
    elif action in ['archive','restore']:
        response.headers['HX-Trigger'] = 'record_state_changed'

    return response


@router.post("/global_search", response_class=HTMLResponse)
async def records_global_search(request: Request, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    current_user = get_user_by_id(payload.uid, db)
    
    page = 1
    
    template, rst = await records_table_view(page, search, 'register', 'all', db, current_user)
    if section != 'register' or panel != 'all':
        template = f"record/{LAYOUT}/table_sidebar.html"
        sidebar = get_sidebar(payload,'register','all',db)
    else:
        sidebar = None
    response = templates.TemplateResponse(template, {'request': request, 'section': 'register', 'panel': 'all', 'sidebar': sidebar, 'search':search} | rst)

    return response

# USERS
@router.get("/users/list", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db)):
    users = get_users(db)
    return templates.TemplateResponse("user/list.html", {"request": request, "users": users})
