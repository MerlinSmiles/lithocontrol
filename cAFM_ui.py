#!/usr/bin/env python
demo = False
import sys
sys.path.append(".\\source")

try:
    import gwy, gwyutils
except:
    demo = True

import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import numpy as np
from pprint import pprint


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.dockarea as pg_dock

import shutil

# %load_ext autoreload
# %autoreload 2


import json

with open('config.json', 'r') as f:
    config = json.load(f)
if demo:
    config['storage'] = config['demo_storage']
print(config['storage'])

def_dxf_file = 'F:/lithography/DesignFiles/current.dxf'
def_dxf_file = config['storage']['def_dxf_file']

import os
import time
from time import sleep
import socket

from source.helpers import *
if not demo:
    from source.convertAFM import *
    from source.ni_measurement import *
from source.socketworker import *
from source.ringbuffer import *
from source.DataStore import *

# from source.treeclass import *
from source.treeclass3 import *
from source.PlotFrame import *
if not demo:
    from source.afmHandler import AFMWorker


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
# selectPen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
sketchPen = pg.mkPen(color='FF0000DD',width=2.5)  #, style=QtCore.Qt.DotLine
movePen = pg.mkPen(color='1E4193',width=2, style=QtCore.Qt.DotLine)  #, style=QtCore.Qt.DotLine
showPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine , width=
selectPen = pg.mkPen(color='00FF00',width=3)  #, style=QtCore.Qt.DotLine , width=



