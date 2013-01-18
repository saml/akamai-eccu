import getpass
import imaplib
import argparse
import sys
import datetime
import re
import time

import sqlalchemy
from flask import Flask, g
import flask
import pytz

import email_settings

app = Flask(__name__)

@app.before_request
def before_request():
    g.db_conn, g.db_tb = get_db()

@app.teardown_request
def teardown_request(exception):
    g.db_conn.close()

@app.route("/")
def report():
    return flask.render_template('report.html')

@app.route("/series")
def report_series():
    now = datetime.datetime.now()
    days_ago = now - datetime.timedelta(days=30) 
    count_series = []
    elapsed_series = []
    utc = datetime.datetime.utcfromtimestamp(0).replace(tzinfo = pytz.UTC)
    for submitted_at, elapsed, count in g.db_conn.execute(sqlalchemy.text('''select submitted_at, (completed_at - submitted_at), count(url) 
            from akamaicache 
            where submitted_at > :start and submitted_at < :end
            group by submitted_at, completed_at 
            order by submitted_at asc'''), start=days_ago, end=now):
        timestamp = (submitted_at - utc).total_seconds() * 1000
        count_series.append([timestamp, count])
        elapsed_series.append([timestamp, elapsed.total_seconds() / 60.0])

    return flask.jsonify(counts = count_series, delays = elapsed_series)



def create_db():
    engine = sqlalchemy.create_engine(email_settings.db)
    engine.execute('''CREATE TABLE akamaicache(
        id SERIAL PRIMARY KEY,
        submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
        completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
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
        typ, data = M.fetch(num, '(BODY.PEEK[TEXT])')
        submitted_at = None
        completed_at = None
        for line in data[0][1].split('\n'):
            line = line.strip()
            if line.startswith('Submission time:'):
                submitted_at = datetime.datetime.strptime(line, 'Submission time:   %a, %d %b %Y %H:%M:%S +0000').replace(tzinfo=pytz.UTC)
            elif line.startswith('Completion time:'):
                completed_at = datetime.datetime.strptime(line, 'Completion time:   %a, %d %b %Y %H:%M:%S +0000').replace(tzinfo=pytz.UTC)
            elif line.startswith('remove url'):
                url = line[len('remove url '):]
                batch.append({'submitted_at': submitted_at, 'completed_at': completed_at, 'url': url})
                print(url, submitted_at, completed_at)
                if len(batch) >= 1000:
                    conn.execute(insert, batch)
                    batch = []
    if len(batch) > 0:
        conn.execute(insert, batch)
    M.close()
    M.logout()

def get_db():
    engine = sqlalchemy.create_engine(email_settings.db)
    conn = engine.connect()
    metadata = sqlalchemy.MetaData()
    tb = sqlalchemy.Table('akamaicache', metadata, autoload=True, autoload_with=engine)
    return (conn, tb)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'create':
            create_db()
        elif cmd == 'drop':
            drop_db()
        elif cmd == 'import':
            conn, tb = get_db()
            import_emails(conn, tb)
    else:
        app.run(debug=True)
        
