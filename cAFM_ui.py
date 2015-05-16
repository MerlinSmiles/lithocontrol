#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)
import numpy as np


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.dockarea as pg_dock

import shutil


# %load_ext autoreload
# %autoreload 2

import sys

sys.path.append(".\\source")

filename = 'D:/lithography/DesignFiles/Untitled-1.dxf'

import os
import time
import socket
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from source.helpers import *
from source.dxf2shape import *
from source.convertAFM import *
from source.socketworker import *
from source.ringbuffer import *
from source.DataStore import *
from source.treeclass import *
from source.ni_measurement import *



colors = ['vivid_yellow','strong_purple','vivid_orange','very_light_blue','vivid_red','grayish_yellow','medium_gray','vivid_green','strong_purplish_pink','strong_blue','strong_yellowish_pink','strong_violet','vivid_orange_yellow','strong_purplish_red','vivid_greenish_yellow','strong_reddish_brown','vivid_yellowish_green','deep_yellowish_brown','vivid_reddish_orange','dark_olive_green']
kelly_colors = dict(vivid_yellow=(255, 179, 0),
            strong_purple=(128, 62, 117),
            vivid_orange=(255, 104, 0),
            very_light_blue=(166, 189, 215),
            vivid_red=(193, 0, 32),
            grayish_yellow=(206, 162, 98),
            medium_gray=(129, 112, 102),
            vivid_green=(0, 125, 52),
            strong_purplish_pink=(246, 118, 142),
            strong_blue=(0, 83, 138),
            strong_yellowish_pink=(255, 122, 92),
            strong_violet=(83, 55, 122),
            vivid_orange_yellow=(255, 142, 0),
            strong_purplish_red=(179, 40, 81),
            vivid_greenish_yellow=(244, 200, 0),
            strong_reddish_brown=(127, 24, 13),
            vivid_yellowish_green=(147, 170, 0),
            deep_yellowish_brown=(89, 51, 21),
            vivid_reddish_orange=(241, 58, 19),
            dark_olive_green=(35, 44, 22))

# mkPen for selected
orangePen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
bluePen = pg.mkPen(color='0000FF')  #, style=QtCore.Qt.DotLine
greenPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine , width=

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
        self.sketchPlot.addItem(self.afmIm)

        self.measurePlot = pg.PlotWidget()
        self.measureDock.addWidget(self.measurePlot)

    def setAfmImage(self, image_data, x= None, y=None):
        if not (x==None or y == None):
            self.afmIm.setRect(pg.QtCore.QRectF(-x/2.0, -y/2.0, x, y))
        self.afmIm.setImage(image_data)
        self.histWidget.setImageItem(self.afmIm)

    def clearSketchPlot(self):
        # return
        self.sketchPlot.clear()
        # self.histWidget.setImageItem(self.afmIm)
        self.sketchPlot.addItem(self.afmIm)

    def savePlot(self, fileName):
        # create an exporter instance, as an argument give it
        # the item you wish to export
        exporter = pg.exporters.ImageExporter(self.sketchPlot.getPlotItem())

        # set export parameters if needed
        exporter.parameters()['width'] = 2048

        # save to file
        exporter.export(fileName)


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
        print self.foldername
        observer.start()
        while True and not self.exiting:
            time.sleep(3)
        observer.stop()
        observer.join()

