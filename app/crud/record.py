import re

from sqlmodel import Session, select, func, text, union_all
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload, aliased, selectinload

from app.core.database import engine
from app.crud.register import get_register_by_alias, get_actor_registers
from app.crud.actor import get_actor_by_id, get_actor_by_alias

from app.models.record import Record, RecordRecord
from app.models.record_actor import RecordActor


current_target_subquery = (
        select(func.min(RecordActor.target))
        #.where(RecordActor.record_id == Record.id)
        .where(RecordActor.handled == 'pending')
        .where(RecordActor.target > 0)
        .correlate(Record) # Ensures it checks target per record
        .scalar_subquery()
    )


def get_record_actor(record_id: int, actor_id: int, db: Session) -> RecordActor:
    smnt = select(RecordActor).where(
    RecordActor.actor_id == actor_id,
    RecordActor.record_id == record_id)

    status = db.exec(smnt).first()

    if not status:
        status = RecordActor(actor_id=actor_id, record_id=record_id)
        db.add(status)
        db.commit()
        db.refresh(status)

    return status

def get_record_by_params(param: str, value, db: Session) -> Record | None:
    smnt = select(Record).where(Record.params[param] == value)
    return db.exec(smnt).one()

def get_record_actor_by_id(record_actor_id: int, db: Session) -> Record | None:
    return db.get(RecordActor, record_actor_id)

def get_record_by_id(record_id: int, db: Session) -> Record | None:
    return db.get(Record, record_id)

def get_num_records(db: Session, search: str = None) -> list[Record]:
    if search:
        return db.exec(select(func.count(Record.id)).where(Record.title.like(f"%{search}%"))).one()

    return db.exec(select(func.count(Record.id))).one()

def get_filter(actor,section, panel, db: Session):
    fn = []
    if section == 'register':
        if panel in ['all','unread']:
            actor_registers = get_actor_registers(actor.scopes, db)
            fn_registers = [Record.register_id == get_register_by_alias(register,db).id for register in actor_registers if actor_registers[register]]
            fn.append(or_(*fn_registers))
            
            if panel == 'unread':
                fn.append(Record.flow=='inbound')
                fn.append(or_(
                    and_(RecordActor == None, Record.created_at > actor.created_at),
                    and_(RecordActor.handled != 'read', Record.created_at > actor.created_at),
                    and_(RecordActor.handled == 'read', Record.created_at <= actor.created_at)
                    )
                )
        elif panel.endswith('_ctr'):
            ctr_alias, flow = panel[:-4].split('-')
            ctr = get_actor_by_alias(ctr_alias, db)
            
            if flow == 'in':
                fn.append(Record.flow == 'outbound')
                fn.append(RecordActor.actor_id == ctr.id)
            else:
                fn.append(Record.flow == 'inbound')
                fn.append(Record.sender_id == ctr.id)

        else:
            register_alias, flow = panel.split('-')
            register = get_register_by_alias(register_alias, db)

            fn.append(Record.register_id==register.id)

            if flow == 'in':
                fn.append(Record.flow=='inbound')
            else:
                fn.append(Record.flow=='outbound')
    elif section == 'board':
        if panel.startswith('inbox'):
            fn.append(Record.flow=='inbound')
            fn.append(RecordActor.target > 0)
            if panel == 'inbox':
                fn.append(Record.state == 'active')
            if panel == 'inbox-snooze':
                fn.append(Record.state == 'snooze')
            elif panel == 'inbox-archived':
                pass
                fn.append(Record.state == 'archived')
        elif panel.startswith('outbox'):
            fn.append(Record.flow=='outbound')
            fn.append(Record.sender_id == actor.id)
            if panel == 'outbox-drafts':
                fn.append(Record.stage == 'draft')
            elif panel == 'outbox-sent':
                fn.append(Record.stage == 'sent')
        elif panel.startswith('incoming-proposals'):
            fn.append(Record.flow=='internal_cr')
            fn.append(RecordActor.target > 0)
            if panel == 'incoming-proposals-to-sign':
                fn.append(RecordActor.handled == 'pending')
                fn.append(RecordActor.target == current_target_subquery)
            elif panel == 'incoming-proposals-signed':
                fn.append(RecordActor.handled != 'pending')
        elif panel.startswith('outcoming-proposals'):
            fn.append(Record.flow=='internal_cr')
            fn.append(Record.sender_id == actor.id)
            if panel == 'outcoming-proposals-drafts':
                fn.append(Record.stage == 'sketch')
                fn.append(Record.state == 'active')
            elif panel == 'outcoming-proposals-circulating':
                fn.append(Record.stage == 'shared')
                fn.append(Record.state == 'active')
            elif panel == 'outcoming-proposals-done':
                fn.append(Record.stage == 'closed')
                fn.append(Record.state == 'active')
            elif panel == 'outcoming-proposals-snooze':
                fn.append(Record.state == 'snooze')
            elif panel == 'outcoming-proposals-archived':
                fn.append(Record.state == 'archived')


    return fn


