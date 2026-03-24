from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy import and_, or_, desc

from app.core.database import engine
from app.models.email import Email

def get_mail_by_uid(uid: str, db: Session) -> Email | None:
    return db.exec(select(Email).where(Email.uid==uid)).all()

def get_last_uid(db: Session) -> int:
    return db.exec(select(func.max(Email.uid))).one()

def add_mail(uid: str, subject: str, date: datetime, from_: str, text: str, db: Session) -> Register:
    email = get_mail_by_uid(uid, db)
    if not email:
        db_mail = Email(uid=uid,subject=subject,date=date,from_=from_,text=text)
        db.add(db_mail); db.commit(); db.refresh(db_mail)
        return db_mail
    else:
        return email

def get_mails(db: Session, section = None, panel = None, search: str = None, limit: int = None, offset: int = None, just_number: bool = False) -> list[Email] | int:
    #fn = get_filter(actor,section, panel, db)
    fn = []

    if search:
        fn.append(get_search_filter(search))
     
    num_stmt = select(func.count(Email.id))
    stmt = select(Email)

    stmt = stmt.limit(limit).offset(offset).order_by(desc(Email.date))
    
    if just_number:
        return db.exec(num_stmt).one()
    
    return db.exec(stmt).all(), db.exec(num_stmt).one()


