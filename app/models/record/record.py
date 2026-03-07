from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime

from app.models.record_actor import RecordActor
from .recordMethods import RecordMethod

class Flow(str, Enum): # Flow of records
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL_CR = "internal_cr"
    INTERNAL_CL = "internal_cl"

class Stage(str, Enum):
    # Inbound
    INBOX = "inbox"
    DESPACHO = "despacho"
    REGISTERED = "registered"
    # Outbound
    DRAFT = "draft"
    OUTBOX = "outbox"
    SENT = "sent"
    # Internal
    SKETCH = "sketch"
    SHARED = "shared"
    CLOSED = "closed"

class State(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SNOOZE = "snooze"

class RecordTag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="record.id")
    tag_id: int = Field(foreign_key="tag.id")

class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None = Field(max_length=10, default="")
    records: list["Record"] = Relationship(back_populates="tags", link_model=RecordTag)


class RecordRecord(SQLModel, table=True):
    record_id: int | None = Field(default=None, foreign_key="record.id", primary_key=True)
    reference_id: int | None = Field(default=None, foreign_key="record.id", primary_key=True)

class Record(SQLModel, RecordMethod, table=True):
    id: int | None = Field(default=None, primary_key=True)
    state: State = Field()
    stage: Stage = Field()
    title: str | None = Field(max_length=500, default="")
    register_id: int | None = Field(default=None, foreign_key="register.id", description="Register")
    flow: Flow = Field()
    sequence: int = Field(description="Sequential number (nn)")
    year: int = Field(description="Year (yy)")
    sender_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor sending/producing the note")
    dept_id: int | None = Field(default=None, foreign_key="dept.id", description="Department in charge of the record")
    params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)#, sa_column=Column("updated_at", SQLModel.__config__.orm_mode and None))

    tags: list["Tag"] = Relationship(link_model=RecordTag)
    sender: "Actor" = Relationship()
    dept: "Dept" = Relationship()
    register: "Register" = Relationship()
    files: list["File"] = Relationship()
    actors: list["RecordActor"] = Relationship(back_populates="record")


    references: list["Record"] = Relationship(
        link_model=RecordRecord,
        sa_relationship_kwargs={
            "primaryjoin": "Record.id == RecordRecord.record_id",
            "secondaryjoin": "Record.id == RecordRecord.reference_id",
        },
    )

    @property
    def stage_icon(self):
        if self.state == 'archived':
            return 'archive-outline'
        elif self.state == 'snooze':
            return 'alarm-snooze'
        
        match self.stage:
            case "inbox":
                return 'file-alert'
            case "despacho":
                return 'briefcase-outline'
            case "registered":
                return 'file-outline'
            case "draft":
                return 'progress-wrench'
            case "outbox":
                return 'timer-sand'
            case "sent":
                return 'email-fast-outline'
            case "sketch":
                return 'progress-wrench'
            case "shared":
                return 'account-arrow-right-outline'
            case "closed":
                return 'check'

