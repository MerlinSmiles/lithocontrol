#!/usr/bin/env python
import sys
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

from PyQt4 import QtCore, QtGui, uic
import socket
import time
import numpy as np

class DXFWorker(QtCore.QThread):

    # dataReady = QtCore.pyqtSignal('QString')

    def __init__(self, data, parent = None):

        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.data = data

    def __del__(self):
        self.wait()


    def run(self):
        print( self.data,  'start' )
        time.sleep(np.random.random()*self.data)
        self.reasult = ['res', self.data]
        self.emit( QtCore.SIGNAL('dataReady(PyQt_PyObject)'), np.array([self.data]) )
        print( self.data,  'end' )
        # self.finished.emit()

        # self.emit(QtCore.SIGNAL("AFMStatus(QString)"), line)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    def done():
        print("Done!", "Done fetching posts!")
    @QtCore.pyqtSlot("PyQt_PyObject")
    def done2(a='None'):
        print("Done!", a)

    threads = []
    for i in range(10):
        t = DXFWorker(i)
        t.start()
        print (i)
        app.connect(t, QtCore.SIGNAL("finished()"), done)
        app.connect(t, QtCore.SIGNAL("dataReady(PyQt_PyObject)"), done2)
    # obj.dataReady.connect(onDataReady)
        threads.append(t)
    # print (threads)

    # obj.moveToThread(thread)

    # if you want the thread to stop after the worker is done
    # you can always call thread.start() again later
    # obj.finished.connect(thread.quit)

    # one way to do it is to start processing as soon as the thread starts
    # this is okay in some cases... but makes it harder to send data to
    # the worker object from the main gui thread.  As you can see I'm calling
    # processA() which takes no arguments
    # thread.started.connect(obj.processA)
    # thread.finished.connect(app.exit)

    # thread.start()

    # another way to do it, which is a bit fancier, allows you to talk back and
    # forth with the object in a thread safe way by communicating through signals
    # and slots (now that the thread is running I can start calling methods on
    # the worker object)
    # QtCore.QMetaObject.invokeMethod(obj, 'processB', Qt.QueuedConnection,
    #                                 QtCore.Q_ARG(int, 2))
    # QtCore.QMetaObject.invokeMethod(obj, 'processB', Qt.QueuedConnection,
    #                                 QtCore.Q_ARG(int, 3))

    # that looks a bit scary, but its a totally ok thing to do in Qt,
    # we're simply using the system that Signals and Slots are built on top of,
    # the QMetaObject, to make it act like we safely emitted a signal for
    # the worker thread to pick up when its event loop resumes (so if its doing
    # a bunch of work you can call this method 10 times and it will just queue
    # up the calls.  Note: PyQt > 4.6 will not allow you to pass in a None
    # instead of an empty list, it has stricter type checking

    sys.exit(app.exec_())
    # app.exec_()