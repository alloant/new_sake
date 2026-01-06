from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Contact(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=50)
    full_name: str | None = Field(max_length=200, default=None)
    actor_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

