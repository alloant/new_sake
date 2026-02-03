from pydantic import BaseModel, computed_field
from app.crud import get_user_registers

def get_settings_form(user, db):
    registers = get_user_registers(user.scopes, db)
    settings = ['limit_records','theme']

    return {'registers': registers, 'role': user.role.value, 'scopes': user.scopes, 'settings': settings}
