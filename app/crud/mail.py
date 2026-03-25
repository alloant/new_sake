from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy import and_, or_, desc, cast, Integer

from app.core.database import engine
from app.models.email import Mail

def get_mail_by_uid(uid: str, db: Session) -> Mail | None:
    return db.exec(select(Mail).where(Mail.uid==uid)).all()

def get_last_uid(db: Session) -> str:
    return db.exec(select(Mail.uid).order_by(cast(Mail.uid, Integer).desc())).first()

def add_mail(uid: str, subject: str, date: datetime, from_: str, text: str, db: Session) -> Register:
    email = get_mail_by_uid(uid, db)
    if not email:
        db_mail = Mail(uid=uid,subject=subject,date=date,from_=from_,text=text)
        db.add(db_mail); db.commit(); db.refresh(db_mail)
        return db_mail
    else:
        return email

def get_mails(db: Session, section = None, panel = None, search: str = None, limit: int = None, offset: int = None, just_number: bool = False, downloaded = True) -> list[Mail] | int:
    num_stmt = select(func.count(Mail.id))
    stmt = select(Mail)

    fn = []
    if search:
        fn.append(or_(Mail.from_.contains(search),Mail.subject.contains(search)))

    if not downloaded:
        fn.append(Mail.downloaded==False)

    stmt = stmt.where(*fn).limit(limit).offset(offset).order_by(desc(Mail.date))
    num_stmt = num_stmt.where(*fn) 
    if just_number:
        return db.exec(num_stmt).one()
    
    return db.exec(stmt).all(), db.exec(num_stmt).one()


