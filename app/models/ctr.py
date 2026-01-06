from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Ctr(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor id")
    full_name: str | None = Field(unique=True, max_length=200, default=None)
    email: str | None = Field(max_length=50)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

