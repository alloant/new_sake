from sqlmodel import Session, select

from app.core.database import engine
from app.models.actor import Actor

def get_actor_by_id(actor_id: int, db: Session = None) -> Actor | None:
    if not db:
        db = Session(engine)
    return db.get(Actor, actor_id)

def get_actor_by_alias(alias: str, db: Session = None) -> Actor | None:
    if not db:
        db = Session(engine)
    return db.exec(select(Actor).where(Actor.alias == alias)).first()

def get_actors(db: Session = None) -> List[Actor]:
    if not db:
        db = Session(engine)
    return db.exec(select(Actor)).all()

def create_actor(alias: str, kind: str, db: Session = None) -> Actor:
    if not db:
        db = Session(engine)
    db_actor = Register(alias=alias, kind=kind)
    db.add(db_actor); db.commit(); db.refresh(db_actor)
    return db_actor
