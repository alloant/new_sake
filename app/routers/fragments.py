import json
from pydantic import BaseModel

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi import UploadFile, File
#from fastapi.templating import Jinja2Templates

from sqlmodel import Session

from authx import TokenPayload

from app.core.auth import auth, get_current_actor_alias_from_cookie, get_payload_from_cookie
from app.core.database import get_db

from app.crud import get_records, get_register_by_alias, get_actor_by_id, get_record_actor, get_record_by_id, get_dept_by_alias
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
    current_actor = get_actor_by_id(payload.uid, db)
    template, rst = await records_view(page, search, section, panel, db, current_actor)
   
    return templates.TemplateResponse(template,{'request': request, 'last_search': None, 'section': section, 'panel': panel} | rst)


@router.post("/records/table", response_class=HTMLResponse)
async def records_table(request: Request, page: int = None, last_search = None, section: str = None, panel: str = None, db: Session = Depends(get_db), current_actor_id: str = Depends(get_current_actor_alias_from_cookie)):
    current_actor = get_actor_by_id(current_actor_id, db)
    form = await request.form()
    data = dict(form)
    search = last_search if last_search else data.get("search")
    
    template, rst = await records_table_view(page, search, section, panel, db, current_actor)
    template = f"record/table_pagination.html"
    
    return templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel, 'search': search} | rst)

@router.get("/records/number", response_class=HTMLResponse)
async def records_hidden_row(request: Request, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_actor = get_actor_by_id(payload.uid, db)
    num = get_records(db = db, actor = current_actor, section = section, panel = panel, just_number = True)
    if num == 0:
        return ''
    return f'<span class="tag is-secondary has-text-secondary is-rounded py-0 px-1" style="font-size: 0.6rem;">{num}</span>'


class Loop(BaseModel):
    index: int

@router.get("/action", response_class=HTMLResponse)
async def action(request: Request, record_id: int, recordactor_id: str, action: str, loop_index: int, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    current_actor = get_actor_by_id(payload.uid, db)
    loop = Loop
    loop.index = loop_index
    if action == 'recursive_search':
        page = 1
        template, rst = await records_table_view(page, f'all_off:{record_id}', 'register', 'all', db, current_actor)
        template = f"record/table_sidebar.html"
        sidebar = get_sidebar(payload,'register','all',db)
        response = templates.TemplateResponse(template, {'request': request, 'section': 'register', 'panel': 'all', 'sidebar': sidebar, 'search':f'all_off:{record_id}'} | rst)

        return response
    template, rst = await action_view(record_id, recordactor_id, action, db, current_actor)
    response = templates.TemplateResponse(template, {'request': request, 'section': section, 'panel': panel, 'current_actor': current_actor, 'loop': loop} | rst)

    if action in ['mark_read','mark_unread']:
        response.headers['HX-Trigger'] = 'read_state_changed'
    elif action in ['archive','restore']:
        response.headers['HX-Trigger'] = 'record_state_changed'

    return response

@router.post("/modify_record", response_class=HTMLResponse)
async def modify_record(request: Request, record_id: int, loop_index: int, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    loop = Loop
    loop.index = loop_index
    form = await request.form()
    data = dict(form)
    current_actor = get_actor_by_id(actor_id = payload.uid, db = db)
    record = get_record_by_id(record_id, db = db)
    status = get_record_actor(record_id = record_id, actor_id = payload.uid, db = db)

    record.title = data['title']
    record.sequence = data['sequence']
    record.year = data['year']

    dept = get_dept_by_alias(data['department'], db = db)
    if dept:
        record.dept_id = dept.id
    
    register = get_register_by_alias(data['register'], db = db)
    if register:
        record.register_id = register.id

    db.add(record)
    db.commit()
    
    return templates.TemplateResponse('record/table_row.html', {'request': request, 'record': record, 'status': status, 'current_actor': current_actor, 'loop': loop})
    return f"record/table_row.html", {"record": record, "status": status}

@router.post("/global_search", response_class=HTMLResponse)
async def records_global_search(request: Request, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    form = await request.form()
    data = dict(form)
    search = data.get("all_search")
    
    current_actor = get_actor_by_id(payload.uid, db)
    
    page = 1
    
    template, rst = await records_table_view(page, search, 'register', 'all', db, current_actor)
    if section != 'register' or panel != 'all':
        template = f"record/table_sidebar.html"
        sidebar = get_sidebar(payload,'register','all',db)
    else:
        sidebar = None
    response = templates.TemplateResponse(template, {'request': request, 'section': 'register', 'panel': 'all', 'sidebar': sidebar, 'search':search} | rst)

    return response

# The post is only for updload files and thinks like that
@router.post("/records/{record_id}/upload_files", response_class=HTMLResponse)
async def records_files(request: Request, record_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    print(record_id,'vamos','$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    return ""
