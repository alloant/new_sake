from pydantic import BaseModel
from datetime import date
from app.views.actions import get_actions

class Action(BaseModel):
    id: str
    title: str
    hxget: str | None = None
    hxtarget: str | None = None
    icon: str | None = None
    perms: list[str] = []

class ActionGroup(BaseModel):
    title: str
    items: list[Action]

class RecordMethod(object):
    @property
    def protocol(self):
        return f'{self.code} {self.sequence}/{str(self.year)[2:]}'

    @property
    def code(self):
        if self.flow.value in self.register.protocol:
            return eval(self.register.protocol[self.flow.value])

        return ''

    @property
    def date(self):
        return self.updated_at.strftime('%Y-%m-%d') if self.updated_at > self.created_at else self.created_at.strftime('%Y-%m-%d')

    @property
    def targets(self):
        return [target for target in self.users if target.target > 0]

    def get_actions(self, state, current_user, section, panel):
        actions = []
        if self.flow == 'inbound':
            actions.append(ActionGroup(title="Read",items=[]))
            if not state or state.read_status == 'read':
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
