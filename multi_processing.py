
print('\n\n')

import multiprocessing as mp
from PyQt4 import QtCore, QtGui
# from MyJob import job_function
import sys, os
import numpy as np
from source.ni_measurement2 import *
from source.buffer import *


class MainWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Setup the OQ listener thread and move the OQ runner object to it

        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        bs = QtGui.QPushButton('Start')
        be = QtGui.QPushButton('End')
        layout.addWidget(bs)
        layout.addWidget(be)
        bs.clicked.connect(self.start_runner)
        be.clicked.connect(self.quit_runner)

        self.stopMeasEvent = mp.Event()

        self.timer = QTime.currentTime()
        self.timer.start()
        self.buffer = Buffer(864000, cols=5)

        self.runner_thread = QtCore.QThread()
        self.runner = Runner(start_signal=self.runner_thread.started, stopMeasEvent=self.stopMeasEvent, timer=self.timer)
        self.runner.new_data.connect(self.handle_msg)
        self.runner.moveToThread(self.runner_thread)

        self.cnt = 0

    def start_runner(self):
        self.runner_thread.start()

    def quit_runner(self):
        print('ending')
        self.stopMeasEvent.set()
        self.runner_thread.exit()
        self.runner_thread.wait()
        print(self.runner_thread.isRunning())

    def handle_msg(self, msg):
        # self.buffer[self.cnt] = msg
        self.buffer.append(msg)
        self.cnt += 1
        # print(msg)
        # if self.cnt%1000 == 0:
        #     print (self.buffer.index)
        #     # print(self.buffer[:self.cnt])
        #     print(self.cnt)
        #     print(msg.shape)
        #     print(self.buffer.get_partial_clear())






# class jobProcess(mp.Process):
#     # def __init__(self, taskQueue, resultQueue, processName):
#     def __init__(self, resultQueue, killEvent):
#         super(jobProcess, self).__init__()
#         # self.taskQueue      = taskQueue
#         self.resultQueue = resultQueue
#         self.killEvent = killEvent
#         # self.processName    = processName

#     def run(self):
#         print("pid %s of process that could be killed" % os.getpid())

#         while not self.killEvent.is_set():s
#             time.sleep(0.01)
#             self.resultQueue.put(np.random.rand(1,5))
#         print("pid %s of process that jsut ended" % os.getpid())
#         return


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
