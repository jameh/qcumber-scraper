from threading import Thread
from scraper.queue import init_queue
from scraper.agent import Agent

agent_count = 10
agents = {Agent() for i in range(agent_count)}

queue = init_queue()

for i in range(agent_count):
    agent = Agent()
    thread = Thread(target=agent, args=(queue,), 
                name='Qcumber Agent {}'.format(i))
    thread.daemon = True
    thread.start()

queue.join()

