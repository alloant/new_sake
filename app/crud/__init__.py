from app.crud.record import get_record_by_id, get_records, get_record_actor, get_record_actor_by_id
from app.crud.register import get_register_by_alias, get_registers, get_actor_registers, has_permission, get_actor_ctrs
from app.crud.actor import get_actor_by_alias, get_actor_by_id, get_ctrs, get_actor_by_email, get_actor_by_ids, get_all_deps, get_all_alias_deps, get_senders_register, get_targets_register
from app.crud.mail import add_mail, get_last_uid, get_mails, add_attachment, get_mail_by_uid
