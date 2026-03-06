from pydantic import BaseModel
from datetime import date

class Action(BaseModel):
    id: str
    title: str
    attr: dict[str,str] = {}
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
        return [target for target in self.actors if target.target > 0]
    
    def link(self, idx: int) -> str:
        if idx <= len(self.files) + 1:
            return self.files[idx].link
        return ""

    def read_status_html(self,status,actor):
        read = True
        if not status:
            if self.created_at > actor.created_at:
                read = False
        elif status.handled != 'read' and self.created_at > actor.created_at:
            read = False
        elif status.handled == 'read' and self.created_at <= actor.created_at:
            read = False
        
        return '' if read else 'has-text-weight-bold'


        
    def get_actions(self, state, current_actor, section, panel, quick_access = False):
        actions = []
        if self.flow in ['inbound']:
            actions.append(ActionGroup(title="Read",items=[]))
            if not state or state.handled == 'unread':
                actions[-1].items.append(Action(id="mark_read", title="Mark as read", attr={"hx-get": "/action?action=mark_read", "hx-target": f"#row-{self.id}"}, icon="mdi-email-check"))
            else:
                actions[-1].items.append(Action(id="mark_unread", title="Mark as unread", attr={"hx-get": "/action?action=mark_unread", "hx-target": f"#row-{self.id}"}, icon="mdi-email-open-outline"))

        if self.flow in ['inbound','internal_cr','internal_cl'] and not quick_access:
            actions.append(ActionGroup(title="Inbox",items=[]))
            if self.state != 'snooze':
                actions[-1].items.append(Action(id="enable_snooze", title="Snooze", attr={"hx-post": "/action?action=enable_snooze", "hx-prompt": "Due date (dd/mm/yyyy)", "hx-target": f"#row-{self.id}"}, icon="mdi-alarm-snooze"))
            else:
                actions[-1].items.append(Action(id="disable_snooze", title="Disable snooze", attr={"hx-get": "/action?action=disable_snooze", "hx-target": f"#row-{self.id}"}, icon="mdi-weather-sunset"))
            
            if self.state != 'archived':
                actions[-1].items.append(Action(id="archive", title="Archive", attr={"hx-get": "/action?action=archive", "hx-target": f"#row-{self.id}"}, icon="mdi-archive-arrow-down"))
            else:
                actions[-1].items.append(Action(id="restore", title="Restore", attr={"hx-get": "/action?action=restore", "hx-target": f"#row-{self.id}"}, icon="mdi-archive-arrow-up-outline"))

        if not quick_access:
            actions.append(ActionGroup(title="Info",
                items=[
                    Action(id="check_info", title="Info about the note", attr={"hx-get": "/action?action=check_info", "hx-target": f"#row-{self.id}"}, icon="mdi-information-outline"),
                    Action(id="recursive_search", title="List all notes related with this entry", attr={"hx-get": "/action?action=recursive_search", "hx-target": f"#main-table"}, icon="mdi-archive-search-outline")
                    ]))

            actions.append(ActionGroup(title="Edition",
                items=[
                    Action(id="edit_record",title="Edit", attr={"hx-get": "/action?action=edit", "hx-target": "#modal-content-target", "onclick": "openModal()"}, icon="mdi-email-edit", perms=[]),
                ]))

        return actions
