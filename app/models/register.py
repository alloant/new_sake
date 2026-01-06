from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON

class Register(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, max_length=10)
    full_name: str | None = Field(max_length=50, default="")
    active: bool | None = Field(default=True)

    protocol: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)

    records: list["Record"] = Relationship(back_populates="register")