class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_dhtmeasure = pyqtSignal(int)
    sig_measure_stop = pyqtSignal(int)

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)

        self.offset_angle = 0
        self.offset_center = [0,0]
        self.dxf_design = None
        self.designPltHandle = []


        splash_pix = QtGui.QPixmap(r'./source/splash2.png')
        self.splash = QtGui.QSplashScreen(splash_pix)
        # adding progress bar
        # progressBar = QProgressBar(self.splash)
        self.splash.setMask(splash_pix.mask())
        self.splash.show()
        self.splash.showMessage("Loading GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)


        uic.loadUi('mainwindow.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool')

        screen = QtGui.QDesktopWidget().screenGeometry()
        # self.setGeometry(0, 0, screen.width(), screen.height())
        self.setGeometry(int(screen.width()/3), int(screen.height()/3), screen.width()/2, screen.height()/2)


        self.setWindowState(self.windowState() & QtCore.Qt.WindowMaximized)

        # self.setGeometry(200,100,900,800)
        self.plotFrame = PlotFrame()
        self.plotSplitter.addWidget(self.plotFrame)
        # self.splitter.setStretch(1,1)

        self.splitter.setSizes([400,1000])
        # self.tree_splitter.set
        self.addToolbars()
        # self.show()
        # Set delegate
        self.splash.showMessage("Loading DXF-storage",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.tree_file.setItemDelegateForColumn(2,DoubleSpinBoxDelegate(self))
        self.tree_file.setItemDelegateForColumn(4,DoubleSpinBoxDelegate(self))

        self.splash.showMessage("Loading Settings",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.colorModel = ColorModel()
        self.colorList = colors
        self.colorDict = kelly_colors
        self.colorModel.addColors(self.colorList, self.colorDict)

        self.settings = {}
        self.settings['measure'] = {}
        self.settings['plot'] = {}
        self.settings['measure']['time'] = QTime()

        self.s_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))
        self.timer = QTime.currentTime()
        self.currentPosition = np.array([np.nan,np.nan,np.nan])
        self.nextPosition = np.array([np.nan,np.nan,np.nan])
        self.sketching = False

        self.afmImageFolder = config['storage']['afmImageFolder']
        self.storeFolder = config['storage']['storeFolder'] + self.s_time + '/'
        self.sketchSubFolder = './'

        if demo:
            print("DDDDDDDDDDDDDDDDDDDDD")
            self.splash.showMessage("Loading DemoMode",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
            self.outDir = './demo/'
            self.afmImageFolder = './demo/afmImages/'
            self.storeFolder = './demo/sketches/' + self.s_time + '/'
            self.sketchSubFolder = './demo/sketches/'


        print( '' )
        print( '' )

        self.splash.showMessage("Loading Stores",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_stores()
        self.newstores = False

        # self.splash.finish(self)

        self.splash.showMessage("Initialize Sketching",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_sketching()
        self.splash.showMessage("Initialize Measurement",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_measurement()
        # self.dht_WorkerThread.run()


        self.afmPoints_columns = ['x', 'y', 'rate']
        self.afmPoints = RingBuffer(36000, cols = self.afmPoints_columns)
        self.sketchPoints = []
        self.vtip = 0

        self.selectedPI = []

        self.log('log', 'init')

        # sleep(2)
        self.splash.showMessage("Showing GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.showMaximized()
        # self.show()
        self.newafmImage()
        self.readDXFFile()
        # pprint(self.settings)
        self.splash.showMessage("Starting Program",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.run()
        self.splash.finish(self)

        # self.btnExit.clicked.connect(self.close)
        # self.actionExit.triggered.connect(self.close)

        # sc = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.actionExit)

        # shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self)
        # shortcut.activated.connect(self.close)

        # self.connect(shortcut, QtCore.SIGNAL("triggered()"), self, QtCore.SLOT("quit()"))

        # print(QtGui.QKeySequence.StandardKey())
        # shortcut = QtGui.QShortcut(self)
        # shortcut.setKey("Ctrl+D")

        # QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)

        # self.actionExit = QtGui.QAction('E&xit',self)
        # self.actionExit.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        # self.actionExit.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        # # shortcut.setKey(QtGui.QKeySequence.Quit)
        # self.connect(shortcut, QtCore.SIGNAL("activated()"), QtCore.SLOT("close()"))


        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        # exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)


        menubar = self.menuBar()
        mainMenu = menubar.addMenu('&Main')
        mainMenu.addAction(exitAction)


        self.reoffset()
        self.pltDesign()

        # self.tree_splitter.setGeometry(500, 100)
        # self.tree_splitter.setStretchFactor(0,1)

        # QtGui.QShortcut(QtGui.QKeySequence("Cmd+Q"), self, self.closeEvent)
        # QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self, self.closeEvent)

        # self.tree_splitter.setMinimumWidth(200)
        # self.splitter.setStretchFactor(3,2)
        # self.tree_splitter.setStretchFactor(2,1)
        # print(self.tree_splitter.size())


    # def keyPressEvent(self, event):
    #     print ('key: %s -' % hex(event.key()))
    #     print ('modifiers:', hex(int(event.modifiers())))

    @QtCore.pyqtSlot("QModelIndex")
    def test(self, bla =None):
        print( bla )

    def init_stores(self):
        c_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))

        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)

        self.log_store = DataStore(filename=self.storeFolder+c_time +'_logging.h5')

        self.ni_store_columns = ['time', 'current','r2p','r4p']
        self.ni_store = RingBuffer(3600000, filename=self.storeFolder+c_time +'_ni_data.h5',cols = self.ni_store_columns)

        self.dht_store_columns = ['time', 'temperature', 'humidity']
        self.dht_store = RingBuffer(360000, filename=self.storeFolder+c_time +'_dht_data.h5',cols = self.dht_store_columns)

    def log(self, column, value):
        # return
        tdelta = self.settings['measure']['time'].elapsed()/1000.0

        if type(column) not in [list,tuple]:
            column = [column]
        if type(value) not in [list,tuple]:
            value = [value]

        values=[[tdelta],value]
        values=[item for sublist in values for item in sublist]

        columns=[['time'],column]
        columns=[item for sublist in columns for item in sublist]

        self.log_store.append(values,columns)
        # print('LOG:\t' + str(column) + '\t' + str(value))

    def init_sketching(self):
        self.inFile = ''
        self.sketchFile = ''
        self.freerate = 4.0
        self.tip_gain = 1.0
        self.tip_offset = 0

        self.afminfo = {}

        self.afmPosition = pg.PlotDataItem(size=5, pen=sketchPen, brush=pg.mkBrush(255, 0, 0, 255))
        self.afmPosition.setZValue(100)
        self.afmNow = pg.PlotDataItem(size=2, pen=sketchPen, brush=pg.mkBrush(0, 0, 255, 255))
        self.afmAll = pg.PlotDataItem(size=2, pen=sketchPen, brush=pg.mkBrush(0, 0, 255, 255))
        self.afmNow.setZValue(110)
        self.afmAll.setZValue(110)

        self.preservePlots = []
        self.preservePlots.append(self.afmPosition)
        self.preservePlots.append(self.afmNow)
        self.preservePlots.append(self.afmAll)

        self.dxffileName = def_dxf_file

        self.headers = ('Name', 'Show', 'Color', 'Volt', 'Rate', 'Angle', 'Step', 'Time', 'Length', 'Closed', 'Order', 'Type')

        if not demo:
            self.splash.showMessage("Initialize AFMWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
            self.AFMthread = AFMWorker()
            self.splash.showMessage("Initialize SocketWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
            self.SocketThread = SocketWorker()

            QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
            QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
            QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("afmImage(QString)"), self.newafmImage)

            QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)
            QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("READY"), self.afmReady)
            QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMStatus(QString)"), self.updateStatus)
            self.AFMthread.monitor(self.afmImageFolder)
            self.SocketThread.monitor()


    def init_measurement(self):
        self.ni_terminate = False

        self.plotlist = {}
        self.update_plotting()
        self.plot_counter = 0

        self.settings['measure']['buffer_size'] = 10000000
        self.settings['measure']['acq_rate'] = 30000          # samples/second
        self.settings['measure']['acq_samples'] = 1000        # every n samples
        self.settings['measure']['device_input'] = "PCI-6251"
        self.settings['measure']['SR_sensitivity'] = 10e-9
        self.settings['measure']['PAR_sensitivity'] = 1e-3
        self.settings['plot']['plot_2pt'] = True
        self.settings['plot']['plot_4pt'] = True
        self.settings['plot']['plot_current'] = True
        self.SRSensitivity.setText("%.0e" %(self.settings['measure']['SR_sensitivity']))
        self.PARSensitivity.setText("%.0e" %(self.settings['measure']['PAR_sensitivity']))
        self.settings['measure']['DHTport'] = 5
        self.spinCom.setValue( self.settings['measure']['DHTport'] )

        self.settings['measure']['in'] = {}
        ch0 = self.settings['measure']['in'][0] = {}
        ch1 = self.settings['measure']['in'][1] = {}


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
        # self.cAmpSpinBox.setValue(self.settings['measure']['in'][0]['curr_amp'])
        # (self._gen_meas_amplitude, self._normamplitudes, self._normphases)

        self.ni_buff = RingBuffer(200000, cols = ['time'] + list(self.settings['measure']['in'].keys()))
        self.settings['measure']['buff'] = self.ni_buff

        self.dht_buff = RingBuffer(200000, cols = self.dht_store_columns)
        self.settings['measure']['dht_buff'] = self.dht_buff

        self.initSerial()
        self.init_dht_plot()

        if not demo:

            self.ni_worker = ni_Worker(self.settings['measure'])
            self.ni_workerThread = None

            self.dht_Worker = dht_Worker(self.settings['measure'])
            self.dht_WorkerThread = None

        self.ni_pi = self.plotFrame.measurePlot.getPlotItem()
        # self.ni_pi.setDownsampling(auto=True)
        self.ni_pi.setClipToView(True)

        # self.ni_pi = self.plotView.getPlotItem()
        self.ni_pi.addLegend()
        self.ni_pi_legend = self.ni_pi.legend
        # self.ni_pi_legend.layout.setAlignment(QtCore.Qt.AlignLeft)
        # print(self.ni_pi_legend.layout.alignment())
        # alignment=QtCore.Qt.AlignHCenter
        self.ni_pi.enableAutoRange('x', True)
        self.ni_pi.enableAutoRange('y', True)
        # self.ni_pi.setXRange(990000, 1000000)

        self.pltG_pi = self.plotFrame.mConductancePlot.getPlotItem()
        # self.pltG_pi.setDownsampling(auto=True)
        self.pltG_pi.setClipToView(True)
        self.pltG_pi.setXLink(self.ni_pi)
        self.pltG_pi.addLegend()
        self.pltG_pi_legend = self.pltG_pi.legend
        # self.pltG_pi.enableAutoRange('x', True)
        self.pltG_pi.enableAutoRange('y', True)
        # li_data = np.array([[gen_meas_amplitude], [normamplitudes], [normphases], [li_r/1e6], [li_g]])
        self.ni_pi_names = ['ch0','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9',]
        self.plotR_names = ['Current1', 'R2pt', 'R4pt']
        self.plotG_names = ['Current2', 'G2pt', 'G4pt']
        # for i in range(5):
        #     self.plotlist.append({'plot': self.ni_pi.plot(name=self.ni_pi_names[i]), 'channel': i})

        for nme in self.plotR_names:
            self.plotlist[nme] = self.ni_pi.plot(name=nme)
        for nme in self.plotG_names:
            self.plotlist[nme] = self.pltG_pi.plot(name=nme)



    @QtCore.pyqtSlot("QString")
    def newafmImage(self, filename=None):
        if demo:
            return
        if filename == None:
            filename = list_directory(self.afmImageFolder)[-1]
            # filename = self.afmImageFolder+'/'+sorted(os.listdir(self.afmImageFolder))[-1]

        filename = os.path.abspath(filename)
        print(filename)

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
        print( 'updateAFM' )

    def doCapture(self):
        self.SocketThread.send_message('Capture\n')
        print( 'Capture' )

    def stageUnload(self):
        self.SocketThread.send_message('StageUnload\n')
        print( 'unload Stage' )

    def stageLoad(self):
        self.SocketThread.send_message('StageLoad\n')
        print( 'Load Stage' )

    @QtCore.pyqtSlot("float, float, float")
    def updateAFMpos(self,x,y,rate):
        self.sketchicar()

    def sketchicar(self):
        try:
            xl,yl,rl = np.copy(self.afmPoints.get_partial())
            # a,b,c = self.currentPosition
            a,b,c = self.afmPoints[-2]
            # x,y,r = self.nextPosition
            x,y,r = self.afmPoints[-1]
            dx = x - a
            dy = y - b

            dd = dx**2 + dy**2
            t = np.sqrt(dd)/r

            tt = self.timer.elapsed()/float(1000)
            dt = tt/t
            dxx = dx*dt
            dyy = dy*dt
            ddd= dxx**2 + dyy**2

            if(dd>=ddd):
                xl[-1] = a+dxx
                yl[-1] = b+dyy
                self.afmNow.setData(xl,yl)
            else:
                pass
        except:
            pass

        # try:
        #     for sk in self.sketchPoints:
        #         xl,yl,rl = sk
        #         self.afmAll.setData(xl,yl)
        # except:
        #     pass

        if self.sketching:
            QtCore.QTimer.singleShot(self.settings['plot']['plot_timing']/1.0, self.sketchicar)

    def afmReady(self):
        self.log('sketch', 'end')
        self.afmPosition.clear()
        self.afmNow.clear()
        self.afmAll.clear()
        for i in self.sketchPoints:
            self.pi.removeItem(i)
        self.sketchPoints = []
        self.afmPoints.clear()

    @QtCore.pyqtSlot("QString")
    def updateStatus(self,line):
        line = str(line)
        # print(line)
        # return
        if line.startswith('vtip'):
            self.statusBar().showMessage(line)
            line = line.split( )
            self.vtip = float(line[1])
            self.log(['sketch','vtip'],['vtip', self.vtip])
            print( 'VTIP ' , self.vtip )

        elif line.startswith('# copy'):
            line = line.split( )
            self.copy = int(line[2])
            self.log(['sketch','copy'],['copy', self.copy])
            print( 'Copy ' , self.copy )
            self.afmPoints.clear()

        elif line.startswith('# start'):
            self.statusBar().showMessage(line)
            self.sketching = True
            self.sketchicar()
            line = line.split( )
            self.log(['sketch','ID'],['start', line[2]])
            self.afmPoints.clear()
            print('Started '+line[2])
        elif line.startswith('# end'):
            self.statusBar().showMessage(line)
            line = line.split( )
            xl,yl,rl = np.copy(self.afmPoints.get_partial())

            ti = pg.PlotDataItem(xl,yl, size=2, pen=sketchPen, brush=pg.mkBrush(0, 0, 255, 255))
            self.sketchPoints.append(ti)
            self.pi = self.plotFrame.sketchPlot.getPlotItem()
            self.pi.addItem(ti)

            self.afmPoints.clear()
            self.log(['sketch','ID'],['end', line[2]])
            print('Finished '+line[2])

        elif line.startswith('Ready'):
            self.statusBar().showMessage(line)
            self.sketching = False
            self.afmReady()
            print( "\nREADY\n" )

        elif line.startswith('xyAbs'):
            self.statusBar().showMessage(line)
            self.sketching = True
            self.timer.restart()
            line = line.split( )
            x = float(line[1])
            y = float(line[2])
            r = float(line[3])
            self.log(['sketch','x','y','r'], ['xyAbs', x, y, r])
            xo, yo = self.transformData([x,y], direction = -1)
            self.afmPoints.append([xo,yo,r])
        else:
            print('unknown', line)


    def doDemo(self):
        data = self.sketchFile.split('\n')
        for line in data:
            # if line.startswith('xyAbs'):
            # dx,dy,dr = self.nextPosition - self.currentPosition
            # r = self.nextPosition[2]
            # dt = np.sqrt(dx**2 + dy**2)/r
            # print(dt)
            self.updateStatus(line)
            # time.sleep(0.5)
            # self.timer.restart()
            self.sketching = True
            # line = line.split( )
            # r = float(line[3])

    def sketchNow(self, index=None):
        self.afmPosition.clear()
        self.afmNow.clear()
        self.afmAll.clear()
        self.sketchFile = ''
        if index == None:
            index = self.model
        nfile = False

        if self.multi_check.checkState() == 2:
            multiples = self.multi_n.value()
            sleep = self.multi_time.value()
            dx = self.multi_dx.value()
            dy = self.multi_dy.value()
        else:
            multiples = 1
            sleep = 0
            dx = 0
            dy = 0


        for cpy in range(multiples):

            offset = [cpy*dx,cpy*dy]
            self.sComment(['copy',cpy])

            for i in range(index.rowCount()):
                # print( '- ', i )
                item = index.getItem(index.index(i))
                if item.checkState == 0:
                    continue
                chitems = item.childItems
                # if item.data(6) == 'Layer':
                self.sAdd('')
                self.sComment(item.data())
                print('fix layer comment')

                if len(chitems) != 0:
                    nfile = True
                    for child in item.childItems:
                        if child.checkState == 0:
                            continue
                        self.sAdd('')
                        # child.data()

                        # print('xx',child.data('Volt'),child.data(1),child.data(2),child.data(3))
                        # print('yy',child.volt)
                        l = [['start'], child.data()]
                        startline = [item for sublist in l for item in sublist]
                        self.sComment(startline)
                        # self.sComment()
                        if child.checkState == 2:

                            data = child.pltData
                            if data != []:
                                for i in data:
                                    print (np.array(i).shape)
                                    # dta = self.transformData(i[::item.pathOrder])
                                    dta = np.add(i[::child.pathOrder],offset)
                                    # pdi = self.pi.plot(dta, pen = showPen)

                            # for chpath in child.pltData[::child.pathOrder]:
                                # dta = chpath[::child.pathOrder]

                                    path = self.transformData( dta ,direction=1)
                                    # print(path)
                                    x,y = path[0]
                                    self.sAdd('vtip\t%f' %(0.0))
                                    self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                                    self.sAdd('vtip\t%f' %float(child.data('Volt')))
                                    r = child.data('Rate')
                                    for x,y in path:
                                    # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                                        self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                                    self.sAdd('vtip\t%f' %(0.0))
                                    self.sComment(['end',child.data('Name')])
            x0,y0 = self.offset_center
            self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(-x0,-y0,self.freerate))
            # self.sAdd('vtip\t%f' %(0.0))
            # time.sleep(sleep)
            self.sAdd('pause\t%.1f' %(sleep))


        if nfile:
            # make sure the afm moves away from the device
            self.saveSketch()

            self.log(['sketch','dir'], ['subfolder', str(self.sketchSubFolder)])
            transmit = 'SketchScript %i \n' % len(self.sketchFile)

            if demo:
                self.doDemo()
            else:
                self.SocketThread.send_message(transmit + self.sketchFile)

    def saveSketch(self):
        self.sketchSubFolder = QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss')

        if not os.path.exists(self.storeFolder + self.sketchSubFolder):
            os.makedirs(str(self.storeFolder + self.sketchSubFolder))

        self.sketchOutDir = str(self.storeFolder + self.sketchSubFolder+'/')
        fname = self.sketchOutDir + 'out.txt'
        f = open(fname, 'w')
        f.write(self.sketchFile)
        f.close()
        try:
            self.plotFrame.savePlot(self.sketchOutDir+'currentSketchView.png')
        except:
            pass
        try:
            filename = sorted(os.listdir(self.afmImageFolder))[-1]
            shutil.copy2(self.afmImageFolder + filename,self.sketchOutDir+filename)
        except:
            pass
        try:
            shutil.copy2('D:/lithography/current.png',self.sketchOutDir+'currentAFMImage.png')
        except:
            pass
        try:
            shutil.copy2(self.dxffileName,self.sketchOutDir+self.dxffileName.split('/')[-1])
        except:
            pass

    def sComment(self, stuff):
        adding = ''
        adding += '# '
        for i in stuff:
            adding += str(i)+ '\t'
        adding += '\n'
        self.sketchFile += adding
        # print( adding )

    def sAdd(self, data):
        self.sketchFile += data
        self.sketchFile += '\n'
        # print( data )

    def abortNow(self):
        self.SocketThread.send_message('Abort\n')

    def shutLithoNow(self):
        self.SocketThread.send_message('shutdown\n')


    def pickFile(self):
        # http://stackoverflow.com/questions/20928023/how-to-use-qfiledialog-options-and-retreive-savefilename
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Select design file', self.dxffileName, filter='*.dxf')
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

        # self.fileIn.setText()
        self.dxf = ezdxf.readfile(self.dxffileName)
        self.model = TreeModel(self.headers, self.dxf, parent=self)


        # self.tree_file.setSizes([20, 300])
        self.tree_file.setModel(self.model)
        # self.tree_file.setColumnHidden(self.headers.index('Show'), True)


        self.tree_file.setDragDropMode( QtGui.QAbstractItemView.InternalMove )
        self.tree_file.setSelectionMode( QtGui.QAbstractItemView.ExtendedSelection )

        for col in ['Closed', 'Show', 'Order']:
            colnum = self.headers.index(col)
            self.tree_file.setItemDelegateForColumn(colnum,CheckBoxDelegate(self, column = col))

        for col in ['Volt', 'Rate', 'Step']:
            colnum = self.headers.index(col)
            self.tree_file.setItemDelegateForColumn(colnum,DoubleSpinBoxDelegate(self))

        self.tree_file.setItemDelegateForColumn(self.model.col('Color'),ColorDelegate(self))


        self.tree_file.expandAll()
        self.tree_file.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)


        # for col in [self.headers.index(col) for col in ['Closed', 'Show']]:
        #     root = self.tree_file.rootIndex()
        #     for i in range(0,self.model.rowCount(root)):
        #         index = self.model.index(i, col)
        #         self.tree_file.openPersistentEditor(index)
        #         item  = self.model.getItem(index)
        #         for ch in range(0,item.childCount()):
        #             index2 = self.model.index(ch, col,  self.model.index(i))
        #             self.tree_file.openPersistentEditor(index2)

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)
        # self.tree_file.setColumnWidth(0, 100)

        self.tree_file.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.tree_file, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.doMenu)
        # print('make last column just as wide as needed')

        ####################
        self.pi = self.plotFrame.sketchPlot.getPlotItem()
        self.plotFrame.clearSketchPlot()
        self.pi.addItem(self.afmPosition)
        self.pi.addItem(self.afmNow)
        self.pi.addItem(self.afmAll)

        self.pi.enableAutoRange('x', True)
        self.pi.enableAutoRange('y', True)
        self.pi.setAspectLocked(lock=True, ratio=1)
        self.pi.showGrid(x=1, y=1, alpha=0.8)



        QtCore.QObject.connect(self.tree_file.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_selection)
        # QtCore.QObject.connect(self.tree_schedule.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('checkChanged(QModelIndex,QModelIndex)'), self.checked)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), self.replot)
        # QtCore.QObject.connect(self.model, QtCore.SIGNAL('recalc(QModelIndex,QModelIndex)'), self.recalc)

        self.updateActions()

    def clicked(self):
        print('point')

    def doMenu(self, point):
        index=self.tree_file.indexAt(point)
        model = index.model()
        headers = model.header
        column = index.column()
        colname = headers[column]
        item = self.tree_file.model().getItem(index)
        # print(colname,item)


    @QtCore.pyqtSlot("QModelIndex", "QModelIndex")
    def recalc(self, index):
        print('X recalc')


    def pltDesign(self):
        # print('in pltdesign')
        if self.dxf_design == None:
            self.dxf_design = ezdxf.readfile('./layout/design.dxf')

        design_pltlist = []

        for i in self.designPltHandle:
            self.pi.removeItem(i)
        self.designPltHandle = []

        if self.offset_check_design.checkState() == 2:
            modelspace = self.dxf_design.modelspace()
            for entity in modelspace:
                # print (entity)
                if entity.dxftype() == 'POLYLINE':
                    data = np.array(list(entity.points()))[:,:2]
                    design_pltlist.append(data)
                if entity.dxftype() == 'LINE':
                    data = np.array(entity.points)[:,:2]
                    design_pltlist.append(data)
                else:
                    continue


            designPen = pg.mkPen(color='00FF00DD', style=QtCore.Qt.DotLine, width=2)
            designBrush = pg.mkBrush(color='00FF00DD')
            for i in design_pltlist:
                pdi = self.pi.plot(i, pen = designPen, brush=designBrush)
                self.designPltHandle.append(pdi)


    def lockOffset(self):
        self.offset_check_lock.stateChanged.connect(self.reoffset)
        if self.offset_check_lock.checkState() == 2:
            self.offset_angle_spin.setEnabled(False)
            self.offset_dx_spin.setEnabled(False)
            self.offset_dy_spin.setEnabled(False)
        else:
            self.offset_angle_spin.setEnabled(True)
            self.offset_dx_spin.setEnabled(True)
            self.offset_dy_spin.setEnabled(True)


    def reoffset(self):
        # print('in reoffset')
        dx = -self.offset_dx_spin.value()
        dy = -self.offset_dy_spin.value()

        self.offset_angle = -self.offset_angle_spin.value()
        self.offset_center = [dx,dy]

        self.plotFrame.setAfmImage(angle = self.offset_angle, offset = self.offset_center, updateRange=False )

        # print(self.plotFrame.afmIm.rect)
        # self.replot()


    def transformData(self, data, angle = None, offset = None, direction = 1):
        # print('in transformData')
        c = data
        if angle == None:
            angle = self.offset_angle
        if offset == None:
            offset = self.offset_center
        offset = -np.array(offset)

        theta = direction*(angle/180.) * np.pi
        rotMatrix = np.array([[np.cos(theta), -np.sin(theta)],
                              [np.sin(theta),  np.cos(theta)]])
        if direction == 1:
            c = np.add(c, direction*offset)
            c = np.dot(c, rotMatrix)
        else:
            c = np.dot(c, rotMatrix)
            c = np.add(c, direction*offset)
        return c

    def remulti_angle(self):

        distance = self.multi_distance.value()
        angle = self.multi_angle.value()
        angle = (angle/180.) * np.pi
        dx = distance * np.cos(angle)
        dy = distance * np.sin(angle)

        self.multi_dx.setValue(dx)
        self.multi_dy.setValue(dy)
        self.remulti()


    def remulti(self):

        dx = self.multi_dx.value()
        dy = self.multi_dy.value()

        if dx != 0:
            theta = np.arctan(dy/dx)
            theta *= 180/np.pi
        else:
            theta = np.sign(dy) * 90

        self.multi_angle.setValue(theta)
        self.multi_distance.setValue(np.sqrt(dx**2 + dy**2))
        # print('in remulti')

        root = self.tree_file.rootIndex()
        for i in range(0,self.model.rowCount(root)):
            index = self.model.index(i, 0)
            # self.tree_file.openPersistentEditor(index)
            item  = self.model.getItem(index)
            for ch in range(0,item.childCount()):
                index2 = self.model.index(ch, 0,  self.model.index(i))
                item = self.model.getItem(index2)
                checked = item.checkState
                if checked != 0:
                    self.replot(index2)

    @QtCore.pyqtSlot("QModelIndex", "QModelIndex")
    def replot(self, index = None):
        # print('in replot')
        if index == None:
            root = self.tree_file.rootIndex()
            for i in range(0,self.model.rowCount(root)):
                index = self.model.index(i, 0)
                item  = self.model.getItem(index)
                for ch in range(0,item.childCount()):
                    index2 = self.model.index(ch, 0,  self.model.index(i))
                    # print(index2)
                    self.replot(index2)
            return

        # print('replot', index, index.column())
        # return
        model = self.model
        item = model.getItem(index)


        # self.pi.removeItem(item.pltHandle)
        for i in item.pltHandle:
            self.pi.removeItem(i)
        item.pltHandle = []

        show = item.data('Show')
        checked = item.checkState
        # print(checked)
        # print('replot', index, index.column(), checked)

        if self.multi_check.checkState() == 2:
            multiples = self.multi_n.value()
            sleep = self.multi_time.value()
            dx = self.multi_dx.value()
            dy = self.multi_dy.value()
        else:
            multiples = 1
            sleep = 0
            dx = 0
            dy = 0


        for cpy in range(multiples):

            offset = [cpy*dx,cpy*dy]

            if (checked != 0) or (show != 0):
                itemcolor = pg.QtGui.QColor(*item.color)
                if checked == 0:
                    itemcolor.setAlpha(44)

                showPen.setColor(itemcolor)

                data = model.getItem(index).pltData
                if data != []:
                    for i in data:
                        # dta = self.transformData(i[::item.pathOrder])
                        dta = np.add(i[::item.pathOrder],offset)
                        pdi = self.pi.plot(dta, pen = showPen)
                        item.pltHandle.append(pdi)
                        x = np.array(dta[0][0])
                        y = np.array(dta[0][1])
                        pdi = self.pi.plot([x], [y], symbolPen=None, symbolBrush=showPen.color(), symbol='s', symbolSize=0.05, pxMode=False)
                        item.pltHandle.append(pdi)

        self.update_selection(None,None)
            # print('pd', item.pltData)
            # for i in item.pltData:
            #     print(i)
            #     # print(i.shape)
            #     print(data.shape)
            #     pdi = self.pi.plot(i, pen = showPen)

            #     item.pltHandle.append(pdi)

        # self.updateActions()


    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def update_selection(self, selected=None, deselected=None):
        model = self.model
        indexes = self.tree_file.selectedIndexes()
        for i in self.selectedPI:
            self.pi.removeItem(i)
        self.selectedPI = []

        items = set([model.getItem(i) for i in indexes])

        # selectPen = pg.mkPen(color='FF750ADD')  #, style=QtCore.Qt.DotLine

        if self.multi_check.checkState() == 2:
            multiples = self.multi_n.value()
            sleep = self.multi_time.value()
            dx = self.multi_dx.value()
            dy = self.multi_dy.value()
        else:
            multiples = 1
            sleep = 0
            dx = 0
            dy = 0

        for cpy in range(multiples):
            offset = [cpy*dx,cpy*dy]

            for item in items:
                show = item.data('Show')
                checked = item.checkState
                if (checked != 0) or (show != 0):
                    if len(item.pltData) > 0 :
                        itemcolor = pg.QtGui.QColor(*item.color)
                        itemcolor.setAlpha(70)
                        if checked == 0:
                            itemcolor.setAlpha(44)

                        selectPen.setColor(itemcolor)
                        for i in item.pltData:
                            # pdi.setZValue(10000)

                            # dta = self.transformData(i[::item.pathOrder])
                            dta = np.add(i[::item.pathOrder],offset)
                            pdi = self.pi.plot(dta, pen = selectPen)
                            self.selectedPI.append(pdi)
                            x = np.array(dta[0][0])
                            y = np.array(dta[0][1])
                            pdi = self.pi.plot([x], [y], symbolPen=None, symbolBrush=itemcolor, symbol='s', symbolSize=0.05, pxMode=False)
                            self.selectedPI.append(pdi)




    @QtCore.pyqtSlot("QModelIndex","QModelIndex")
    def checked(self, index):
        return
        # print('checked', index, index.column())
        # self.replot(index)
        # model = self.model
        # item = model.getItem(index)

        # print( 'Color',         item.color)
        # print( 'Closed',        item.is_closed)
        # print( 'parentItem',    item.parentItem)
        # print( 'itemData',      item.itemData)
        # print( 'childItems',    item.childItems)
        # print( 'Show',          item.show)
        # print( 'entity',        item.entity)
        # print( 'pltHandle',     item.pltHandle)
        # print( 'checkState',    item.checkState)
        # print( 'Angle',         item.fillAngle)
        # print( 'Step',          item.fillStep)
        # print( 'Volt',       item.volt)
        # print( 'Rate',          item.rate)
        # print( 'length',        item.length)
        # print( 'Time',          item.sketchTime)
        # print( 'Name',          item.name)
        # print( 'Type',          item.type)




    # def insertChild(self):
    #     index = self.tree_file.selectionModel().currentIndex()
    #     model = self.tree_file.model()

    #     if model.columnCount(index) == 0:
    #         if not model.insertColumn(0, index):
    #             return

    #     if not model.insertRow(0, index):
    #         return

    #     for column in range(model.columnCount(index)):
    #         child = model.index(0, column, index)
    #         model.setData(child, "[No data]", QtCore.Qt.EditRole)
    #         if model.headerData(column, QtCore.Qt.Horizontal) is None:
    #             model.setHeaderData(column, QtCore.Qt.Horizontal,
    #                     "[No header]", QtCore.Qt.EditRole)

    #     self.tree_file.selectionModel().setCurrentIndex(model.index(0, 0, index),
    #             QtGui.QItemSelectionModel.ClearAndSelect)
    #     self.updateActions()

    # def insertColumn(self):
    #     model = self.tree_file.model()
    #     column = self.tree_file.selectionModel().currentIndex().column()

    #     changed = model.insertColumn(column + 1)
    #     if changed:
    #         model.setHeaderData(column + 1, QtCore.Qt.Horizontal,
    #                 "[No header]", QtCore.Qt.EditRole)

    #     self.updateActions()

    #     return changed

    # def insertRow(self):
    #     index = self.tree_file.selectionModel().currentIndex()
    #     model = self.tree_file.model()

    #     if not model.insertRow(index.row()+1, index.parent()):
    #         return

    #     self.updateActions()

    #     for column in range(model.columnCount(index.parent())):
    #         child = model.index(index.row()+1, column, index.parent())
    #         model.setData(child, "[No data]", QtCore.Qt.EditRole)

    # def removeColumn(self):
    #     model = self.tree_file.model()
    #     column = self.tree_file.selectionModel().currentIndex().column()

    #     changed = model.removeColumn(column)
    #     if changed:
    #         self.updateActions()

    #     return changed

    # def removeRow(self):
    #     index = self.tree_file.selectionModel().currentIndex()
    #     model = self.tree_file.model()

    #     if (model.removeRow(index.row(), index.parent())):
    #         self.updateActions()

    def updateActions(self):
        self.pltDesign()
        return
        # hasSelection = not self.tree_file.selectionModel().selection().isEmpty()
        # self.removeRowAction.setEnabled(hasSelection)
        # self.removeColumnAction.setEnabled(hasSelection)

        # hasCurrent = self.tree_file.selectionModel().currentIndex().isValid()
        # self.insertRowAction.setEnabled(hasCurrent)
        # self.insertColumnAction.setEnabled(hasCurrent)

        # if hasCurrent:
        #     self.tree_file.closePersistentEditor(self.tree_file.selectionModel().currentIndex())

        #     row = self.tree_file.selectionModel().currentIndex().row()
        #     column = self.tree_file.selectionModel().currentIndex().column()
        #     # if self.tree_file.selectionModel().currentIndex().parent().isValid():
        #         # self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
        #     # else:
        #         # self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))


    def addToolbars(self):
        exitAction            = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_delete.png'), 'Exit', self)
        closeConnectionAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_delete.png'), 'Shut down Lithocontrol on AFM', self)
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
        unloadStageAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/arrow_up_red.png'), 'Unload stage', self)
        loadStageAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/arrow_down.png'), 'Load stage', self)
        sketchAction          = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_accept.png'), 'Sketch Now', self)
        abortSketchAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_deny.png'), 'Abort Lithography', self)
        sketchFolderAction    = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_edit.png'), 'Sketch Folder', self)
        afmFolderAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_search.png'), 'AFM Image Folder', self)
        afmFolderReloadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_reload.png'), 'Reload AFM Image Folder', self)
        dxfLoadAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_add.png'), 'Load dxf', self)
        dxfReloadAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_refresh.png'), 'Reload dxf', self)
        dxfClearAction        = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_deny.png'), 'Clear dxf', self)

        QtCore.QObject.connect(closeConnectionAction, QtCore.SIGNAL('triggered()'), self.shutLithoNow )

        # QtCore.QObject.connect(exitAction, QtCore.SIGNAL('triggered()'), self.close )
        # exitAction.setShortcut('Ctrl+Q')
        # exitAction.setStatusTip('Exit application')

        # scClose = QtGui.QShortcut(QtGui.QKeySequence(("Ctrl+Q", "Quit")))
        # scClose2 = QtGui.QShortcut(QtGui.QKeySequence(("Cmd+Q", "Quit")))
        # QtCore.QObject.connect(scClose, QtCore.SIGNAL('triggered()'), self.close)
        # QtCore.QObject.connect(scClose2, QtCore.SIGNAL('triggered()'), self.close)


        QtCore.QObject.connect(captureAction,          QtCore.SIGNAL('triggered()'), self.doCapture )
        QtCore.QObject.connect(capture_abortAction,    QtCore.SIGNAL('triggered()'), self.doCaptureAbort )
        QtCore.QObject.connect(capture_forceAction,    QtCore.SIGNAL('triggered()'), self.doCaptureForce )
        QtCore.QObject.connect(frame_downAction,       QtCore.SIGNAL('triggered()'), self.doFrameDown )
        QtCore.QObject.connect(frame_upAction,         QtCore.SIGNAL('triggered()'), self.doFrameUp )

        QtCore.QObject.connect(engageAction,           QtCore.SIGNAL('triggered()'), self.doEngage )
        QtCore.QObject.connect(withdrawAction,         QtCore.SIGNAL('triggered()'), self.doWithdraw )




        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measure_start )
        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.graficar )
        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.dhticar )
        QtCore.QObject.connect(favoriteMeasureAction,  QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(acceptMeasureAction,    QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.measure_stop )

        QtCore.QObject.connect(loadStageAction,        QtCore.SIGNAL('triggered()'), self.stageLoad )
        QtCore.QObject.connect(unloadStageAction,      QtCore.SIGNAL('triggered()'), self.stageUnload )

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
        toolbar.addAction(closeConnectionAction)
        # toolbar.addAction(exitAction)

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
        plttoolbar.addSeparator()
        plttoolbar.addAction(loadStageAction)
        plttoolbar.addAction(unloadStageAction)

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
            # self.settings['measure']['dht_serial'] = None

            # try:
            #     self.dht_WorkerThread.quit()
            # except:
            #     pass
            self.settings['measure']['DHTport'] = self.spinCom.value()
            self.settings['measure']['dht_serial'] = serial.Serial(self.settings['measure']['DHTport']-1, baudrate=115200, timeout=5) # opens, too.
            self.sig_dhtmeasure.emit(500)

            # print(self.dht_Worker)#.running
            # self.dht_Worker = dht_Worker(self.settings['measure'])
            # self.dht_WorkerThread = QtCore.QThread()
            # self.dht_Worker.terminate.connect(self.setterminate)
            # self.dht_Worker.moveToThread(self.dht_WorkerThread)
            # self.dht_WorkerThread.start()

            # self.sig_dhtmeasure.connect(self.dht_Worker.run)
            # self.sig_dhtmeasure.connect(self.dhticar)
            # self.sig_measure_stop.connect(self.dht_Worker.stop)

        except:
            print( 'dht failed' )
            self.settings['measure']['dht_serial'] = None
            pass

    def closeEvent(self,event):
        if demo:
            event.accept()
            return

        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes | QtGui.QMessageBox.No , QtGui.QMessageBox.Yes)
        if reply==QtGui.QMessageBox.Yes:
            self.SocketThread.send_message('ClientClose\n')
            sleep(1)
            self.SocketThread.stop()

            self.measure_save()
            self.measure_stop()
            if not demo:
                self.ni_workerThread.quit()
                self.dht_WorkerThread.quit()
                try:
                    self.settings['measure']['dht_serial'].close()
                except:
                    pass
            event.accept()
        else:
            event.ignore()


    def makeDataset(self):
        pass

    def run(self):
        if not demo:
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
        self.plot_update_time.valueChanged.connect(self.update_plotting)
        self.spinCom.valueChanged.connect(self.update_plotting)
        self.spinCom.valueChanged.connect(self.initSerial)
        self.SRSensitivity.editingFinished.connect(self.update_plotting)
        self.PARSensitivity.editingFinished.connect(self.update_plotting)

        self.spinCom.valueChanged.connect(self.initSerial)

        #xxx
        self.multi_check.stateChanged.connect(self.remulti)
        self.multi_n.editingFinished.connect(self.remulti)
        self.multi_time.editingFinished.connect(self.remulti)
        self.multi_dx.editingFinished.connect(self.remulti)
        self.multi_dy.editingFinished.connect(self.remulti)

        self.multi_angle.editingFinished.connect(self.remulti_angle)
        self.multi_distance.editingFinished.connect(self.remulti_angle)


        self.offset_check_lock.stateChanged.connect(self.lockOffset)
        self.offset_check_design.stateChanged.connect(self.pltDesign)
        self.offset_angle_spin.valueChanged.connect(self.reoffset)
        self.offset_dx_spin.valueChanged.connect(self.reoffset)
        self.offset_dy_spin.valueChanged.connect(self.reoffset)



        if not demo:
            self.sig_measure.connect(self.ni_worker.run)
            self.sig_measure_stop.connect(self.ni_worker.stop)

            self.sig_dhtmeasure.connect(self.dht_Worker.run)
            self.sig_dhtmeasure.connect(self.dhticar)
            # self.sig_measure_stop.connect(self.dht_Worker.stop)

            self.ni_workerThread.start()
            self.dht_WorkerThread.start()


        self.sig_dhtmeasure.emit(500)


        # self.show()

    def update_plotting(self):
        if self.check_plot.checkState() == 2:
            self.settings['plot']['plot_measurement'] = True
        else:
            self.settings['plot']['plot_measurement'] = False

        if self.check_2pt.checkState() == 2:
            self.settings['plot']['plot_2pt'] = True
        else:
            self.settings['plot']['plot_2pt'] = False

        if self.check_4pt.checkState() == 2:
            self.settings['plot']['plot_4pt'] = True
        else:
            self.settings['plot']['plot_4pt'] = False

        if self.check_current.checkState() == 2:
            self.settings['plot']['plot_current'] = True
        else:
            self.settings['plot']['plot_current'] = False

        for i in self.plotlist:
            i.clear()

        self.settings['plot']['plot_timing'] = self.plot_update_time.value()
        self.settings['measure']['SR_sensitivity'] = float(self.SRSensitivity.text ())
        self.settings['measure']['PAR_sensitivity'] = float(self.PARSensitivity.text ())
        self.settings['measure']['DHTport'] = self.spinCom.value()
        self.SRSensitivity.setText("%.0e" %(self.settings['measure']['SR_sensitivity']))
        self.PARSensitivity.setText("%.0e" %(self.settings['measure']['PAR_sensitivity']))

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
            print( 'Error clearing ni_store' )
            print( sys.exc_info() )
        try:
            # self.dht_store.clear()
            # self.dht_buff.clear()
            pass
        except:
            print( 'Error clearing dht_store' )
            print( sys.exc_info() )
        self.newstores = True


    def measure_save(self):
        self.ni_store.save_data()
        self.dht_store.save_data()
        self.log_store.save_data()

    def setterminate(self):
        self.ni_terminate = True

    def init_dht_plot(self):
        self.dht_pi = self.plotFrame.dhtPlot.getPlotItem()
        self.dht_pi.clear()
        self.dht_pi.addLegend()
        self.dht_pi.enableAutoRange('x', True)
        self.dht_pi.enableAutoRange('y', True)

        self.hplot = pg.PlotDataItem()
        self.tplot = pg.PlotDataItem()
        self.tplot.setPen(color=kelly_colors['vivid_orange'])
        self.hplot.setPen(color=kelly_colors['vivid_green'])
        self.dht_pi.addItem(self.hplot)
        self.dht_pi.addItem(self.tplot)
        self.dht_pi.legend.addItem(self.tplot, 'Temperature')
        self.dht_pi.legend.addItem(self.hplot, 'Humidity')

    def dhticar(self):
        if self.settings['measure']['dht_buff'].size > 0:
            raw_buffer = self.settings['measure']['dht_buff'].get_partial_clear()
            dtime = raw_buffer[0]
            dtmp = raw_buffer[1]
            dhum = raw_buffer[2]
            self.dht_store.append([dtime,dtmp,dhum])
            self.text_temp.setText('Tmp: %.1f\xb0C'%(dtmp.mean()))
            self.text_hum.setText('Hum: %.1f%%'%(dhum.mean()))

            self.tplot.setData(x=self.dht_store.get_partial()[0], y=self.dht_store.get_partial()[1])
            self.hplot.setData(x=self.dht_store.get_partial()[0], y=self.dht_store.get_partial()[2])


            self.dht_pi.legend.items = []
            self.dht_pi.legend.addItem(self.hplot, 'Humidity' + ' = ' + '%.1f %%RH' % dhum.mean())
            self.dht_pi.legend.addItem(self.tplot, 'Temperature' + ' = ' + '%.1f ' % dtmp.mean() +u"\u00b0"+'C')

        if not self.ni_terminate:
            QtCore.QTimer.singleShot(500, self.dhticar)



    def graficar(self):

        if self.settings['measure']['buff'].size > 0:
            raw_buffer = self.settings['measure']['buff'].get_partial_clear()

            d_time = raw_buffer[0]
            d_ch0 = raw_buffer[1]
            d_ch1 = raw_buffer[2]

            current = np.abs(d_ch0*self.settings['measure']['SR_sensitivity']/10.0)
            r2pt = np.abs(self.settings['measure']['in'][0]['amplitude'] / current)

            a_b = d_ch1*self.settings['measure']['PAR_sensitivity']/10
            r4pt = np.abs(a_b / current)

            self.ni_store.append([d_time, current, r2pt, r4pt])

        if self.settings['plot']['plot_measurement']:
            if self.ni_store.size>1:
                n = 0
                self.plot_counter +=1
                raw_buffer = self.ni_store.get_partial()

                d_time = raw_buffer[0]
                current = raw_buffer[1]
                r2pt = raw_buffer[2]
                r4pt = raw_buffer[3]

                g2pt = 1.0/r2pt *1e6
                g4pt = 1.0/r4pt *1e6
                mask = np.isfinite(g2pt) & np.isfinite(g4pt) & np.isfinite(d_time) & (d_time > 0.1)
                g2pt = g2pt[mask]
                g4pt = g4pt[mask]
                current2 = current[mask]
                d_time = d_time[mask]

                n = 1
                av_len = -10
                if self.plot_counter>11:
                    self.ni_pi_legend.items = []
                    self.pltG_pi_legend.items = []

                if self.settings['plot']['plot_current'] == True:
                    if self.plot_counter>11:

                        try:
                            av_curr = np.average(current[av_len:])*1e9
                            self.ni_pi_legend.addItem(self.plotlist['Current1'], 'Current' + ' = ' + '%.2f nA' % av_curr)
                            self.pltG_pi_legend.addItem(self.plotlist['Current2'], 'Current' + ' = ' + '%.2f nA' % av_curr)
                        except:
                            self.ni_pi_legend.addItem(self.plotlist['Current1'], 'Current')
                            self.pltG_pi_legend.addItem(self.plotlist['Current2'], 'Current')
                            pass

                    self.plotlist['Current1'].setData(x=d_time, y=current*1e9)
                    self.plotlist['Current1'].setPen(color=kelly_colors[colors[n]])
                    self.plotlist['Current2'].setData(x=d_time, y=current2*1e9)
                    self.plotlist['Current2'].setPen(color=kelly_colors[colors[n]])

                n = 2
                if self.settings['plot']['plot_2pt'] == True:
                    if self.plot_counter>11:
                        try:
                            av_2pt = np.average(r2pt[av_len:])/1000.0
                            self.ni_pi_legend.addItem(self.plotlist['R2pt'], 'R2pt' + ' = ' + '%.0f kOhm' % av_2pt)
                        except:
                            self.ni_pi_legend.addItem(self.plotlist['R2pt'], 'R2pt')
                            pass

                    self.plotlist['R2pt'].setData(x=d_time, y=r2pt/1000.0)
                    self.plotlist['R2pt'].setPen(color=kelly_colors[colors[n]])

                n = 3
                if self.settings['plot']['plot_4pt'] == True:
                    if self.plot_counter>11:
                        try:
                            av_4pt = np.average(r4pt[av_len:])/1000.0
                            self.ni_pi_legend.addItem(self.plotlist['R4pt'], 'R4pt' + ' = ' + '%.0f kOhm' % av_4pt)
                        except:
                            self.ni_pi_legend.addItem(self.plotlist['R4pt'], 'R4pt')
                            pass

                    self.plotlist['R4pt'].setData(x=d_time, y=r4pt/1000.0)
                    self.plotlist['R4pt'].setPen(color=kelly_colors[colors[n]])




                n = 2
                if self.settings['plot']['plot_2pt'] == True:
                    if self.plot_counter>11:
                        try:
                            av_2pt = np.average(g2pt[av_len:])
                            self.pltG_pi_legend.addItem(self.plotlist['G2pt'], 'g2pt' + ' = ' + '%.0f uS' % av_2pt)
                        except:
                            self.pltG_pi_legend.addItem(self.plotlist['G2pt'], 'g2pt')
                            pass

                    self.plotlist['G2pt'].setData(x=d_time, y=g2pt)
                    self.plotlist['G2pt'].setPen(color=kelly_colors[colors[n]])

                n = 3
                if self.settings['plot']['plot_4pt'] == True:
                    if self.plot_counter>11:
                        try:
                            av_4pt = np.average(g4pt[av_len:])
                            self.pltG_pi_legend.addItem(self.plotlist['G4pt'], 'g4pt' + ' = ' + '%.0f uS' % av_4pt)
                        except:
                            self.pltG_pi_legend.addItem(self.plotlist['G4pt'], 'g4pt')
                            pass

                    self.plotlist['G4pt'].setData(x=d_time, y=g4pt)
                    self.plotlist['G4pt'].setPen(color=kelly_colors[colors[n]])

            # self.plot_counter = 0

        if not self.ni_terminate:
            QtCore.QTimer.singleShot(self.settings['plot']['plot_timing'], self.graficar)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())
