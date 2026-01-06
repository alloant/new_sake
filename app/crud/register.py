from sqlmodel import Session, select

from app.core.database import engine
from app.models.register import Register

def get_register_by_id(register_id: int, db: Session = None) -> Register | None:
    if not db:
        db = Session(engine)
    return db.get(Register, register_id)

def get_register_by_alias(alias: str, db: Session = None) -> Register | None:
    if not db:
        db = Session(engine)
    return db.exec(select(Register).where(Register.alias == alias)).first()

def get_registers(db: Session = None) -> list[Register]:
    if not db:
        db = Session(engine)
    return db.exec(select(Register)).all()

def create_register(alias: str, full_name: str, db: Session = None) -> Register:
    if not db:
        db = Session(engine)
    db_register = Register(alias=alias, full_name=full_name)
    db.add(db_register); db.commit(); db.refresh(db_register)
    return db_register
