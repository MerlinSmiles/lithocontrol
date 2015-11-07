
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import time

class MyHandler(PatternMatchingEventHandler):
    def __init__(self, parent = None):
        super( MyHandler, self ).__init__()
        self.parent = parent
        patterns = ["*.*"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        # print( event.src_path, event.event_type  # print( now only for degug )

        self.parent.emit(QtCore.SIGNAL("afmImage(QString)"), event.src_path)

    # def on_modified(self, event):
    #     self.process(event)

    def on_created(self, event):
        self.process(event)

class AFMWorker(QtCore.QThread):

    def __init__(self, parent = None):

        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.foldername = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def monitor(self, foldername):
        self.exiting = False
        self.foldername = foldername
        self.start()

    def stop(self):
        self.exiting = True
        self.wait()

    def run(self):
        observer = Observer()
        observer.schedule(MyHandler(self), path=self.foldername)
        print( 'Monitoring ' + self.foldername )
        observer.start()
        while True and not self.exiting:
            time.sleep(1)
        observer.stop()
        observer.join()