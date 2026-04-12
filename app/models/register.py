from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON
from enum import Enum

class Type(str, Enum):
    NOTE = 'note'
    PROPOSAL = 'proposal'

class Register(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, max_length=10)
    full_name: str | None = Field(max_length=50, default="")
    active: bool | None = Field(default=True)
    type: Type = Field(default='note')

    protocol: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)

    #records: list["Record"] = Relationship(back_populates="register")
