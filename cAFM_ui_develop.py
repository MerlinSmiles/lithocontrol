#!/usr/bin/env python
demo = False
import sys
sys.path.append(".\\source")

import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import logging
from source import custom_logger
from source.custom_logger_widget import LogDialog

# log = logging.getLogger('root')
log = custom_logger.getLogger('root','DEBUG','./logs/logfile.log')

from source.sketch_data_widget import SketchDataDialog
from source.script_editor import editorWidget
# import sketch_script

try:
    import gwy,  gwyutils
except:
    demo = True
# demo = True


import numpy as np
from pprint import pprint


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate, QDateTime
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
# if demo:
#     config['storage'] = config['demo_storage']
# print(config['storage'])

def_dxf_file = 'F:/lithography/DesignFiles/current.dxf'
def_dxf_file = config['storage']['def_dxf_file']

import os
import time
from time import sleep
import socket
# log.setLevel('DEBUG')


from source.helpers import *
if not demo:
    from source.convertAFM import *
    from source.ni_measurement import *
else:
    from source.ni_measurement_demo import *
from source.socketworker import *
from source.buffer import *

# from source.treeclass import *
from source.treeclass3 import *
from source.PlotFrame import *
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
sketchedPen = pg.mkPen(color='FF000077',width=3.5)  #, style=QtCore.Qt.DotLine
movePen = pg.mkPen(color='1E4193',width=2, style=QtCore.Qt.DotLine)  #, style=QtCore.Qt.DotLine
showPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine , width=
selectPen = pg.mkPen(color='00FF00',width=3)  #, style=QtCore.Qt.DotLine , width=

class sItem(object):
    def __init__(self, item):
        self.item = item
        self.model = item.model
        self.color = item.color
        self.show = item.show
        self.parentItem = item.parentItem
        self.itemData = item.itemData
        self.childItems = item.childItems
        self.entity = item.entity
        self.pltHandle = item.pltHandle
        self.pltData = item.pltData
        self.checkState = item.checkState
        self.length = item.length
        self.sketchTime = item.sketchTime
        self.type = item.type
        self.meta = item.meta

        self.is_closed = item.is_closed
        self.fillAngle = item.fillAngle
        self.fillStep = item.fillStep
        self.pathOrder = item.pathOrder
        self.name = item.name
        self.parentName = item.parent().name
        self.volt = item.volt
        self.rate = item.rate
        self.offset = [0,0]
        self.sketchData = ''

    def data(self):
        datalist = [self.type,
                    self.name,
                    self.parentName,
                    self.volt,
                    self.rate,
                    self.fillAngle,
                    self.fillStep,
                    self.offset,
                    self.color,
                    self.show,
                    self.checkState,
                    self.length,
                    self.sketchTime,
                    self.is_closed,
                    self.pathOrder]

        return datalist


