#!/usr/bin/python3

import json
import sys
import re
import datetime
import imaplib
import email
import signal
from email.parser import BytesParser
from email.message import EmailMessage
from email import policy



IMAP_SERVER = "corpmail.tensor.ru"
IMAP_LOGIN = "noc@tensor.ru"
IMAP_PASSWORD = "7xR7eMvz"
IMAP_SEARCH_DAYS = 3



def check_mail(address):
        # date = datetime.date.today().strftime("%d-%b-%Y")
        with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
            imap.login(IMAP_LOGIN, IMAP_PASSWORD)

            for mailbox in ('INBOX', 'INBOX/processed'):
                imap.select(mailbox, readonly=True)
                status, data = imap.uid(
                    'sort',
                    '(REVERSE DATE)',
                    'UTF-8',
                    f'(FROM "{address}")')
                uids = data[0].split()
                if len(uids) == 0:
                    print('!')
                    continue
                uid = uids[0]
                print(uid)

                result, data = imap.uid('fetch', uid, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email,policy=policy.default)
                email_message = BytesParser(policy=policy.default).parsebytes(raw_email)
                subject = email_message
                payload = email_message.get_content()
                re_ = re.search(r'High', payload)
                if re_:
                    print('!!!S')
                # print(payload)
                # for i in msg:
                #     print(i)
                




check_mail('antiddos@rt.ru')