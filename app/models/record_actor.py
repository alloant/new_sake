from enum import Enum
from pydantic import ConfigDict
from datetime import date

from sqlalchemy import Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import SQLModel, Field, Relationship, Column, select

class HandledStatus(str, Enum):
    NONE = ""
    # Notes
    READ = "read" # When target it goes from unread to pending
    UNREAD = "unread"
    MUSTREAD = "mustread"
    # Notes status for the actor
    PENDING = "pending"
    DONE = "done"
    ONHOLD = "onhold"
    # Proposals
    UNSIGNED = "unsigned"
    RETURN = "return"
    DENY = "deny"
    APPROVED = "approved"
    

class RecordActor(SQLModel, table=True):
    model_config = ConfigDict(ignored_types=(hybrid_property,))
    id: int | None = Field(default=None, primary_key=True)
    actor_id: int = Field(foreign_key="actor.id", index=True)
    record_id: int = Field(foreign_key="record.id", index=True)

    handled: HandledStatus = Field(default="", index=True)
    target: int = Field(default=0, index=True) # 0 means not involve. > 0 means involved. The number marks the order
    
    
    #params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    params: dict = Field(
        sa_column=Column(MutableDict.as_mutable(JSON), nullable=False), 
        default_factory=dict
    )


    due_date: date | None = Field(default_factory=None)
    record: "Record" = Relationship(back_populates="actors")
    actor: "Actor" = Relationship()
    
    # Add a composite index in table_args for sorting efficiency
    model_config = {
        "table_args": (
            Index("idx_record_target_handled", "record_id", "target", "handled"),
        )
    }
    
