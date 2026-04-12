from datetime import datetime
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import JSON


class Kind(str, Enum): # Roles of users
    CR = "cr"
    USER = "user"
    CONTACT = "contact"
    CTR = "ctr"
    DEP = "dep"

class ActorSettings(object):
    def get_setting(self,setting):
        if setting in self.settings:
            return self.settings[setting]

        match setting:
            case 'limit_records':
                return 20
            case 'font_size':
                return 2
            case 'theme':
                return 'light'
            case 'admin_active':
                return False
            case 'lang':
                return 'en'
            case 'actor_tags':
                return ''

    @property
    def admin(self):
        if 'admin' in self.scopes and self.get_setting('admin_active'):
            return True
        return False

class Actor(SQLModel, ActorSettings, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, index=True, max_length=50)
    abbr: str = Field(default="", max_length=2)
    full_name: str | None = Field(max_length=200, default=None)
    email: str = Field(max_length=200, default=None)
    kind: Kind = Field()
    is_active: bool = True
    color: str | None = Field(max_length=10, default=None)
    scopes: list[str] = Field(sa_column=Column(JSON, nullable=False), default_factory=list)
    params: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    settings: dict[str, object] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    #records: list["Record"] = Relationship(back_populates="sender")
    
    @property
    def role(self):
        if 'dr' in self.scopes:
            return 'dr'
        elif 'of' in self.scopes:
            return 'of'
        else:
            return 'cl'
    
    @property
    def ctrs_alias(self):
        rst = []
        for scope in self.scopes:
            if scope.startswith('ctr_'):
                rst.append(scope.split(':')[0][4:])
        
        return rst
    @property
    def target_description(self):
        if self.kind == 'user' and 'departments' in self.params:
            return "|".join(self.params['departments'])
        elif self.kind == 'ctr' and 'works' in self.params:
            return "|".join(self.params['works'])
        elif self.kind == 'contact' and 'lang' in self.params:
            return "|".join(self.params['lang'])

        return ''
