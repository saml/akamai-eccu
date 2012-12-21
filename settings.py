import os

username='your akamai username'
password='your akamai password'
notification_email='email where you want notification to be sent'
endpoint='https://control.akamai.com/webservices/services/PublishECCU'

#please download wsdl from: https://control.akamai.com/webservices/services/PublishECCU?wsdl
wsdl_url='file://%s' % os.path.join(os.path.dirname(__file__), 'PublishECCU.wsdl')

try:
    from settings_local import *
except ImportError:
    pass

