import getpass
import imaplib
import argparse
import sys
import datetime
import re

import sqlalchemy

import email_settings

SUBMISSION_TIME = re.compile(r'^Submission time:\s+(\S.+)$')
COMPLETION_TIME = re.compile(r'^Completion time:\s+(\S.+)$')
def create_db():
    engine = sqlalchemy.create_engine(email_settings.db)
    engine.execute('''CREATE TABLE akamaicache(
        id SERIAL PRIMARY KEY,
        submitted_at TIMESTAMP NOT NULL,
        completed_at TIMESTAMP NOT NULL,
        url VARCHAR(255) NOT NULL
    )''')
    engine.execute('''CREATE INDEX akamaicache_submitted_at_idx ON akamaicache(submitted_at)''')
    engine.execute('''CREATE INDEX akamaicache_completed_at_idx ON akamaicache(completed_at)''')

def drop_db():
    engine = sqlalchemy.create_engine(email_settings.db)
    engine.execute('''DROP INDEX IF EXISTS akamaiCache_completed_at_idx''')
    engine.execute('''DROP INDEX IF EXISTS akamaiCache_submitted_at_idx''')
    engine.execute('''DROP TABLE IF EXISTS akamaiCache''')



def import_emails(conn, tb):
    M = imaplib.IMAP4_SSL(email_settings.host, email_settings.port)
    M.login(email_settings.username, email_settings.password)
    M.select()
    typ, data = M.search(None, 'FROM', '"ccu-notify@akamai.com"')
    insert = tb.insert()
    batch = []
    for num in data[0].split():
        typ, data = M.fetch(num, '(RFC822)')
        submitted_at = None
        completed_at = None
        for line in data[0][1].split('\n'):
            line = line.strip()
            if line.startswith('Submission time:'):
                submitted_at = datetime.datetime.strptime(line, 'Submission time:   %a, %d %b %Y %H:%M:%S +0000')
            elif line.startswith('Completion time:'):
                completed_at = datetime.datetime.strptime(line, 'Completion time:   %a, %d %b %Y %H:%M:%S +0000')
            elif line.startswith('remove url'):
                url = line[len('remove url '):]
                batch.append({'submitted_at': submitted_at, 'completed_at': completed_at, 'url': url})
                if len(batch) >= 1000:
                    conn.execute(insert, batch)
                    batch = []
    if len(batch) > 0:
        conn.execute(insert, batch)
    M.close()
    M.logout()

#ID:                a341ec5e-f7a6-11e1-95e7-609895e76098
#Domain:            production
#Requestor:         webops@nymag.com
#Submission time:   Wed, 05 Sep 2012 22:11:27 +0000
#Completion time:   Wed, 05 Sep 2012 22:13:47 +0000
#URL/cpcode count:  14
#
#Content purged:
#
#remove url http://pixel.nymag.com/imgs/fashion/daily/2012/09/06/06-hair-products.o.jpg/a_2x-square.jpg
#remove url http://pixel.nymag.com/imgs/fashion/daily/2012/09/06/06-hair-products.o.jpg/a_146x97.jpg


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'create':
            create_db()
        if cmd == 'drop':
            drop_db()
    else:
        engine = sqlalchemy.create_engine(email_settings.db)
        conn = engine.connect()
        metadata = sqlalchemy.MetaData()
        tb = sqlalchemy.Table('akamaicache', metadata, autoload=True, autoload_with=engine)
        import_emails(conn, tb)
    
