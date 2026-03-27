import os
import datetime
from imap_tools import MailBox, AND, UidRange

from app.crud import add_mail, add_attachment, get_last_uid

SERVER = os.getenv("EMAIL_CARDUMEN_SERVER")
USER = os.getenv("EMAIL_CARDUMEN_USER")
PASS = os.getenv("EMAIL_CARDUMEN_SECRET")


def get_unseen_mails():
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        return list(mailbox.fetch(AND(seen=False), mark_seen=True, headers_only=True, reverse=True))
    
    return []

def get_all_mails(limit: int):
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        return list(mailbox.fetch(mark_seen=True, headers_only=True, reverse=True, limit=limit))
    
    return []

def get_last_mails(last_uid: str):
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        return list(mailbox.fetch(criteria=AND(uid=f'{last_uid}:*'),mark_seen=True, reverse=True))

    return []

def add_last_mails_db(db: Session):
    last_uid = get_last_uid(db)
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        for mail in mailbox.fetch(criteria=AND(uid=f'{last_uid}:*'),mark_seen=True, reverse=True):
            add_mail(uid=mail.uid, subject=mail.subject, date=mail.date, from_=mail.from_, text=mail.text, db=db)
            for att in mail.attachments:
                add_attachment(mail.uid, att, db)

def add_mails_db(db):
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        for mail in mailbox.fetch(mark_seen=True, headers_only=True):
            add_mail(uid=mail.uid, subject=mail.subject, date=mail.date, from_=mail.from_, text=mail.text, db=db)


def get_mails():
    # Fetch only from the last 7 days
    date_limit = datetime.date.today() - datetime.timedelta(days=7)

    # Get date, subject and body len of all emails from INBOX folder
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        for msg in mailbox.fetch(AND(seen=False), mark_seen=True, headers_only=True):
            print(msg.uid, msg.subject, msg.from_, msg.date, msg.text, msg.attachments)
