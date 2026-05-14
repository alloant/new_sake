import math
from app.crud import get_record_by_id, get_records, get_record_actor, get_record_actor_by_id, get_actor_registers, get_ctrs, get_all_deps, get_all_alias_deps, get_senders_register, get_targets_register, get_dispatcher_alias, get_tags, get_actor_by_alias
from app.routers.websocket import broadcast_channels

from app.services.drive import list_folder

def pagination(num_records: int, page: int, limit_records: int):
    num_pages = math.ceil(num_records / limit_records)
    page = 1 if not page else page
    if page == 1:
        prev = None
        if num_pages > 1:
            next = 2
        else:
            next = None
    else:
        prev = page - 1
        if page < num_pages:
            next = page + 1
        else:
            next = None
    last = page*limit_records if page*limit_records < num_records else num_records

    return {'num_pages': num_pages, 'page': page, 'prev': prev, 'next': next, 'first': (page-1)*limit_records+1, 'last': last}


def get_title(section,panel):
    return panel.replace('-',' ').title()

def get_advance_search_data(db, current_actor, section: str, panel: str) -> dict:
    registers = get_actor_registers(db,current_actor.scopes, only_alias=False)
    departments = get_all_deps(db)
    tags = get_tags(db)
    actor_tags = current_actor.settings['actor_tags'].split(',') if 'actor_tags' in current_actor.settings else []
    return {'registers': registers, 'departments': departments, 'tags': tags, 'actor_tags': actor_tags}

async def records_view(page: int = None, search: str = None, section: str = None, panel: str = None, db = None, current_actor = None):
    limit_records = current_actor.get_setting('limit_records')
    records, num_records = get_records(db=db,actor=current_actor,section=section,panel=panel,search=search,limit=limit_records,offset=page)
    advance_search = get_advance_search_data(db, current_actor, section, panel)
    
    return f"record/main.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor, "advance_search": advance_search}


async def records_table_view(db: Session, current_actor: Actor, section: str, panel: str, page: int = None, search = None, data = None):
    limit_records = current_actor.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_records(db=db,actor=current_actor,section=section,panel=panel,search=search,data=data,limit=limit_records,offset=offset)

    return f"record/table.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor}

async def action_view(db: Session, payload, record_id: int, status_id: int, action: str, current_actor: Actor, section: str, panel: panel):
    record = get_record_by_id(db,record_id)
    if status_id:
        status = get_record_actor_by_id(db, record_actor_id = status_id)
    else:
        status = get_record_actor(db, record_id = record_id, actor_id = current_actor.id)
  
    if action == "mark_read":
        if record.created_at > current_actor.created_at:
            if status.target > 0:
                status.handled = "pending"
            else:
                status.handled = "read"
        else:
            status.handled = "unread"
    elif action == "mark_unread":
        if record.created_at > current_actor.created_at:
            status.handled = "unread"
        else:
            if status.target > 0:
                status.handled = "read"
            else:
                status.handled = "pending"
    elif action == "archive":
        if record.flow == 'inbound':
            status.handled = "done"
            all_done = True
            for target in record.targets:
                if target.handled != 'done':
                    all_done = False
                    break
            if all_done:
                record.state = "done"
        elif record.flow == 'internal_cr':
            record.state = "done"
    elif action == "restore":
        if record.flow == 'inbound':
            record.state = "pending"
            status.handled = "pending"
        elif record.flow == 'internal_cr':
            record.state = "pending"
    elif action in ["edit_record","sign_note"]:
        registers = get_actor_registers(db,current_actor.scopes)
        departments = get_all_alias_deps(db)
        senders = get_senders_register(db,record.flow,record.register.alias)
        available_targets = get_targets_register(db, record.flow, record.register.alias)
        tags = get_tags(db)
        selected_targets = record.targets_id
        areas = ['Aes','Aso','Asmo','Ind','J']
        return "forms/form_record.html", {'action': action, 'record': record, 'status': status, 'registers': registers, 'departments': departments, 'senders': senders, 'available_targets': available_targets, 'checked_targets': selected_targets, 'tags': tags, 'areas': areas}
    elif action == 'edit_record_cl':
        ctr_alias, flow = panel[:-4].split('-')
        available_targets = get_targets_register(db, record.flow, 'ctr', ctr_alias=ctr_alias)
        selected_targets = record.targets_ctr_id(ctr_alias)
        tags = ['asd','qwe']
        return "forms/form_record_cl.html", {'ctr_alias': ctr_alias,'action': action, 'record': record, 'status': status, 'available_targets': available_targets, 'checked_targets': selected_targets, 'tags': tags}
    elif action == "edit_targets":
        available_targets = get_ctrs(db)
        selected_targets = record.targets
        return "forms/form_targets.html", {'record': record, 'available_targets': available_targets, 'checked_targets': selected_targets}
    elif action == 'edit_actor_tags':
        if section == 'cl':
            ctr_alias, flow = panel[:-4].split('-')
            ctr = get_actor_by_alias(db,ctr_alias)
            status_section = get_record_actor(db, record_id = record_id, actor_id = ctr.id)
            tags = ctr.settings['actor_tags'].split(',') if 'actor_tags' in ctr.settings else []
            checked_tags = status_section.params['actor_tags'] if status and 'actor_tags' in status_section.params else []

        else:
            tags = current_actor.settings['actor_tags'].split(',') if 'actor_tags' in current_actor.settings else []
            checked_tags = status.params['actor_tags'] if status and 'actor_tags' in status.params else []
        
        return "forms/form_actor_tags.html", {'record': record, 'status': status, 'actor': current_actor, 'tags': tags, 'checked_tags': checked_tags}
    elif action == "start_circulation":
        record.stage = "shared"
        sock_targets = [f'actor_{alias}' for alias in record.current_targets_alias]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'New proposal to sign {record.protocol}')
    elif action == "stop_circulation":
        record.stage = "sketch"
    elif action == "sign_record":
        status.handled = "approved"
        done = True
        for target in record.targets:
            if target.actor_id != status.actor_id and target.handled != 'approved':
                done = False
                break
        if done:
            record.stage = 'closed'
            db.add(record)
            sock_targets = [f'actor_{record.sender.alias}']
        else:
            sock_targets = [f'actor_{alias}' for alias in record.current_targets_alias]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'New proposal to sign {record.protocol}')
    elif action == "quick_sign": # Despacho action
        status.params['dispatcher_signature'] = True
        sock_targets = [f'actor_{alias}' for alias in get_dispatcher_alias(db)]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'Note {record.protocol} was dispatched by other dr')
    elif action == "quick_unsign": # Despacho action
        status.params['dispatcher_signature'] = False
        sock_targets = [f'actor_{alias}' for alias in get_dispatcher_alias(db)]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'Note {record.protocol} was dispatched by other dr')
    elif action == 'upload_file':
        files = await list_folder(payload, '/team-folders/docker')
        print(files)


    if action in ['mark_read','mark_unread','sign_record', 'quick_sign', 'quick_unsign', 'start_circulation', 'stop_circulation']:
        db.add(status); db.commit(); db.refresh(status)
    elif action in ['archive','restore','start_circulation','stop_circulation']:
        db.add(record); db.commit(); db.refresh(record)

    return f"record/table_row.html", {"record": record, "status": status}
