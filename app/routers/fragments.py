import json
import io
import base64
import asyncio
from datetime import timedelta

from pydantic import BaseModel

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi import UploadFile, File
from fastapi.responses import RedirectResponse
#from fastapi.templating import Jinja2Templates

from sqlmodel import Session, select

from authx import TokenPayload

from app.core.auth import auth, get_current_actor_alias_from_cookie, get_payload_from_cookie
from app.core.imap import get_unseen_mails, get_all_mails, add_mails_db, get_last_mails, add_last_mails_db
from app.core.database import get_db
from app.core.sso import create_cookie_response

from app.models.mail import Attachment

from app.services.drive import upload_bytes_and_convert

from app.crud import get_records, get_mails, get_register_by_alias, get_actor_by_id, get_record_actor, get_record_by_id, add_mail, get_last_uid, get_mail_by_uid, get_actor_by_alias, get_actor_by_ids, add_recordactor, get_tags, get_targets_register

from app.views.settings import get_settings_form
from app.views.records import records_view, records_table_view, action_view
from app.views.mails import mails_view, mails_table_view
from app.views.sidebar import get_sidebar

# Initialize the router and templates
router = APIRouter()

from .main import templates

#Settings
@router.get("/settings", name="settings")
async def settings(request: Request, section:str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_actor = get_actor_by_id(db, payload.uid)
    available_targets = get_targets_register(db, 'outbound', 'ctr')
    checked_targets = current_actor.ctrs_alias

    return templates.TemplateResponse(
        request=request, 
        name="forms/form_settings.html", 
        context={"section": section, "panel": panel, "actor_role": current_actor.role, "actor": current_actor, "available_targets": available_targets, 'checked_targets': checked_targets, "settings": get_settings_form(db,current_actor)}
    )

## Settings/profile part
@router.post("/settings", name="settings")
async def settings_post(request: Request, actor_id:int, section: str, panel: str, db: Session = Depends(get_db), payload = Depends(get_payload_from_cookie)):
    current_actor = get_actor_by_id(db,payload.uid)
    edit_actor = get_actor_by_id(db,actor_id)
    provider = payload.provider
    form = await request.form()
    data = dict(form)

    ctrs = form.getlist('user_ids')
    scopes = []
    settings = {}
    for setting in data:
        if '_' in setting:
            kind, key = setting.split('_', 1)
            if kind == 'actor':
                if key == 'kind':
                    if data[setting] == 'dr':
                        scopes.append('dr')
                        scopes.append(f'prop:editor')
                        scopes.append(f'cg:editor')
                        scopes.append(f'asr:editor')
                        scopes.append(f'r:editor')
                        scopes.append(f'ctr:editor')
                    elif data[setting] == 'of':
                        scopes.append('of')
                        scopes.append(f'prop:editor')
                        scopes.append(f'cg:viewer')
                        scopes.append(f'asr:viewer')
                        scopes.append(f'r:viewer')
                        scopes.append(f'ctr:viewer')
                    else:
                        scopes.append('cl')
            elif kind == 'register':
                if data[setting]:
                    scopes.append(f'{key}:{data[setting]}')
            elif kind == 'setting': 
                settings[key] = int(data[setting]) if data[setting].isdigit() else data[setting]

            elif kind == 'perm':
                if data[setting] == 'on':
                    scopes.append(key)
   
    if not 'setting_kind' in data:
        scopes.append('ctr')
        scopes.append('contact:ctr')

    for ctr_id in ctrs:
        ctr = get_actor_by_id(db,ctr_id)
        scopes.append(f'ctr_{ctr.alias}:editor')

    edit_actor.is_active = 'is_active' in data
    edit_actor.full_name = data['full_name']
    edit_actor.abbr = data['abbr']
    edit_actor.scopes = scopes
    edit_actor.settings = settings

    db.add(edit_actor)
    db.commit()
    
    user_payload = {
        "uid": current_actor.id,
        "alias": current_actor.alias,
        "provider": provider,
        "lang": settings['lang'],
        "data": {"kind": "user"},
        "google_access_token": payload.access_token if provider == "google" else None,
        "google_refresh_token": payload.refresh_token if provider == "google" else None,
    }
    # Generate the new token
    cookie_duration = 60 * 60 * 24 * 7
    access_token = auth.create_access_token("sake", data=user_payload, expires_delta=timedelta(seconds=cookie_duration))

    # Redirect properly with 303 (since we are coming from a POST)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Set the updated cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True, # Set to True in production
        samesite="lax",
        max_age=cookie_duration
    )
    
    return response
    return create_cookie_response(user_payload=user_payload, provider=provider)

