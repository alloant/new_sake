from pydantic import BaseModel, model_validator
from datetime import date, datetime
import re
from markupsafe import Markup

def highlight_hashtags(text):
    # Regex to find words starting with #
    #pattern = r'(#\w+)'
    pattern = r'#(\w+)' 
    
    # Replace with Bulma tag HTML
    replacement = r'<span class="has-background-link-light has-text-warning-dark px-1 is-radius-rounded" style="border-radius: 4px;">\1</span>'
    highlighted = re.sub(pattern, replacement, text)
    return Markup(highlighted)


class Action(BaseModel):
    record_id: int
    id: str
    record_id: int
    title: str
    attr: dict[str,str] = {}
    extra_class: str = ""
    icon: str | None = None
    perms: list[str] = []

    @model_validator(mode="after")
    def render(self):
        for k in self.attr:
            self.attr[k] = self.attr[k].format(record_id = self.record_id)

        return self

class ActionGroup(BaseModel):
    title: str
    items: list[Action]


def ACTIONS():
    from fastapi_babel import _
    ACTIONS = {}
    ACTIONS['sign_note'] = {"id": "sign_note_record", "title": _("Sign note"), "attr": {"hx-get": "/action?action=sign_note", "hx-target": "#modal-content-target", "onclick": "openModal()"}, "icon": "mdi-file-sign", "perms": []}
    ACTIONS['quick_sign'] = {"id": "quick_sign", "title": _("Quick sign"), "attr": {"hx-get": "/action?action=quick_sign", "hx-target": "#row-{record_id}"}, "icon": "mdi-draw-pen"}
    
    ACTIONS['mark_read'] = {"id": "mark_read", "title": _("Mark as read"), "attr": {"hx-get": "/action?action=mark_read", "hx-target": "#row-{record_id}"}, "icon": "mdi-email-check"}
    ACTIONS['mark_unread'] = {"id": "mark_unread", "title": _("Mark as unread"), "attr": {"hx-get": "/action?action=mark_unread", "hx-target": "#row-{record_id}"}, "icon": "mdi-email-open-outline"}
    ACTIONS['enable_snooze'] = {"id": "enable_snooze", "title": _("Hold"), "attr": {"hx-post": "/action?action=enable_snooze", "hx-prompt": "Due date (dd/mm/yyyy)", "hx-target": "#row-{record_id}"}, "icon": "mdi-alarm-snooze"}
    ACTIONS['disable_snooze'] = {"id": "disable_snooze", "title": _("Unhold"), "attr": {"hx-get": "/action?action=disable_snooze", "hx-target": "#row-{record_id}"}, "icon": "mdi-weather-sunset"}
    ACTIONS['archive'] = {"id": "archive", "title": _("Archive"), "attr": {"hx-get": "/action?action=archive", "hx-target": "#row-{record_id}"}, "icon": "mdi-archive-arrow-down"}
    ACTIONS['restore'] = {"id": "restore", "title": _("Restore"), "attr": {"hx-get": "/action?action=restore", "hx-target": "#row-{record_id}"}, "icon": "mdi-archive-arrow-up-outline"}

    ACTIONS['check_info'] = {"id": "check_info", "title": _("Info about the note"), "attr": {"hx-get": "/action?action=check_info", "hx-target": "#row-{record_id}"}, "icon": "mdi-information-outline"}
    ACTIONS['recursive_search'] = {"id": "recursive_search", "title": _("List all notes related with this entry"), "attr": {"hx-get": "/action?action=recursive_search", "hx-target": "#main-table"}, "icon": "mdi-archive-search-outline"}
    ACTIONS['edit_record'] = {"id": "edit_record", "title": _("Edit"), "attr": {"hx-get": "/action?action=edit", "hx-target": "#modal-content-target", "onclick": "openModal()"}, "icon": "mdi-email-edit", "perms": []}
    ACTIONS['edit_targets'] = {"id": "edit_targets", "title": _("Edit targets"), "attr": {"hx-get": "/action?action=edit_targets", "hx-target": "#modal-content-target", "onclick": "openModal()"}, "icon": "mdi-account-group"}
    ACTIONS['delete_record'] = {"id": "delete_record", "title": _("Delete"), "attr": {"hx-get": "/action?action=delete", "hx-target": "#row-{record_id}", "hx-confirm": "Are you sure you want to delete the record?"}, "icon": "mdi-delete-circle-outline", "extra_class": "has-text-danger"}


    ACTIONS['start_circulation'] = {"id": "start_circulation", "title": _("Start circulation"), "attr": {"hx-get": "/action?action=start_circulation", "hx-target": "#row-{record_id}"}, "icon": "mdi-file-send"}
    ACTIONS['stop_circulation'] = {"id": "stop_circulation", "title": _("Stop circulation"), "attr": {"hx-get": "/action?action=stop_circulation", "hx-target": "#row-{record_id}"}, "icon": "mdi-file-cancel", "extra_class": "has-text-danger"}
    ACTIONS['sign_record'] = {"id": "sign_record", "title": _("Sign and pass"), "attr": {"hx-get": "/action?action=sign_record", "hx-target": "#row-{record_id}"}, "icon": "mdi-file-sign"}

    return ACTIONS

