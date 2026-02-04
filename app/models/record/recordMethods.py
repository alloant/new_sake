from pydantic import BaseModel
from datetime import date

class Action(BaseModel):
    id: str
    title: str
    hxget: str = ""
    hxtarget: str = ""
    hxtrigger: str | None = None
    modal: bool = False
    other: str = ""
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
    
    def link(self, idx: int) -> str:
        if idx <= len(self.files) + 1:
            return self.files[idx].link
        return ""

    def read_status_html(self,status,user):
        read = True
        if not status:
            if self.created_at > user.created_at:
                read = False
        elif status.read_status != 'read' and self.created_at > user.created_at:
            read = False
        elif status.read_status == 'read' and self.created_at <= user.created_at:
            read = False
        
        return '' if read else 'has-text-weight-bold'


    def get_actions(self, state, current_user, section, panel):
        actions = []
        if self.flow in ['inbound','internal_cr','internal_cl']:
            actions.append(ActionGroup(title="Read",items=[]))
            if not state or state.read_status == 'unread':
                actions[-1].items.append(Action(id="mark_read", title="Mark as read", hxget="/action?action=mark_read", icon="mdi-email-check"))
            else:
                actions[-1].items.append(Action(id="mark_unread", title="Mark as unread", hxget="/action?action=mark_unread", icon="mdi-email-open-outline"))

            actions.append(ActionGroup(title="Inbox",items=[]))
            if self.state != 'snooze':
                actions[-1].items.append(Action(id="enable_snooze", title="Snooze", hxget="/action?action=enable_snooze", icon="mdi-alarm-snooze"))
            else:
                actions[-1].items.append(Action(id="disable_snooze", title="Disable snooze", hxget="/action?action=disable_snooze", icon="mdi-weather-sunset"))
            
            if self.state != 'archived':
                actions[-1].items.append(Action(id="archive", title="Archive", hxget="/action?action=archive", icon="mdi-archive-arrow-down"))
            else:
                actions[-1].items.append(Action(id="restore", title="Restore", hxget="/action?action=restore", icon="mdi-archive-arrow-up-outline"))

        actions.append(ActionGroup(title="Info",
            items=[
                Action(id="check_info", title="Info about the note", hxget="/action?action=check_info", icon="mdi-information-outline"),
                Action(id="recursive_search", title="List all notes related with this entry", hxget="/action?action=recursive_search", icon="mdi-archive-search-outline", hxtarget="#main-table")
                ]))

        actions.append(ActionGroup(title="Edition",
            items=[
                Action(id="edit_record",title="Edit", hxget="/action?action=edit", hxtarget="#modal-content-target", modal=True, icon="mdi-email-edit", perms=[]),
            ]))

        return actions
