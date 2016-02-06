import sys, time
from PyQt4 import QtCore, QtGui
import numpy as np
class MyApp(QtGui.QWidget):
 def __init__(self, parent=None):
  QtGui.QWidget.__init__(self, parent)

  self.setGeometry(300, 300, 280, 600)
  self.setWindowTitle('threads')

  self.layout = QtGui.QVBoxLayout(self)

  self.testButton = QtGui.QPushButton("test")
  self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
  self.listwidget = QtGui.QListWidget(self)

  self.layout.addWidget(self.testButton)
  self.layout.addWidget(self.listwidget)

  self.threadPool = []

 def add(self, text):
  """ Add item to list widget """
  print "Add: " + text
  self.listwidget.addItem(text)
  self.listwidget.sortItems()

 def data(self, data):
  """ Add item to list widget """
  print data

 def addBatch(self,text="test",iters=6,delay=0.3):
  """ Add several items to list widget """
  for i in range(iters):
   time.sleep(np.random.random()) # artificial time delay
   self.add(text+" "+str(i))

 def addBatch2(self,text="test",iters=6,delay=0.3, data=1):
  for i in range(iters):
   time.sleep(np.random.random()) # artificial time delay
   self.emit( QtCore.SIGNAL('add(PyQt_PyObject)'), np.random.random(data) )

 def test(self):
  self.listwidget.clear()
  # adding in main application: locks ui
  #self.addBatch("_non_thread",iters=6,delay=0.3)

  # adding by emitting signal in different thread
  self.threadPool.append( WorkThread('bla') )
  self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update(QString)"), self.add )
  self.threadPool[len(self.threadPool)-1].start()

  # generic thread using signal
  self.threadPool.append( GenericThread(self.addBatch2,"from generic thread using signal ",delay=0.3, data=4) )
  self.disconnect( self, QtCore.SIGNAL("add(PyQt_PyObject)"), self.data )
  self.connect( self, QtCore.SIGNAL("add(PyQt_PyObject)"), self.data )
  self.threadPool[len(self.threadPool)-1].start()

  print('here')

class WorkThread(QtCore.QThread):
 def __init__(self, name):
  QtCore.QThread.__init__(self)
  self.name = name

 def __del__(self):
  self.wait()

 def run(self):
  print self.name
  for i in range(6):
   time.sleep(0.3) # artificial time delay
   self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) )
  return

class GenericThread(QtCore.QThread):
 def __init__(self, function, *args, **kwargs):
  QtCore.QThread.__init__(self)
  self.function = function
  self.args = args
  self.kwargs = kwargs

 def __del__(self):
  self.wait()

 def run(self):
  self.function(*self.args,**self.kwargs)
  return

# run
app = QtGui.QApplication(sys.argv)
test = MyApp()
test.show()
app.exec_()