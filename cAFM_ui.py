#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic

import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.dockarea as pg_dock


# %load_ext autoreload
# %autoreload 2

import sys

from convertAFM import convertAFM

sys.path.append("D:\\Projects\\qtlab\\source")
sys.path.append("D:\\Projects\\qtlab\\instrument_plugins")
import Keithley_merlin_junk
keithley = Keithley_merlin_junk.Keithley_2400('Keithley', address='GPIB0::2::INSTR', reset=False)
keithley.set_output_state(0)
keithley.set_source_voltage(0)
keithley.set_output_state(1)

filename = 'D:/lithography/DesignFiles/Untitled-1.dxf'

import os
import time
import socket
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
# import operatorfmimages
# import dxfgrabber
# from collections import Counter
# import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
# from scipy.interpolate import interp1d
from source.helpers import *
from source.dxf2shape import *

# mkPen for selected
orangePen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
bluePen = pg.mkPen(color='0000FF')  #, style=QtCore.Qt.DotLine
greenPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine

class PlotFrame(QtGui.QWidget):
    def __init__( self, parent=None):
        super(PlotFrame, self).__init__(parent)
        self.area = pg_dock.DockArea()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.area)
        self.setLayout(layout)

        self.sketchDock = pg_dock.Dock("Skecthing", size=(500, 300))     ## give this dock the minimum possible size
        self.measureDock = pg_dock.Dock("Measuring", size=(500,300))

        self.area.addDock(self.sketchDock, 'top')
        self.area.addDock(self.measureDock, 'bottom')

        data = pg.gaussianFilter(np.random.normal(size=(256, 256)), (20, 20))
        self.afmIm = pg.ImageItem(data)
        self.afmIm.setZValue(-1000)

        self.sketchPlot = pg.PlotWidget()
        self.sketchPlot.enableAutoRange('x', True)
        self.sketchPlot.enableAutoRange('y', True)
        self.sketchPlot.setAspectLocked(lock=True, ratio=1)
        self.sketchPlot.showGrid(x=1, y=1, alpha=0.8)
        self.sketchDock.addWidget(self.sketchPlot, 0, 0)


        self.histWidget = pg.HistogramLUTWidget()
        self.sketchDock.addWidget(self.histWidget, 0, 1)

        self.histWidget.setImageItem(self.afmIm)
        self.p = self.sketchPlot.addItem(self.afmIm)
        self.sketchPlot.plot(np.random.normal(size=100))




        self.measurePlot = pg.PlotWidget()
        self.measurePlot.plot(np.random.normal(size=100))
        self.measureDock.addWidget(self.measurePlot)

    def setAfmImage(self, image_data, x= None, y=None):
        if not (x==None or y == None):
            self.afmIm.setRect(pg.QtCore.QRectF(-x/2.0, -y/2.0, x, y))
        self.afmIm.setImage(image_data)



    def clearSketchPlot(self):
        # return
        self.sketchPlot.clear()
        self.histWidget.setImageItem(self.afmIm)
        self.sketchPlot.addItem(self.afmIm)


