from pydantic import BaseModel, computed_field

def has_permission(user_perms, required_perms):
    if not required_perms:
        return True

    for u_perm in user_perms:
        for r_perm in required_perms:
            if u_perm == r_perm or u_perm.startswith(f"{r_perm}:"):
                return True

    return False

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



ACTIONS = [
    ActionGroup(
        title="Notes",
        items=[
            Action(id="mark_read", title="Mark as read", hxget="/action?action=mark_read", icon="mdi-email-check-outline", perms=[]),
            Action(id="mark_unread", title="Mark as unread", hxget="/action?action=mark_unread", icon="mdi-email-open-outline", perms=[]),
        ],
    ),
    ActionGroup(
        title="Inbox",
        items=[
            Action(id="enable_snooze", title="Snooze", hxget="/action?action=enable_snooze", icon="mdi-email-check-outline", perms=[]),
            Action(id="disable_snooze", title="Disable snooze", hxget="/action?action=disable_snooze", icon="mdi-email-check-outline", perms=[]),
            Action(id="archive", title="Archive", hxget="/action?action=archive", icon="mdi-archive-arrow-down-outline", perms=[]),
            Action(id="restore", title="Restore", hxget="/action?action=restore", icon="mdi-archive-arrow-up-outline", perms=[]),
        ],
    ),
    ActionGroup(
        title="Info",
        items=[
            Action(id="check_info", title="Info about the note", hxget="/action?action=check_info", icon="mdi-information-outline", perms=[]),
            Action(id="recursive_search", title="List all notes related with this entry", hxget="/action?action=recursive_search", icon="mdi-archive-search-outline", perms=[]),
        ],
    ),
]


def get_actions(user_perms,section,panel):
    filtered_actions = []
    for group in ACTIONS:
        allowed_items = []
        # Check which items the user is allowed to see
        for item in group.items:
            if has_permission(user_perms,item.perms):
                allowed_items.append(item)
        
        if allowed_items:
            filtered_actions.append(ActionGroup(title=group.title, items=allowed_items))

    return filtered_actions


