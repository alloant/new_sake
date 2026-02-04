from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON

from .user_default_settings import UserSettings

class Role(str, Enum): # Roles of users
    DR = "dr"
    OF = "of"
    CL = "cl"

class User(SQLModel, UserSettings, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor_id: int | None = Field(default=None, foreign_key="actor.id", description="Actor id")
    email: str = Field(unique=True, index=True, max_length=50)
    full_name: str | None = Field(max_length=200, default=None)
    role: Role = Field()
    is_active: bool = True
    hashed_password: str = Field(max_length=200, default="")
    scopes: list[str] = Field(sa_column=Column(JSON, nullable=False), default_factory=list)
    
    actor: "Actor" = Relationship()

    settings: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    #records: list["RecordUser"] = Relationship(back_populates="user")