class SocketWorker(QtCore.QThread):

    def __init__(self, parent = None):

        QtCore.QThread.__init__(self, parent)
        self.exiting = False

        self.host = 'nanoman'
        self.remote_ip = None
        self.port = 12345
        self.sock = None
        self.init = False
        self.connected = False

        self.initSocket()
        self.connectSocket()

    def __del__(self):
        self.stop()

    def initSocket(self):
        try:
            #create an AF_INET, STREAM socket (TCP)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
            self.init =  False

        try:
            self.remote_ip = socket.gethostbyname( self.host )
        except socket.gaierror:
            #could not resolve
            print 'Hostname could not be resolved. Exiting'
            self.init =  False
        self.init =  True

    def connectSocket(self):
        #Connect to remote server
        if not self.init:
            self.initSocket()
        if self.connected:
            self.disconnectSocket()
        try:
            self.sock.connect((self.remote_ip , self.port))
            print 'Socket Connected to ' + self.host + ' on ip ' + self.remote_ip
            self.connected = True
        except:
            self.connected = False
            pass

    def disconnectSocket(self):
        try:
            self.sock.close()
            print 'Socket disconnected'
            self.connected = False
        except:
            pass

    def send_message(self, message):
        if not self.connected:
            self.connectSocket()
        try :
            #Set the whole string
            self.sock.sendall(message)
            # print 'sending message'
        except socket.error:
            #Send failed
            print 'Send failed trying again with reconnect'
            self.initSocket()
            self.connectSocket()
            try :
                #Set the whole string
                # print 'sending message'
                self.sock.sendall(message)
            except socket.error:
                #Send failed
                print 'Send failed: Serious error'

    def recv_message(self, timeout =0, buf = 4096):
        if not self.connected:
            self.connectSocket()
        try:
            self.sock.settimeout(timeout)
            msg = self.sock.recv(buf)
            return msg
        except socket.error, e:
            return False
        else:
            print 'got a message, do something :)'
            pass

    def monitor(self):
        self.exiting = False
        self.start()

    def stop(self):
        self.exiting = True
        self.init = False
        self.connected = False
        self.disconnectSocket()

    def run(self):
        self.exiting = False
        if not self.connected:
            self.connectSocket()

        while not self.exiting:
            time.sleep(1)
            msg = self.recv_message(timeout = 0.05)
            if msg:
                lines = msg.splitlines()
                for line in lines:
                    # self.statusBar().showMessage(line)
                    self.emit(QtCore.SIGNAL("AFMStatus(QString)"), line)
                    if line.startswith('vtip'):
                        line = line.split( )
                        volt = float(line[1])
                        print 'VTIP ' , volt
                        # keithley.set_source_voltage(volt*4)
                    elif line.startswith('Ready'):
                        # keithley.set_source_voltage(0)
                        print "\n\nREADY\n\n"
                    elif line.startswith('xyAbs'):
                        line = line.split( )
                        x = float(line[1])
                        y = float(line[2])
                        r = float(line[3])
                        self.emit(QtCore.SIGNAL("AFMpos(float, float, float)"), x,y,r)





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
        # print event.src_path, event.event_type  # print now only for degug

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
        observer.start()
        while True and not self.exiting:
            time.sleep(3)
        observer.stop()
        observer.join()

class TreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.dxfData = None
        self.pltData = None
        self.entity = None
        self.pltHandle = []
        self.checkState = QtCore.Qt.Unchecked
        self.fillAngle = 0
        self.fillStep = 0.1
        self.volt = 10
        self.rate = 1.0
        self.length = 0.0
        self.sketchTime = 0.0
