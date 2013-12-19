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

    def run(self, agent, queue):
        ##
        # Modify the agent's cookie state
        ##
        cookiejar = agent.local.auth_cookies.copy()
        requests.utils.add_dict_to_cookiejar(cookiejar, self.cookies)
        agent.local.session.cookies = cookiejar

        ##
        # Make the request for the page
        ##
        page = agent.local.session.request(self.method, self.action, self.payload)

        ##
        # Parse the page
        ##
        try:
            self.parser(page, self, agent, queue)
        except Exception as e:
            # TODO: Make this only fail a limited number of times before giving up
            print('WARNING: Parsing request {} failed ({})'.format(str(self), str(e)), 
                    file=sys.stderr)
            queue.put(self)

        ##
        # Mark the task as done
        ##
        queue.task_done()


class Agent(object):

    LOGIN_URL = 'https://my.queensu.ca/'
    SOLUS_URL = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/s/WEBLIB_QU_SSO.FUNCLIB_01.FieldFormula.IScript_SSO?tab=SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL'

    def maybe_continue_page(self, page):
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
            return self.local.session.request('POST', action, data=payload)

    def authenticate(self):
        print('Trying to authenticate')
        print(self.local.session)
        ##
        # Load the login page from the server to set initial cookies
        ##
        login_page = self.local.session.request('GET', self.LOGIN_URL)
        print('Login Page')

        ##
        # Send the login request
        ##
        login_payload = {
            'j_username': config['SOLUS_NETID'],
            'j_password': config['SOLUS_PASSWD'],
            'IDButton': '%C2%A0Log+In%C2%A0'
        }
        loggedin_page = self.local.session.request('POST', 
                            login_page.url, data=login_payload)
        loggedin_page = self.maybe_continue_page(loggedin_page)
        print('Loggedin Page')

        ##
        # Open the SOLUS homepage (performs SSO login)
        ##
        solus_page = self.local.session.request('GET', self.SOLUS_URL)
        solus_page = self.maybe_continue_page(solus_page)
        print("***** SOLUS PAGE *****")
        print(solus_page.text)
        print("***** SOLUS PAGE *****")

    def __call__(self, queue):
        """ Call the agent object to start processing """

        print('WHAT?')
        self.local = threading.local()

        ##
        # Create this Agent's Requests Session
        ##
        self.local.session = requests.Session()
        self.local.session.mount('https://', SSLAdapter())

        print('Session Created')
        print(self)

        ##
        # Authenticate with SSO
        ##
        try:
            self.authenticate()
        except:
            print('???')
        print('Auth')
        self.local.auth_cookies = self.local.session.cookies.copy()

        print('Authenticated')

        ##
        # Process requests off of the stack
        ##
        while(True):
            print('WAITING')
            request = queue.get()
            print('GET REQUEST!')
            request.run(self, queue)
            print('REQUEST DONE!')

