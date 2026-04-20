import re

from sqlmodel import Session, select, func, text, union_all
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload, aliased, selectinload

from app.core.database import engine
from app.crud.register import get_register_by_alias, get_actor_registers
from app.crud.actor import get_actor_by_id, get_actor_by_alias

from app.models.record import Record, RecordRecord, Tag
from app.models.record_actor import RecordActor


current_target_subquery = (
        select(func.min(RecordActor.target))
        .where(RecordActor.record_id == Record.id)
        .where(RecordActor.handled == 'pending')
        .where(RecordActor.target > 0)
        .correlate(Record) # Ensures it checks target per record
        .scalar_subquery()
    )

def get_tags(db: Session):
    return db.exec(select(Tag)).all()

def get_record_actor(db: Session, record_id: int, actor_id: int) -> RecordActor:
    smnt = select(RecordActor).where(
    RecordActor.actor_id == actor_id,
    RecordActor.record_id == record_id)

    status = db.exec(smnt).first()

    if not status:
        print('NEW ONE:')
        status = RecordActor(actor_id=actor_id, record_id=record_id)
        db.add(status)
        db.commit()
        db.refresh(status)

    return status

def get_record_by_params(db: Session, param: str, value) -> Record | None:
    smnt = select(Record).where(Record.params[param] == value)
    return db.exec(smnt).one()

def get_record_actor_by_id(db: Session, record_actor_id: int) -> Record | None:
    return db.get(RecordActor, record_actor_id)

def get_record_by_id(db: Session, record_id: int) -> Record | None:
    return db.get(Record, record_id)

def get_num_records(db: Session, search: str = None) -> list[Record]:
    if search:
        return db.exec(select(func.count(Record.id)).where(Record.title.like(f"%{search}%"))).one()

    return db.exec(select(func.count(Record.id))).one()

def get_filter(db: Session, actor: Actor, section: str, panel: str):
    if 'permanent' or section == 'cl' in actor.scopes:
        fn = []
    elif 'dr' in actor.scopes:
        fn = [Record.audience != 'permanent']
    elif 'of' in actor.scopes:
        fn = [Record.audience == 'all']
    
    if section == 'register':
        if panel.endswith('in'):
            fn.append(Record.stage == 'registered')
            fn.append(Record.flow=='inbound')
        else:
            fn.append(Record.stage == 'sent')
            fn.append(Record.flow=='outbound')
        
        register_alias, flow = panel.split('-')
        register = get_register_by_alias(db,register_alias)
        
        fn.append(Record.register_id==register.id)

    elif section == 'cl':
        if panel.endswith('in_ctr'):
            pass
            fn.append(Record.flow == 'outbound')
            fn.append(Record.stage == 'sent')
            #fn.append(RecordActor.actor_id == actor.id)
        else:
            fn.append(Record.flow == 'inbound')
            fn.append(Record.stage == 'registered')
            fn.append(Record.sender_id == actor.id)
        
        register = get_register_by_alias(db,'ctr')
        fn.append(Record.register_id==register.id)

    elif section == 'board':
        if panel == 'despacho':
            fn.append(Record.stage=='despacho') 
            return fn

        if panel in ['all','mustread','unread']:
            actor_registers = get_actor_registers(db,actor.scopes)
            fn_registers = [Record.register_id == get_register_by_alias(db,register).id for register in actor_registers if actor_registers[register]]
            fn.append(or_(*fn_registers))
            
            if panel == 'all':
                fn.append(or_(
                Record.stage.in_(['registered','sent']),
                and_(or_(Record.sender_id==actor.id,Record.has_actor_target(actor.id)),or_(
                    and_(Record.stage=='shared', RecordActor == 'approved'),
                    and_(Record.stage=='shared', RecordActor.target == current_target_subquery),
                    Record.stage == 'closed'
                ))
            ))

            elif panel == 'unread':
                fn.append(Record.stage == 'registered')
                fn.append(Record.flow=='inbound')
                fn.append(or_(
                    and_(RecordActor == None, Record.created_at > actor.created_at),
                    and_(RecordActor.handled.in_(['unread','mustread']), Record.created_at > actor.created_at),
                    and_(RecordActor.handled == 'read', Record.created_at <= actor.created_at)
                    )
                )
            elif panel == 'mustread':
                fn.append(Record.stage == 'registered')
                fn.append(Record.flow=='inbound')
                fn.append(RecordActor.handled == 'mustread')

        elif panel.startswith('inbox'):
            fn.append(Record.stage == 'registered')
            fn.append(Record.flow=='inbound')
            fn.append(RecordActor.target > 0)
            if panel == 'inbox':
                #fn.append(Record.state == 'active') For global state record for all actors
                fn.append(RecordActor.handled == 'pending')
            if panel == 'inbox-snooze':
                #fn.append(Record.state == 'snooze')
                fn.append(RecordActor.handled == 'onhold')
            elif panel == 'inbox-archived':
                pass
                #fn.append(Record.state == 'archived')
                fn.append(RecordActor.handled == 'done')
        
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
                fn.append(Record.stage=='shared')
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
    start_record = get_record_by_id(db,start_id)
    start_ids = [start_id]

    for reference in start_record.references:
        start_ids.append(reference.id)

    start_ids = ",".join([str(r) for r in start_ids])

    sql = text(f"""
        WITH RECURSIVE connected_ids AS (
            -- Start with all IDs involved in the initial records
            SELECT record_id AS id FROM recordrecord WHERE record_id IN ({start_ids}) OR reference_id IN ({start_ids})
            UNION
            SELECT reference_id AS id FROM recordrecord WHERE record_id IN ({start_ids}) OR reference_id IN ({start_ids})
            
            UNION
            
            -- Find any record where either side of the link matches an ID we already found
            SELECT CASE 
                WHEN rr.record_id = c.id THEN rr.reference_id 
                ELSE rr.record_id 
            END
            FROM recordrecord rr
            JOIN connected_ids c ON (rr.record_id = c.id OR rr.reference_id = c.id)
        )
        SELECT id FROM connected_ids
        """)

    all_ids = list(set([int(start_id)] + [item[0] for item in db.exec(sql).unique().all()]))

    return Record.id.in_(all_ids)