@router.get("/settings_ctr", name="settings")
async def settings(request: Request, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    #current_actor = get_actor_by_id(db, payload.uid)
    ctr_alias = panel
    ctr = get_actor_by_alias(db, ctr_alias)

    available_targets = [] # get_targets_register(db, 'outbound', 'ctr')
    checked_targets = [] #ctr.ctrs_alias

    return templates.TemplateResponse(
        request=request, 
        name="forms/form_settings_ctr.html", 
        context={"section": section, "panel": panel, "actor_role": ctr.role, "actor": ctr, "available_targets": available_targets, 'checked_targets': checked_targets, "settings": get_settings_form(db,ctr)}
    )


## SIDEBAR
@router.get("/sidebar", response_class=HTMLResponse)
def sidebar_fragment(request: Request, section: str | None = "board", panel: str | None = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    sidebar = get_sidebar(db,payload,section,panel)

    return templates.TemplateResponse(
        request=request, 
        name="sidebar/main.html", 
        context={"sidebar": sidebar, "section": section, "panel": panel}
    )

@router.get("/sidebar-top", response_class=HTMLResponse)
def sidebar_top_fragment(request: Request, new_sidebar = None, myData = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    section = 'board'
    panel = 'all'
    sidebar = get_sidebar(db,payload,section,panel)

    return templates.TemplateResponse(
        request=request, 
        name="sidebar/sidebar-top.html", 
        context={"sidebar": sidebar, "section": section, "panel": panel}
    )

# RECORDS
@router.get("/records", response_class=HTMLResponse)
async def records(request: Request, search:str = None, page: int = None, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_actor = get_actor_by_id(db,payload.uid)
    template, rst = await records_view(page, search, section, panel, db, current_actor)

    return templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'last_search': None, 'section': section, 'panel': panel} | rst
    )


@router.post("/records/table", response_class=HTMLResponse)
async def records_table(request: Request, page: int = None, last_search = None, section: str = None, panel: str = None, db: Session = Depends(get_db), current_actor_id: str = Depends(get_current_actor_alias_from_cookie)):
    current_actor = get_actor_by_id(db,current_actor_id)
    form = await request.form()
    data = dict(form)
    if 'tag_ids' in data:
        data['tag_ids'] = form.getlist('tag_ids')
    if 'actor_tags' in data:
        data['actor_tags'] = form.getlist('actor_tags')

    search = last_search if last_search else data.get("search")
    
    template, rst = await records_table_view(db=db, current_actor=current_actor, section=section, panel=panel, page=page, search=search, data=data)
    template = f"record/table_pagination.html"

    return templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'section': section, 'panel': panel, 'search': search} | rst
    )