class RecordMethod(object):
    @property
    def protocol(self):
        if self.sequence == 0:
            if self.references:
                return f'Ref {self.references[0].protocol}'
            else:
                return 'Ref'
        else:
            return f'{self.code} {self.sequence}/{str(self.year)[2:]}'

    @property
    def code(self):
        if self.flow.value in self.register.protocol:
            return eval(self.register.protocol[self.flow.value])
        return ''

    @property
    def date_python(self):
        return self.updated_at if self.updated_at > self.created_at else self.created_at

    @property
    def title_hashtag(self):
        return highlight_hashtags(self.title)

    @property
    def date(self):
        return self.date_python.strftime('%Y-%m-%d')

    @property
    def date_html(self):
        dt = self.date_python
        if datetime.now().year == dt.year:
            return dt.strftime("%d %b")
        return dt.strftime('%Y-%m-%d')

    @property
    def targets(self):
        rst = [target for target in self.actors if target.target > 0]
        if self.flow in ['inbound', 'internal_cr']:
            return sorted(rst, key=lambda x: x.target)

        return rst

    @property
    def targets_id(self):
        return [target.actor.id for target in self.actors if target.target > 0]

    @property
    def current_target_sequence(self):
        missing_targets = [target.target for target in self.actors if target.target > 0 and target.handled == 'pending']
        if missing_targets:
            return min(missing_targets)
        else:
            return 0

    @property
    def current_targets_alias(self):
        current_sequence = 0
        targets = []
        for target in self.actors:
            if target.target == 0:
                continue
            if target.handled == 'pending':
                if current_sequence == 0:
                    current_sequence = target.target
                if current_sequence == target.target:
                    targets.append(target.actor.alias)
                elif current_sequence < target.target:
                    break

        return targets

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
        all_actions = ACTIONS()
        actions = []
        if self.flow == 'inbound' and self.stage == 'despacho':
            actions.append(ActionGroup(title="Despacho",items=[]))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['sign_note']))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['quick_sign']))

        if self.flow == 'inbound' and self.stage == 'registed':
            actions.append(ActionGroup(title="Read",items=[]))
            if not state or (state.handled != 'read' and self.created_at > current_actor.created_at) or (state.handled == 'read' and self.created_at <= current_actor.created_at):
                actions[-1].items.append(Action(record_id=self.id,**all_actions['mark_read']))
            else:
                actions[-1].items.append(Action(record_id=self.id,**all_actions['mark_unread']))
        
        if self.flow == 'internal_cr':
            actions.append(ActionGroup(title="Proposals", items=[]))
            if current_actor.id in self.targets_id:
                actions[-1].items.append(Action(record_id=self.id,**all_actions['sign_record']))
            elif self.sender_id == current_actor.id:
                if self.stage == 'sketch':
                    actions[-1].items.append(Action(record_id=self.id,**all_actions['start_circulation']))
                elif self.stage == 'shared':
                    actions[-1].items.append(Action(record_id=self.id,**all_actions['stop_circulation']))


        if (self.flow == 'inbound' and self.stage == 'registered') or self.flow == 'internal_cr' and self.sender_id == current_actor.id and self.stage != 'shared':
            actions.append(ActionGroup(title="Inbox",items=[]))
            if self.state != 'snooze':
                actions[-1].items.append(Action(record_id=self.id,**all_actions['enable_snooze']))
            else:
                actions[-1].items.append(Action(record_id=self.id,**all_actions['disable_snooze']))
        
            if self.state != 'archived':
                actions[-1].items.append(Action(record_id=self.id,**all_actions['archive']))
            else:
                actions[-1].items.append(Action(record_id=self.id,**all_actions['restore']))

        if not quick_access:
            actions.append(ActionGroup(title="Info", items=[]))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['check_info']))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['recursive_search']))
        
        if (not quick_access or self.title == '') and (current_actor.admin or self.flow == 'outbound' and self.stage == 'draft' or self.flow == 'internal_cr' and self.sender_id == current_actor.id):
            actions.append(ActionGroup(title="Edit", items=[]))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['edit_record']))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['edit_targets']))
            actions[-1].items.append(Action(record_id=self.id,**all_actions['delete_record']))


        return actions

    @property
    def progress(self):
        if self.flow.startswith('internal'):
            if not self.targets:
                return "","account-off" # title, icon
            else:
                current = self.current_target_sequence
                done = []
                now = []
                next = []
                cont = 0
                for target in self.targets:
                    if target.handled == 'approved':
                        cont += 1
                        done.append(target.actor.alias)
                    elif current == target.target:
                        now.append(target.actor.alias)
                    else:
                        next.append(target.actor.alias)
                
                title = f"Done:{'-'.join(done)}&#10;&#10;Now:{'-'.join(now)}&#10;&#10;Next:{'-'.join(next)}"
                if cont == 0:
                    return title, "hexagon-outline"
                else:
                    progress = cont / len(self.targets)
                    return title, f"hexagon-slice-{round(progress * 6)}"
        return None, None


    def avatar_circle(self, align, title, avatar):
        return f'<div class="avatar-circle is-flex is-align-items-center is-justify-content-center has-tooltip-multiline has-tooltip-arrow has-tooltip-right has-tooltip-text-{align}" data-tooltip="{title}">{avatar}</div>'

    @property
    def avatar_html(self):
        match self.flow:
            case 'inbound':
                targets = self.targets

                if not targets:
                    title = ""
                    avatar = '<i class="iconify" data-width="1.25em" data-icon="mdi-account"></i>'
                    align = "center"
                elif len(targets) == 1:
                    title = targets[0].actor.alias
                    avatar = f'<span style="font-size: 0.7em;">{targets[0].actor.abbr.upper()}</span>'
                    align = "center"
                else:
                    if self.stage == "despacho":
                        rst = ""
                        for target in targets:
                            rst += self.avatar_circle("center", target.actor.alias, f'<span style="font-size: 0.7em;">{target.actor.abbr.upper()}</span>')
                        return f'<div class="is-flex">{rst}</div>'
                    else:
                        title = " - ".join([target.actor.alias for target in targets])
                        avatar = '<i class="iconify" data-width="1.25em" data-icon="mdi-account-multiple"></i>'
                        align = "center"
            case 'outbound':
                title = self.sender.alias
                avatar = f'<span style="font-size: 0.7em;">{self.sender.abbr.upper()}</span>'
                align = "center"
            case 'internal_cr' | 'internal_cl':
                title, icon = self.progress
                avatar = f'<i class="iconify" data-width="1.25em" data-icon="mdi-{icon}"></i>'
                align = "left"
            case _:
                return ''

        return self.avatar_circle(align, title, avatar)
        return f'<div class="avatar-circle is-flex is-align-items-center is-justify-content-center mr-4 has-tooltip-multiline has-tooltip-arrow has-tooltip-right has-tooltip-text-{align}" data-tooltip="{title}">{avatar}</div>'

