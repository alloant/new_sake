from enum import Enum
from sqlalchemy.dialects.mysql import JSON
from sqlmodel import SQLModel, Field, Relationship, Column

from app.views.actions import Action, ActionGroup

class ReadStatus(str, Enum):
    READ = "read"
    UNREAD = "unread"
    MUSTREAD = "mustread"

class TargetAction(str, Enum):
    PENDING = "pending"
    RETURN = "return"
    DENY = "deny"
    APPROVED = "approved"

class RecordUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    record_id: int = Field(foreign_key="record.id")

    read_status: ReadStatus = Field(default=ReadStatus.UNREAD)
    
    target: int = Field(default=0) # 0 means not involve. > 0 means involved. The number marks the order
    target_action: TargetAction = Field(default=TargetAction.PENDING)
    
    params: dict[str,str] = Field(sa_column=Column(JSON, nullable=False), default_factory=dict)
    
    record: "Record" = Relationship(back_populates="users")
    user: "User" = Relationship(back_populates="records")

    @property
    def read_status_html(self):
        if self.read_status == ReadStatus.READ:
            return ''
        return 'has-text-weight-bold'

    def get_actions(self, record, current_user, section, panel):
        actions = []
        if record.flow == 'inbound':
            actions.append(ActionGroup(title="Read",items=[]))
            if self.read_status == 'read':
                actions[-1].items.append(Action(id="mark_unread", title="Mark as unread", hxget="/action?action=mark_unread", icon="mdi-email-open-outline"))
            else:
                actions[-1].items.append(Action(id="mark_read", title="Mark as read", hxget="/action?action=mark_read", icon="mdi-email-check-outline"))

        actions.append(ActionGroup(title="Inbox",
            items=[
                Action(id="enable_snooze", title="Snooze", hxget="/action?action=enable_snooze", icon="mdi-alarm-snooze"),
                Action(id="disable_snooze", title="Disable snooze", hxget="/action?action=disable_snooze", icon="mdi-weather-sunset"),
                Action(id="archive", title="Archive", hxget="/action?action=archive", icon="mdi-archive-arrow-down-outline"),
                Action(id="restore", title="Restore", hxget="/action?action=restore", icon="mdi-archive-arrow-up-outline")
                ]))

        actions.append(ActionGroup(title="Info",
            items=[
                Action(id="check_info", title="Info about the note", hxget="/action?action=check_info", icon="mdi-information-outline"),
                Action(id="recursive_search", title="List all notes related with this entry", hxget="/action?action=recursive_search", icon="mdi-archive-search-outline")
                ]))

        return actions
