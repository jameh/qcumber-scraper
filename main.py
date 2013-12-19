import logging
from threading import Thread
try:
    from queue import Queue, Empty
except ImportError:
    # Python 2.x
    from Queue import Queue, Empty

from navigation import SolusSession
from scraper import SolusScraper

class ScrapeJob(dict):
    """
    Holds data on a scraper job. Includes default arguments.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        # Supply custom defaults
        self["deep"] = self.get("deep", True)
        self["letters"] = self.get("letters", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self["subject_start"] = self.get("subject_start", 0)
        self["subject_step"] = self.get("subject_step", 1)
        self["subject_end"] = self.get("subject_end", None)
        self["course_start"] = self.get("course_start", 0)
        self["course_end"] = self.get("course_end", None)


class JobManager(object):
    """Handles dividing up the scraping work and starting the scraper threads"""

    def __init__(self, user, passwd, config):
        """Initialize the Scraper object"""

        self.user = user
        self.passwd = passwd
        self.config = config
        self.jobs = Queue()

        # Enforce a range of 1 - 10 threads with a default of 5
        self.config["threads"] = max(min(self.config.get("threads", 5), 10), 1)
        self.config["job"] = self.config.get("job", ScrapeJob())
        
        # Divide up the work for the number of threads
        self.make_jobs()
    
    def start(self):
        """Start running the scraping threads"""

        self.start_jobs()

    def make_jobs(self):
        """Takes the configuration and returns a list of jobs"""

        job = self.config["job"]
        letters = job["letters"]

        threads_per_letter = int((self.config["threads"] - 1)/len(letters) + 1)

        for l in letters:
            job_letter = ScrapeJob(job)
            job_letter["letters"] = l
            for s in range(0, threads_per_letter):
                temp = ScrapeJob(job_letter)
                temp["subject_start"] = s
                temp["subject_step"] = threads_per_letter
                logging.info("Made job: {0}".format(temp))
                self.jobs.put_nowait(temp)
    
    def run_jobs(self):
        """Initialize a SOLUS session and run the jobs"""

        # Initialize the session
        try:
            session = SolusSession(self.user, self.passwd)
        except EnvironmentError as e:
            logging.critical(e)
            # Can't log in, therefore can't do any jobs
            # As long as at least 1 of the threads can log in,
            # the scraper will still work
            return

        # Run all the jobs in the job queue
        while True:
            job = self.jobs.get()

            # Run the job
            SolusScraper(session, job).start()
            self.jobs.task_done()

    def start_jobs(self):
        """Start the threads that perform the jobs"""

        threads = []
        for x in range(self.config["threads"]):
            threads.append(Thread(target=self.run_jobs))
            threads[-1].daemon = True
            threads[-1].start()

        self.jobs.join()


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    # Testing
    config = dict(
        name = "Shallow scrape with threading",
        description = "Scrapes the entire catalog using multiple threads",
        threads = 2,
        job = ScrapeJob(letters="AB", deep=False)
    )

    # Get credientials
    try:
        from config import SCRAPER_USER, SCRAPER_PASS
    except ImportError:
        logging.critical("No credientials found. Create a config.py file with SCRAPER_USER and SCRAPER_PASS constants")

    # Start scraping
    JobManager(SCRAPER_USER, SCRAPER_PASS, config).start()
