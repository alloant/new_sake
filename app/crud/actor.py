from sqlmodel import Session, select, and_, or_

from app.core.database import engine
from app.models.actor import Actor

def get_actor_by_id(actor_id: int, db: Session) -> Actor | None:
    return db.get(Actor, actor_id)

def get_actor_by_ids(actor_ids: list[int], db: Session) -> Actor | None:
    return db.exec(select(Actor).where(Actor.id.in_(actor_ids))).all()

def get_actor_by_alias(alias: str, db: Session) -> Actor | None:
    return db.exec(select(Actor).where(Actor.alias == alias)).first()

def get_actor_by_email(email: str, db: Session) -> Actor | None:
    return db.exec(select(Actor).where(Actor.email == email)).first()

def get_actors(db: Session) -> list[Actor]:
    return db.exec(select(Actor)).all()

def create_actor(alias: str, kind: str, db: Session) -> Actor:
    db_actor = Register(alias=alias, kind=kind)
    db.add(db_actor); db.commit(); db.refresh(db_actor)
    return db_actor

def get_ctrs(db: Session, filter: str = "") -> list(Actor):
    if filter:
        return db.exec(select(Actor).where(and_(or_(Actor.alias.contains(filter),Actor.full_name.contains(filter)),Actor.kind=='ctr',Actor.is_active==1)).order_by(Actor.alias)).all()
    return db.exec(select(Actor).where(and_(Actor.kind=='ctr',Actor.is_active==1)).order_by(Actor.alias)).all()

def get_all_deps(db: Session):
    return select(Actor).where(and_(Actor.active,Actor.kind=='dep')).all()

def get_all_alias_deps(db: Session):
    return db.exec(select(Actor.alias).where(and_(Actor.is_active,Actor.kind=='dep')).order_by(Actor.alias)).all()

def get_senders_register(db: Session, flow: str, register_alias: str, ctr_alias: str = None) -> list(Actor):
    if flow == 'inbound':
        return db.exec(select(Actor).where(and_(Actor.is_active,or_(Actor.kind=='ctr',Actor.kind=='contact'),Actor.scopes.contains(f'contact:{register_alias}'))).order_by(Actor.alias)).all()
    elif flow in ['outbound','internal_cr']: ## Note we are sending. Sender is a dr o of
        return db.exec(select(Actor).where(and_(Actor.is_active, Actor.kind=='user',or_(Actor.scopes.contains('of'),Actor.scopes.contains('dr')))).order_by(Actor.alias)).all()
    elif flow == 'internal_cl': ## Note we are sending. Sender is a dr o of
        return db.exec(select(Actor).where(and_(Actor.is_active, Actor.kind=='user',Actor.scopes.contains(f'ctr_{ctr_alias}:editor'))).order_by(Actor.alias)).all()

def get_targets_register(db: Session, flow: str, register_alias: str, ctr_alias: str = None) -> list(Actor):
    if flow == 'outbound':
        return db.exec(select(Actor).where(and_(Actor.is_active,Actor.scopes.contains(f'contact:{register_alias}'))).order_by(Actor.alias)).all()
    elif flow in ['inbound','internal_cr']: ## Note we are sending. Sender is a dr o of
        return db.exec(select(Actor).where(and_(Actor.is_active, Actor.kind=='user',or_(Actor.scopes.contains('of'),Actor.scopes.contains('dr')))).order_by(Actor.alias)).all()
    elif flow == 'internal_cl': ## Note we are sending. Sender is a dr o of
        return db.exec(select(Actor).where(and_(Actor.is_active, Actor.kind=='user',Actor.scopes.contains(f'ctr_{ctr_alias}:editor'))).order_by(Actor.alias)).all()
