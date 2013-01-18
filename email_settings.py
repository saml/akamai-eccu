host = 'your imap host'
port = 993 # your imap port
username = 'your imap username that gets akamai notification emails'
password = 'your email password'
db = 'postgresql://akamai_email:akamai_email@127.0.0.1/akamai_email'

try:
    from email_settings_local import *
except ImportError:
    pass
