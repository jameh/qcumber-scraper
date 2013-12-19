import re
import requests.utils
from bs4 import BeautifulSoup
from scraper.agent import Request

from urllib.parse import urljoin

def _get_win0(soup):
    form = soup.find('form', {'name': 'win0'})
    if not form:
        print(soup)
        raise "HOLY SHIT"
    action = form.get('action')
    payload = {}
    for data in form.find_all('input', type='hidden'):
        payload[data.get('name')] = data.get('value')

    return {
        'action': action,
        'payload': payload
    }

def _cookie_state(session):
    d = requests.utils.dict_from_cookiejar(session.cookies)
    del d['PS_TOKENEXPIRE']
    return d # {'PS_PERSIST': d['PS_PERSIST']}

def course_catalog(page, request, session, queue):
    soup = BeautifulSoup(page.text)
    win0 = _get_win0(soup)
    cookies = _cookie_state(session)

    for char in 'abcdef':
        payload = win0['payload'].copy()
        payload['ICAction'] = 'DERIVED_SSS_BCC_SSR_ALPHANUM_{}'.format(char.upper())

        queue.put(Request(
            action=urljoin(page.url, win0['action']),
            method='POST',
            payload=payload,
            cookies=cookies,
            parser=alphanum,
            description='Alphanum ({}) parser'.format(char)
        ))

    return True

def alphanum(page, request, session, queue):
    soup = BeautifulSoup(page.text)
    win0 = _get_win0(soup)
    cookies = _cookie_state(session)

    subjects = soup.find_all('a', id=re.compile(r'DERIVED_SSS_BCC_GROUP_BOX_1\$84\$\$'))

    for subject_tag in subjects:
        payload = win0['payload'].copy()
        payload['ICAction'] = subject_tag['id']

        Request(
            action=urljoin(page.url, win0['action']),
            method='POST',
            payload=payload,
            cookies=cookies,
            parser=subject,
            description='Parse subject {}'.format(subject_tag.string)
        ).run(session, queue, task=False)
    return True

def subject(page, request, session, queue):
    soup = BeautifulSoup(page.text)
    win0 = _get_win0(soup)
    cookies = _cookie_state(session)

    courses = soup.find_all('a', id=re.compile(r'CRSE_NBR\$'))

    i=0
    for course_tag in courses:
        i+=1
        if i>2:
            return True
        payload = win0['payload'].copy()
        payload['ICAction'] = course_tag['id']

        queue.put(Request(
            action=urljoin(page.url, win0['action']),
            method='POST',
            payload=payload,
            cookies=cookies,
            parser=course,
            description='Parse course {} - {}'.format(request.description, course_tag.string)
        ))
    return True

def course(page, request, session, queue):
    print('HOLY SHITTTY!')

    return True
