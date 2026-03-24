import os
import datetime
from imap_tools import MailBox, AND, UidRange

from app.crud import add_mail

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
        return list(mailbox.fetch(mark_seen=True, headers_only=True, reverse=True))

    return []


def add_mails_db(db):
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        for mail in mailbox.fetch(mark_seen=True, headers_only=True):
            print(mail.uid)
            add_mail(uid=mail.uid, subject=mail.subject, date=mail.date, from_=mail.from_, text=mail.text, db=db)


def get_mails():
    # Fetch only from the last 7 days
    date_limit = datetime.date.today() - datetime.timedelta(days=7)

    # Get date, subject and body len of all emails from INBOX folder
    with MailBox(SERVER).login(USER, PASS) as mailbox:
        for msg in mailbox.fetch(AND(seen=False), mark_seen=True, headers_only=True):
            print(msg.uid, msg.subject, msg.from_, msg.date, msg.text, msg.attachments)
