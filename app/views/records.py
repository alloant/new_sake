import math
from app.crud import get_records

RECORDS_LIMIT=20

def pagination(num_pages: int, page: int):
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

    return {'num_pages': num_pages, 'page': page, 'prev': prev, 'next': next, 'first': (page-1)*RECORDS_LIMIT+1, 'last': page*RECORDS_LIMIT}


def get_title(section,panel):
    return panel.replace('-',' ').title()

async def records_view(page: int = None, search: str = None, section: str = None, panel: str = None, db = None, current_user = None):
    limit_records = current_user.get_setting('limit_records')
    records, num_records = get_records(db=db,user=current_user,section=section,panel=panel,search=search,limit=limit_records,offset=page)
    num_pages = math.ceil(num_records / limit_records)

    return "record/main.html", {"records": records, "pagination": pagination(num_pages,page), "title": get_title(section,panel), 'num_records': num_records}


async def records_table_view(page: int = None, search = None, section: str = None, panel: str = None, db = None, current_user = None):
    limit_records = current_user.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_records(db=db,user=current_user,section=section,panel=panel,search=search,limit=limit_records,offset=offset)
    num_pages = math.ceil(num_records / limit_records)

    return "record/table.html", {"records": records, "pagination": pagination(num_pages,page), "title": get_title(section,panel), 'num_records': num_records}


