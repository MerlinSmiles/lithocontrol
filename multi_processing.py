import multiprocessing as mp
from multiprocessing import Process, Queue
from PyQt4 import QtCore, QtGui
# from MyJob import job_function
import sys, os
import numpy as np
from source.ni_measurement2 import *

from source.ringbuffer2 import *




class jobProcess(mp.Process):
    # def __init__(self, taskQueue, resultQueue, processName):
    def __init__(self, resultQueue, killEvent):
        super(jobProcess, self).__init__()
        # self.taskQueue      = taskQueue
        self.resultQueue = resultQueue
        self.killEvent = killEvent
        # self.processName    = processName

    def run(self):
        print("pid %s of process that could be killed" % os.getpid())

        while not self.killEvent.is_set():
            time.sleep(0.02)
            self.resultQueue.put(np.random.rand(1,5))
        print("pid %s of process that jsut ended" % os.getpid())
        return



class Runner(QtCore.QObject):
    """
    Runs a job in a separate process and forwards messages from the job to the
    main thread through a pyqtSignal.
    """
    msg_from_job = QtCore.pyqtSignal(object)

    def __init__(self, start_signal,kill_event, parent=None):
        super(Runner, self).__init__(parent)
        self.kill_event = kill_event
        self.queue = Queue()
        start_signal.connect(self._run)

    def _run(self):
        print('inrun')
        self.kill_event.clear()
        # self.p = jobProcess(self.queue, self.kill_event)
        self.p = ni_Worker(self.queue, self.kill_event)
        # self.p = Process(target=ni_Worker, args=(self.queue, self.kill_event))
        self.p.start()
        self.get()

    def get(self):
        # print('inget')
        if self.kill_event.is_set():
            self.p.join()
            print('process ended')
        else:
            msg = self.queue.get()
            self.msg_from_job.emit(msg)
            # if msg == 'done':
            #     print('donedone')
            #     break

            QtCore.QTimer.singleShot(0, self.get)


    # def _stop(self):
        # print('stopping')
        # self.kill_event.set()
        # self.running = False

# Things below live on the main thread

class MainWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Setup the OQ listener thread and move the OQ runner object to it

        win = self
        layout = QtGui.QGridLayout()
        win.setLayout(layout)
        bs = QtGui.QPushButton('Start')
        be = QtGui.QPushButton('End')
        layout.addWidget(bs)
        layout.addWidget(be)

        self.timer = QTime.currentTime()
        self.buffer = RingBuffer2(200000,4)


        self.kill_event = mp.Event()
        self.runner_thread = QtCore.QThread()
        self.runner = Runner(start_signal=self.runner_thread.started, kill_event=self.kill_event)

        self.runner.msg_from_job.connect(self.handle_msg)
        self.runner.moveToThread(self.runner_thread)
        # self.runner_thread.start()
        print('init')
        bs.clicked.connect(self.start_runner)
        # bs.clicked.connect(self.runner_thread.start)
        be.clicked.connect(self.quit_runner)
        # QtCore.QTimer.singleShot(1, self.quit_runner)
        self.cnt = 0
        self.t = 0


        # self.run_job('test')
    # def run_job(self):
    #     """ Call this to start a new job """
    #     print('starting')
        # self.runner.job_input = input
        # QtCore.QTimer.singleShot(3000, self.quit_runner)
        # self.runner_thread.start()
        # print('init')

    def start_runner(self):
        self.runner_thread.start()

    def quit_runner(self):
        print('ending')
        self.kill_event.set()
        self.runner_thread.exit()
        self.runner_thread.wait()
        print(self.runner_thread.isRunning())
        # print('quit 1')
        # print('quit 2')
        # # self.runner_thread.quit()
        # print('quit 3')

    def handle_msg(self, msg):
        self.buffer.append(msg)
        self.cnt += 1
        if self.cnt>100:
            self.cnt = 0
            # t = self.timer.elapsed()
            # print (self.buffer.data.shape)
            print (self.buffer.get_partial_clear())
            # print(type(msg))
            # self.t = t
            # print(self.timer.elapsed()/1000)
        # print(msg)

        # self.timer.restart()


if __name__ == '__main__':
    print('\n\n')
    mp.freeze_support()

    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    # time.sleep(3)
    # main.quit_runner()
    # self.runner._stop()
    # window = MainWindow()
    # window.show()
    sys.exit(app.exec_())


# import multiprocessing
# class MyFancyClass(object):

#     def __init__(self, name):
#         self.name = name

#     def do_something(self):
#         proc_name = multiprocessing.current_process().name
#         print '\n\nDoing something fancy in %s for %s!' % (proc_name, self.name)
# def worker(q):
#     while(1):
#         obj = q.get()
#         if obj:
#             obj.do_something()
# if __name__ == '__main__':
#     queue = multiprocessing.Queue()
#     p = multiprocessing.Process(target=worker, args=(queue,))
#     p.start()
#     # p.start()

#     # queue.put(MyFancyClass('Fancy Dan1'))
#     queue.put(MyFancyClass('Fancy Dan2'))
#     # p.start()

#     queue.put(MyFancyClass('Fancy Dan3'))

#     # Wait for the worker to finish
#     queue.close()
#     queue.join_thread()
#     p.join()

# import pickle
# import multiprocessing
# from multiprocessing import Process, Pipe, Event
# import time
# import numpy as np
# import sys
# from source.generator import reader, writer
# print('\n\n')

# from PyQt4.QtCore import QTime, QTimer, QDate

# if __name__=='__main__':
#     timer = QTime.currentTime()
#     terminate_measurement = Event()
#     pipe_read, pipe_write = Pipe()
#     tasks = multiprocessing.Queue()
#     mgr = multiprocessing.Manager()
#     settings = mgr.dict()
#     settings['time'] = timer
#     settings['kkk'] = 1
#     settings['measure'] = False

#     reader_p = reader(pipe_read,terminate_measurement,tasks,settings)
#     reader_p.daemon = True

#     writer_p = writer(pipe_write,terminate_measurement,tasks,settings)
#     writer_p.daemon = True

#     # del writer_p.context
#     # del reader_p.process


#     writer_p.start()            # Launch the writer process
#     reader_p.start()            # Launch the reader process
#     settings['measure'] = True  # Finally starts the measurement

#     time.sleep(1)
#     tasks.put({'key':5})
#     settings['kkk'] = 2
#     time.sleep(1)
#     # Stop processes
#     terminate_measurement.set()
#     # Finish and close processes
#     writer_p.join()
#     reader_p.join()
#     pipe_read.close()
#     pipe_write.close()

#     print ('Finished')
