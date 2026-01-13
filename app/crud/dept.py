from sqlmodel import Session, select

from app.core.database import engine
from app.models.dept import Dept

def get_dept_by_id(dept_id: int, db: Session = None) -> Dept | None:
    if not db:
        db = Session(engine)
    return db.get(Dept, dept_id)

def get_dept_by_alias(alias: str, db: Session = None) -> Dept | None:
    if not db:
        db = Session(engine)
    return db.exec(select(Dept).where(Dept.alias == alias)).first()

def get_dept_by_actor_id(actor_id: int, db: Session = None) -> Dept | None:
    if not db:
        db = Session(engine)
    return db.exec(select(Dept).where(Dept.actor_id == actor_id)).first()

def get_depts(db: Session = None) -> List[Dept]:
    if not db:
        db = Session(engine)
    return db.exec(select(Dept)).all()

def create_dept(alias: str, kind: str, db: Session = None) -> Dept:
    if not db:
        db = Session(engine)
    db_dept = Dept(alias=alias, kind=kind)
    db.add(db_dept); db.commit(); db.refresh(db_dept)
    return db_dept
