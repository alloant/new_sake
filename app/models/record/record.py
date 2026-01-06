from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.models.record_user import RecordUser
from .recordMethods import RecordMethod

class Flow(str, Enum): # Flow of records
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL_CR = "internal_cr"
    INTERNAL_CL = "internal_cl"

class Record(SQLModel, RecordMethod, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None = Field(max_length=500, default="")
    register_id: int | None = Field(default=None, foreign_key="register.id", description="Register")
    flow: Flow = Field()
    sequence: int = Field(description="Sequential number (nn)")
    year: int = Field(description="Year (yy)")
    sender_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor sending/producing the note")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)#, sa_column=Column("updated_at", SQLModel.__config__.orm_mode and None))
    
    users: list["RecordUser"] = Relationship(back_populates="record")
    sender: "Actor" = Relationship(back_populates="records")
    register: "Register" = Relationship(back_populates="records")

