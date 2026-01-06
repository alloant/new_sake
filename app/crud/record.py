from sqlmodel import Session, select, func
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from app.core.database import engine
from app.crud.register import get_register_by_alias, get_user_registers
from app.models.record import Record
from app.models.record_user import RecordUser

def get_record(record_id: int, db: Session = None) -> Record | None:
    if not db:
        db = Session(engine)
    return db.get(Record, record_id)

def get_num_records(db: Session = None, search: str = None) -> list[Record]:
    if not db:
        db = Session(engine)

    if search:
        return db.exec(select(func.count(Record.id)).where(Record.title.like(f"%{search}%"))).one()

    return db.exec(select(func.count(Record.id))).one()

def get_filter(user,section, panel):
    fn = []
    if section == 'register':
        if panel == 'all':
            user_registers = get_user_registers(user.scopes)
            fn_registers = [Record.register_id == get_register_by_alias(register).id for register in user_registers if user_registers[register]]
            fn.append(or_(*fn_registers))
        elif panel == 'unread':
            pass
        else:
            register_alias, flow = panel.split('-')
            register = get_register_by_alias(register_alias)

            fn.append(Record.register_id==register.id)

            if flow == 'in':
                fn.append(Record.flow=='inbound')
            else:
                fn.append(Record.flow=='outbound')


    return fn

def get_records(db: Session = None, user = None, section = None, panel = None, search: str = None, limit: int = None, offset: int = None) -> list[Record]:
    if not user:
        return []

    if not db:
        db = Session(engine)

    fn = get_filter(user,section, panel)
    
    fn.append( or_(RecordUser.user_id == user.id,RecordUser.user_id.is_(None)) )
    if search:
        fn.append(Record.title.like(f"%{search}%"))
    
    num_stmt = select(func.count(Record.id)).join(RecordUser, isouter=True).where(*fn)
    stmt = select(Record, RecordUser).join(RecordUser, isouter=True).where(*fn).options(joinedload(Record.sender),joinedload(Record.register)).limit(limit).offset(offset) # I put the joinload to always get the register and sender because I am going to use it.
    return db.exec(stmt).all(), db.exec(num_stmt).one()


def get_records_for_user(sender_id: int, db: Session = None) -> list[Record]:
    if not db:
        db = Session(engine)
    return db.exec(select(Record).where(Record.sender_id == sender_id)).all()

def get_record_by_protocol(protocol: str, sequence: int, year: int, db: Session = None) -> Record | None:
    if not db:
        db = Session(engine)
    return db.exec(select(Record).where((Record.protocol == protocol) & (Record.sequence == sequence) & (Record.year == year))).all()

def create_record(record_in: RecordCreate, db: Session = None) -> Record:
    if not db:
        db = Session(engine)
    
    db_rec = Record(title=record_in.title, sequence=record_in.sequence, year=record_in.year, flow=record_in.flow, sender_id=record_in.sender_id)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec

def update_record(db_rec: Record, rec_in: RecordUpdate, db: Session = None) -> Record:
    if not db:
        db = Session(engine)
    data = rec_in.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(db_rec, k, v)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec
