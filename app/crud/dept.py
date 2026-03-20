from sqlmodel import Session, select

from app.core.database import engine
from app.models.dept import Dept

def get_dept_by_id(dept_id: int, db: Session) -> Dept | None:
    return db.get(Dept, dept_id)

def get_dept_by_alias(alias: str, db: Session) -> Dept | None:
    return db.exec(select(Dept).where(Dept.alias == alias)).first()

def get_dept_by_actor_id(actor_id: int, db: Session) -> Dept | None:
    return db.exec(select(Dept).where(Dept.actor_id == actor_id)).first()

def get_all_dept(db: Session = None) -> List[Dept]:
    return db.exec(select(Dept)).all()

def get_all_dept_alias(db: Session = None) -> List[Dept]:
    return db.exec(select(Dept.alias)).all()

def create_dept(alias: str, kind: str, db: Session) -> Dept:
    db_dept = Dept(alias=alias, kind=kind)
    db.add(db_dept); db.commit(); db.refresh(db_dept)
    return db_dept
