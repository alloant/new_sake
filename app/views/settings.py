from pydantic import BaseModel, computed_field
from app.crud import get_actor_registers, get_ctrs

def get_settings_form(actor, db):
    registers = get_actor_registers(actor.scopes, db)
    remove = {'cg','asr','r','ctr'}
    clean_registers = {k: v for k, v in registers.items() if k not in remove}

    ctrs = get_ctrs(db)
    ctrs_actor = {}
    
    for ctr in ctrs:
        if any(item.startswith(f'ctr_{ctr.alias}') for item in actor.scopes):
            ctrs_actor[ctr.alias] = 'checked'
        else:
            ctrs_actor[ctr.alias] = ''

    settings = ['limit_records','theme','admin_active','lang']

    return {'registers': clean_registers, 'ctrs':ctrs_actor, 'kind': actor.kind.value, 'scopes': actor.scopes, 'settings': settings}
