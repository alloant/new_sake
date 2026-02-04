from enum import Enum
from sqlalchemy.dialects.mysql import JSON
from sqlmodel import SQLModel, Field, Relationship, Column

class ReadStatus(str, Enum):
    READ = "read"
    UNREAD = "unread"
    MUSTREAD = "mustread"

class TargetAction(str, Enum):
    PENDING = "pending"
    RETURN = "return"
    DENY = "deny"
    APPROVED = "approved"

class RecordUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    record_id: int = Field(foreign_key="record.id")

    read_status: ReadStatus = Field(default=ReadStatus.UNREAD)
    
    target: int = Field(default=0) # 0 means not involve. > 0 means involved. The number marks the order
    target_action: TargetAction = Field(default=TargetAction.PENDING)
    
    params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    
    record: "Record" = Relationship(back_populates="users")
    user: "User" = Relationship()

    
