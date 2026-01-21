from pydantic import BaseModel, computed_field
from app.crud import get_registers

def has_permission(user_perms, required_perms):
    if not required_perms:
        return True

    for u_perm in user_perms:
        for r_perm in required_perms:
            if u_perm == r_perm or u_perm.startswith(f"{r_perm}:"):
                return True

    return False

class MenuSection(BaseModel):
    id: str
    title: str
    icon: str
    perms: list[str] = []
    active: str = ""
    
    @computed_field
    @property
    def link(self) -> str:
        return f"/sidebar?section={self.id}"

SECTIONS = [
    MenuSection(id='board',title='Dashboard',icon='mdi-bulletin-board',perms=['dr','of']),
    MenuSection(id='register',title='Registers',icon='mdi-file-cabinet',perms=['dr','of']),
    MenuSection(id='sccr',title='Secretary',icon='mdi-mail',perms=['sccr']),
    MenuSection(id='pages',title='Pages',icon='mdi-folder-information',perms=['dr','of']),
]

def get_sections(user_perms,active_section: str):
    sections = []
    
    for section in SECTIONS:
        if has_permission(user_perms,section.perms):
            section.active = 'is-link' if section.id == active_section else ''
            sections.append(section)

    return sections



class MenuItem(BaseModel):
    id: str
    title: str
    link: str | None = None
    icon: str | None = None
    perms: list[str] = []
    active: str = ""
    show_count: bool = False
    hx_trigger: str = ""

class MenuGroup(BaseModel):
    title: str
    items: list[MenuItem]

# Your master menu definition

FULL_MENU = {}
FULL_MENU['board'] = [
    MenuGroup(
        title="Despacho",
        items=[
            MenuItem(id="despacho", title="Despacho", link="/?section=board&panel=despacho", icon="mdi-briefcase", perms=["despacho"], show_count=True),
        ],
    ),
    MenuGroup(
        title="My inbox",
        items=[
            MenuItem(id="inbox", title="Inbox", link="/?section=board&panel=inbox", icon="mdi-inbox-arrow-down", perms=["dr","of"], show_count=True,hx_trigger=",record_state_changed from:body"),
            MenuItem(id="inbox-snooze", title="Snooze", link="/?section=board&panel=inbox-snooze", icon="mdi-alarm-snooze", perms=["dr","of"], show_count=True),
            MenuItem(id="inbox-archived", title="Archived", link="/?section=board&panel=inbox-archived", icon="mdi-archive", perms=["dr","of"]),
        ],
    ),

    MenuGroup(
        title="My outbox",
        items=[
            MenuItem(id="outbox-drafts", title="Drafts", link="/?section=board&panel=outbox-drafts", icon="mdi-note-edit", perms=["dr","of"], show_count=True),
            MenuItem(id="outbox-sent", title="Sent", link="/?section=board&panel=outbox-sent", icon="mdi-email-fast", perms=["dr","of"]),
        ]
    ),
    MenuGroup(
        title="Proposals",
        items=[
            MenuItem(id="incoming-proposals-to-sign", title="To sign", link="/?section=board&panel=incoming-proposals-to-sign", icon="mdi-pen", perms=["dr","of"], show_count=True),
            MenuItem(id="incoming-proposals-signed", title="Signed", link="/?section=board&panel=incoming-proposals-signed", icon="mdi-draw-pen", perms=["dr","of"]),
        ]
    ),
    MenuGroup(
        title="My proposals",
        items=[
            MenuItem(id="outcoming-proposals-drafts", title="Drafts", link="/?section=board&panel=outcoming-proposals-drafts", icon="mdi-note-edit", perms=["dr","of"], show_count=True),
            MenuItem(id="outcoming-proposals-circulating", title="Circulating", link="/?section=board&panel=outcoming-proposals-circulating", icon="mdi-account-arrow-right-outline", perms=["dr","of"], show_count=True),
            MenuItem(id="outcoming-proposals-done", title="Done", link="/?section=board&panel=outcoming-proposals-done", icon="mdi-check-circle-outline", perms=["dr","of"], show_count=True),
            MenuItem(id="outcoming-proposals-snooze", title="Snooze", link="/?section=board&panel=outcoming-proposals-snooze", icon="mdi-alarm-snooze", perms=["dr","of"], show_count=True),
            MenuItem(id="outcoming-proposals-archived", title="Archived", link="/?section=board&panel=outcoming-proposals-archived", icon="mdi-archive", perms=["dr","of"]),
        ]
    ),
]