def get_advance_search_filter(db: Session, data: dict):
    fn = []
    if not data:
        return fn
    
    if 'tag_ids' in data:
        fn.append( Record.tags.any(Tag.id.in_(data['tag_ids'])) ) 

    if 'actor_tags' in data:
        fn.append(RecordActor.params['actor_tags'].contains(data['actor_tags']))

    if 'flow' in data and data['flow']:
        fn.append(Record.flow==data['flow'])
    
    if 'register' in data and data['register']:
        fn.append(Record.register_id==data['register'])
    
    if 'sender' in data and data['sender']:
        fn.append(Record.sender.alias==data['sender'])
    
    if 'target-' in data and data['target']:
        fn.append(Record.actors==data['flow'])
    
    if 'department' in data and data['department']:
        fn.append(Record.unit_id==data['department'])
    
    if 'sequence' in data and data['sequence']:
        fn.append(Record.sequence==data['sequence'])
    
    if 'year' in data and data['year']:
        fn.append(Record.year==data['year'])
    
    if 'audience' in data and data['audience']:
        fn.append(Record.audience==data['audience'])
    
    if 'area' in data and data['area']:
        fn.append(Record.area==data['area'])

    return fn

def get_records(db: Session, actor: Actor, section: str, panel: str, search: str = None, data: dict = None, limit: int = None, offset: int = None, just_number: bool = False) -> list[Record] | int:
    if section == 'cl':
        ctr_alias, flow = panel[:-4].split('-')
        ctr = get_actor_by_alias(db,ctr_alias)
    
        fn = get_filter(db,ctr,section, panel)
    else:
        fn = get_filter(db,actor,section, panel)

    fn += get_advance_search_filter(db,data)

    if search:
        if search.startswith('all_off:'):
            fn.append(get_recursive_ids(search[8:], actor, db, limit, offset))
        else:
            fn.append(get_search_filter(search))
   
    num_stmt = select(func.count(Record.id))
    if section == 'cl':
        record_ctr = aliased(RecordActor, name="status_ctr")
        stmt = select(Record, RecordActor, record_ctr, current_target_subquery.label("target_order"))
        join_condition_ctr = and_(
            Record.id == record_ctr.record_id, 
            record_ctr.actor_id == ctr.id
        )
    else:
        stmt = select(Record, RecordActor, current_target_subquery.label("target_order"))

    join_condition = and_(
        Record.id == RecordActor.record_id, 
        RecordActor.actor_id == actor.id
    )
 
    if section == 'board':
        if panel.startswith('inbox') or panel.startswith('incoming'):
            stmt = stmt.join(RecordActor, join_condition).where(*fn)
            num_stmt = num_stmt.join(RecordActor, join_condition).where(*fn)
        elif panel.startswith('outbox') or panel.startswith('outcoming') or panel in ['all','mustread','unread', 'despacho']:
            stmt = stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
            num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
    elif section == 'register':
        stmt = stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
        num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).where(*fn)
    elif section == 'cl':
        if flow == 'in':
            stmt = stmt.join(RecordActor, join_condition, isouter=True).join(record_ctr, join_condition_ctr).where(*fn)
            num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).join(record_ctr, join_condition_ctr).where(*fn)
        else:
            stmt = stmt.join(RecordActor, join_condition, isouter=True).join(record_ctr, join_condition_ctr, isouter=True).where(*fn)
            num_stmt = num_stmt.join(RecordActor, join_condition, isouter=True).join(record_ctr, join_condition_ctr, isouter=True).where(*fn)

    stmt = stmt.options(
        joinedload(Record.sender),
        joinedload(Record.register),
        joinedload(Record.unit),
        selectinload(Record.tags),
        selectinload(Record.actors),
        selectinload(Record.files),
        selectinload(Record.references),
        joinedload(RecordActor.actor),
        joinedload(RecordActor.record)
    ).limit(limit).offset(offset).order_by(desc(Record.updated_at),Record.sequence.desc())
    
    if just_number:
        return db.exec(num_stmt).one()
    
    return db.exec(stmt).unique().all(), db.exec(num_stmt).one()

def get_all_records(db: Session) -> list[Record]:
    stmt = select(Record)

    return db.exec(stmt).all()

def get_records_for_actor(db: Session, sender_id: int) -> list[Record]:
    return db.exec(select(Record).where(Record.sender_id == sender_id)).all()

def get_record_by_protocol(db: Session, protocol: str, sequence: int, year: int) -> Record | None:
    return db.exec(select(Record).where((Record.protocol == protocol) & (Record.sequence == sequence) & (Record.year == year))).all()

def create_record(db: Session, record_in: RecordCreate) -> Record:
    db_rec = Record(title=record_in.title, sequence=record_in.sequence, year=record_in.year, flow=record_in.flow, sender_id=record_in.sender_id)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec

def update_record(db: Session, db_rec: Record, rec_in: RecordUpdate) -> Record:
    data = rec_in.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(db_rec, k, v)
    db.add(db_rec); db.commit(); db.refresh(db_rec)
    return db_rec
