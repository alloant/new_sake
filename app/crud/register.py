from sqlmodel import Session, select

from app.core.database import engine
from app.models.register import Register

def get_register_by_id(register_id: int, db: Session) -> Register | None:
    return db.get(Register, register_id)

def get_register_by_alias(alias: str, db: Session) -> Register | None:
    return db.exec(select(Register).where(Register.alias == alias)).first()

def get_registers(db: Session = None) -> list[Register]:
    return db.exec(select(Register)).all()

def create_register(alias: str, full_name: str, db: Session) -> Register:
    db_register = Register(alias=alias, full_name=full_name)
    db.add(db_register); db.commit(); db.refresh(db_register)
    return db_register

def has_permission(user_perms, required_perms):
    if not required_perms:
        return True

    for u_perm in user_perms:
        for r_perm in required_perms:
            if u_perm == r_perm or u_perm.startswith(f"{r_perm}:"):
                return u_perm

    return ''

def get_user_registers(user_perms, db: Session):
    registers = get_registers(db)
    available = {}
    for register in registers:
        available[register.alias] = has_permission(user_perms,[register.alias])

    return available

