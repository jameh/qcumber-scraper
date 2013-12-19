try:
    from queue import Queue # Python3
except ImportError:
    from Queue import Queue # Python2

import scraper.parsers as parsers
from scraper.agent import Request

def init_queue():
    ##
    # Create the Queue object
    ##
    queue = Queue()

    ##
    # Add a request for the course catalog
    ##
    queue.put(Request(
        action='https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL',
        method='GET',
        payload={'ICAction': ''},
        parser=parsers.course_catalog,
        description='Base Course Catalog Request',
    ))

    return queue

