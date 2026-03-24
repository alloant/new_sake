import math

from app.crud import get_mails

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

async def mails_view(page: int = None, search: str = None, section: str = None, panel: str = None, db = None, current_actor = None):
    limit_records = current_actor.get_setting('limit_records')
    records, num_records = get_mails(db=db,section=section,panel=panel,search=search,limit=limit_records,offset=page)
    
    return f"sccr/main.html", {"mails": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor}


async def mails_table_view(page: int = None, search = None, section: str = None, panel: str = None, db = None, current_actor = None):
    limit_records = current_actor.get_setting('limit_records')
    offset = (page - 1)*limit_records if page else None
    records, num_records = get_mails(db=db,section=section,panel=panel,search=search,limit=limit_records,offset=offset)

    return f"sccr/table.html", {"mails": records, "pagination": pagination(num_records,page,limit_records), "title": get_title(section,panel), 'num_records': num_records, "current_actor": current_actor}


