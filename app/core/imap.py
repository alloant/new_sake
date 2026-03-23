import os
from imap_tools import MailBox, AND

SERVER = os.getenv("EMAIL_CARDUMEN_SERVER")
USER = os.getenv("EMAIL_CARDUMEN_USER")
PASS = os.getenv("EMAIL_CARDUMEN_SECRET")

print(SERVER,USER)
# Get date, subject and body len of all emails from INBOX folder
with MailBox(SERVER).login(USER, PASS) as mailbox:
    for msg in mailbox.fetch():
        print(msg.date, msg.subject, len(msg.text or msg.html))
