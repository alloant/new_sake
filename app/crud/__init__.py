from app.crud.record import get_record_by_id, get_records, get_record_actor, get_record_actor_by_id
from app.crud.register import get_register_by_alias, get_registers, get_actor_registers, has_permission, get_actor_ctrs
from app.crud.actor import get_actor_by_alias, get_actor_by_id, get_ctrs, get_actor_by_email, get_actor_by_ids
from app.crud.dept import get_all_dept, get_all_dept_alias, get_dept_by_alias
from app.crud.mail import add_mail, get_last_uid, get_mails, add_attachment, get_mail_by_uid