def get_search_filter(search):
    fn = []
    
    # Try to find protocols
    pattern_protocol = r"\b(\d+)/(\d{2})\b"
    matches = re.findall(pattern_protocol, search)
    cleaned_search = re.sub(pattern_protocol, "", search)
    cleaned_search = " ".join(cleaned_search.split())

    for match in matches:
        fn.append(and_(Record.sequence==int(match[0]),Record.year==2000+int(match[1])))

    # Numbers to equal them to sequence
    for word in cleaned_search.split(' '):
        if word.isdigit():
            fn.append(Record.sequence==int(word))

    # In title try find the whole search and the cleaned one.
    fn.append(Record.title.like(f"%{cleaned_search}%"))
    fn.append(Record.title.like(f"%{search}%"))

    return or_(*fn)


def get_recursive_ids(start_id: int, actor: "Actor", db: Session, limit: int = None, offset:int = None):
    start_record = get_record_by_id(start_id, db)
    start_ids = [start_id]
    for reference in start_record.references:
        start_ids.append(reference.id)

    start_ids = ",".join([str(r) for r in start_ids])
    
    sql = text(
        f"""
        WITH RECURSIVE R AS (
            SELECT record_id, reference_id FROM recordrecord 
            WHERE record_id IN ({start_ids}) OR reference_id IN ({start_ids})
            UNION
            -- Use a more specific join to prevent infinite loops/duplicates
            SELECT rr.record_id, rr.reference_id 
            FROM recordrecord rr
            INNER JOIN R ON rr.record_id = R.reference_id
        )
        SELECT record_id FROM R
        UNION
        SELECT reference_id FROM R
        """
    )
    all_ids = db.exec(sql).unique().all()

    #all_ids = list(set([start_id] + [item for sublist in all_ids for item in sublist]))
    all_ids = list(set([int(start_id)] + [item[0] for item in all_ids]))

    return Record.id.in_(all_ids)

def get_records(db: Session, actor = None, section = None, panel = None, search: str = None, limit: int = None, offset: int = None, just_number: bool = False) -> list[Record] | int:
    if not actor:
        return []

    fn = get_filter(actor,section, panel, db)

    if search:
        if search.startswith('all_off:'):
            fn.append(get_recursive_ids(search[8:], actor, db, limit, offset))
        else:
            fn.append(get_search_filter(search))
    
    if panel.endswith('in_ctr'):
        ctr_alias, flow = panel[:-4].split('-')
        ctr = get_actor_by_alias(ctr_alias, db)

        join_condition = and_(
            Record.id == RecordActor.record_id, 
            RecordActor.actor_id == ctr.id
        )
    else:
        join_condition = and_(
            Record.id == RecordActor.record_id, 
            RecordActor.actor_id == actor.id
        )
     
    num_stmt = select(func.count(Record.id))
    stmt = select(Record, RecordActor, current_target_subquery.label("target_order"))

    if section == 'board':
        if panel.startswith('inbox') or panel.startswith('incoming'):
            stmt = stmt.join(RecordActor, join_condition).where(*fn, RecordActor.actor_id==actor.id)
            num_stmt = num_stmt.join(RecordActor, join_condition).where(*fn, RecordActor.actor_id==actor.id)
        elif panel.startswith('outbox') or panel.startswith('outcoming'):
            stmt = stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
            num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
    elif section == 'register':
        stmt = stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
        num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
    
    stmt = stmt.options(
        joinedload(Record.sender),
        joinedload(Record.register),
        joinedload(Record.dept),
        selectinload(Record.tags),
        selectinload(Record.actors),
        selectinload(Record.files),
        selectinload(Record.references),
        joinedload(RecordActor.actor),
        joinedload(RecordActor.record)
    ).limit(limit).offset(offset).order_by(desc(Record.updated_at))
    
    if just_number:
        return db.exec(num_stmt).one()
    
    return db.exec(stmt).unique().all(), db.exec(num_stmt).one()

def get_all_records(db: Session) -> list[Record]:
    stmt = select(Record)

    return db.exec(stmt).all()

def get_records_for_actor(sender_id: int, db: Session) -> list[Record]:
    return db.exec(select(Record).where(Record.sender_id == sender_id)).all()

def get_record_by_protocol(protocol: str, sequence: int, year: int, db: Session) -> Record | None:
    return db.exec(select(Record).where((Record.protocol == protocol) & (Record.sequence == sequence) & (Record.year == year))).all()

def create_record(record_in: RecordCreate, db: Session) -> Record:
    db_rec = Record(title=record_in.title, sequence=record_in.sequence, year=record_in.year, flow=record_in.flow, sender_id=record_in.sender_id)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec

def update_record(db_rec: Record, rec_in: RecordUpdate, db: Session) -> Record:
    data = rec_in.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(db_rec, k, v)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec
