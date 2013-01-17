host = 'your imap host'
port = 993 # your imap port
username = 'your imap username that gets akamai notification emails'
password = 'your email password'
db = 'sqlite://'

try:
    from email_settings_local import *
except ImportError:
    pass
