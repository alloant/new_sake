from sqlmodel import Session

from app.core.database import engine, get_old_data

from app.models import User, Actor, Record, Register, Contact, Ctr

from app.crud.actor import get_actor_by_alias, get_actors
from app.crud.register import get_register_by_alias
from app.crud.record import create_record
from app.crud.user import create_user, get_users

def transfer_registers():
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


def transfer_actors():
    db = Session(engine)
    rows = get_old_data('SELECT * from user')
    actors = []
    for row in rows:
        if not row['alias'] in actors:
            kind = 'self' if row['category'] == 'me' else row['category']
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
        print(title)
        db_record = Record(title=title,register_id=register_id,sequence=sequence,year=year,flow=flow,sender_id=actor.id)

        db.add(db_record)

    db.commit()
        
        


