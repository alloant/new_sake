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
        return db.exec(select(Actor).where(and_(or_(Actor.alias.contains(filter),Actor.full_name.contains(filter)),Actor.kind=='ctr',Actor.is_active==1))).all()
    return db.exec(select(Actor).where(and_(Actor.kind=='ctr',Actor.is_active==1))).all()

def get_all_deps(db: Session):
    return select(Actor).where(and_(Actor.active,Actor.kind=='dep')).all()

def get_all_alias_deps(db: Session):
    return db.exec(select(Actor.alias).where(and_(Actor.is_active,Actor.kind=='dep'))).all()
