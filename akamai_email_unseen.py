import imaplib
import email_settings

M = imaplib.IMAP4_SSL(email_settings.host, email_settings.port)
M.login(email_settings.username, email_settings.password)
M.select()
typ, data = M.search(None, 'ALL')
for num in data[0].split():
    M.store(num, '-FLAGS', '\\Seen')
M.close()
M.logout()
