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

class Area(str, Enum):
    AES = "aes"
    ASO = "#c96969"
    ASMO = "#69c98f"
    IND = "#697cc9"
    J = "#c6c969"

class Audience(str, Enum):
    ALL = 'all'
    DR = 'dr'
    PERMANENT = 'permanent'

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
    state: State = Field(max_length=20)
    stage: Stage = Field(max_length=20)
    audience: Audience = Field(default=Audience.ALL, max_length=10)
    title: str | None = Field(max_length=500, default="")
    flow: Flow = Field(max_length=20)
    sequence: int = Field(description="Sequential number (nn)")
    year: int = Field(description="Year (yy)")
    register_id: int | None = Field(default=None, foreign_key="register.id", description="Register")
    area: Area = Field(max_length=4, default="aes")
    params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)

    sender_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor sending/producing the note")
    unit_id: int | None = Field(default=None, foreign_key="actor.id", description="Department in charge of the record")

    sender: "Actor" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Record.sender_id]" # Tell SQLAlchemy which key to use
        }
    )

    unit: "Actor" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Record.unit_id]"
        }
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)#, sa_column=Column("updated_at", SQLModel.__config__.orm_mode and None))

    tags: list["Tag"] = Relationship(link_model=RecordTag)
    register: "Register" = Relationship()
    files: list["File"] = Relationship()
    actors: list["RecordActor"] = Relationship(back_populates="record", sa_relationship_kwargs={"order_by": "RecordActor.target,RecordActor.handled.desc()"})


    references: list["Record"] = Relationship(
        link_model=RecordRecord,
        sa_relationship_kwargs={
            "primaryjoin": "Record.id == RecordRecord.record_id",
            "secondaryjoin": "Record.id == RecordRecord.reference_id",
        },
    )

    def stage_icon(self, status):
        if self.state == 'archived':
            title = 'Archived'
            color, icon = 'font-color-inactive', 'archive-outline'
        elif self.state == 'snooze':
            title = 'On hold'
            color, icon = 'font-color-inactive', 'alarm-snooze'
        
        match self.stage:
            case "inbox":
                title = ''
                color, icon = 'font-color-active', 'file-alert'
            case "despacho":
                if status and status.params.get('dispatcher_signature'):
                    title = 'Signed'
                    color, icon = 'font-color-inactive', 'briefcase-outline'
                else:
                    signatures = []
                    for actor in self.actors:
                        if actor.params.get('dispatcher_signature'):
                            signatures.append(actor.alias)
                    if signatures:
                        rst =  ", ".join(signatures)
                        title = f"Pending (signed by {rst})"
                        color, icon = 'font-color-active', 'briefcase-account'
                    else:
                        title = "Pending"
                        color, icon = 'font-color-active', 'briefcase'
            case "registered":
                title = ''
                color, icon = 'font-color-active', 'file'
            case "draft":
                title = ''
                color, icon = 'font-color-active', 'progress-wrench'
            case "outbox":
                title = ''
                color, icon = 'font-color-active', 'timer-sand'
            case "sent":
                title = ''
                color, icon = 'font-color-active', 'email-fast-outline'
            case "sketch":
                title = ''
                color, icon = 'font-color-active', 'progress-wrench'
            case "shared":
                title = ''
                color, icon = 'font-color-active', 'account-arrow-right-outline'
            case "closed":
                title = ''
                color, icon = 'font-color-active', 'check'
        
        if self.audience == 'permanent':
            color = 'font-color-permanent'

        if title:
            return f'<div class="iconify has-tooltip-multiline has-tooltip-arrow has-tooltip-right" data-tooltip="{title}"><i class="iconify" data-width="1em" data-icon="mdi-{icon}" style="color: var(--{color});"></i></div>'
        
        return f'<div class="iconify"><i class="iconify" data-width="1em" data-icon="mdi-{icon}" style="color: var(--{color});"></i></div>'
