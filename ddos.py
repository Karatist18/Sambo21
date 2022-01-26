#!/usr/bin/python3

import redis
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

# Constants
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_HASH = 'ddos'

IMAP_SERVER = "corpmail.tensor.ru"
IMAP_LOGIN = "noc@tensor.ru"
IMAP_PASSWORD = "7xR7eMvz"
IMAP_SEARCH_DAYS = 1

class DDoSChecker:
    def __init__(self, name, emailAddress, startPattern, endPattern, importance):
        self.name = name
        self.address = emailAddress
        self.start = re.compile(startPattern)
        self.end = re.compile(endPattern)
        self.importance = re.compile(importance) ##### Добавляю ещё одну переменную класса (high)
        self.read_redis()
        if self.status is None:
            self.status = False
            self.update_redis()

    def read_redis(self):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.status = (r.hmget(REDIS_HASH, self.name) == 'False')
        r.close()

    def update_redis(self):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.hset(REDIS_HASH, self.name, str(self.status))
        r.close()

    def check_mail(self):
        date = datetime.date.today().strftime("%d-%b-%Y")
        with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
            imap.login(IMAP_LOGIN, IMAP_PASSWORD)

            for mailbox in ('INBOX', 'INBOX/processed'):
                imap.select(mailbox, readonly=True)
                status, data = imap.uid(
                    'sort',
                    '(REVERSE DATE)',
                    'UTF-8',
                    f'(FROM "{self.address}") (SINCE "{date}")')
                uids = data[0].split()
                if len(uids) == 0:
                    continue
                uid = uids[0]

                result, data = imap.uid('fetch', uid, '(RFC822)')
                raw_email = data[0][1]
                email_message = BytesParser(policy=policy.default).parsebytes(raw_email)
                subject = email_message['Subject']
                payload = email_message.get_content() ## Достаю текст сообщения
                if self.end.search(subject):
                    self.status = False
                    return
                if self.start.search(subject) and self.importance.search(payload): ## Чтобы метрика изменилась, проверяем два совпадения
                    self.status = True
                    return

    def run(self):
        self.check_mail()
        self.update_redis()
        return json.dumps({
            'isp': self.name,
            'status': int(self.status),
            })

if __name__ == "__main__":
    def signal_handler(sig, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    ispCheckers = DDoSChecker('RosTelecom', "antiddos@rt.ru", r'(alert|attack)', r'done', r'High')

    for line in sys.stdin:
        try:
            for ispChecker in ispCheckers:
                print(ispChecker.run())
            sys.stdout.flush()
        except Exception as e:
            print(e, file=sys.stderr)
