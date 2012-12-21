import requests
from suds.client import Client

import base64
from cStringIO import StringIO
import xml.etree.ElementTree as ET
import datetime
import argparse
import urlparse

import settings

def eccu_doc_for_purge_dir(path_to_purge):
    root = ET.Element('eccu')
    parent = root
    names = (name for name in path_to_purge.split('/') if name)
    for name in names:
        parent = ET.SubElement(parent, 'match:recursive-dirs', {'value': name})
    revalidate = ET.SubElement(parent, 'revalidate')
    revalidate.text = 'now'
    return ET.tostring(root) #'<?xml version="1.0"?>\n' + ET.tostring(root)
    #xml = StringIO()
    #xml.write('<?xml version="1.0"?>\n')
    #xml.write(ET.tostring(root))
    #return xml

class AkamaiEccu(object):
    def __init__(self, username=settings.username, password=settings.password, endpoint=settings.endpoint):
        self.username = username
        self.password = password
        self.auth = (username, password)
        self.endpoint = endpoint

    def do_GET(self, endpoint=None):
        if not endpoint:
            endpoint = self.endpoint
        return requests.get(self.endpoint, auth=self.auth)

    def do_POST(self, endpoint=None):
        if not endpoint:
            endpoint = self.endpoint


def main(argv=None):
    parser = argparse.ArgumentParser(description='purges akamai directory')
    parser.add_argument('url', help='url of directory to purge')
    args = parser.parse_args()

    url = urlparse.urlparse(args.url)
    host = url.netloc
    path = url.path

    client = Client(url=settings.wsdl_url, location=settings.endpoint, username=settings.username, password=settings.password)

    eccu_doc = eccu_doc_for_purge_dir(path)
    now = str(datetime.datetime.now())
    print(eccu_doc)
    result = client.service.upload(
            filename='eccu-purge-dir-' + now, 
            contents=eccu_doc, 
            notes='purging dir: ' + args.url,
            versionString=now,
            propertyName=host,
            propertyType='hostheader',
            propertyNameExactMatch=True,
            statusChageEmail=settings.notification_email)
    print(result)

if __name__ == '__main__':
    main()
