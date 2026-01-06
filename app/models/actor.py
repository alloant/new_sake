from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class Kind(str, Enum): # Kind of actors
    USER = "user"
    CONTACT = "contact"
    CTR = "ctr"
    DEPT = "dept"

class Actor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, index=True, max_length=50)
    kind: Kind = Field()
    
    records: list["Record"] = Relationship(back_populates="sender")

