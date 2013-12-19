from __future__ import print_function

import sys
import threading
import requests
from bs4 import BeautifulSoup

from scraper.ssladapter import SSLAdapter
from scraper.config import config

class Request(object):
    def __init__(self, action, method='GET', cookies=None, payload=None, parser=None, description=''):
        self.action = action
        self.method = method
        self.payload = payload
        self.parser = parser
        self.description = description
        self.cookies = cookies

    def run(self, session, queue, task=True):
        print('running {}'.format(self.description))
        ##
        # Modify the session's cookie state
        ##
        requests.utils.add_dict_to_cookiejar(session.cookies, self.cookies)

        ##
        # Make the request for the page
        ##
        page = session.request(self.method, self.action, self.payload)

        ##
        # Parse the page
        ##
        try:
            self.parser(page, self, session, queue)
        except Exception as e:
            # TODO: Make this only fail a limited number of times before giving up
            print('WARNING: Parsing request {} failed ({})'.format(str(self.description), str(e)), 
                    file=sys.stderr)
            # queue.put(self)

        ##
        # Mark the task as done
        ##
        if task:
            queue.task_done()


LOGIN_URL = 'https://my.queensu.ca/'
SOLUS_URL = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/s/WEBLIB_QU_SSO.FUNCLIB_01.FieldFormula.IScript_SSO?tab=SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL'

def _maybe_continue_page(session, page):
    """
    Sometimes requests can land you on a `continue` page
    Normally this redirects using javascript
    This simulates the javascript and submits the form
    """

    soup = BeautifulSoup(page.text)
    form = soup.find('form')
    if not form:
        # Don't need to redirect
        return page
    else:
        action = form.get('action')
        payload = {}
        for data in form.find_all('input', type='hidden'):
            payload[data.get('name')] = data.get('value')

        # Request the redirected page
        return session.request('POST', action, data=payload)

def _authenticate(session):
    ##
    # Load the login page from the server to set initial cookies
    ##
    login_page = session.request('GET', LOGIN_URL)

    ##
    # Send the login request
    ##
    login_payload = {
        'j_username': config['SOLUS_NETID'],
        'j_password': config['SOLUS_PASSWD'],
        'IDButton': '%C2%A0Log+In%C2%A0'
    }
    loggedin_page = session.request('POST', login_page.url, data=login_payload)
    loggedin_page = _maybe_continue_page(session, loggedin_page)

    ##
    # Open the SOLUS homepage (performs SSO login)
    ##
    solus_page = session.request('GET', SOLUS_URL)
    solus_page = _maybe_continue_page(session, solus_page)

def agent(queue):
    try:
        ##
        # Create this Agent's Requests Session
        ##
        session = requests.Session()
        session.mount('https://', SSLAdapter())

        ##
        # Authenticate with SSO
        ##
        _authenticate(session)
        auth_cookies = session.cookies.copy()
        print('Authenticated')

        ##
        # Process requests off of the stack
        ##
        while(True):
            request = queue.get()
            request.run(session, queue)

            # Clobber any changes to the cookies
            session.cookies = auth_cookies.copy()
    except Exception as e:
        print('ERROR: An agent has crashed!')
        raise e

