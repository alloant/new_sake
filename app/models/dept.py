from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Dept(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str | None = Field(max_length=10, default=None)
    full_name: str | None = Field(max_length=100, default=None)
    color: str | None = Field(max_length=10, default=None)
    actor_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    records: list["Record"] = Relationship(back_populates="dept")
