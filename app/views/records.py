import math
from app.crud import get_record_by_id, get_records, get_record_actor, get_record_actor_by_id, get_actor_registers, get_ctrs, get_all_alias_deps, get_senders_register, get_targets_register, get_dispatcher_alias, get_tags
from app.routers.websocket import broadcast_channels

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

async def records_view(page: int = None, search: str = None, section: str = None, panel: str = None, db = None, current_actor = None):
    limit_records = current_actor.get_setting('limit_records')
    records, num_records = get_records(db=db,actor=current_actor,section=section,panel=panel,search=search,limit=limit_records,offset=page)
    
    return f"record/main.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor}


async def records_table_view(page: int = None, search = None, section: str = None, panel: str = None, db = None, current_actor = None):
    limit_records = current_actor.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_records(db=db,actor=current_actor,section=section,panel=panel,search=search,limit=limit_records,offset=offset)

    return f"record/table.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor}

async def action_view(record_id,status_id, action, db, current_actor):
    record = get_record_by_id(record_id, db = db)
    if status_id:
        status = get_record_actor_by_id(record_actor_id = status_id, db = db)
    else:
        status = get_record_actor(record_id = record_id, actor_id = current_actor.id, db = db)
  
    if action == "mark_read":
        if record.created_at > current_actor.created_at:
            status.handled = "read"
        else:
            status.handled = "unread"
    elif action == "mark_unread":
        if record.created_at > current_actor.created_at:
            status.handled = "unread"
        else:
            status.handled = "read"
    elif action == "archive":
        record.state = "archived"
    elif action == "restore":
        record.state = "active"
    elif action in ["edit","sign_note"]:
        registers = get_actor_registers(current_actor.scopes,db)
        departments = [''] + get_all_alias_deps(db)
        senders = get_senders_register(db,record.flow,record.register.alias)
        available_targets = get_targets_register(db, record.flow, record.register.alias)
        tags = get_tags(db)
        selected_targets = record.targets_id
        return "forms/record.html", {'action': action, 'record': record, 'status': status, 'registers': registers, 'departments': departments, 'senders': senders, 'available_targets': available_targets, 'checked_targets': selected_targets, 'tags': tags}
    elif action == "edit_targets":
        available_targets = get_ctrs(db)
        selected_targets = record.targets
        return "forms/form_targets.html", {'record': record, 'available_targets': available_targets, 'checked_targets': selected_targets}
    elif action == "start_circulation":
        record.stage = "shared"
        sock_targets = [f'actor_{alias}' for alias in record.current_targets_alias]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'New proposal to sign {record.protocol}')
    elif action == "stop_circulation":
        record.stage = "sketch"
    elif action == "sign_record":
        status.handled = "approved"
        sock_targets = [f'actor_{alias}' for alias in record.current_targets_alias]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'New proposal to sign {record.protocol}')
    elif action == "quick_sign": # Despacho action
        status.params['dispatcher_signature'] = True
        sock_targets = [f'actor_{alias}' for alias in get_dispatcher_alias(db)]
        await broadcast_channels(channels = sock_targets, actor_alias = current_actor.alias, msg = f'Note {record.protocol} was dispatched by other dr')

    if action in ['mark_read','mark_unread','sign_record', 'quick_sign']:
        db.add(status); db.commit(); db.refresh(status)
    elif action in ['archive','restore','start_circulation','stop_circulation']:
        db.add(record); db.commit(); db.refresh(record)

    return f"record/table_row.html", {"record": record, "status": status}
