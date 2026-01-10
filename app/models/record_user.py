from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class ReadStatus(str, Enum):
    READ = "read"
    UNREAD = "unread"
    MUSTREAD = "mustread"

class RecordUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    record_id: int = Field(foreign_key="record.id")

    read_status: ReadStatus = Field(default=ReadStatus.UNREAD)
    is_owner: bool = Field(default=False)
    
    record: "Record" = Relationship(back_populates="users")
    user: "User" = Relationship(back_populates="records")
    #record: "Record" = Relationship(back_populates="users")
    #user: "User" = Relationship(back_populates="records")

    @property
    def read_status_html(self):
        if self.read_status == ReadStatus.READ:
            return ''
        return 'has-text-weight-bold'

