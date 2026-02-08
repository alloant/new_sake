from datetime import datetime
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON

class Kind(str, Enum): # Roles of users
    USER = "user"
    CONTACT = "contact"
    CTR = "ctr"

class ActorSettings(object):
    def get_setting(self,setting):
        if setting in self.settings:
            return self.settings[setting]

        match setting:
            case 'limit_records':
                return 20
            case 'theme':
                return 'light'

class Actor(SQLModel, ActorSettings, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, index=True, max_length=50)
    full_name: str | None = Field(max_length=200, default=None)
    email: str = Field(max_length=200, default=None)
    kind: Kind = Field()
    is_active: bool = True
    scopes: list[str] = Field(sa_column=Column(JSON, nullable=False), default_factory=list)
    settings: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    #records: list["Record"] = Relationship(back_populates="sender")