class MainWindow(QtGui.QMainWindow):

    outputReady = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        global log
        self.dateTime = QDateTime.currentDateTime()
        self.timer = self.dateTime.time()
        self.dater = self.dateTime.date()
        self.lastpostime = 0
        self.offset_angle = 0
        self.offset_center = [0,0]
        self.dxf_design = None
        self.designPltHandle = []
        self.sketchList = []


        # str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))
        self.s_time = str(self.dateTime.toString('yyyy-MM-dd_HH-mm-ss'))

        self.afmImageFolder = config['storage']['afmImageFolder']
        self.storeFolder = config['storage']['storeFolder'] + self.s_time + '/'
        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)

        # for hdlr in log.handlers:
        #     hdlr.close()
        #     log.removeHandler(hdlr)
        log = custom_logger.getLogger('root','DEBUG')
        self.logfile = self.storeFolder+'logfile.log'
        self.logHandler = custom_logger.RotateHandler(os.path.abspath(self.logfile),maxBytes=10e6, backupCount=5)
        log.addHandler(self.logHandler)
        log.info('TIME: ' + self.s_time)


        splash_pix = QtGui.QPixmap(r'./source/splash2.png')
        self.splash = QtGui.QSplashScreen(splash_pix)
        # adding progress bar
        # progressBar = QProgressBar(self.splash)
        self.splash.setMask(splash_pix.mask())
        self.splash.show()
        self.splash.showMessage("Loading GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)


        # self.splash.showMessage("Starting Measurement",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # self.measurementProcess()


        uic.loadUi('mainwindow.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool')

        screen = QtGui.QDesktopWidget().screenGeometry()
        # self.setGeometry(0, 0, screen.width(), screen.height())
        self.setGeometry(int(screen.width()/3), int(screen.height()/3), screen.width()/2, screen.height()/2)


        self.setWindowState(self.windowState() & QtCore.Qt.WindowMaximized)

        self.centralWidget().layout().setContentsMargins(2,2,2,2)
        self.gridLayout_2.setContentsMargins(2,2,2,2)
        self.gridLayout_2.setSpacing(2)


        self.plotFrame = PlotFrame()
        self.tabSketchBox = QtGui.QVBoxLayout()
        self.tabSketchBox.setContentsMargins(0,0,0,0)
        self.tabSketchBox.addWidget(self.plotFrame)

        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setMovable(True)
        self.tabWidget.setDocumentMode(True)

        self.tabSketching = QtGui.QWidget()
        self.tabSketching.setContentsMargins(0,0,0,0)
        self.tabSketching.setLayout(self.tabSketchBox)

        self.tabLogging = LogDialog()
        self.tabSketchData = SketchDataDialog()
        self.tabSketchScript = editorWidget('./user_scripts/parse_script.py')
        self.tabParseScript = editorWidget('./user_scripts/parse_dxf.py')

        self.tabWidget.addTab(self.tabSketching, 'Sketching')
        self.tabWidget.addTab(self.tabLogging, 'Logging')
        self.tabWidget.addTab(self.tabParseScript, 'DXF Script')
        self.tabWidget.addTab(self.tabSketchScript, 'Sketch Script')
        self.tabWidget.addTab(self.tabSketchData, 'Sketch Data')
        self.tabWidget.tabBar().setTabTextColor(2, pg.QtGui.QColor('#FF0000'))

            # if type(item) == QtGui.QLayoutItem:
            #     doSomeStuff(item.layout())
        self.splitter.addWidget(self.tabWidget)

        # stylesheet = """
        #             QTabBar::tab:selected {background: gray;}
        #             QTabBar::tab:tabSketchData {background: red;}
        #             QTabWidget>QWidget>QWidget{background: gray;}
        #             """
        # self.tabWidget.setStyleSheet(stylesheet)


        self.splitter.setSizes([500,1000])



        self.addToolbars()

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
        # self.settings['measure']['time'] = QTime()

        self.currentPosition = np.array([np.nan,np.nan,np.nan])
        self.nextPosition = np.array([np.nan,np.nan,np.nan])
        self.sketching = False


        self.sketchSubFolder = './'

        if demo:
            print("DDDDDDDDDDDDDDDDDDDDD")
            log.info("INIT: Demo activated")
            self.splash.showMessage("Loading DemoMode",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
            self.outDir = './demo/'
            self.afmImageFolder = './demo/afmImages/'
            self.storeFolder = './demo/sketches/' + self.s_time + '/'
            self.sketchSubFolder = './demo/sketches/'


        print( '' )
        print( '' )

        log.debug("INIT: Loading Stores")
        self.splash.showMessage("Loading Stores",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_stores()
        self.newstores = False

        # self.splash.finish(self)

        log.debug("INIT: Sketching")
        self.splash.showMessage("Initialize Sketching",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_sketching()
        log.debug("INIT: Measurement")
        self.splash.showMessage("Initialize Measurement",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)


        self.afmPoints_columns = ['x', 'y', 'rate']
        self.afmPoints = Buffer(36000, cols = self.afmPoints_columns)
        self.sketchPoints = []
        self.status_vtip = 0

        self.selectedPI = []

        # sleep(2)
        log.debug("INIT: GUI")
        self.splash.showMessage("Showing GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.showMaximized()
        # self.show()
        self.newafmImage()
        self.readDXFFile()
        # pprint(self.settings)

        log.debug("INIT: Program")
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

        # log.debug('Adebug message')
        # log.info('Ainfo message')
        # log.warning('Awarning message')
        # log.error('Aerror message')
        # print ('AOld school hand made print message')



        self.reoffset()
        self.pltDesign()
        self.savicar()

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

    def init_stores(self):

        c_time = str(int(self.timer.elapsed()/1000.0))

        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)
        fname = self.storeFolder+c_time + '_log-sketch.log'
        self.init_log(fname)

        log.debug('New stores: %s'%fname)

    def init_log(self, filename):
        formatter = logging.Formatter('%(message)s')
        self.slog = logging.getLogger('status_logger')
        self.slog.setLevel('INFO')
        shandler = logging.FileHandler(filename)
        shandler.setFormatter(formatter)
        self.slog.addHandler(shandler)

    def log(self, *args):
        tdelta = self.timer.elapsed()/1000.0

        line = {'time': tdelta}.__repr__()
        line += ', '
        for i in args:
            # line += str(i)
            line += i.__repr__()
            line += ', '
        line = line[:-2]
        self.slog.info(line)
        log.debug(line)


    def init_sketching(self):
        self.inFile = ''
        self.sketchFile = ''
        self.freerate = 7.0
        # self.tip_gain = 1.0
        # self.tip_offset = 0

        self.afminfo = {}

        # self.afmPosition = pg.PlotDataItem(size=5, pen=sketchedPen)
        # self.afmPosition.setZValue(100)
        self.afmNow = pg.PlotDataItem(size=2, pen=sketchPen)
        # self.afmAll = pg.PlotDataItem(size=2, pen=showPen)
        self.afmNow.setZValue(110)
        # self.afmAll.setZValue(110)

        self.preservePlots = []
        # self.preservePlots.append(self.afmPosition)
        self.preservePlots.append(self.afmNow)
        # self.preservePlots.append(self.afmAll)

        self.dxffileName = def_dxf_file

        self.headers = ('Name', 'Show', 'Color', 'Volt', 'Rate', 'Angle', 'Step', 'Time', 'Length', 'Closed', 'Order', 'Type')

        log.debug("INIT: AFMWorker")
        self.splash.showMessage("Initialize AFMWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.AFMthread = AFMWorker()
        log.debug("INIT: SocketWorker")
        self.splash.showMessage("Initialize SocketWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.SocketThread = SocketWorker(host = 'nanoman', port = 12345, demo=False)

        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("afmImage(QString)"), self.newafmImage)

        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)
        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("READY"), self.afmReady)
        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMStatus(QString)"), self.updateStatus)
        self.AFMthread.monitor(self.afmImageFolder)

        self.SocketThread.new_data.connect(self.updateStatus)
        self.SocketThread.monitor()


        # self.splash.showMessage("Initialize SocketWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # self.measureSocketThread = SocketWorker(host = 'localhost', port = 23456)
        # self.measureSocketThread.new_data.connect(self.socket_msg)
        # self.measureSocketThread.monitor()

    def measurementProcess(self):
        # self.pushButton.setEnabled(0)
        # self.pushButton.setText("Please Wait")
        # self.outputReady.connect(self.normal_output_written)
        # return
        command = "python"
        args =  ["-u", "ni_ui_bak.py", "-t", str(self.dateTime.toString('yyyy-MM-dd HH:mm:ss.zzz'))] #str(self.dateTime.toPyDateTime())

        self.mprocess = QtCore.QProcess(self)
        # self.mprocess.started.connect(self.onStarted)
        # self.mprocess.finished.connect(self.onFinished)
        self.mprocess.readyReadStandardOutput.connect(self.process_output)
        self.mprocess.readyReadStandardError.connect(self.process_error)
        # self.mprocess.stateChanged.connect(self.onStateChanged)
        # msg = str(self.mprocess.readAllStandardOutput())
        # self.outputReady.emit(msg)

        start = self.mprocess.startDetached(command, args)
        log.debug("New Process")



    def process_output(self):
        return
        output = self.mprocess.readAllStandardOutput()
        log.warning('process_output')
        print(output)

    def process_error(self):
        return
        output = self.mprocess.readAllStandardError()
        log.warning('process_error')
        print(output)

# def startit():
#     proc.start('python',['sleeper.py','10'])

# app.connect(button, QtCore.SIGNAL('clicked()'),startit)
# app.connect(proc,QtCore.SIGNAL('readyReadStandardOutput()'),process_output)

    # def normal_output_written(self, msg):
        # print('written:', msg)
    # def onStarted(self):
    #     print('Measurement started')
    #     # self.measurementProcess()


    # def onStateChanged(self, arg):
    #     print('Measurement onStateChanged')
    #     print(arg)
    #     # self.measurementProcess()

    # def onFinished(self, exitCode):
    #     print('Measurement window closed, restarting')
    #     self.measurementProcess()


    @QtCore.pyqtSlot("QString")
    def newafmImage(self, filename=None):
        if demo:
            return
        if filename == None:
            filename = list_directory(self.afmImageFolder)[-1]
            # filename = self.afmImageFolder+'/'+sorted(os.listdir(self.afmImageFolder))[-1]

        filename = os.path.abspath(filename)
        log.info("New AFM image: %s"%filename)
        # print(filename)

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
        log.warning( 'updateAFM' )

    def doCapture(self):
        self.SocketThread.send_message('Capture\n')
        log.info( 'AFM Capture' )

    def stageUnload(self):
        self.SocketThread.send_message('StageUnload\n')
        log.info( 'AFM unload Stage' )

    def stageLoad(self):
        self.SocketThread.send_message('StageLoad\n')
        log.info( 'AFM Load Stage' )

    # @QtCore.pyqtSlot("float, float, float")
    # def updateAFMpos(self,x,y,rate):
    #     self.sketchicar()

    def sketchicar(self):
        try:
            points = np.copy(self.afmPoints.get())
            xl,yl,rl = points.T
            # a,b,c = self.currentPosition
            a,b,c = points[-2]
            # x,y,r = self.nextPosition
            x,y,r = points[-1]
            dx = x - a
            dy = y - b

            dd = dx**2 + dy**2
            t = np.sqrt(dd)/r

            tt = (self.timer.elapsed()-self.lastpostime)/1000.0
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

        if self.sketching:
            QtCore.QTimer.singleShot(self.settings['plot']['plot_timing']/1.0, self.sketchicar)
        # else:
        #     print('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    def afmReady(self):
        # self.afmPosition.clear()
        self.afmNow.clear()
        # self.afmAll.clear()
        for i in self.sketchPoints:
            self.pi.removeItem(i)
        self.sketchPoints = []
        self.afmPoints.clear()

    @QtCore.pyqtSlot("QString")
    def updateStatus(self,line):
        line = str(line)
        # print(line)
        # return
        if line.startswith('# CheckAbort'):
            self.SocketThread.send_message('# continue\n')
            log.debug('STATUS: CheckAbort')
        elif line.startswith('vtip'):
            line = line.split( )
            self.status_vtip = float(line[1])
            self.log({'vtip': self.status_vtip})
            log.debug('STATUS: vtip %f' %self.status_vtip )
            # self.statusBar().showMessage(line)
        elif line.startswith('xyAbs'):
            # self.sketching = True
            self.statusBar().showMessage(line)
            self.lastpostime = self.timer.elapsed()
            line = line.split( )
            x = float(line[1])
            y = float(line[2])
            r = float(line[3])
            self.status_position = [x, y, r]
            self.log({'xyAbs': self.status_position})
            xo, yo = self.transformData([x,y], direction = -1)
            self.afmPoints.append([xo,yo,r])
        elif line.startswith('# sketching'):
            # print(line)
            line = line.split( )
            stat = line[2]
            # print(stat)
            if stat == 'start':
                self.sketching = True
                self.sketchicar()
                log.debug('STATUS: sketching start')
            elif stat == 'end':
                self.sketching = False
                log.debug('STATUS: sketching end')
                self.multi_check.setCheckState(0)
        elif line.startswith('# start'):
            line = line.split( )
            self.status_entity = line[2]
            self.log({'sketch': 'start'}, {'ID': line[2]})
            self.afmPoints.clear()
            log.info('STATUS: started '+line[2])
            # self.statusBar().showMessage(line)
        elif line.startswith('# end'):
            self.status_entity = ''
            line = line.split( )
            points = np.array(self.afmPoints.get())
            xl,yl,rl = np.copy(points).T

            ti = pg.PlotDataItem(xl,yl, pen=sketchedPen)
            self.sketchPoints.append(ti)
            self.pi = self.plotFrame.sketchPlot.getPlotItem()
            self.pi.addItem(ti)

            self.afmNow.clear()
            self.afmPoints.clear()
            self.log({'sketch': 'end'}, {'ID': line[2]})
            log.info('STATUS: finished '+line[2])
            # self.statusBar().showMessage(line)
        elif line.startswith('Ready'):
            self.status_state = 'Ready'
            self.sketching = False
            self.afmReady()
            self.afmReady()
            self.log({'status': 'ready'})
            log.info( "STATUS: READY" )
            self.statusBar().showMessage(line)
            self.measure_save()
        elif line.startswith('ABORT'):
            self.status_state = 'Ready'
            self.sketching = False
            self.afmReady()
            log.info( "STATUS: ABORT" )
            self.log({'status': 'abort'})
            self.statusBar().showMessage(line)
            self.measure_save()
        elif line.startswith('Parsing Script...'):
            self.afmReady()
            self.log({'status': 'busy'})
            self.status_state = 'Sketching'
        elif line.startswith('# entity'):
            sline = line.split()
            # [2] is the type, polyline etc...
            self.status_entity = sline[3]

            self.log({'entity': sline[3]}, {'type': sline[2]}, {'data': line})
            log.info('STATUS: entity '+sline[3])
            # print(line)
        elif line.startswith('# copy'):
            line = line.split( )
            self.status_copy = int(line[2])
            self.log({'copy': self.status_copy})
            log.info( 'STATUS: copy %d' %self.status_copy )
            self.afmPoints.clear()

        elif line.startswith('pause'):
            self.statusBar().showMessage(line)
            line = line.split( )
            self.status_pause = float(line[1])
            self.log({'pause': self.status_pause})

            log.info( 'STATUS: pause %f' %self.status_pause )
        elif line.startswith('SketchScript'):
            pass
        else:
            if line != '':
                print('unknown')
                print(line)


    def doDemo(self):
        log.info('Starting Demo')
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

    def s_comment(self, child, *args):
        string = ''
        string += '# '
        for arg in args:
            string += str(arg)+ '\t'
        string = string[:-1]
        string += '\n'
        child.sketchData += string


    def s_instruction(self, child, *args):
        string = ''
        for arg in args:
            string += str(arg)+ '\t'
        string = string[:-1]
        string += '\n'
        child.sketchData += string

    def prepareItem(self, child):
        child.sketchData = ''
        self.s_comment(child, 'start', child.name)
        self.s_comment(child, 'entity', *child.data() )

        data = child.pltData
        if data != []:
            for i in data:
                dta = np.add(i[::child.pathOrder],child.offset)

                path = self.transformData( dta ,direction=1)
                # print(path)
                x,y = path[0]
                self.s_instruction(child, 'vtip', 0.0)
                self.s_instruction(child, 'xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                self.s_instruction(child, 'vtip', 0.0)
                self.s_instruction(child, 'vtip\t%f' %float(child.volt))
                r = child.rate
                for x,y in path:
                # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                    self.s_instruction(child, 'xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                self.s_instruction(child, 'vtip\t%f' %float(child.volt))
                self.s_instruction(child, 'vtip', 0.0)
                self.s_comment(child, 'end', child.name)

        # creates an empty line
        self.s_instruction(child)


    def sketchAdd(self, data):
        if isinstance(data, list):
            for i in data:
                pass
        elif isinstance(data, str):
            self.sketchList.append(data+'\n')
        elif isinstance(data, sItem):
            self.prepareItem(data)
            self.sketchList.append(data)

    def sketchFinish(self):
        self.sketchFile = '# sketching start\n'
        for data in self.sketchList:
            # print(type(data))
            if isinstance(data, str):
                self.sketchFile += data

            elif isinstance(data, sItem):
                self.sketchFile += data.sketchData
            else:
                raise TypeError

        x0,y0 = self.offset_center
        self.sketchFile += 'xyAbs\t%.4f\t%.4f\t%.3f\n' %(-x0,-y0,self.freerate)
        self.sketchFile += '# sketching end\n'
        # return sketchFile

    def getItem(self,item):
        return self.model.getItem(model.index(item))

    def sketchPrepare(self, root):
        # HEERE!
        # Function receives the root Item of the data-tree

        exec(self.tabSketchScript.getFile())
        # layers = root.childItems

        # # layers = [self.getItem for i in layers]
        # for layer in layers:
        #     if layer.checkState == 0:
        #         continue
        #     self.sketchAdd(sItem(layer))

        #     for child in layer.childItems:
        #         # if child.checkState == 0:
        #         #     continue
        #         # print(child.childItems)
        #         item = sItem(child)
        #         # item.is_closed
        #         # item.fillAngle
        #         # item.fillStep
        #         # item.pathOrder
        #         # item.name
        #         # item.volt
        #         # print(item.volt)
        #         # item.rate
        #         # item.offset
        #         self.sketchAdd(item)




    def sketchNow(self, index=None):
        # self.afmPosition.clear()
        self.afmNow.clear()
        # self.afmAll.clear()
        # self.sketchFile = ''
        self.sketchList = []
        if index == None:
            index = self.model

        self.sketchPrepare(index.rootItem)
        self.sketchFinish()

        self.saveSketch()

        self.log({'dir': str(self.sketchSubFolder)})
        transmit = 'SketchScript %i \n' % len(self.sketchFile)

        log.info('STATUS: subfolder %s'%str(self.sketchSubFolder))
        if demo:
            self.doDemo()
        else:
            self.SocketThread.send_message(transmit + self.sketchFile)

        self.tabSketchData.insertText(self.sketchFile)

    def sComment(self, stuff, prefix=''):
        adding = ''
        adding += '# '
        adding += prefix
        for i in stuff:
            adding += str(i)+ '\t'
        adding += '\n'
        self.sketchFile += adding
        # print( adding )

    def saveSketch(self):
        self.sketchSubFolder = 'sketch_%i'%(self.timer.elapsed()/1000.0)

        if not os.path.exists(self.storeFolder + self.sketchSubFolder):
            os.makedirs(str(self.storeFolder + self.sketchSubFolder))

        self.sketchOutDir = str(self.storeFolder + self.sketchSubFolder+'/')
        fname = self.sketchOutDir + 'out.txt'
        with open(fname, 'w') as f:
            f.write(self.sketchFile)

        fname = self.sketchOutDir + 'SketchScript.py'
        with open(fname, 'w') as f:
            f.write(self.tabSketchScript.getFile())

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


    def sAdd(self, data):
        self.sketchFile += data
        self.sketchFile += '\n'
        # print( data )

    def abortNow(self):
        self.SocketThread.send_message('abort\n')
        log.info('STATUS: Sent abort')

    def shutLithoNow(self):
        self.SocketThread.send_message('shutdown\n')
        log.info('STATUS: Sent shutdown')
        self.SocketThread.disconnectSocket()


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

    def expand(self,layer):
        items = layer.getRows()
        for num, item in enumerate(items):
            self.tree_file.expand(item.index())

    def collapse(self,layer):
        items = layer.getRows()
        for num, item in enumerate(items):
            self.tree_file.collapse(item.index())

    def parseModelSettings(self):
        exec(self.tabParseScript.getFile())



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

        self.tree_file.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        # self.tree_file.setEditTriggers(QtGui.QTreeView.DoubleClicked | QtGui.QAbstractItemView.SelectedClicked)
        for col in ['Closed', 'Show', 'Order']:
            colnum = self.headers.index(col)
            self.tree_file.setItemDelegateForColumn(colnum,CheckBoxDelegate(self, column = col))

        for col in ['Volt', 'Rate', 'Step']:
            colnum = self.headers.index(col)
            self.tree_file.setItemDelegateForColumn(colnum,DoubleSpinBoxDelegate(self))

        self.tree_file.setItemDelegateForColumn(self.model.col('Color'),ColorDelegate(self))



        self.tree_file.expandAll()
        self.parseModelSettings()

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
        # self.pi.addItem(self.afmPosition)
        self.pi.addItem(self.afmNow)
        # self.pi.addItem(self.afmAll)

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
        log.warning('point')

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
        log.warning('X recalc')


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
                    plist = list(entity.points())
                    plist.append(plist[0])
                    data = np.array(plist)[:,:2]
                    design_pltlist.append(data)
                if entity.dxftype() == 'LINE':
                    print(type(entity.points))
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

        self.plotFrame.setAfmImage(angle = self.offset_angle, offset = self.offset_center, updateRange=False  )

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
        self.remulti_calc()

    def remulti_calc(self):

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

    def remulti(self):

        dx = self.multi_dx.value()
        dy = self.multi_dy.value()

        theta = np.arctan2(dy,dx)
        theta *= 180/np.pi

        self.multi_angle.setValue(theta)
        self.multi_distance.setValue(np.sqrt(dx**2 + dy**2))
        # print('in remulti')
        self.remulti_calc()


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
        measureAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'Start Measurement Process', self)
        acceptMeasureAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save Measurement', self)
        favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite', self)
        stopMeasureAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measure', self)
        unloadStageAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/arrow_up_red.png'), 'Unload stage', self)
        loadStageAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/arrow_down.png'), 'Load stage', self)
        reconnectAction       = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/arrow_refresh.png'), 'Reconnect to AFM', self)
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

        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measurementProcess)

        QtCore.QObject.connect(captureAction,          QtCore.SIGNAL('triggered()'), self.doCapture )
        QtCore.QObject.connect(capture_abortAction,    QtCore.SIGNAL('triggered()'), self.doCaptureAbort )
        QtCore.QObject.connect(capture_forceAction,    QtCore.SIGNAL('triggered()'), self.doCaptureForce )
        QtCore.QObject.connect(frame_downAction,       QtCore.SIGNAL('triggered()'), self.doFrameDown )
        QtCore.QObject.connect(frame_upAction,         QtCore.SIGNAL('triggered()'), self.doFrameUp )

        QtCore.QObject.connect(engageAction,           QtCore.SIGNAL('triggered()'), self.doEngage )
        QtCore.QObject.connect(withdrawAction,         QtCore.SIGNAL('triggered()'), self.doWithdraw )

        QtCore.QObject.connect(loadStageAction,        QtCore.SIGNAL('triggered()'), self.stageLoad )
        QtCore.QObject.connect(unloadStageAction,      QtCore.SIGNAL('triggered()'), self.stageUnload )

        QtCore.QObject.connect(reconnectAction,        QtCore.SIGNAL('triggered()'), self.reconnectNow )
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
        plttoolbar.addAction(reconnectAction)
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


    def reconnectNow(self):
        log.info('Reconnect Socket')
        self.SocketThread.connectSocket()

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



    def closeEvent(self,event):
        if demo:
            event.accept()
            return

        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes | QtGui.QMessageBox.No , QtGui.QMessageBox.Yes)
        if reply==QtGui.QMessageBox.No:
            event.ignore()
        else:
            self.SocketThread.send_message('ClientClose\n')
            # print(self.mprocess)
            # print('aaaaa', self.mprocess.state())
            # print('terminate')
            # self.mprocess.terminate()
            # # self.mprocess.waitForFinished()
            # print('finished')
            # print('aaaaa', self.mprocess.state())
            # self.hide()
            self.measure_save()
            # sleep(5)
            # self.mprocess.kill()
            # print(self.mprocess)
            # try:
            #     pass
            #     # self.mprocess.kill()
            # except:
            #     pass
            # try:
            #     self.AFMThread.stop()
            # except:
            #     pass
            # try:
            #     self.SocketThread.stop()
            # except:
            #     pass

            # print('hidden')
            # # print('aaaaa', self.mprocess.state())
            # sleep(5)
            # print('waited')
            # print('aaaaa', self.mprocess.state())
            # print(self.mprocess)
            # self.mprocess.kill()
            # print(self.mprocess)
            # print('aaaaa', self.mprocess.state())
            # self.show()
            # self.close()
            # self.deleteLater()
            event.accept()
            # sys.exit()

    def update_plotting(self):
        self.settings['plot']['plot_timing'] = self.plot_update_time.value()
        pass

    def makeDataset(self):
        pass

    def run(self):

        self.update_plotting()
        self.plot_update_time.valueChanged.connect(self.update_plotting)

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

    def measure_save(self):
        return

    def savicar(self):
        # log.debug('SAVING')
        self.measure_save()
        QtCore.QTimer.singleShot(10 *1000, self.savicar)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    # app.setStyleSheet('stylesheet.qss')

    # css = QtCore.QFile('./stylesheet.qss')
    # css.open(QtCore.QIODevice.ReadOnly)
    # if css.isOpen():
    with open('./stylesheet.css', 'r') as f:
         read_data = f.read()
    # f.closed
    app.setStyleSheet(read_data)
    # css.close()

    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())

    handlers = log.handlers[:]
    for handler in handlers:
        handler.close()
        log.removeHandler(handler)
