from pydantic import BaseModel, computed_field
from app.crud import get_registers, get_actor_registers, has_permission, get_actor_ctrs, get_actor_by_id


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

def SECTIONS():
    from fastapi_babel import _
    return [
        MenuSection(id='board',title=_('Dashboard'),icon='mdi-bulletin-board',perms=['dr','of']),
        MenuSection(id='register',title=_('Registers'),icon='mdi-file-cabinet',perms=['dr','of']),
        MenuSection(id='sccr',title=_('Secretary'),icon='mdi-mail',perms=['sccr']),
        MenuSection(id='cl',title=_('Cl work'),icon='mdi-calendar-check',perms=['ctr_*']),
    ]

def get_sections(actor_perms,active_section: str):
    sections = []
    
    for section in SECTIONS():
        if has_permission(actor_perms,section.perms):
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
    blank: bool = False

class MenuGroup(BaseModel):
    title: str
    items: list[MenuItem]
    has_settings: bool = False
    panel: str = ""

# Your master menu definition

def FULLMENU(section):
    from fastapi_babel import _
    FULL_MENU = {}
    FULL_MENU['board'] = [
        MenuGroup(
            title="Despacho",
            items=[
                MenuItem(id="despacho", title=_("Despacho"), link="/?section=board&panel=despacho", icon="mdi-briefcase", perms=["despacho"], show_count=True),
            ],
        ),

        MenuGroup(
            title="Notes",
            items=[
                MenuItem(id="all", title=_("All"), link="/?section=board&panel=all", icon="mdi-web", perms=["user"]),
                MenuItem(id="mustread", title=_("Must read"), link="/?section=board&panel=mustread", icon="mdi-message-star", perms=["user"], show_count=True,hx_trigger=",read_state_changed from:body"),
                MenuItem(id="unread", title=_("Unread"), link="/?section=board&panel=unread", icon="mdi-message-badge", perms=["user"],show_count=True,hx_trigger=",read_state_changed from:body"),
            ],
        ),

        MenuGroup(
            title="My inbox",
            items=[
                MenuItem(id="inbox", title=_("Inbox"), link="/?section=board&panel=inbox", icon="mdi-inbox-arrow-down", perms=["user"], show_count=True, hx_trigger=", record_state_changed from:body, socket-updated from:body"),
                MenuItem(id="inbox-snooze", title=_("On hold"), link="/?section=board&panel=inbox-snooze", icon="mdi-car-brake-hold", perms=["user"], hx_trigger=", record_state_changed from:body, socket-updated from:body", show_count=True),
                MenuItem(id="inbox-archived", title=_("Archived"), link="/?section=board&panel=inbox-archived", icon="mdi-archive", perms=["user"]),
            ],
        ),

        MenuGroup(
            title="My outbox",
            items=[
                MenuItem(id="outbox-drafts", title=_("Drafts"), link="/?section=board&panel=outbox-drafts", icon="mdi-note-edit", perms=["user"], show_count=True, hx_trigger=", socket-updated from:body"),
                MenuItem(id="outbox-sent", title=_("Sent"), link="/?section=board&panel=outbox-sent", icon="mdi-email-fast", perms=["user"]),
            ]
        ),
        MenuGroup(
            title="Proposals",
            items=[
                MenuItem(id="incoming-proposals-to-sign", title=_("To sign"), link="/?section=board&panel=incoming-proposals-to-sign", icon="mdi-file-outline", perms=["user"], show_count=True, hx_trigger=",proposal_sign_changed from:body, socket-updated from:body"),
                MenuItem(id="incoming-proposals-signed", title=_("Signed"), link="/?section=board&panel=incoming-proposals-signed", icon="mdi-file-sign", perms=["user"]),
            ]
        ),
        MenuGroup(
            title="My proposals",
            items=[
                MenuItem(id="outcoming-proposals-drafts", title=_("Drafts"), link="/?section=board&panel=outcoming-proposals-drafts", icon="mdi-note-edit", perms=["user"], show_count=True, hx_trigger=",proposal_state_changed from:body"),
                MenuItem(id="outcoming-proposals-circulating", title=_("Circulating"), link="/?section=board&panel=outcoming-proposals-circulating", icon="mdi-account-arrow-right-outline", perms=["user"], show_count=True, hx_trigger=",proposal_state_changed from:body, socket-updated from:body"),
                MenuItem(id="outcoming-proposals-done", title=_("Aproved"), link="/?section=board&panel=outcoming-proposals-done", icon="mdi-check-circle-outline", perms=["user"], show_count=True, hx_trigger=",proposal_state_changed from:body, socket-updated from:body"),
                MenuItem(id="outcoming-proposals-snooze", title=_("On hold"), link="/?section=board&panel=outcoming-proposals-snooze", icon="mdi-car-brake-hold", perms=["user"], show_count=True, hx_trigger=",proposal_state_changed from:body"),
                MenuItem(id="outcoming-proposals-archived", title=_("Archived"), link="/?section=board&panel=outcoming-proposals-archived", icon="mdi-archive", perms=["user"], hx_trigger=",proposal_state_changed from:body"),
            ]
        ),
    ]

    FULL_MENU['sccr'] = [
        MenuGroup(
            title="Cardumen mail",
            items=[
                MenuItem(id="new_mail", title=_("New mail"), link="/?section=sccr&panel=new_mail", icon="mdi-mailbox-up", perms=["sccr"], show_count=True, hx_trigger=", cardumen_state_changed from:body"),
                MenuItem(id="inbox_cardumen", title=_("Inbox"), link="/?section=sccr&panel=inbox_cardumen", icon="mdi-mailbox-open", perms=["sccr"]),
            ]
        ),
        MenuGroup(
            title="Mailbox",
            items=[
                MenuItem(id="inbox-sccr", title=_("Inbox"), link="/?section=sccr&panel=inbox-sccr", icon="mdi-inbox-arrow-down", perms=["sccr"]),
                MenuItem(id="outbox-sccr", title=_("Outbox"), link="/?section=sccr&panel=outbox-sccr", icon="mdi-email-fast", perms=["sccr"]),
            ]
        ),
        MenuGroup(
            title="Others",
            items=[
                MenuItem(id="sensitive", title=_("Sensitive"), link="/?section=sccr&panel=sensitive", icon="mdi-incognito-circle", perms=["sccr"]),
            ]
        ),

    ]

    FULL_MENU['pages'] = [
        MenuGroup(
            title=_("Documentation"),
            items=[
                MenuItem(id="documentation_cl", title=_("Documentation"), link="https://nas.prome.sg:5001/ns/sharing/AOJHa", icon="mdi-information", perms=[""], blank = True),
            ]
        ),
        MenuGroup(
            title=_("Documentation"),
            items=[
                MenuItem(id="documentation_cr", title=_("Documentation"), link="https://nas.prome.sg:5001/ns/sharing/zQLJ9", icon="mdi-information", perms=[""], blank = True)
            ]
        ),

    ]

    FULL_MENU['settings'] = [

    ]

    FULL_MENU['cl'] = [
        MenuGroup(
            title =_("Dashboard"),
            items=[]
        )
    ]

    return FULL_MENU[section]

