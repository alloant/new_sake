from enum import Enum
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import SQLModel, Field, Relationship, Column

class HandledStatus(str, Enum):
    NONE = ""
    # Notes
    READ = "read"
    UNREAD = "unread"
    MUSTREAD = "mustread"
    # Notes cl when the ctr is the actor
    PENDING = "pending"
    DONE = "done"
    # Proposals
    UNSIGNED = "unsigned"
    RETURN = "return"
    DENY = "deny"
    APPROVED = "approved"
    

class RecordUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor_id: int = Field(foreign_key="actor.id")
    record_id: int = Field(foreign_key="record.id")

    handled: HandledStatus = Field(default="")
    target: int = Field(default=0) # 0 means not involve. > 0 means involved. The number marks the order
    
    #params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    params: dict = Field(
        sa_column=Column(MutableDict.as_mutable(JSON), nullable=False), 
        default_factory=dict
    )    
    record: "Record" = Relationship(back_populates="actors")
    actor: "Actor" = Relationship()

class RecordSection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor_id: int = Field(foreign_key="actor.id") # Here is gona be a ctr or cr
    record_id: int = Field(foreign_key="record.id")

    handled: HandledStatus = Field(default="")
    target: int = Field(default=0) # 0 means not involve. > 0 means involved. The number marks the order
    
    #params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    params: dict = Field(
        sa_column=Column(MutableDict.as_mutable(JSON), nullable=False), 
        default_factory=dict
    )    
    #record: "Record" = Relationship()
    #actor: "Actor" = Relationship()
