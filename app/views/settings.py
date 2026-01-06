from pydantic import BaseModel, computed_field
from app.crud import get_registers

def has_permission(user_perms, required_perms):
    if not required_perms:
        return True

    for u_perm in user_perms:
        for r_perm in required_perms:
            if u_perm == r_perm or u_perm.startswith(f"{r_perm}:"):
                return u_perm

    return ''

def get_settings_registers(user_perms):
    registers = get_registers()
    available = {}
    for register in registers:
        available[register.alias] = has_permission(user_perms,[register.alias])

    return available
            


def get_settings_form(user):
    registers = get_settings_registers(user.scopes)

    return {'registers': registers, 'role': user.role.value}
