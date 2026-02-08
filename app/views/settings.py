from pydantic import BaseModel, computed_field
from app.crud import get_actor_registers

def get_settings_form(actor, db):
    registers = get_actor_registers(actor.scopes, db)
    remove = {'cg','asr','r','ctr'}
    clean_registers = {k: v for k, v in registers.items() if k not in remove}
    settings = ['limit_records','theme']

    return {'registers': clean_registers, 'kind': actor.kind.value, 'scopes': actor.scopes, 'settings': settings}
