from sqlmodel import Session

from app.core.database import engine, get_old_data

from app.models import User, Actor, Record, RecordUser, Register, Contact, Ctr
from app.models.record.record import Tag, RecordTag

from app.crud.actor import get_actor_by_alias, get_actors
from app.crud.register import get_register_by_alias
from app.crud.record import create_record, get_all_records
from app.crud.user import create_user, get_users, get_user_by_id, get_user_by_actor_id

def transfer_registers_old():
    db = Session(engine)
    rows = get_old_data('SELECT * from register')
    registers = []
    for row in rows:
        if not row['alias'] in registers:
            print(row['alias'])
            db_register = Register(alias=row['alias'],full_name=row['name'])
            registers.append(row['alias'])
            db.add(db_register)
    db.commit()

def transfer_registers():
    db = Session(engine)
    regs = [
        {'id': 1, 'alias': 'cg', 'full_name': 'General Council', 'active': 1, 'protocol': {'inbound': "getattr(getattr(self,'sender'),'alias')", 'outbound': "'Aes'"}},
        {'id':2, 'alias': 'asr', 'full_name': 'Regional Advisory', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'cr-asr'"}},
        {'id':3, 'alias': 'ctr', 'full_name': 'Centers', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'cr'"}},
        {'id':4, 'alias': 'r', 'full_name': 'Regions', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'Aes-r'"}},
        {'id':5, 'alias': 'vcr', 'full_name': 'Regional Vicar', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'vcr'"}},
        {'id':6, 'alias': 'vc', 'full_name': 'Regional Vicars', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'vc'"}},
        {'id':7, 'alias': 'dg', 'full_name': 'Delegate', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'dg'"}},
        {'id':8, 'alias': 'cc', 'full_name': 'cc', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'cc'"}},
        {'id':9, 'alias': 'desr', 'full_name': 'Preffect', 'active': 1, 'protocol': {"inbound": "getattr(getattr(self,'sender'),'alias')","outbound": "'pffer'"}},
        {'id':10, 'alias': 'mat', 'full_name': 'Proposals', 'active': 1, 'protocol': {"internal_cr": "getattr(getattr(self,'sender'),'alias')","outbound": "''"}}
    ]

    for reg in regs:
        print(reg)
        db_register = Register(id=reg['id'],alias=reg['alias'],full_name=reg['full_name'],active=reg['active'],protocol=reg['protocol'])
        db.add(db_register)

    db.commit()

def transfer_actors():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    actors = []
    for row in rows:
        if not row['alias'] in actors:
            kind = 'contact' if row['category'] == 'me' else row['category']
            kind = 'user' if row['category'] in ['dr','of','cl'] else kind
            print(row['alias'],kind)
            db_actor = Actor(alias=row['alias'],kind=kind)
            actors.append(row['alias'])
            db.add(db_actor)
    db.commit()

def transfer_users():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    emails = []
    actors = get_actors()
    for row in rows:
        if row['email'] and row['category'] in ['dr','of','cl']:
            if not row['email'] in emails:
                print(row['alias'],row['email'], row['name'])
                #actor = get_actor_by_alias(row['alias'])
                for actor in actors:
                    if actor.alias == row['alias']:
                        break
                db_user = User(email=row['email'], hashed_password='', full_name=row['name'],role="dr",actor_id=actor.id)
                db.add(db_user)
                emails.append(row['email'])
    db.commit()

def transfer_contacts():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    alias = []
    actors = get_actors()
    for row in rows:
        if row['alias'] and row['category'] == 'contact':
            if not row['alias'] in alias:
                print(row['alias'],row['email'], row['name'])

                for actor in actors:
                    if actor.alias == row['alias']:
                        break
                db_contact = Contact(email=row['email'], full_name=row['name'],actor_id=actor.id)
                db.add(db_contact)
                alias.append(row['alias'])
    db.commit()

def transfer_ctrs():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    alias = []
    actors = get_actors()
    for row in rows:
        if row['alias'] and row['category'] == 'contact':
            if not row['alias'] in alias:
                print(row['alias'],row['email'], row['name'])

                for actor in actors:
                    if actor.alias == row['alias']:
                        break
                db_ctr = Ctr(email=row['email'], full_name=row['name'],actor_id=actor.id)
                db.add(db_ctr)
                alias.append(row['alias'])
    db.commit()

def transfer_notes():
    db = Session(engine)
    rows = get_old_data('SELECT * from note')
    users = get_old_data('SELECT * from user')

    actors = get_actors()
    
    for row in rows:
        title = row['content']
        sequence = row['num']
        year = row['year']
        reg = row['register_id']

        register_id = reg
        
        for user in users:
            if user['id'] == row['sender_id']:
                break
       
        for actor in actors:
            if actor.alias == user['alias']:
                break
        
        if reg == 10:
            flow = 'internal_cr'
        else:
            if user['category'] in ['dr','of']:
                flow = 'outbound'
            else:
                flow = 'inbound'
        
        match row['status']:
            case 'draft':
                stage = 'draft' if flow == 'outbound' else 'sketch'
            case 'registered':
                stage = 'registered'
            case 'sent':
                stage = 'sent'
            case 'approved':
                stage = 'closed'
            case 'shared':
                stage = 'shared'
            case 'despacho':
                stage = 'despacho'

        state = 'active' if row['archived'] == 0 else 'archived'

        print(title)
        db_record = Record(title=title,stage=stage,state=state,register_id=register_id,sequence=sequence,year=year,flow=flow,sender_id=actor.id, created_at=row['n_date'], updated_at=row['n_date'], params={'old_id': row['id']})

        db.add(db_record)

    db.commit()


def transfer_note_user():
    db = Session(engine)
    records = get_all_records()

    for record in records:
        old_id = record.params['old_id']
        print(old_id,record.title)
        status = get_old_data(f'SELECT * FROM noteuser WHERE note_id = {old_id}')
        for state in status:
            read = "read" if state['read'] == 0 else "unread"
            if state['target'] == 1:
                target = state['target_order'] + 1
                target_action = 'approved' if state['target_acted'] == 1 else 'pending'
            else:
                target = 0
                target_action = 'pending'
            user_old_id = state['user_id']
            user_old = get_old_data(f'SELECT * FROM user WHERE id = {user_old_id}')[0]
            actor = get_actor_by_alias(user_old['alias'], db)
            user = get_user_by_actor_id(actor.id, db)
            if user:
                db_record_user = RecordUser(user_id=user.id,record_id=record.id,read_status=read,target=target,target_action=target_action)
            
            db.add(db_record_user)
    db.commit()

def transfer_tags():
    db = Session(engine)
    tags = get_old_data("SELECT * FROM tag")

    for tag in tags:
        new_tag = Tag(id=tag['id'],title=tag['text'])
        db.add(new_tag)

    db.commit()

def transfer_record_tag():
    db = Session(engine)
    records = get_all_records()

    for record in records:
        old_record_id = record.params['old_id']
        tags = get_old_data(f"SELECT * FROM note_tag WHERE note_id = {old_record_id}")
        for tag in tags:
            recordtag = RecordTag(record_id=record.id,tag_id=tag['tag_id'])
            db.add(recordtag)

    db.commit()