@router.get("/records/number", response_class=HTMLResponse)
async def records_hidden_row(request: Request, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_actor = get_actor_by_id(db,payload.uid)
    num = get_records(db = db, actor = current_actor, section = section, panel = panel, just_number = True)
    if num == 0:
        return ''

    return f'<span class="tag is-dark is-rounded py-0 px-2" style="font-size: 0.6rem;">{num}</span>'


class Loop(BaseModel):
    index: int


@router.get("/new_record", response_class=HTMLResponse)
async def action(request: Request, section: str = None, panel: str = None, record_type: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    current_actor = get_actor_by_id(db,payload.uid)
    print(current_actor,section,panel,record_type)


@router.get("/action", response_class=HTMLResponse)
async def action(request: Request, record_id: int, recordactor_id: str, action: str, loop_index: int, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    current_actor = get_actor_by_id(db,payload.uid)
    loop = Loop
    loop.index = loop_index
    if action == 'recursive_search':
        page = 1
        template, rst = await records_table_view(db=db, current_actor=current_actor, section='board', panel='all', page=page, search=f'all_off:{record_id}')
        template = f"record/table_sidebar.html"
        sidebar = get_sidebar(db,payload,'board','all')

        return templates.TemplateResponse(
            request=request, 
            name=template, 
            context={'section': 'board', 'panel': 'all', 'sidebar': sidebar, 'search':f'all_off:{record_id}'} | rst
        )

    
    template, rst = await action_view(db, record_id, recordactor_id, action, current_actor, section, panel)

    response = templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'section': section, 'panel': panel, 'current_actor': current_actor, 'loop': loop} | rst
    )

    if action in ['mark_read','mark_unread']:
        response.headers['HX-Trigger'] = 'read_state_changed'
    elif action in ['archive','restore']:
        response.headers['HX-Trigger'] = 'record_state_changed'
    elif action in ['sign_record']:
        response.headers['HX-Trigger'] = 'proposal_sign_changed'
    elif action in ['start_circulation','stop_circulation', '']:
        response.headers['HX-Trigger'] = 'proposal_state_changed'

    return response

@router.post("/modify_record", response_class=HTMLResponse)
async def modify_record(request: Request, record_id: int, loop_index: int, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    loop = Loop
    loop.index = loop_index
    form = await request.form()
    data = dict(form)
    
    current_actor = get_actor_by_id(db, actor_id = payload.uid)
    record = get_record_by_id(db, record_id)
    status = get_record_actor(db, record_id = record_id, actor_id = payload.uid)
   
    if data['submit_form'] == 'save_tags':
        actor_tags = form.getlist("actor_tags")
        status.params['actor_tags'] = actor_tags
        if data['due_date'] and (record.flow == 'inbound' and section != 'cl' or record.flow == 'outbound' and section == 'cl' or record.flow in ['internal_cr','internal_cl']):
            status.due_date = data['due_date']
        if record.flow == 'inbound' and section != 'cl' or record.flow == 'outbound' and section == 'cl':
            status.handled = data['status']
        elif record.flow == 'internal_cr':
            record.state = data['status']
        
        db.add(record)
        db.add(status)
        db.commit()
        db.refresh(status)
        db.refresh(record)

        response = templates.TemplateResponse(
            request=request, 
            name="record/table_row.html", 
            context={'record': record, 'status': status, 'current_actor': current_actor, 'loop': loop}
        )

        if record.flow == 'inbound' and section != 'cl' or record.flow == 'outbound' and section == 'cl':
            response.headers['HX-Trigger'] = 'record_state_changed'
        elif record.flow == 'internal_cr':
            response.headers['HX-Trigger'] = 'proposal_state_changed'

        return response
    
    if data['submit_form'] == 'save_sign':
        status.params['dispatcher_signature'] = True
        db.add(status)

    list_new_actors = form.getlist("user_ids")
    new_actors = set(list_new_actors)
   
    map_actors = {str(ra.actor_id): ra for ra in record.actors}
    current_actors = set(map_actors.keys())
   
    for actor_id in (current_actors - new_actors):
        map_actors[actor_id].target = 0
    
    for actor_id in new_actors:
        if actor_id in current_actors:
            map_actors[actor_id].target = list_new_actors.index(actor_id) + 1
        else: # A new one
            status_actor = get_record_actor(db, record_id = record_id, actor_id = actor_id)
            status_actor.target = list_new_actors.index(actor_id) + 1
            db.add(status_actor)
    
    new_tags = set(form.getlist("tag_ids"))
    map_tags = {str(ra.id): ra for ra in record.tags}
    current_tags = set(map_tags.keys())

    map_all_tags = {str(ra.id): ra for ra in get_tags(db)}

    for tag_id in (current_tags - new_tags):
        record.tags.remove(map_all_tags[tag_id])

    for tag_id in (new_tags - current_tags):
        record.tags.append(map_all_tags[tag_id])
    
    record.title = data['title']
    record.area = data['area']
    record.audience = data['audience']
    #record.comments = data['comments']
    record.sequence = data['sequence']
    record.year = data['year']

    unit = get_actor_by_alias(db, data['department'])
    if unit:
        record.unit_id = unit.id
    else:
        record.unit_id = None
    
    register = get_register_by_alias(db, data['register'])
    if register:
        record.register_id = register.id

    db.add(record)
    db.commit()
    db.refresh(record)

    return templates.TemplateResponse(
        request=request, 
        name="record/table_row.html", 
        context={'record': record, 'status': status, 'current_actor': current_actor, 'loop': loop, 'section': section, 'panel': panel}
    )


@router.post("/modify_record_cl", response_class=HTMLResponse)
async def modify_record(request: Request, record_id: int, loop_index: int, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    loop = Loop
    loop.index = loop_index
    form = await request.form()
    data = dict(form)
    ctr_alias, flow = panel[:-4].split('-')
    
    #current_actor = get_actor_by_id(db, actor_id = payload.uid)
    ctr = get_actor_by_alias(db, ctr_alias)
    current_actor = get_actor_by_id(db, actor_id = payload.uid)
    record = get_record_by_id(db, record_id)
    status = get_record_actor(db, record_id = record_id, actor_id = current_actor.id)
    status_section = get_record_actor(db, record_id = record_id, actor_id = ctr.id)
    
    if data['submit_form'] == 'save_tags':
        actor_tags = form.getlist("actor_tags")
        status_section.params['actor_tags'] = actor_tags
        db.add(status_section); db.commit(); db.refresh(status_section)

        return templates.TemplateResponse(
            request=request, 
            name="record/table_row_cl.html", 
            context={'section': section, 'panel': panel, 'record': record, 'status': status, 'status_section': status_section, 'current_actor': current_actor, 'loop': loop}
        )

    new_targets = form.getlist("user_ids")
    set_new_targets = set(new_targets)

    targets = record.targets_ctr(ctr_alias)
    map_targets = {str(ra.actor_id): ra for ra in targets}
    set_targets = set(map_targets.keys())
   
    for actor_id in (set_targets - set_new_targets):
        map_targets[actor_id].target = 0
    
    for actor_id in set_new_targets:
        if actor_id in set_targets:
            map_targets[actor_id].target = new_targets.index(actor_id) + 1
        else: # A new one
            status_actor = get_record_actor(db, record_id = record_id, actor_id = actor_id)
            status_actor.target = new_targets.index(actor_id) + 1
            db.add(status_actor)

    db.add(record)
    db.commit()
    db.refresh(record)

    return templates.TemplateResponse(
        request=request, 
        name="record/table_row_cl.html", 
        context={'ctr_alias': ctr_alias, 'record': record, 'status': status, 'status_section': status_section, 'current_actor': current_actor, 'loop': loop, 'section': section, 'panel': panel}
    )


@router.post("/global_search", response_class=HTMLResponse)
async def records_global_search(request: Request, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    form = await request.form()
    data = dict(form)
    if 'tag_ids' in data:
        data['tag_ids'] = form.getlist('tag_ids')
    if 'actor_tags' in data:
        data['actor_tags'] = form.getlist('actor_tags')

    search = data.get("all_search")
    
    current_actor = get_actor_by_id(db, payload.uid)
    
    page = 1
    
    template, rst = await records_table_view(db=db, current_actor=current_actor, section='board', panel='all', page=page, search=search, data=data)
    if section != 'board' or panel != 'all':
        template = f"record/table_sidebar.html"
        sidebar = get_sidebar(db, payload,'board','all')
    else:
        sidebar = None

    return templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'section': 'board', 'panel': 'all', 'sidebar': sidebar, 'search':search} | rst
    )


# The post is only for updload files and thinks like that
@router.post("/records/{record_id}/upload_files", response_class=HTMLResponse)
async def records_files(request: Request, record_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    return ""

@router.get("/sccr", response_class=HTMLResponse)
async def mails(request: Request, search: str = None, page: int = None, section: str = None, panel: str = None, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    current_actor = get_actor_by_id(db, payload.uid)
    limit_records = current_actor.get_setting('limit_records')

    template, rst = await mails_view(page, search, section, panel, db, current_actor, downloaded = False if panel == 'new_mail' else True)

    response = templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'section': section, 'panel': panel} | rst
    )

    if panel == 'new_mail':
        response.headers['HX-Trigger'] = 'cardumen_state_changed'

    return response


@router.post("/sccr/table", response_class=HTMLResponse)
async def mails_table(request: Request, page: int = None, last_search = None, section: str = None, panel: str = None, db: Session = Depends(get_db), current_actor_id: str = Depends(get_current_actor_alias_from_cookie)):
    current_actor = get_actor_by_id(db, current_actor_id)
    form = await request.form()
    data = dict(form)
    search = last_search if last_search else data.get("search")

    if panel.startswith('update_'):
        add_last_mails_db(db)
        panel = panel[7:]
        notification = {'notification_message': 'Mail updated', 'notification_color': 'info'}
    else:
        notification = {'notification_message': '', 'notification_color': ''}
    
    template, rst = await mails_table_view(page, search, section, panel, db, current_actor, downloaded = False if panel == 'new_mail' else True)
    template = f"sccr/table_pagination.html"

    return templates.TemplateResponse(
        request=request, 
        name=template, 
        context={'section': section, 'panel': panel, 'search': search} | rst | notification
    )

@router.get("/sccr/number", response_class=HTMLResponse)
async def sccr_hidden_row(request: Request, section: str, panel: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(auth.access_token_required)):
    num = get_mails(db = db, section = section, panel = panel, just_number = True, downloaded = False if panel == 'new_mail' else True)
    if num == 0:
        return ''

    return f'<span class="tag is-dark is-rounded py-0 px-2" style="font-size: 0.6rem;">{num}</span>'

@router.get("/sccr/action", response_class=HTMLResponse)
async def sccr_action(request: Request, mail_uid: int, action: str, db: Session = Depends(get_db), payload: TokenPayload = Depends(get_payload_from_cookie)):
    mail = get_mail_by_uid(db, mail_uid)
    
    if action == 'add_to_sake':
        cont = 0
        for att in mail.attachments:
            rst = await upload_bytes_and_convert(payload, att.file_data, att.name, '/docker')
            if rst:
                cont += 1
                att.file_data = b""
                db.add(att)
        if cont == len(mail.attachments):
            mail.downloaded = True
            db.add(mail)
        db.commit()
    elif action == 'mark_as_downloaded':
        mail.downloaded = True
        for att in mail.attachments:
            att.file_data = b""
            db.add(att)
        db.add(mail); db.commit(); db.refresh(mail)

    response = templates.TemplateResponse(
        request=request, 
        name="sccr/table_row.html", 
        context={'mail': mail}
    )

    if action in ['mark_as_downloaded','add_to_sake']:
        response.headers['HX-Trigger'] = 'cardumen_state_changed'

    return response


@router.get("/sccr/download/{attachment_id}")
async def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    # 1. Get the record from the database
    statement = select(Attachment).where(Attachment.id == attachment_id)
    attachment = db.exec(statement).one()

    if not attachment:
        return {"error": "File not found"}

    # 2. Use BytesIO to turn bytes into a "file-like" object
    file_stream = io.BytesIO(attachment.file_data)

    # 3. Return a StreamingResponse
    # 'Content-Disposition' forces the browser to download the file instead of viewing it
    headers = {
        'Content-Disposition': f'attachment; filename="{attachment.name}"'
    }

    return StreamingResponse(file_stream, media_type="application/octet-stream", headers=headers)