FULL_MENU['sccr'] = [
    MenuGroup(
        title="Import",
        items=[
            MenuItem(id="mail", title="Import mail", link="/?section=sccr&panel=mail", icon="mdi-mailbox", perms=["sccr"]),
        ]
    ),
    MenuGroup(
        title="Mailbox",
        items=[
            MenuItem(id="inbox-sccr", title="Inbox", link="/?section=sccr&panel=inbox-sccr", icon="mdi-inbox-arrow-down", perms=["sccr"]),
            MenuItem(id="outbox-sccr", title="Outbox", link="/?section=sccr&panel=outbox-sccr", icon="mdi-email-fast", perms=["sccr"]),
        ]
    ),
    MenuGroup(
        title="Others",
        items=[
            MenuItem(id="sensitive", title="Sensitive", link="/?section=sccr&panel=sensitive", icon="mdi-incognito-circle", perms=["sccr"]),
        ]
    ),

]

FULL_MENU['pages'] = [
    MenuGroup(
        title="Import",
        items=[
        ]
    ),
]

FULL_MENU['settings'] = [

]

def get_panel(user_perms,section,panel):
    if section == 'register':
        return get_panel_register(user_perms,panel)
    
    filtered_menu = []
    for group in FULL_MENU[section]:
        allowed_items = []
        # Check which items the user is allowed to see
        for item in group.items:
            if has_permission(user_perms,item.perms):
                allowed_items.append(item)
                if item.id == panel:
                    allowed_items[-1].active = "is-active"
                else:
                    allowed_items[-1].active = ""
        
        if allowed_items:
            filtered_menu.append(MenuGroup(title=group.title, items=allowed_items))

    return filtered_menu

def get_panel_register(user_perms,panel):
    registers = get_registers()
    menu = []
    items = []
    items.append(MenuItem(id=f"all",title="All",link=f"/?section=register&panel=all",icon="mdi-web"))
    items[-1].active = "is-active" if "all" == panel else ""
    items.append(MenuItem(id=f"unread",title="Unread",link=f"/?section=register&panel=unread",icon="mdi-message-badge",show_count=True,hx_trigger=",read_state_changed from:body"))
    items[-1].active = "is-active" if "unread" == panel else ""
    menu.append(MenuGroup(title="All registers", items=items))

    for register in registers:
        if has_permission(user_perms,[register.alias]):
            items = []
            items.append(MenuItem(id=f"{register.alias}-in",title=f"Inbox {register.alias}",link=f"/?section=register&panel={register.alias}-in",icon="mdi-inbox-arrow-down"))
            items[-1].active = "is-active" if f"{register.alias}-in" == panel else ""
            items.append(MenuItem(id=f"{register.alias}-out",title=f"Outbox {register.alias}",link=f"/?section=register&panel={register.alias}-out",icon="mdi-email-fast"))
            items[-1].active = "is-active" if f"{register.alias}-out" == panel else ""

            menu.append(MenuGroup(title=register.full_name, items=items))
    return menu

def get_sidebar(payload,section,panel):
    sections = get_sections([payload.data['role']] + payload.scopes,section)
    panel = get_panel([payload.data['role']] + payload.scopes,section,panel)

    return {'user_alias': payload.alias, 'sections': sections, 'panel': panel}