def get_panel(db,actor_perms,section,panel):
    if section == 'register':
        return get_panel_register_cr(db,actor_perms,panel)
    elif section == 'cl':
        return get_panel_register_cl(db,actor_perms,panel)

    
    filtered_menu = []
    for group in FULLMENU(section):
        allowed_items = []
        # Check which items the actor is allowed to see
        for item in group.items:
            if has_permission(actor_perms,item.perms):
                allowed_items.append(item)
                if item.id == panel:
                    allowed_items[-1].active = "is-active"
                else:
                    allowed_items[-1].active = ""
        
        if allowed_items:
            filtered_menu.append(MenuGroup(title=group.title, items=allowed_items))

    filtered_menu.append(FULLMENU('pages')[0])
    return filtered_menu

def get_panel_register_cr(db,actor_perms,panel):
    registers = get_registers(db)
    menu = []
    items = []

    for register in registers:
        if has_permission(actor_perms,[register.alias]) and register.type == 'note':
            items = []
            items.append(MenuItem(id=f"{register.alias}-in",title=f"Inbox {register.alias}",link=f"/?section=register&panel={register.alias}-in",icon="mdi-inbox-arrow-down"))
            items[-1].active = "is-active" if f"{register.alias}-in" == panel else ""
            items.append(MenuItem(id=f"{register.alias}-out",title=f"Outbox {register.alias}",link=f"/?section=register&panel={register.alias}-out",icon="mdi-email-fast"))
            items[-1].active = "is-active" if f"{register.alias}-out" == panel else ""

            menu.append(MenuGroup(title=register.full_name, items=items))
    
    return menu

def get_panel_register_cl(db,actor_perms,panel):
    menu = []
    items = []

    ctrs = get_actor_ctrs(db,actor_perms)

    for ctr in ctrs:
        items = []
        items.append(MenuItem(id=f"{ctr}-in_ctr",title=f"Inbox {ctr}",link=f"/?section=cl&panel={ctr}-in_ctr",icon="mdi-inbox-arrow-down"))
        items[-1].active = "is-active" if f"{ctr}-in_ctr" == panel else ""
        items.append(MenuItem(id=f"{ctr}-out_ctr",title=f"Outbox {ctr}",link=f"/?section=cl&panel={ctr}-out_ctr",icon="mdi-email-fast"))
        items[-1].active = "is-active" if f"{ctr}-out_ctr" == panel else ""

        menu.append(MenuGroup(title=f'Register {ctr}', items=items, has_settings = True, panel = ctr))
    
    
    menu.append(FULLMENU('pages')[0])
    
    return menu

def get_sidebar(db,payload,section,panel):
    current_actor = get_actor_by_id(db,payload.uid)
    if current_actor.role == 'cl':
        sections = []
        panel = get_panel(db,[payload.data['kind']] + current_actor.scopes,section,panel)
    else:
        sections = get_sections([payload.data['kind']] + current_actor.scopes,section)
        panel = get_panel(db,[payload.data['kind']] + current_actor.scopes,section,panel)

    return {'actor_alias': payload.alias, 'sections': sections, 'panel': panel}
