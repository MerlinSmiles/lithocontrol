import sys
import numpy as np
import time
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal
import multiprocessing as mp
from multiprocessing import Queue, Process, freeze_support


class Runner(QtCore.QObject):

    new_data = QtCore.pyqtSignal(object)

    def __init__(self, start_signal, stopMeasEvent, timer=None, parent=None):
        super(Runner, self).__init__(parent)
        self.stopMeasEvent = stopMeasEvent
        self.queue = Queue()
        self.timer = timer
        start_signal.connect(self.run)
        print('initRunner')

    def run(self):
        print('runner run')
        self.stopMeasEvent.clear()
        self.p = ni_Worker(self.queue, self.stopMeasEvent, timer=self.timer)
        self.p.start()
        self.get()

    def get(self):
        # print('inget')
        if self.stopMeasEvent.is_set():
            self.p.join()
            print('Measurement Process ended')
        else:
            msg = self.queue.get()
            # msg = str(np.random.random())
            self.new_data.emit(msg)
            QtCore.QTimer.singleShot(0, self.get)

class ni_Worker(mp.Process):
    def __init__(self, resultQueue, stopMeasEvent, timer=None):
        super(ni_Worker, self).__init__()
        print('init worker')
        if timer is None:
            timer = QTime.currentTime()
            timer.start()
        self.timer = timer

        self.resultQueue = resultQueue
        self.stopMeasEvent = stopMeasEvent
        print("initializing DAQ-process")

        self.nChannels = 2
        self.data = np.zeros(self.nChannels+1)

        # app = QtGui.QApplication(sys.argv)
        # window = subWindow()
        # self.show()
        # sys.exit(app.exec_())

    def run(self):
        print('worker run')
        while not self.stopMeasEvent.is_set():
            time.sleep(0.04)
            self.data[0] = self.timer.elapsed()/1000.0
            self.data[1:] = np.random.rand(self.nChannels)
            # print('xx', self.data)
            self.resultQueue.put(self.data)
        return


# class subWindow(QtGui.QMainWindow):
#     sig_measure = pyqtSignal(int)
#     def __init__(self, parent=None):
#         super(subWindow, self).__init__(parent)

class MainWindow(QtGui.QMainWindow):
    sig_measure = pyqtSignal(int)
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.stopMeasEvent = mp.Event()
        self.ni_runner_thread = QtCore.QThread()
        self.ni_runner = Runner(start_signal=self.ni_runner_thread.started, stopMeasEvent=self.stopMeasEvent)
        self.ni_runner.new_data.connect(self.handle_msg)
        self.ni_runner.moveToThread(self.ni_runner_thread)
        self.sig_measure.connect(self.ni_runner_thread.start)
        self.ni_runner_thread.start()
        # self.sig_measure.emit(500)

    def handle_msg(self, msg):
        print(msg)


if __name__ == '__main__':
    freeze_support()

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())










# class MyApp(Process):

#    def __init__(self):
#         self.queue = Queue(1)
#         super(MyApp, self).__init__()
#         app = QtGui.QApplication([])
#         print('xx')
#         window = MainWindow()
#         window.show()

#    def run(self):
#         return_value = str(np.random.random())
#         self.queue.put(return_value)
#         # while True:
#         #     time.sleep(1)
#         # sys.exit(app.exec_())


# if __name__ == '__main__':
#     freeze_support()
#     app1 = MyApp()
#     app1.start()
#     # app1.join()
#     print("App 1 returned: " + app1.queue.get())

#     app2 = MyApp()
#     app2.start()
#     # app2.join()
#     print("App 2 returned: " + app2.queue.get())

#     app3 = MyApp()
#     app3.start()
#     # app3.join()
#     print("App 3 returned: " + app3.queue.get())

#     # app = QtGui.QApplication(sys.argv)
#     # window = MainWindow()
#     # # window.show()

