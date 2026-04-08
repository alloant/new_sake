from pydantic import BaseModel, computed_field
from app.crud import get_actor_registers, get_ctrs

def get_settings_form(db,current_actor):
    registers = get_actor_registers(db,current_actor.scopes)
    remove = {'cg','asr','r','ctr'}
    clean_registers = {k: v for k, v in registers.items() if k not in remove}

    ctrs = get_ctrs(db)
    ctrs_actor = {}
    
    for ctr in ctrs:
        if any(item.startswith(f'ctr_{ctr.alias}') for item in current_actor.scopes):
            ctrs_actor[ctr.alias] = 'checked'
        else:
            ctrs_actor[ctr.alias] = ''

    settings = {
        'limit_records': {'type': 'select', 'options': list(range(20,31))},
        'font_size': {'type': 'select', 'options': list(range(1,6))},
        'theme': {'type': 'select', 'options': ['light', 'dark']},
        'actor_tags': {'type': 'str'},
        'lang': {'type': 'select', 'options': ['en','ja']}
    }

    if 'admin' in current_actor.scopes:
        settings['admin_active'] = {'type': 'bool'}

    return {'registers': clean_registers, 'ctrs':ctrs_actor, 'kind': current_actor.kind.value, 'scopes': current_actor.scopes, 'settings': settings}
