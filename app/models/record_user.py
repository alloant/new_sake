from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class ReadStatus(str, Enum):
    READ = "read"
    UNREAD = "unread"
    MUSTREAD = "mustread"

class RecordUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    record_id: int | None = Field(default=None, foreign_key="record.id", primary_key=True)

    read_status: ReadStatus = Field()
    is_owner: bool = Field(default=False)
    
    record: "Record" = Relationship(back_populates="users")
    user: "User" = Relationship(back_populates="records")
    #record: "Record" = Relationship(back_populates="users")
    #user: "User" = Relationship(back_populates="records")

