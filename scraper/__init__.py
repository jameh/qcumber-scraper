import logging
logging.basicConfig(level=logging.DEBUG)

import os
from requests import Session, utils
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
from bs4 import BeautifulSoup

class SSLAdapter(HTTPAdapter):
    '''An HTTPS Transport Adapter that uses an arbitrary SSL version.
    http://lukasa.co.uk/2013/01/Choosing_SSL_Version_In_Requests/
    '''
    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version

        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=self.ssl_version)


s = Session()
s.mount('https://', SSLAdapter(ssl_version=ssl.PROTOCOL_TLSv1))

login_page = s.request('GET', 'https://my.queensu.ca/')

payload = {
    'j_username': os.environ['SOLUS_NETID'],
    'j_password': os.environ['SOLUS_PASSWD'],
    'IDButton': '%C2%A0Log+In%C2%A0',
}
continue_page = s.request('POST', login_page.url, data=payload)
soup = BeautifulSoup(continue_page.text)

form = soup.find('form')
action = form.get('action')

payload = {}
for data in form.find_all('input', type='hidden'):
    payload[data.get('name')] = data.get('value')

loggedin_page = s.request('POST', action, data=payload)

soup = BeautifulSoup(loggedin_page.text)

link = soup.find('a', text='SOLUS')

continue_page = s.get(link.get('href')) # For some reason this always gives me an error processing authentication request problem.  

soup = BeautifulSoup(continue_page.text)

form = soup.find('form')
action = form.get('action')

payload = {}
for data in form.find_all('input', type='hidden'):
    payload[data.get('name')] = data.get('value')

solus_page = s.request('POST', action, data=payload)

# catalog_page = s.request('POST', 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL', data={'ICAction': ''})


