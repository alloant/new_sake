import math
from app.core.config import LAYOUT
from app.crud import get_record, get_records, get_record_user, get_record_user_by_id

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

async def records_view(page: int = None, search: str = None, section: str = None, panel: str = None, db = None, current_user = None):
    limit_records = current_user.get_setting('limit_records')
    records, num_records = get_records(db=db,user=current_user,section=section,panel=panel,search=search,limit=limit_records,offset=page)
    return f"record/{LAYOUT}/main.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_user": current_user}


async def records_table_view(page: int = None, search = None, section: str = None, panel: str = None, db = None, current_user = None):
    limit_records = current_user.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_records(db=db,user=current_user,section=section,panel=panel,search=search,limit=limit_records,offset=offset)

    return f"record/{LAYOUT}/table.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_user": current_user}

async def action_view(record_id,status_id, action, db, current_user):
    record = get_record(record_id)
    if status_id:
        status = get_record_user_by_id(record_user_id = status_id, db = db)
    else:
        status = get_record_user(record_id = record_id, user_id = current_user.id, db = db)

    if action == "mark_read":
        status.read_status = "read"
    elif action == "mark_unread":
        status.read_status = "unread"

    db.add(status); db.commit(); db.refresh(status)

    return f"record/{LAYOUT}/table_row.html", {"record": record, "status": status}