class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_measure_stop = pyqtSignal(int)

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)
        uic.loadUi('mainwindow.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool')
        self.setGeometry(500,100,1200,1000)
        self.plotFrame = PlotFrame()
        self.plotSplitter.addWidget(self.plotFrame)
        # self.splitter.setStretch(1,1)
        self.splitter.setStretchFactor(1,1)

        self.show()

        self.settings = {}
        self.settings['time'] = QTime()

        self.s_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))

        self.outDir = 'U:/'
        self.afmImageFolder = 'D:/lithography/afmImages/'
        self.storeFolder = 'D:/lithography/sketches/' + self.s_time + '/'
        self.sketchSubFolder = './'

        print ''
        print ''

        self.addToolbars()
        self.init_stores()
        self.newstores = False
        self.init_sketching()
        self.init_measurement()

        self.log('log', 'init')

    def init_stores(self):
        c_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))

        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)

        self.log_store = DataStore(filename=self.storeFolder+c_time +'_logging.h5')

        self.ni_store_columns = ['time', 'current','r2p','r4p']
        self.ni_store = RingBuffer(360000, filename=self.storeFolder+c_time +'_ni_data.h5',cols = self.ni_store_columns)

        self.dht_store_columns = ['time', 'temperature', 'humidity']
        self.dht_store = RingBuffer(360000, filename=self.storeFolder+c_time +'_dht_data.h5',cols = self.dht_store_columns)

    def log(self, column, value):
        tdelta = self.settings['time'].elapsed()/1000.0
        self.log_store.append([tdelta,value], ['time', column])

    def init_sketching(self):
        self.inFile = ''
        self.sketchFile = ''
        self.freerate = 2.0
        self.tip_gain = 1.0
        self.tip_offset = 0

        self.afminfo = {}

        self.centerCoord = np.array([0,0])

        self.afmPosition = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0, 255))
        self.afmPosition.setZValue(100)


        self.preservePlots = []
        self.preservePlots.append(self.afmPosition)


        self.dxffileName = filename

        self.headers = ('Name', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Closed', 'Type')
        self.AFMthread = AFMWorker()
        self.SocketThread = SocketWorker()

        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("afmImage(QString)"), self.newafmImage)

        QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)
        QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("READY"), self.afmReady)
        QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMStatus(QString)"), self.updateStatus)
        self.AFMthread.monitor(self.afmImageFolder)
        self.SocketThread.monitor()
        self.readDXFFile()

    def afmReady(self):
        self.log('sketch', 'end')
        self.afmPosition.clear()


    def init_measurement(self):
        self.ni_terminate = False

        self.plotlist = []
        self.update_plotting()
        self.plot_counter = 0

        self.settings['buffer_size'] = 10000000
        self.settings['acq_rate'] = 30000          # samples/second
        self.settings['acq_samples'] = 1000        # every n samples
        self.settings['device_input'] = "PCI-6251"
        self.settings['SR_sensitivity'] = 10e-9
        self.settings['PAR_sensitivity'] = 1e-3
        self.settings['plot_2pt'] = True
        self.settings['plot_4pt'] = True
        self.settings['plot_current'] = True
        self.SRSensitivity.setText("%.0e" %(self.settings['SR_sensitivity']))
        self.PARSensitivity.setText("%.0e" %(self.settings['PAR_sensitivity']))
        self.settings['plotR'] = True
        self.settings['DHTport'] = 6
        self.initSerial()

        self.settings['in'] = {}
        ch0 = self.settings['in'][0] = {}
        ch1 = self.settings['in'][1] = {}


        ch0['channel'] = "ai0"
        ch0['name'] = 'Current'
        ch0['curr_amp'] = 0
        ch0['amplitude'] = 1e-3
        # amplification = 200mV / 10V
        amplification = 10e-9/10.0
        ch0['multiplier'] = amplification
        ch0['min'] = -10 # +/- 100 mV is the minimum bipolar range
        ch0['max'] = 10
        ch0['plot_raw'] = True
        ch0['freq_chan'] = 0

        ch1['channel'] = "ai1"
        ch1['name'] = 'A-B'
        ch1['amplitude'] = 1*1e-3
        amplification = 0.001/10.0
        ch1['multiplier'] = amplification
        ch1['min'] = -10
        ch1['max'] = 10
        ch1['plot_raw'] = True
        ch1['freq_chan'] = 0
        ch1['curr_amp'] = 0
        self.spinCom.setValue( self.settings['DHTport'] )
        # self.cAmpSpinBox.setValue(self.settings['in'][0]['curr_amp'])
        # (self._gen_meas_amplitude, self._normamplitudes, self._normphases)
        print  ['time'] + self.settings['in'].keys()

        self.ni_buff = RingBuffer(2000, cols = ['time'] + self.settings['in'].keys())
        self.settings['buff'] = self.ni_buff

        self.dht_buff = RingBuffer(2000, cols = self.dht_store_columns)
        self.settings['dht_buff'] = self.dht_buff



        self.ni_worker = ni_Worker(self.settings)
        self.ni_workerThread = None

        self.dht_Worker = dht_Worker(self.settings)
        self.dht_WorkerThread = None

        self.ni_pi = self.plotFrame.measurePlot.getPlotItem()
        # self.ni_pi = self.plotView.getPlotItem()
        self.ni_pi.addLegend()
        self.ni_pi_legend = self.ni_pi.legend
        self.ni_pi.enableAutoRange('x', True)
        # self.ni_pi.setXRange(990000, 1000000)
        self.ni_pi.enableAutoRange('y', True)
        # li_data = np.array([[gen_meas_amplitude], [normamplitudes], [normphases], [li_r/1e6], [li_g]])
        self.ni_pi_names = ['ch0','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9',]
        for i in range(5):
            self.plotlist.append({'plot': self.ni_pi.plot(name=self.ni_pi_names[i]), 'channel': i})
        self.run()

    def saveSketch(self):
        self.settings['time'].elapsed()
        self.sketchSubFolder = QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss')

        if not os.path.exists(self.storeFolder + self.sketchSubFolder):
            os.makedirs(self.storeFolder + self.sketchSubFolder)


        data = self.sketchFile
        self.sketchOutDir = str(self.storeFolder + self.sketchSubFolder+'/')
        fname = self.sketchOutDir + 'out.txt'
        f = open(fname, 'w')
        f.write(data)
        f.close()
        try:
            self.plotFrame.savePlot(self.sketchOutDir+'currentSketchView.png')
        except:
            pass
        try:
            filename = sorted(os.listdir(self.afmImageFolder))[-1]
            shutil.copy2(self.afmImageFolder + filename,self.sketchOutDir+filename)
            shutil.copy2('D:/lithography/current.png',self.sketchOutDir+'currentAFMImage.png')
        except:
            pass

        self.log('sketch', str(self.storeFolder + self.sketchSubFolder))

    @QtCore.pyqtSlot("QString")
    def newafmImage(self, filename=None):
        if filename == None:
            filename = self.afmImageFolder+'/'+sorted(os.listdir(self.afmImageFolder))[-1]

        filename = os.path.abspath(filename)

        ret = convertAFM(filename)
        if ret == False:
            return
        self.afmData, self.afminfo = ret[0], ret[1]

        if self.afmData.any() == None:
            return

        self.afmData = np.array(self.afmData)
        x = self.afminfo['width']
        y = self.afminfo['height']

        self.plotFrame.setAfmImage(self.afmData,x,y)

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
        line = str(line)
        self.statusBar().showMessage(line)
        if line.startswith('vtip'):
            line = line.split( )
            volt = float(line[1])
            self.log('vtip', volt)
            print 'VTIP ' , volt
        elif line.startswith('Ready'):
            self.afmPosition.clear()
            self.afmReady()
            print "\n\nREADY\n\n"
        elif line.startswith('xyAbs'):
            line = line.split( )
            x = float(line[1])
            y = float(line[2])
            r = float(line[3])
            # self.emit(QtCore.SIGNAL("AFMpos(float, float, float)"), x,y,r)
            self.updateAFMpos(x,y,r)

    def sketchNow(self, index=None):
        self.afmPosition.clear()
        self.sketchFile = ''
        if index == None:
            index = self.model
        nfile = False
        print "Sketching Now"
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
                            self.sAdd('vtip\t%f' %((float(child.data(1))/self.tip_gain)-self.tip_offset))
                            r = child.data(2)
                            for x,y in np.add(path,-self.centerCoord):
                            # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                                self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                            self.sAdd('vtip\t%f' %(0.0))
        if nfile:
            self.writeFile(self.sketchFile)
            self.saveSketch()

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
        fname = str(self.outDir + 'out.tmp')
        f = open(fname, 'w')
        f.write(data)
        f.close()
        try:
            os.remove(fname[:-3] + 'txt')
        except:
            pass
        os.rename(fname, fname[:-3] + 'txt')
        self.SocketThread.send_message('sketch out.txt\n')
        self.log('sketch', 'start')

    def abortNow(self):
        self.SocketThread.send_message('Abort\n')

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

    def pickSketchImageDirectory(self):
        sketchFolder = QtGui.QFileDialog.getExistingDirectory(self, 'Select Sketch Folder', self.sketchFolder)
        if sketchFolder:
            self.sketchFolder = sketchFolder


    def reloadafmImageDirectory(self):
        self.newafmImage()

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
        # self.tree_schedule.setModel(self.model)
        # self.tree_schedule.expandAll()

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)
            # self.tree_schedule.resizeColumnToContents(column)



        self.pi = self.plotFrame.sketchPlot.getPlotItem()
        self.plotFrame.clearSketchPlot()
        self.pi.addItem(self.afmPosition)

        self.pi.enableAutoRange('x', True)
        self.pi.enableAutoRange('y', True)
        self.pi.setAspectLocked(lock=True, ratio=1)
        self.pi.showGrid(x=1, y=1, alpha=0.8)



        QtCore.QObject.connect(self.tree_file.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        # QtCore.QObject.connect(self.tree_schedule.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
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

        # if checked == 0:
            # hide item if unchecked
            # self.tree_schedule.setRowHidden(index.row(),index.parent(), True)
        # else:
            # self.tree_schedule.setRowHidden(index.row(),index.parent(), False)
        data = model.getItem(index).pltData
        if data and checked != 0:
            for i in data:
                pdi = self.pi.plot(i, pen = greenPen)
                item.pltHandle.append(pdi)
        self.updateActions()


    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def update_plot(self, selected, deselected):
        index = selected.indexes()
        self.tree_file.setCurrentIndex(index[0])
        # self.tree_schedule.setCurrentIndex(index[0])
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
        measureAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'New Measurement', self)
        acceptMeasureAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save Measurement', self)
        favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite', self)
        stopMeasureAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measure', self)
        sketchAction          = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_accept.png'), 'Sketch Now', self)
        abortSketchAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_deny.png'), 'Abort Lithography', self)
        sketchFolderAction    = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_edit.png'), 'Sketch Folder', self)
        afmFolderAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_search.png'), 'AFM Image Folder', self)
        afmFolderReloadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_reload.png'), 'Reload AFM Image Folder', self)
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




        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measure_start )
        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.graficar )
        QtCore.QObject.connect(favoriteMeasureAction,  QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(acceptMeasureAction,    QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.measure_stop )

        QtCore.QObject.connect(sketchAction,           QtCore.SIGNAL('triggered()'), self.sketchNow )
        QtCore.QObject.connect(abortSketchAction,      QtCore.SIGNAL('triggered()'), self.abortNow )
        QtCore.QObject.connect(sketchFolderAction,     QtCore.SIGNAL('triggered()'), self.pickSketchImageDirectory )
        QtCore.QObject.connect(afmFolderAction,        QtCore.SIGNAL('triggered()'), self.pickafmImageDirectory )
        QtCore.QObject.connect(afmFolderReloadAction,  QtCore.SIGNAL('triggered()'), self.reloadafmImageDirectory )
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
        plttoolbar.addAction(sketchFolderAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(afmFolderAction)
        plttoolbar.addAction(afmFolderReloadAction)
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




    def initSerial(self):
        try:
            self.settings['dht_serial'] = None
            try:
                self.dht_WorkerThread.quit()
            except:
                pass
            self.settings['dht_serial'] = serial.Serial(self.settings['DHTport']-1, baudrate=115200, timeout=5) # opens, too.

            self.dht_Worker = dht_Worker(self.settings)
            self.dht_WorkerThread = QtCore.QThread()
            self.dht_Worker.terminate.connect(self.setterminate)
            self.dht_Worker.moveToThread(self.dht_WorkerThread)
            self.dht_WorkerThread.start()

            self.sig_measure.connect(self.dht_Worker.run)
            self.sig_measure_stop.connect(self.dht_Worker.stop)
        except:
            print 'dht failed'
            self.settings['dht_serial'] = None
            pass

    def closeEvent(self,event):
        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if reply==QtGui.QMessageBox.Yes:
            self.measure_save()
            self.measure_stop()
            self.ni_workerThread.quit()
            self.dht_WorkerThread.quit()

            event.accept()
        else:
            event.ignore()


    def makeDataset(self):
        pass

    def run(self):
        self.ni_workerThread = QtCore.QThread()
        self.ni_worker.terminate.connect(self.setterminate)
        self.ni_worker.moveToThread(self.ni_workerThread)
        self.dht_WorkerThread = QtCore.QThread()
        self.dht_Worker.terminate.connect(self.setterminate)
        self.dht_Worker.moveToThread(self.dht_WorkerThread)


        self.check_plot.stateChanged.connect(self.update_plotting)
        self.check_2pt.stateChanged.connect(self.update_plotting)
        self.check_4pt.stateChanged.connect(self.update_plotting)
        self.check_current.stateChanged.connect(self.update_plotting)
        self.radio_plotR.toggled.connect(self.update_plotting)
        self.radio_plotC.toggled.connect(self.update_plotting)
        self.plot_update_time.valueChanged.connect(self.update_plotting)
        self.spinCom.valueChanged.connect(self.update_plotting)
        self.spinCom.valueChanged.connect(self.initSerial)
        self.SRSensitivity.editingFinished.connect(self.update_plotting)
        self.PARSensitivity.editingFinished.connect(self.update_plotting)



        self.sig_measure.connect(self.ni_worker.run)
        self.sig_measure_stop.connect(self.ni_worker.stop)

        self.sig_measure.connect(self.dht_Worker.run)
        self.sig_measure_stop.connect(self.dht_Worker.stop)

        self.ni_workerThread.start()
        self.dht_WorkerThread.start()

        self.show()

    def update_plotting(self):
        if self.check_plot.checkState() == 2:
            self.settings['acq_plot'] = True
        else:
            self.settings['acq_plot'] = False

        if self.check_2pt.checkState() == 2:
            self.settings['plot_2pt'] = True
        else:
            self.settings['plot_2pt'] = False

        if self.check_4pt.checkState() == 2:
            self.settings['plot_4pt'] = True
        else:
            self.settings['plot_4pt'] = False

        if self.check_current.checkState() == 2:
            self.settings['plot_current'] = True
        else:
            self.settings['plot_current'] = False

        for i in self.plotlist:
            i['plot'].clear()

        self.settings['plot_timing'] = self.plot_update_time.value()
        self.settings['SR_sensitivity'] = float(self.SRSensitivity.text ())
        self.settings['PAR_sensitivity'] = float(self.PARSensitivity.text ())
        self.settings['plotR'] = self.radio_plotR.isChecked()
        self.settings['DHTport'] = self.spinCom.value()
        self.SRSensitivity.setText("%.0e" %(self.settings['SR_sensitivity']))
        self.PARSensitivity.setText("%.0e" %(self.settings['PAR_sensitivity']))

    def measure_start(self):
        if self.newstores == True:
            self.init_stores()
            self.newstores = False

        self.ni_terminate = False
        self.sig_measure.emit(500)

    def measure_stop(self):
        self.ni_terminate = True
        self.sig_measure_stop.emit(500)
        try:
            self.ni_store.clear()
            self.ni_buff.clear()
        except:
            print 'Error clearing ni_store'
            print sys.exc_info()
        try:
            self.dht_store.clear()
            self.dht_buff.clear()
        except:
            print 'Error clearing dht_store'
            print sys.exc_info()
        self.newstores = True


    def measure_save(self):
        self.ni_store.save_data()
        self.dht_store.save_data()
        self.log_store.save_data()

    def setterminate(self):
        self.ni_terminate = True

    def graficar(self):

        if self.settings['buff'].size > 0:
            raw_buffer = self.settings['buff'].get_partial_clear()

            d_time = raw_buffer[0]
            d_ch0 = raw_buffer[1]
            d_ch1 = raw_buffer[2]

            current = np.abs(d_ch0*self.settings['SR_sensitivity']/10.0)
            r2pt = np.abs(self.settings['in'][0]['amplitude'] / current)

            a_b = d_ch1*self.settings['PAR_sensitivity']/10
            r4pt = np.abs(a_b / current)

            self.ni_store.append([d_time, current, r2pt, r4pt])

        if self.settings['dht_buff'].size > 0:
            raw_buffer = self.settings['dht_buff'].get_partial_clear()
            a = raw_buffer[0].mean()
            b = raw_buffer[1].mean()
            c = raw_buffer[2].mean()
            self.dht_store.append([a,b,c])
            self.text_temp.setText('Tmp: %.1f\xb0C'%(raw_buffer[1].mean()))
            self.text_hum.setText('Hum: %.1f%%'%(raw_buffer[2].mean()))

        if self.settings['acq_plot']:
            if self.ni_store.size>1:
                n = 0
                self.plot_counter +=1
                raw_buffer = self.ni_store.get_partial()

                d_time = raw_buffer[0]
                current = raw_buffer[1]

                n += 1
                av_len = -10
                if self.plot_counter>11:
                    self.ni_pi_legend.items = []

                if self.settings['plot_current'] == True:
                    if self.plot_counter>11:

                        try:
                            av_curr = np.average(current[av_len:])*1e9
                            self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'Current' + ' = ' + '%.2f nA' % av_curr)
                        except:
                            self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'Current')
                            pass

                    self.plotlist[n]['plot'].setData(x=d_time, y=current*1e9)
                    self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])
                n += 1

                if self.settings['plotR']:
                    r2pt = raw_buffer[2]
                    r4pt = raw_buffer[3]

                    if self.settings['plot_2pt'] == True:
                        if self.plot_counter>11:
                            try:
                                av_2pt = np.average(r2pt[av_len:])/1000.0
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt' + ' = ' + '%.1f kOhm' % av_2pt)
                            except:
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=r2pt/1000.0)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

                    n += 1
                    if self.settings['plot_4pt'] == True:
                        if self.plot_counter>11:

                            self.plot_counter = 0
                            try:
                                av_4pt = np.average(r4pt[av_len:])/1000.0
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt' + ' = ' + '%.1f kOhm' % av_4pt)
                            except:
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=r4pt/1000.0)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

                if not self.settings['plotR']:
                    g2pt = 1.0/raw_buffer[2] *1e6
                    g4pt = 1.0/raw_buffer[3] *1e6

                    if self.settings['plot_2pt'] == True:
                        if self.plot_counter>11:
                            try:
                                av_2pt = np.average(g2pt[av_len:])
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'g2pt' + ' = ' + '%.1f uS' % av_2pt)
                            except:
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'g2pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=g2pt)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

                    n += 1
                    if self.settings['plot_4pt'] == True:
                        if self.plot_counter>11:

                            self.plot_counter = 0
                            try:
                                av_4pt = np.average(g4pt[av_len:])
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'g4pt' + ' = ' + '%.1f uS' % av_4pt)
                            except:
                                self.ni_pi_legend.addItem(self.plotlist[n]['plot'], 'g4pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=g4pt)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

        if not self.ni_terminate:
            QtCore.QTimer.singleShot(self.settings['plot_timing'], self.graficar)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
