import math
from app.crud import get_records

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

    return "record/main.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_user": current_user}


async def records_table_view(page: int = None, search = None, section: str = None, panel: str = None, db = None, current_user = None):
    limit_records = current_user.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_records(db=db,user=current_user,section=section,panel=panel,search=search,limit=limit_records,offset=offset)

    return "record/table.html", {"records": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_user": current_user}

async def action_view(record, action, db, current_user):
    return "record/table_row.html", {"record": record}
