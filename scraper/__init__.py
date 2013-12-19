from threading import Thread
from scraper.queue import init_queue
from scraper.agent import agent

agent_count = 10

queue = init_queue()

for i in range(agent_count):
    thread = Thread(target=agent, args=(queue,), 
                name='Qcumber Agent {}'.format(i))
    thread.daemon = True
    thread.start()

queue.join()

