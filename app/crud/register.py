from datetime import date
from sqlmodel import Session, select, func, and_

from app.core.database import engine
from app.models.register import Register
from app.models.record import Record

def get_register_by_id(db: Session, register_id: int) -> Register | None:
    return db.get(Register, register_id)

def get_register_by_alias(db: Session, alias: str) -> Register | None:
    return db.exec(select(Register).where(Register.alias == alias)).first()

def get_registers(db: Session = None) -> list[Register]:
    return db.exec(select(Register)).all()

def get_last_sequence(db: Session, register_id: int, sender: Actor = None):
    if sender:
        last = db.exec(select(func.max(Record.sequence)).where(and_(Record.register_id==register_id,Record.year==date.today().year,Record.sender_id==sender.id))).one()
    else:
        last = db.exec(select(func.max(Record.sequence)).where(and_(Record.register_id==register_id,Record.year==date.today().year,Record.flow=='outbound'))).one()

    return int(last) + 1

def create_register(db: Session, alias: str, full_name: str) -> Register:
    db_register = Register(alias=alias, full_name=full_name)
    db.add(db_register); db.commit(); db.refresh(db_register)
    return db_register

def has_permission(actor_perms, required_perms):
    if not required_perms:
        return True

    for u_perm in actor_perms:
        for r_perm in required_perms:
            if r_perm.endswith('*'):
                if u_perm.startswith(f"{r_perm[:-1]}"):
                    return u_perm
            else:
                if u_perm == r_perm or u_perm.startswith(f"{r_perm}:"):
                    return u_perm

    return ''

def get_actor_registers(db: Session, actor_perms, only_alias = True):
    registers = get_registers(db)
    available = {}
    
    if only_alias:
        for register in registers:
            available[register.alias] = has_permission(actor_perms,[register.alias])
    else:
        return [register for register in registers if has_permission(actor_perms,[register.alias])]

    return available

def get_actor_ctrs(db: Session, actor_perms):
    rst = []
    for u_perm in actor_perms:
        if u_perm.startswith("ctr_"):
            ctr_alias = u_perm[4:]
            rst.append(ctr_alias.split(':')[0])

    return rst
