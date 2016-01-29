import multiprocessing as mp
import time
import numpy as np
import sys

print('\n\n')


class writer(mp.Process):
    def __init__(self, pipe_write,terminate, tasks, settings):
        mp.Process.__init__(self)
        self.pipe_write = pipe_write
        self.terminate = terminate
        self.tasks = tasks
        self.settings = settings
        self.p = mp.current_process()
        self.n = 1

    def run(self):
        cnt = 0
        while self.terminate.is_set() == False:
            if not self.tasks.empty():
                self.parse_tasks()
            if self.settings['measure']:
                cnt+=1
                tdelta = self.settings['time'].elapsed()/1000.0
                data = [tdelta,np.random.random(),np.random.random()]
                self.pipe_write.send(data)             # Write 'count' numbers into the input pipe
                # time.sleep(0.01)

        print('Sent %i packages'%cnt)
        print('Exiting %s:'%self.name, self.p.name, self.p.pid)
        sys.stdout.flush() # do not buffer...(?)
        return

    def parse_tasks(self):
        elem = self.tasks.get()
        if type(elem) is dict:
            if 'key' in elem:
                self.n = elem['key']
                print('got', elem['key'])


class reader(mp.Process):
    def __init__(self, pipe_read, terminate, tasks, settings):
        mp.Process.__init__(self)
        self.pipe_read = pipe_read
        self.terminate = terminate
        self.tasks = tasks
        self.settings = settings
        self.p = mp.current_process()
        self.n = 1

    def run(self):
        cnt = 0
        # self.pipe_read.clear()
        while self.terminate.is_set() == False:
            if not self.tasks.empty():
                self.parse_tasks()
            if self.pipe_read.poll():
                cnt +=1
                msg = self.pipe_read.recv()    # Read from the output pipe and do nothing
                if self.settings['measure']:
                    print(msg, self.n)
        print('Received %i packages'%cnt)
        print('Exiting %s:'%self.name, self.p.name, self.p.pid)
        sys.stdout.flush() # do not buffer...(?)
        return

    def parse_tasks(self):
        elem = self.tasks.get()
        if type(elem) is dict:
            if 'key' in elem:
                self.n = elem['key']
                print('got', elem['key'])

