from sqlmodel import Session, select
from argon2 import PasswordHasher

from app.core.database import engine
from app.models import Actor


def hash_password(str_password): 
    ph = PasswordHasher()
    return ph.hash(str_password)

def verify_password(hash_password,password):
    try:
        ph.verify(hash_result, password)
        return True
    except Exception as e:
        return False

def get_user_by_id(user_id: int, db: Session) -> User | None:
    return db.get(User, user_id)

def get_user_by_email(email: str, db: Session) -> User | None:
    return db.exec(select(User).where(User.email == email)).first()

def get_user_by_actor_id(actor_id: int, db: Session) -> User | None:
    return db.exec(select(User).where(User.actor_id == actor_id)).first()

def get_users(db: Session = None) -> list[User]:
    return db.exec(select(User)).all()

def verify_user_password(db_user: User, password: str):
    return verify_password(db_user.hashed_password,password)

def create_user(email: str, full_name: str, password: str, db: Session) -> User:
    hashed = hash_password(password)
    db_user = User(email=email, hashed_password=hashed, full_name=full_name, kind="user")
    db.add(db_user); db.commit(); db.refresh(db_user)
    return db_user

def update_user(db_user: User, attr: str, value, db: Session) -> User:
    setattr(db_user, attr, value)
    db.add(db_user); db.commit(); db.refresh(db_user)
    return db_user
