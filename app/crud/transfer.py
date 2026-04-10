from sqlmodel import Session

from app.core.database import engine, get_old_data

from app.models import Actor, Record, RecordUser, Register, File, RecordRecord
from app.models.record.record import Tag, RecordTag

from app.crud.actor import get_actor_by_alias, get_actors
from app.crud.register import get_register_by_alias
from app.crud.record import create_record, get_all_records, get_record_by_params


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
        {'id':10, 'alias': 'prop', 'full_name': 'Proposals', 'active': 1, 'protocol': {"internal_cr": "getattr(getattr(self,'sender'),'alias')","outbound": "''"}}
    ]

    for reg in regs:
        print(reg)
        db_register = Register(id=reg['id'],alias=reg['alias'],full_name=reg['full_name'],active=reg['active'],protocol=reg['protocol'])
        db.add(db_register)

    db.commit()

def transfer_find_depts():
    db = Session(engine)
    records = get_all_records(db)

    for record in records:
        if record.unit_id:
            continue

        old_record_id = record.params['old_id']
        tags = get_old_data(f'SELECT tag.text from tag, note_tag where tag.id = note_tag.tag_id and note_tag.note_id = {old_record_id}')
        print(tags)
        dept_found = False
        for tag in tags:
            if tag['text'] == 'desr':
                dept = get_actor_by_alias(db,'pffer')
            elif tag['text'] == 'stgr':
                dept = get_actor_by_alias(db,'dest')
            else:
                dept = get_actor_by_alias(db,tag['text'])
            if dept:
                record.unit_id = dept.id
                db.add(record)
                dept_found = True
                break
        """
        if not dept_found:
            print('/',record.sender,'/')
            dept = get_dept_by_actor_id(record.sender_id,db)
            print('++',dept,'++')
            if dept:
                record.unit_id = dept.id
                db.add(record)
                print('#######',record)
                dept_found = True
                break
            else:
                for target in record.targets:
                    dept = get_dept_by_actor_id(target.actor.id,db)
                    if dept:
                        record.unit_id = dept.id
                        db.add(record)
                        dept_found = True
                        break
        """
    db.commit()

def transfer_files():
    db = Session(engine)
    files = get_old_data('SELECT * from file')

    for file in files:
        print(file)
        record = get_record_by_params(db,'old_id',file['note_id'])
        if record:
            db_file = File(name=file['path'],record_id=record.id,permanent_link=file['permanent_link'], created_at=file['date'],updated_at=file['date'])
            db.add(db_file)
    db.commit()



def transfer_users():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    alias = []

    for row in rows:
        if not row['alias'] in alias:
            if row['category'] in ['dr','of','cl']:
                kind = 'user'
            elif row['category'] == 'contact':
                kind = 'contact'
            elif row['category'] == 'ctr':
                kind = 'ctr'
            else:
                kind = 'user'

            print(row['alias'],row['email'], row['name'])

            db_actor = Actor(alias=row['alias'],kind=kind,email=row['email'],full_name=row['name'],created_at=row['date'], scopes=[row['category']])
            db.add(db_actor)
            alias.append(row['alias'])

    #Now deps
    departments = {
        'vcr':  {'full_name': 'Regional vicar', 'color': '#C9A8A8'},
        'vc':   {'full_name': 'Vicars',         'color': '#D0B1A6'},
        'df':   {'full_name': 'Defensor',       'color': '#D9C6A5'},
        'dg':   {'full_name': 'Delegate',       'color': '#B7C9B9'},
        'sccr': {'full_name': 'Secretary',      'color': '#9FBEB7'},
        'sm':   {'full_name': 'St Michael',     'color': '#A9C7DA'},
        'sr':   {'full_name': 'St Raphael',     'color': '#A9A9C6'},
        'sg':   {'full_name': 'St Gabriel',     'color': '#B3AFC6'},
        'ar':   {'full_name': 'Administrator',  'color': '#D8A9C0'},
        'dest': {'full_name': 'Prefecto',       'color': '#96B99E'},
        'pffer':{'full_name': 'Prefecto',       'color': '#C6D1A9'},
        'aop':  {'full_name': 'Apostolate public opinion',  'color': '#BFC5C7'}
    }

    for dep, values in departments.items():
        db_actor = Actor(alias=dep, kind='dep', email='', full_name=values['full_name'], scopes=[], color=values['color'])
        db.add(db_actor)

    db.commit()

def transfer_contacts():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    alias = []
    actors = get_actors(db)
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
    actors = get_actors(db)
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

    actors = get_actors(db)
    
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
    records = get_all_records(db)

    for record in records:
        old_id = record.params['old_id']
        print(old_id,record.title)
        status = get_old_data(f'SELECT * FROM noteuser WHERE note_id = {old_id}')
        for state in status:
            add_it = True
            target = 0
            if record.flow == 'inbound':
                handled = "read" if state['read'] == 1 else "unread"
                target = state['target']
            elif record.flow == 'internal_cr':
                if state['target'] == 1:
                    target = state['target_order'] + 1
                    handled = 'approved' if state['target_acted'] == 1 else 'pending'
                else:
                    target = 0
                    handled = 'pending'
            elif record.flow == 'outbound':
                if state['target'] == 1:
                    target = 1
                    handled = 'done' if state['target_acted'] == 1 else 'pending'
                else:
                    add_it = False

            if add_it:            
                user_old_id = state['user_id']
                user_old = get_old_data(f'SELECT * FROM user WHERE id = {user_old_id}')[0]
                actor = get_actor_by_alias(db,user_old['alias'])
            
                if actor:
                    db_record_user = RecordUser(actor_id=actor.id,record_id=record.id,handled=handled,target=target)
            
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
    records = get_all_records(db)

    for record in records:
        old_record_id = record.params['old_id']
        tags = get_old_data(f"SELECT tag.text as tag_text, tag.id as tag_id FROM note_tag, tag WHERE note_tag.tag_id = tag.id AND note_tag.note_id = {old_record_id}")
        for tag in tags:
            if tag['tag_text'] in ['Ind','J','Aso','Asmo']: # Is Area
                record.area = tag['tag_text'].lower()
                db.add(record)
            elif record.unit and record.unit.alias != tag['tag_text']:
                recordtag = RecordTag(record_id=record.id,tag_id=tag['tag_id'])
                db.add(recordtag)

    db.commit()

def transfer_references():
    db = Session(engine)
    records = get_all_records(db)

    for record in records:
        old_record_id = record.params['old_id']
        references = get_old_data(f"SELECT * FROM note_ref WHERE note_id = {old_record_id}")
        for reference in references:
            print(reference)
            new_reference = get_record_by_params(db,'old_id',reference['ref_id'])
            if new_reference:
                recordref = RecordRecord(record_id=record.id,reference_id=new_reference.id)
            db.add(recordref)

        db.commit()