#     shape.type = None # [VirtualElectrode, line, area]

    def redraw(self):
        print 'called'
        self.setDxfData(dxf2shape(self.entity, fill_step = self.fillStep, fill_angle=self.fillAngle))

    def setCheckState(self, value):
        if value == 2:
            self.checkState = QtCore.Qt.Checked
        elif value == 1:
            self.checkState = QtCore.Qt.PartiallyChecked
        else:
            self.checkState = QtCore.Qt.Unchecked
        return self.checkState

    def setEntity(self, entity):
        self.entity = entity
        self.redraw()

    def setDxfData(self, data):
        self.dxfData = data
        self.pltData = []
        for k in self.dxfData:
            self.pltData.append(k.reshape((-1,2)))
        # self.calcTime()

    def calcLength(self):
        dat = np.array(self.pltData).reshape((-1,2))
        dat_b = np.roll(dat,-1)
        dist = 0
        for k in range(len(dat)-1):
            dist += np.linalg.norm(dat[k]-dat_b[k])

        self.length = dist
        print dist

    def calcTime(self):
        self.calcLength()
        self.sketchTime = self.length / float(self.rate)
        print self.sketchTime

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column=None):
        if column == None:
            return self.itemData[:]
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self, self.model)
            self.childItems.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.insert(position, None)

        for child in self.childItems:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False
        if self.model.rootData[column] == 'Angle':
            if self.fillAngle != value:
                self.fillAngle = value
                self.redraw()
        elif self.model.rootData[column] == 'Step':
            if self.fillStep != value:
                self.fillStep = value
                self.redraw()
        elif self.model.rootData[column] == 'Closed':
            if self.entity.is_closed != value:
                self.entity.is_closed = value
        elif self.model.rootData[column] == 'Time':
            if self.sketchTime != value:
                self.sketchTime = value
                # self.redraw()

        self.itemData[column] = value
        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.checks = {}

        self.rootData = [header for header in headers] # Header Names
        self.rootItem = TreeItem(self.rootData, model=self)
        self.setupModelData(data, self.rootItem)

        self._checked=[[False for i in xrange(self.columnCount())] for j in xrange(self.rowCount())]

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None
        item = self.getItem(index)
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return 0

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def checkState(self, index):
        return self.getItem(index).checkState

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column=0, parent=QtCore.QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def insertColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows,
                self.rootItem.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def childCount(self, parent=QtCore.QModelIndex()):
        return self.rowCount(parent)

    def are_parent_and_child(self, parent, child):
        while child.isValid():
            if child == parent:
                return True
            child = child.parent()
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):

        if (role == QtCore.Qt.CheckStateRole and index.column() == 0):
            self.layoutAboutToBeChanged.emit()
            item = self.getItem(index)

            item.setCheckState(value)
            self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index)

            cc = item.childCount()
            if cc > 0:
                for i in range(cc):
                    chindex =  self.createIndex(i, 0, item.child(i))
                    self.setData(chindex,value,role)


            item = self.getItem(index.parent())
            cc = item.childCount()
            no_checked = 0
            if cc > 0:
                for i in range(cc):
                    if item.child(i).checkState == 2:
                        no_checked+=1
                if no_checked == cc:
                    item.setCheckState(2)
                elif no_checked > 0:
                    item.setCheckState(1)
                else:
                    item.setCheckState(0)
                # self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index.parent())

            self.layoutChanged.emit()
            return True

        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            # if self.rootData[index.column()] == 'Angle':
            #     item.redraw()

            self.emit(QtCore.SIGNAL('redraw(QModelIndex)'), index)
            self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)
                # , value

        return result

    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole or orientation != QtCore.Qt.Horizontal:
            return False

        result = self.rootItem.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def getColumns(self):
        columns = []
        for i in range(self.columnCount()):
            columns.append(self.headerData(i,QtCore.Qt.Horizontal))
        return columns

    def getRows(self):
        rows = []
        for i in range(self.rowCount()):
            rows.append(self.getItem(self.index(i)))
        return rows

    def clearData(self):
        self.rootItem = TreeItem(self.rootData, model=self)

    def setupModelData(self, data, parent):
        columns = self.getColumns()
        parents = [parent]
        indentations = [0]

        number = 0
        layers = {}
        parent_dict = {}
        while number < len(data.entities):
            # entities are right in dxf file!!
            entity = data.entities[number]
            # print entity.is_closed
            if entity.dxftype not in ['POLYLINE']:
                number +=1
                continue
            layer = entity.layer
            parent = parents[-1]
            # columnData = ['Name', 'Type']
            if layer not in layers:
                layers[layer] = {'Name': layer, 'Type': 'Layer'}
                parent.insertChildren(parent.childCount(), 1,
                                    self.rootItem.columnCount())

                parent_dict[layer] = parent.child(parent.childCount() -1)
                thisChild = parent.child(parent.childCount() -1)


                for column in range(len(columns)):
                    key = columns[column]
                    if key in layers[layer]:
                        thisChild.setData(column, layers[layer][key])

                # for column in range(len(columnData)):
                    # parent.child(parent.childCount() -1).setData(column, layers[layer][columnData[column]])
                    # print columnData[column], layers[layer][columnData[column]]

            parent = parent_dict[layer]

            parent.insertChildren(parent.childCount(), 1,
                                self.rootItem.columnCount())

            thisChild = parent.child(parent.childCount() -1)
            # print thisChild

            # entity.is_closed = True
            thisChild.setEntity(entity)

            # print self.headerData(0,QtCore.Qt.Horizontal)

            # print str(entity.is_closed)
            item_data = {'Name': 'Id'+str(number),
                         'Type': entity.dxftype,
                         'Closed': entity.is_closed,
                         'Voltage': thisChild.volt,
                         'Angle': thisChild.fillAngle,
                         'Rate': thisChild.rate,
                         'Step': thisChild.fillStep,
                         'Time': thisChild.sketchTime}
            # print columnData
            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
                    thisChild.setData(column, item_data[key])

            number += 1


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)
        uic.loadUi('mainwindow2.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool')
        self.setGeometry(500,100,1200,1000)
        self.plotFrame = PlotFrame()
        self.plotSplitter.addWidget(self.plotFrame)

        self.show()

        self.actionExit.triggered.connect(QtGui.qApp.quit)

        self.outDir = 'U:/'
        self.afmImageFolder = 'D:/lithography/afmImages/'

        self.inFile = ''
        self.sketchFile = ''
        self.freerate = 2.0
        self.tip_gain = 4.0
        self.tip_offset = 0

        self.afminfo = {}
        # self.fileOut.setText(self.outDir)
        self.centerCoord = np.array([0,0])

        self.afmPosition = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(180, 180, 255, 255))

        # n = 5
        # pos = np.random.normal(size=(2,n))
        # spots = [{'pos': pos[:,i], 'data': 1} for i in range(n)] + [{'pos': [0,0], 'data': 1}]
        # self.afmPosition.addPoints(spots)

        self.preservePlots = []
        self.preservePlots.append(self.afmPosition)


        self.dxffileName = filename

        self.headers = ('Name', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Closed', 'Type')

        # QtCore.QObject.connect(self.loadFile, QtCore.SIGNAL('clicked()'), self.pickFile)
        # QtCore.QObject.connect(self.saveDirectory, QtCore.SIGNAL('clicked()'), self.pickDirectory)
        QtCore.QObject.connect(self.butUnload, QtCore.SIGNAL('clicked()'), self.stageUnload)
        QtCore.QObject.connect(self.butLoad, QtCore.SIGNAL('clicked()'), self.stageLoad)
        # QtCore.QObject.connect(self.fileIn, QtCore.SIGNAL('returnPressed()'), self.updateFileInText)

        print ''
        print ''

        self.AFMthread = AFMWorker()
        self.SocketThread = SocketWorker()

        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("afmImage(QString)"), self.newafmImage)

        QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)
        QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMStatus(QString)"), self.updateStatus)


        self.AFMthread.monitor(self.afmImageFolder)
        self.SocketThread.monitor()
        self.addToolbars()



        self.readDXFFile()


        # self.tree_file.selectionModel().selectionChanged.connect(self.updateActions)
        # self.tree_file.model().dataChanged.connect(self.clicked)

        # self.actionsMenu.aboutToShow.connect(self.updateActions)
        # self.insertRowAction.triggered.connect(self.insertRow)
        # self.insertColumnAction.triggered.connect(self.insertColumn)
        # self.removeRowAction.triggered.connect(self.removeRow)
        # self.removeColumnAction.triggered.connect(self.removeColumn)
        # self.insertChildAction.triggered.connect(self.insertChild)

    @QtCore.pyqtSlot("QString")
    def newafmImage(self, filename=None):
        if filename == None:
            filename = self.afmImageFolder+sorted(os.listdir(self.afmImageFolder))[-1]

        filename = os.path.abspath(filename)
        self.afmData, self.afminfo = convertAFM(filename)
        if self.afmData.any() == None:
            return
        # self.afmImage = pg.ImageItem(self.afmData)
        # self.afmImage.setZValue(-1000)  # make sure image is behind other data
        x = self.afminfo['width']
        y = self.afminfo['height']

        self.plotFrame.setAfmImage(self.afmData,x,y)


        # print self.pi.listDataItems()

    def updateAFM(self):
        print 'updateAFM'

    def doCapture(self):
        self.SocketThread.send_message('Capture\n')
        print 'Capture'

    def stageUnload(self):
        self.SocketThread.send_message('StageUnload\n')
        print 'unload Stage'

    def stageLoad(self):
        self.SocketThread.send_message('StageLoad\n')
        print 'Load Stage'

    @QtCore.pyqtSlot("float, float, float")
    def updateAFMpos(self,x,y,rate):
        print 'afmpos: ', x,y,rate
        self.afmPosition.addPoints([{'pos': [x,y]}])

    @QtCore.pyqtSlot("QString")
    def updateStatus(self,line):
        self.statusBar().showMessage(line)

    def sketchNow(self, index=None):
        self.afmPosition.clear()
        self.sketchFile = ''
        if index == None:
            index = self.model
        nfile = False
        print "here I will sketch the file"
        for i in range(index.rowCount()):
            # print '- ', i
            item = index.getItem(index.index(i))
            if item.checkState == 0:
                continue
            chitems = item.childItems
            # if item.data(6) == 'Layer':
            self.sAdd('')
            self.sComment(item.data())
                # continue
            # print '- ' ,
            if len(chitems) != 0:
                nfile = True
                for child in item.childItems:
                    if child.checkState == 0:
                        continue
                    self.sAdd('')
                    self.sComment(child.data())
                    if child.checkState == 2:
                        for path in child.pltData:
                            x,y = np.add(path[0],-self.centerCoord)
                            self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                            self.sAdd('vtip\t%f' %((child.data(1)/self.tip_gain)-self.tip_offset))
                            r = child.data(2)
                            for x,y in np.add(path,-self.centerCoord):
                            # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                                self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                            self.sAdd('vtip\t%f' %(0.0))
        if nfile:
            self.writeFile(self.sketchFile)

    def sComment(self, stuff):
        adding = ''
        adding += '# '
        for i in stuff:
            adding += str(i)+ '\t'
        adding += '\n'
        self.sketchFile += adding
        # print adding

    def sAdd(self, data):
        self.sketchFile += data
        self.sketchFile += '\n'
        # print data

    def writeFile(self, data):
        self.outDir = str(self.outDir)
        fname = self.outDir + 'out.tmp'
        f = open(fname, 'w')
        f.write(data)
        f.close()
        try:
            os.remove(fname[:-3] + 'txt')
        except:
            pass
        os.rename(fname, fname[:-3] + 'txt')
        # print  fname[:-3] + 'txt'

        self.SocketThread.send_message('sketch out.txt\n')

    def abortNow(self):
        self.SocketThread.disconnectSocket()

    def shutLithoNow(self):
        self.SocketThread.send_message('shutdown\n')
        self.SocketThread.stop()


    def pickFile(self):
        # http://stackoverflow.com/questions/20928023/how-to-use-qfiledialog-options-and-retreive-savefilename
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Select design file', self.inFile, selectedFilter='*.dxf')
        if filename:
            self.dxffileName = str(filename)
            self.readDXFFile()

    def pickDirectory(self):
        outDir = QtGui.QFileDialog.getExistingDirectory(self, 'Select output Directory', self.outDir)
        if outDir:
            self.outDir = outDir
            # self.fileOut.setText(self.outDir)

    def pickafmImageDirectory(self):
        afmImageFolder = QtGui.QFileDialog.getExistingDirectory(self, 'Select AFM Image Folder', self.afmImageFolder)
        if afmImageFolder:
            self.afmImageFolder = afmImageFolder


    def reloadafmImageDirectory(self):
        # logfiles = sorted(os.listdir(self.afmImageFolder))
        # logfiles[-1]
        self.newafmImage()

    # def updateFileInText(self):
    #     self.inFile = str(self.fileIn.text())
    #     self.fileIn.setText(self.inFile)
    #     self.dxffileName = str(self.inFile)
    #     self.readDXFFile()

    # def reloadDXFFile(self):
        # self.readDXFFile()

    def clearDXFFile(self):
        try:
            self.model.clearData()
            self.model.reset()

            del self.dxf

            self.plotFrame.clearSketchPlot()

            self.updateActions()
        except:
            pass

    def readDXFFile(self):
        self.clearDXFFile()

        # self.fileIn.setText(self.dxffileName)
        self.dxf = dxfgrabber.readfile(self.dxffileName)

        self.model = TreeModel(self.headers, self.dxf)

        self.tree_file.setModel(self.model)
        self.tree_file.expandAll()
        self.tree_schedule.setModel(self.model)
        self.tree_schedule.expandAll()

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)
            self.tree_schedule.resizeColumnToContents(column)



        self.pi = self.plotFrame.sketchPlot.getPlotItem()
        self.plotFrame.clearSketchPlot()
        self.pi.addItem(self.afmPosition)

        self.pi.enableAutoRange('x', True)
        self.pi.enableAutoRange('y', True)
        self.pi.setAspectLocked(lock=True, ratio=1)
        self.pi.showGrid(x=1, y=1, alpha=0.8)



        QtCore.QObject.connect(self.tree_file.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        QtCore.QObject.connect(self.tree_schedule.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('checkChanged(QModelIndex)'), self.checked)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('redraw(QModelIndex)'), self.redraw)

        self.updateActions()

    @QtCore.pyqtSlot("QModelIndex")
    def redraw(self, index):
        model = self.model

        item = model.getItem(index)

        checked = item.checkState
        if not checked == 0:
            # clear plot from item
            for i in item.pltHandle:
                self.pi.removeItem(i)
            item.pltHandle = []

            data = model.getItem(index).pltData
            if data:
                for i in data:
                    pdi = self.pi.plot(i, pen = greenPen)
                    item.pltHandle.append(pdi)

            self.updateActions()

        # print self.pi.listDataItems()


    @QtCore.pyqtSlot("QModelIndex")
    def checked(self, index):
        model = self.model
        item = model.getItem(index)
        checked = item.checkState

        # clear plot from item
        for i in item.pltHandle:
            self.pi.removeItem(i)
        item.pltHandle = []

        if checked == 0:
            # hide item if unchecked
            self.tree_schedule.setRowHidden(index.row(),index.parent(), True)
        else:
            self.tree_schedule.setRowHidden(index.row(),index.parent(), False)
            data = model.getItem(index).pltData
            if data:
                for i in data:
                    pdi = self.pi.plot(i, pen = greenPen)
                    item.pltHandle.append(pdi)
        self.updateActions()


    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def update_plot(self, selected, deselected):
        print 'here'
        index = selected.indexes()
        self.tree_file.setCurrentIndex(index[0])
        self.tree_schedule.setCurrentIndex(index[0])
        deindex = deselected.indexes()
        model = self.tree_file.model()
        # print 'bb', index[0], model.getItem(index[0])
        for idx in index:
            item = model.getItem(idx)
            for i in item.pltHandle:
                i.setPen(orangePen)
        for idx in deindex:
            item = model.getItem(idx)
            for i in item.pltHandle:
                i.setPen(greenPen)


        self.updateActions()


    def insertChild(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

        if model.columnCount(index) == 0:
            if not model.insertColumn(0, index):
                return

        if not model.insertRow(0, index):
            return

        for column in range(model.columnCount(index)):
            child = model.index(0, column, index)
            model.setData(child, "[No data]", QtCore.Qt.EditRole)
            if model.headerData(column, QtCore.Qt.Horizontal) is None:
                model.setHeaderData(column, QtCore.Qt.Horizontal,
                        "[No header]", QtCore.Qt.EditRole)

        self.tree_file.selectionModel().setCurrentIndex(model.index(0, 0, index),
                QtGui.QItemSelectionModel.ClearAndSelect)
        self.updateActions()

    def insertColumn(self):
        model = self.tree_file.model()
        column = self.tree_file.selectionModel().currentIndex().column()

        changed = model.insertColumn(column + 1)
        if changed:
            model.setHeaderData(column + 1, QtCore.Qt.Horizontal,
                    "[No header]", QtCore.Qt.EditRole)

        self.updateActions()

        return changed

    def insertRow(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

        if not model.insertRow(index.row()+1, index.parent()):
            return

        self.updateActions()

        for column in range(model.columnCount(index.parent())):
            child = model.index(index.row()+1, column, index.parent())
            model.setData(child, "[No data]", QtCore.Qt.EditRole)

    def removeColumn(self):
        model = self.tree_file.model()
        column = self.tree_file.selectionModel().currentIndex().column()

        changed = model.removeColumn(column)
        if changed:
            self.updateActions()

        return changed

    def removeRow(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

        if (model.removeRow(index.row(), index.parent())):
            self.updateActions()

    def updateActions(self):
        hasSelection = not self.tree_file.selectionModel().selection().isEmpty()
        self.removeRowAction.setEnabled(hasSelection)
        self.removeColumnAction.setEnabled(hasSelection)

        hasCurrent = self.tree_file.selectionModel().currentIndex().isValid()
        self.insertRowAction.setEnabled(hasCurrent)
        self.insertColumnAction.setEnabled(hasCurrent)

        if hasCurrent:
            self.tree_file.closePersistentEditor(self.tree_file.selectionModel().currentIndex())

            row = self.tree_file.selectionModel().currentIndex().row()
            column = self.tree_file.selectionModel().currentIndex().column()
            # if self.tree_file.selectionModel().currentIndex().parent().isValid():
                # self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
            # else:
                # self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))


    def addToolbars(self):
        exitAction            = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_delete.png'), 'Exit', self)
        captureAction         = QtGui.QAction(QtGui.QIcon('icons/afm/a_0006_capture.png'), 'Capture', self)
        capture_abortAction   = QtGui.QAction(QtGui.QIcon('icons/afm/a_0008_capture_abort.png'), 'Capture Abort', self)
        capture_forceAction   = QtGui.QAction(QtGui.QIcon('icons/afm/a_0007_capture_force.png'), 'Capture Force', self)
        frame_downAction      = QtGui.QAction(QtGui.QIcon('icons/afm/a_0004_frame_down.png'), 'Frame Down', self)
        frame_upAction        = QtGui.QAction(QtGui.QIcon('icons/afm/a_0003_frame_up.png'), 'Frame Up', self)
        engageAction          = QtGui.QAction(QtGui.QIcon('icons/afm/a_0005_engage.png'), 'Engage', self)
        withdrawAction        = QtGui.QAction(QtGui.QIcon('icons/afm/a_0000_withdraw.png'), 'Withdraw', self)
        measureAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'Measure', self)
        acceptMeasureAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save and Clear', self)
        favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite and Clear', self)
        stopMeasureAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measure', self)
        sketchAction          = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_accept.png'), 'Sketch Now', self)
        abortSketchAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_deny.png'), 'Abort Lithography', self)
        afmfolderAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_search.png'), 'AFM Image Folder', self)
        afmfolderReloadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_reload.png'), 'Reload AFM Image Folder', self)
        dxfLoadAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_add.png'), 'Load dxf', self)
        dxfReloadAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_refresh.png'), 'Reload dxf', self)
        dxfClearAction        = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_deny.png'), 'Clear dxf', self)



        QtCore.QObject.connect(exitAction, QtCore.SIGNAL('triggered()'), self.close )
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')

        QtCore.QObject.connect(captureAction,          QtCore.SIGNAL('triggered()'), self.doCapture )
        QtCore.QObject.connect(capture_abortAction,    QtCore.SIGNAL('triggered()'), self.doCaptureAbort )
        QtCore.QObject.connect(capture_forceAction,    QtCore.SIGNAL('triggered()'), self.doCaptureForce )
        QtCore.QObject.connect(frame_downAction,       QtCore.SIGNAL('triggered()'), self.doFrameDown )
        QtCore.QObject.connect(frame_upAction,         QtCore.SIGNAL('triggered()'), self.doFrameUp )

        QtCore.QObject.connect(engageAction,           QtCore.SIGNAL('triggered()'), self.doEngage )
        QtCore.QObject.connect(withdrawAction,         QtCore.SIGNAL('triggered()'), self.doWithdraw )




        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measure )
        QtCore.QObject.connect(acceptMeasureAction,    QtCore.SIGNAL('triggered()'), self.measure )
        QtCore.QObject.connect(favoriteMeasureAction,  QtCore.SIGNAL('triggered()'), self.measure )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.measure )

        QtCore.QObject.connect(sketchAction,           QtCore.SIGNAL('triggered()'), self.sketchNow )
        QtCore.QObject.connect(abortSketchAction,      QtCore.SIGNAL('triggered()'), self.abortNow )
        QtCore.QObject.connect(afmfolderAction,        QtCore.SIGNAL('triggered()'), self.pickafmImageDirectory )
        QtCore.QObject.connect(afmfolderReloadAction,  QtCore.SIGNAL('triggered()'), self.reloadafmImageDirectory )
        QtCore.QObject.connect(dxfLoadAction,          QtCore.SIGNAL('triggered()'), self.pickFile )
        QtCore.QObject.connect(dxfReloadAction,        QtCore.SIGNAL('triggered()'), self.readDXFFile )
        QtCore.QObject.connect(dxfClearAction,         QtCore.SIGNAL('triggered()'), self.clearDXFFile )



        iconSize = QtCore.QSize(32,32)
        toolbar = self.addToolBar('Exit')
        toolbar.setIconSize(iconSize)
        toolbar.addAction(exitAction)

        plttoolbar = self.addToolBar('Sketching')
        plttoolbar.setIconSize(iconSize)
        plttoolbar.addAction(sketchAction)
        plttoolbar.addAction(abortSketchAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(afmfolderAction)
        plttoolbar.addAction(afmfolderReloadAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(dxfLoadAction)
        plttoolbar.addAction(dxfReloadAction)
        plttoolbar.addAction(dxfClearAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(measureAction)
        plttoolbar.addAction(favoriteMeasureAction)
        plttoolbar.addAction(acceptMeasureAction)
        plttoolbar.addAction(stopMeasureAction)

        afmToolbar = self.addToolBar('AFM')
        afmToolbar.setIconSize(iconSize)
        afmToolbar.addAction(engageAction)
        afmToolbar.addAction(withdrawAction)
        afmToolbar.addSeparator()
        afmToolbar.addAction(captureAction)
        afmToolbar.addAction(capture_forceAction)
        afmToolbar.addAction(capture_abortAction)
        afmToolbar.addSeparator()
        afmToolbar.addAction(frame_downAction)
        afmToolbar.addAction(frame_upAction)



        # QtCore.QObject.connect(self.saveDirectory, QtCore.SIGNAL('clicked()'), self.pickDirectory)
        # QtCore.QObject.connect(self.sketchThis, QtCore.SIGNAL('clicked()'), self.sketchNow)
        # QtCore.QObject.connect(self.abortLitho, QtCore.SIGNAL('clicked()'), self.abortNow)
        # QtCore.QObject.connect(self.shutLitho, QtCore.SIGNAL('clicked()'), self.shutLithoNow)
        # QtCore.QObject.connect(self.butUnload, QtCore.SIGNAL('clicked()'), self.stageUnload)
        # QtCore.QObject.connect(self.butLoad, QtCore.SIGNAL('clicked()'), self.stageLoad)
        # QtCore.QObject.connect(self.butCapture, QtCore.SIGNAL('clicked()'), self.doCapture)
        # QtCore.QObject.connect(self.fileOut, QtCore.SIGNAL('returnPressed()'), self.updateDirText)
        # QtCore.QObject.connect(self.fileIn, QtCore.SIGNAL('returnPressed()'), self.updateFileInText)


        # QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
        # QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
        # QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("afmImage(QString)"), self.newafmImage)

        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)


    def measure(self):
        pass
    def doCapture(self):
        self.SocketThread.send_message('Capture')
    def doCaptureAbort(self):
        self.SocketThread.send_message('CaptureAbort')
    def doCaptureForce(self):
        self.SocketThread.send_message('CaptureForce')
    def doFrameDown(self):
        self.SocketThread.send_message('FrameDown')
    def doFrameUp(self):
        self.SocketThread.send_message('FrameUp')
    def doEngage(self):
        self.SocketThread.send_message('Engage')
    def doWithdraw(self):
        self.SocketThread.send_message('Withdraw')

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
