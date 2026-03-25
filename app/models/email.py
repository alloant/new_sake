from sqlmodel import SQLModel, Field
from datetime import datetime

class Mail(SQLModel, table=True):
    id: int | None = Field(default = None, primary_key = True)
    uid: str = Field(max_length = 10)
    from_: str = Field(max_length = 100)
    subject: str = Field(max_length = 500, default = None)
    text: str = Field(max_length = 500, default = None)
    date: datetime = Field()
    downloaded: bool = Field(default = False)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
