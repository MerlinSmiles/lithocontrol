#!/usr/bin/env python
# unicode characters http://archive.oreilly.com/pub/a/xml/excerpts/unicode-explained/tables-writing-characters.html
demo = False
import sys, getopt
sys.path.append(".\\source")

import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import numpy as np
from pprint import pprint


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate, QDateTime
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.dockarea as pg_dock

import shutil

import json

with open('config.json', 'r') as f:
    config = json.load(f)
if demo:
    config['storage'] = config['demo_storage']
print(config['storage'])

import multiprocessing as mp
from source.ni_measurement2 import *
from source.dht_measurement import *
from source.buffer import *
from source.ringbuffer2 import *

import os
import time
from time import sleep
# import socket
import serial

from source.helpers import *
from source.socketworker import *
from source.DataStore import *
# from source.treeclass import *
from source.niPlotFrame import *
# from source.afmHandler import AFMWorker
from source.settingstree import *


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


class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_dht_measure = pyqtSignal(int)
    sig_measure_stop = pyqtSignal(int)
    sig_dht_measure_stop = pyqtSignal(int)

    def __init__(self, parent=None, time=None):

        super(MainWindow, self).__init__(parent)

        if time==None:
            print('No time received')
            self.dateTime = QDateTime.currentDateTime()
        else:
            self.dateTime = QDateTime.fromString(time, 'yyyy-MM-dd HH:mm:ss.zzz')
            # print('Got time')
        print(self.dateTime.toPyDateTime())

        self.timer = self.dateTime.time()
        self.dater = self.dateTime.date()

        self.s_time = str(self.dateTime.toString('yyyy-MM-dd_HH-mm-ss'))
        print(self.s_time)

        frameGm = self.frameGeometry()
        # screen = QtGui.QApplication.desktop().screenNumber(2)
        centerPoint = QtGui.QApplication.desktop().screenGeometry(1).center()
        # centerPoint = screen.center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


        splash_pix = QtGui.QPixmap(r'./source/splash2.png')
        self.splash = QtGui.QSplashScreen(splash_pix)
        # self.splash.moveCenter(centerPoint)
        self.splash.move(frameGm.topLeft())
        # adding progress bar
        # progressBar = QProgressBar(self.splash)
        self.splash.setMask(splash_pix.mask())
        self.splash.show()
        self.splash.showMessage("Loading GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)


        uic.loadUi('mainwindow_ni.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool (Measurement)')

        screen = QtGui.QDesktopWidget().screenGeometry()
        # self.setGeometry(0, 0, screen.width(), screen.height())
        self.setGeometry(int(screen.width()/3), int(screen.height()/3), screen.width()/2, screen.height()/2)


        self.setWindowState(self.windowState() & QtCore.Qt.WindowMaximized)

        # self.setGeometry(200,100,900,800)
        self.plotFrame = niPlotFrame()
        self.plotSplitter.addWidget(self.plotFrame)
        # self.splitter.setStretch(1,1)

        self.splitter.setSizes([50,1000])
        self.initParamTree()

        self.addToolbars()
        # self.show()
        # Set delegate

        self.splash.showMessage("Loading Settings",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        # self.colorModel = ColorModel()
        self.colorList = colors
        self.colorDict = kelly_colors
        # self.colorModel.addColors(self.colorList, self.colorDict)

        self.settings = {}
        self.settings['measure'] = {}
        self.settings['measure']['time'] = QTime()
        self.settings['measure']['time'].start()
        print( '' )
        print('make time of main and this program synced')
        print( '' )

        self.p.param("Measurements","Storage",'Folder').setValue(config['storage']['storeFolder'])
        self.p.param("Measurements","Storage",'Subfolder').setValue(self.s_time)

        self.storeFolder = config['storage']['storeFolder'] + self.s_time + '/'

        self.splash.showMessage("Loading Stores",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_stores()
        self.newstores = False

        self.splash.showMessage("Initialize Measurement",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

############
        self.stopMeasEvent = mp.Event()
        self.ni_runner_thread = QtCore.QThread()
        self.ni_runner = Runner(start_signal=self.ni_runner_thread.started, stopMeasEvent=self.stopMeasEvent, timer=self.timer)
        self.ni_runner.new_data.connect(self.handle_msg)
        self.ni_runner.moveToThread(self.ni_runner_thread)
        self.sig_measure.connect(self.ni_runner_thread.start)
        self.sig_measure_stop.connect(self.ni_runner.stop)
        # self.ni_runner_thread.start()
        self.sig_measure.emit(500)
        self.cnt = 0



        # self.dht_stopMeasEvent = mp.Event()
        # self.dht_runner_thread = QtCore.QThread()
        # self.dht_runner = DhtRunner(start_signal=self.dht_runner_thread.started, stopMeasEvent=self.dht_stopMeasEvent, timer=self.timer, port=5)
        # self.dht_runner.new_data.connect(self.handle_msg_dht)
        # self.dht_runner.moveToThread(self.dht_runner_thread)
        # self.dht_runner_thread.start()
        # self.dht_cnt = 0


        self.initSerial()
        self.init_dht_plot()

        self.dht_Worker = dht_Worker(self.dht_serial, self.dht_store, self.timer)
        # self.dht_WorkerThread = None
        self.dht_WorkerThread = QtCore.QThread()
        self.dht_Worker.moveToThread(self.dht_WorkerThread)

        self.sig_dht_measure.connect(self.dht_Worker.run)
        # self.sig_dht_measure.connect(self.dhticar)
        self.sig_dht_measure_stop.connect(self.dht_Worker.stop)

        self.dht_WorkerThread.start()

        self.sig_dht_measure.emit(500)

        # columns = len(self.dht_store_columns)
        # self.dht_buff = RingBuffer(10000, cols = columns)
        # self.settings['measure']['dht_buff'] = self.dht_store

############

        # self.init_measurement()

        self.splash.showMessage("Initialize Plot",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.log('log', 'init')


        # self.show()

        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        # exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        menubar = self.menuBar()
        mainMenu = menubar.addMenu('&Main')
        mainMenu.addAction(exitAction)

        self.measurement_pause = True


        # self.splitter.setStretchFactor(3,2)




        self.init_measurement()
        # if self.newstores == True:
        # self.init_stores()
        # self.newstores = False



        # self.splash.showMessage("Initialize SocketWorker",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # self.SocketThread = SocketWorker(host = 'localhost', port = 23456)
        # self.SocketThread.new_data.connect(self.socket_msg)
        # self.SocketThread.monitor()




        # sleep(2)
        self.splash.showMessage("Showing GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # self.showMaximized()

        self.move(frameGm.topLeft())
        self.showMaximized()
        self.splash.showMessage("Starting Program",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.run()
        self.splash.finish(self)

        self.savicar()
        self.graficar()
        self.dhticar()

        # if self.settings['measure']['dht_serial'] == None:
        #     self.initSerial()


        # if self.measurement_pause:
        # print('########', self.ni_store.get().shape)

        # self.SocketThread.send_message('Capture\n')




    def initSerial(self):
        print('serial init called')
        try:
            print(self.settings['measure']['dht_serial'])
        except:
            pass
        try:
            port = self.p.param('Measurements','Instruments','DHT-arduino','Serial Port').value()
            self.dht_serial = serial.Serial(port-1, baudrate=115200, timeout=5) # opens, too.
            # if self.dht_serial != None:
                # self.run_dht()
            # self.sig_dht_measure.emit(500)

        except:
            print( 'dht failed' )
            self.dht_serial = None
            # QtCore.QTimer.singleShot(5000, self.initSerial)


    def initParamTree(self):
        params = [
            {'name': 'Plotting', 'type': 'group', 'children': [
                {'name': 'Enable', 'type': 'bool', 'value': 1},
                {'name': 'Plot Current', 'type': 'bool', 'value': 1},
                {'name': 'Plot 2p', 'type': 'bool', 'value': 1},
                {'name': 'Plot 4p', 'type': 'bool', 'value': 1},
                {'name': 'Plot Timing', 'type': 'float', 'value': 0.15, 'siPrefix': True, 'suffix': 's', 'step':0.01, 'limits': (0, 1000)},
                {'name': 'R-limit', 'type': 'float', 'value': 1e8, 'siPrefix': True, 'suffix': 'ohm', 'step':1000, 'limits': (0, np.inf)},
                {'name': 'G-limit', 'type': 'float', 'value': 100e-6, 'siPrefix': True, 'suffix': 'S', 'step':1000, 'limits': (0, np.inf)},
                {'name': 'Plot DHT', 'type': 'bool', 'value': 1},
                {'name': 'DHT Timing', 'type': 'float', 'value': 0.4, 'siPrefix': True, 'suffix': 's', 'step':0.01, 'limits': (0, 1000)},
            ]},
            {'name': 'Measurements', 'type': 'group', 'children': [
              {'name': 'Current Data', 'type': 'group', 'children': [
                    {'name': 'Temperature', 'type': 'float', 'value': 20.1, 'siPrefix': True, 'suffix': '\xb0C', 'readonly': True},
                    {'name': 'Humidity', 'type': 'float', 'value': 11.1, 'siPrefix': True, 'suffix': '%', 'readonly': True},
                    {'name': 'Current', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'R2pt', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'R4pt', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'G2pt', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'G4pt', 'type': 'str', 'value': '', 'readonly': True},
                    # {'name': 'GMMM', 'type': 'float', 'value': 11.1, 'siPrefix': True, 'suffix': 'A', 'readonly': True},
              ]},
              {'name': 'Storage', 'type': 'group', 'expanded': True, 'children': [
                    {'name': 'Folder', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'Subfolder', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'Logfile prefix', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'Saving interval', 'type': 'float', 'value': 10, 'siPrefix': True, 'suffix': 's', 'step':1, 'limits': (5, 10000)},
                    {'name': 'Last saved', 'type': 'str', 'value': '', 'readonly': True},
              ]},
              {'name': 'Instruments', 'type': 'group', 'expanded': False, 'children': [
                {'name': 'DHT-arduino', 'type': 'group', 'children': [
                      {'name': 'Serial Port', 'type': 'int', 'value': 5},
                ]},
                {'name': 'SR-LockIn', 'type': 'group', 'children': [
                      {'name': 'Sensitivity', 'type': 'float', 'value': 10e-09, 'suffix': 'A'},
                      {'name': 'Amplitude', 'type': 'float', 'value': 1e-3, 'suffix': 'V'},
                ]},
                {'name': 'PAR-LockIn', 'type': 'group', 'expanded': False, 'children': [
                      {'name': 'Sensitivity', 'type': 'float', 'value': 1.0e-3, 'suffix': 'V'},
                ]},
              ]},
            ]},
        ]
        self.p = Parameter.create(name='params', type='group', children=params)
        self.p.sigTreeStateChanged.connect(self.change)
        # Too lazy for recursion:
        for child in self.p.children():
            child.sigValueChanging.connect(self.valueChanging)
            for ch2 in child.children():
                ch2.sigValueChanging.connect(self.valueChanging)

        t = ParameterTree()
        t.setIndentation(10)
        t.setParameters(self.p, showTop=False)
        t.setWindowTitle('pyqtgraph example: Parameter Tree')


        self.tree_splitter.insertWidget(0, t)

    def change(self, param, changes):
        for param, change, data in changes:
            path = self.p.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
            # print('  parameter: %s'% childName)
            # print('  change:    %s'% change)
            # print('  data:      %s'% str(data))
            # print('  ----------')
            if childName == 'Plotting.R-limit':
                self.pltR_pi.setLimits(yMax=self.p.param("Plotting",'R-limit').value())
            elif childName == 'Plotting.G-limit':
                self.pltG_pi.setLimits(yMax=self.p.param("Plotting",'G-limit').value())

        pass
        # print('tree changes:')
        # print(param, changes)



    def valueChanging(self, param, value):
        return
        print("Value changing (not finalized):", param, value)

    @QtCore.pyqtSlot("QModelIndex")
    def test(self, bla =None):
        print( bla )

    def init_stores(self):
        print('init_stores')
        # c_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))
        c_time = str(int(self.timer.elapsed()/1000.0))
        # tdelta = self.settings['measure']['time'].elapsed()/1000.0

        self.p.param("Measurements","Storage",'Logfile prefix').setValue(c_time)
        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)

        nifile = self.storeFolder+c_time +'_ni_data.h5'
        dhtfile = self.storeFolder+c_time +'_dht_data.h5'
        logname = self.storeFolder+c_time +'_log-data.h5'

        self.log_store = DataStore(filename=logname, columns=['time', 'log'])

        self.ni_store_columns = ['time', 'current','r2p','r4p']
        self.ni_store = Buffer(3600000, cols=self.ni_store_columns, filename=nifile)
        self.ni_stepper = 1000
        self.ni_plot_counter = 0

        self.dht_store_columns = ['time', 'temperature', 'humidity']
        self.dht_store = Buffer(3600000, cols = self.dht_store_columns, filename=dhtfile)


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

        # self.SocketThread = SocketWorker()
        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMpos(float, float, float)"), self.updateAFMpos)
        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("READY"), self.afmReady)
        # QtCore.QObject.connect(self.SocketThread, QtCore.SIGNAL("AFMStatus(QString)"), self.updateStatus)
        # self.SocketThread.monitor()

    def init_measurement(self):
        print('init_measurement')
        self.stopMeasEvent.clear()
        # self.dht_stopMeasEvent.clear()

        # self.initSerial()

        self.pltR_pi = self.plotFrame.mResistanceeasurePlot.getPlotItem()
        self.pltR_pi.clear()
        self.pltR_pi.setClipToView(True)
        # self.pltR_pi.setDownsampling(auto = True)

        self.pltR_pi.addLegend()
        # alignment=QtCore.Qt.AlignHCenter
        self.pltR_pi.enableAutoRange('x', True)
        self.pltR_pi.enableAutoRange('y', True)
        # self.pltR_pi.setXRange(990000, 1000000)

        self.pltG_pi = self.plotFrame.mConductancePlot.getPlotItem()
        self.pltR_pi.clear()
        self.pltG_pi.setClipToView(True)

        self.pltG_pi.setXLink(self.pltR_pi)
        self.pltG_pi.addLegend()
        # self.pltG_pi.enableAutoRange('x', True)
        self.pltG_pi.enableAutoRange('y', True)

        self.pltR_pi.setLimits(yMin=0, yMax=self.p.param("Plotting",'R-limit').value())
        self.pltG_pi.setLimits(yMin=0, yMax=self.p.param("Plotting",'G-limit').value())

        # li_data = np.array([[gen_meas_amplitude], [normamplitudes], [normphases], [li_r/1e6], [li_g]])
        self.pltR_pi_names = ['ch0','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9',]
        self.plotR_names = ['Current1', 'R2pt', 'R4pt']
        self.plotG_names = ['Current2', 'G2pt', 'G4pt']
        # for i in range(5):
        #     self.plotlist.append({'plot': self.pltR_pi.plot(name=self.pltR_pi_names[i]), 'channel': i})

        # for nme in self.plotR_names:
        #     self.plotlist[-1][nme] = self.pltR_pi.plot(name=nme)
        # for nme in self.plotG_names:
        #     self.plotlist[-1][nme] = self.pltG_pi.plot(name=nme)

        self.initplot()

    # def start_runner(self):

    def quit_runner(self):
        print('ending')
        self.stopMeasEvent.set()
        print('set')
        # self.dht_stopMeasEvent.set()
        self.ni_runner_thread.exit()
        print('exit')
        self.ni_runner_thread.wait()
        print('wait')
        # print(self.ni_runner_thread.isRunning())

    def handle_msg(self, msg):
        if self.measurement_pause:
            return
        time, ch0, ch1, ch2, ch3 = msg

        srsens = self.p.param("Measurements",'Instruments', "SR-LockIn", "Sensitivity").value()/10
        srampl = self.p.param("Measurements",'Instruments', "SR-LockIn", "Amplitude").value()
        parsens = self.p.param("Measurements",'Instruments', "PAR-LockIn", "Sensitivity").value()/10

        current = np.abs(ch0*srsens)
        # print(current)
        r2pt = np.abs(float(srampl) / current)
        a_b = ch1*parsens
        r4pt = np.abs(a_b / current)

        data = [time, current, r2pt, r4pt]
        self.ni_store.append(data)
        self.cnt += 1

    def handle_msg_dht(self, msg):
        # if self.measurement_pause:
        #     return
        data = msg
        self.dht_store.append(data)
        self.dht_cnt += 1

    # def socket_msg(self, msg):
    #     print(msg)
        # if self.measurement_pause:
        #     return
        # data = msg
        # self.dht_store.append(data)
        # self.dht_cnt += 1


    @QtCore.pyqtSlot("QString")
    def updateStatus(self,line):
        line = str(line)
        self.statusBar().showMessage(line)


    def addToolbars(self):
        measureAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'Start Measurement', self)
        acceptMeasureAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save Measurement now', self)
        # favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite', self)
        stopMeasureAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measurement', self)

        # QtCore.QObject.connect(closeConnectionAction, QtCore.SIGNAL('triggered()'), self.shutLithoNow )


        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measure_start )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.start_runner )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.graficar )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.dhticar )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.savicar )
        # QtCore.QObject.connect(favoriteMeasureAction,  QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(acceptMeasureAction,    QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.measure_stop )
        # QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.quit_runner )


        iconSize = QtCore.QSize(32,32)
        # toolbar = self.addToolBar('Exit')
        # toolbar.setIconSize(iconSize)

        plttoolbar = self.addToolBar('Measurement')
        plttoolbar.addAction(measureAction)
        # plttoolbar.addAction(favoriteMeasureAction)
        plttoolbar.addAction(acceptMeasureAction)
        plttoolbar.addAction(stopMeasureAction)


    def measure(self):
        print('in measrue thing')
        pass


    def closeEvent(self,event):

        self.sig_measure_stop.emit(50)

        # splash_pix = QtGui.QPixmap(r'./source/splash2.png')
        # self.splash = QtGui.QSplashScreen(splash_pix)
        # adding progress bar
        # progressBar = QProgressBar(self.splash)
        # self.splash.setMask(splash_pix.mask())

        self.splash.show()
        # self.hide()
        self.splash.showMessage("Closing",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.splash.showMessage("measure_save",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.measure_save()

        self.splash.showMessage("quit_runner",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # print(event)
        self.quit_runner()
        self.splash.showMessage("measure_stop",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.measure_stop()
        self.splash.showMessage("ni_runner_thread",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        try:
            self.ni_runner_thread.quit()
        except:
            pass
        self.splash.showMessage("dht_WorkerThread",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        try:
            self.dht_WorkerThread.quit()
        except:
            pass
        self.splash.showMessage("dht_serial",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        try:
            self.dht_serial.close()
        except:
            pass

        self.splash.showMessage("Cleaning up",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.splash.finish(self)
        # time.sleep(5)
        # reply=QtGui.QMessageBox.question(self,'Message',"Closing!",QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

        # reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes | QtGui.QMessageBox.No , QtGui.QMessageBox.Yes)
        # if reply==QtGui.QMessageBox.Yes:
        event.accept()

        # self.ni_workerThread.quit()
        # if demo:
        #     event.accept()
        #     return





    def run(self):
        self.run_ni()

    # def run_dht(self):

    #     self.dht_Worker = dht_Worker(self.settings['measure'])
    #     self.dht_WorkerThread = QtCore.QThread()
    #     # self.dht_Worker.terminate.connect(sig_dht_measure_stop)
    #     self.dht_Worker.moveToThread(self.dht_WorkerThread)
    #     self.sig_dht_measure.connect(self.dht_Worker.run)
    #     self.sig_dht_measure.connect(self.dhticar)
    #     self.sig_dht_measure_stop.connect(self.dht_Worker.stop)

    #     self.dht_WorkerThread.start()
    #     self.dhticar()

    def run_ni(self):
        return
        # if not demo:
        # self.ni_workerThread = QtCore.QThread()
        # self.ni_worker.moveToThread(self.ni_workerThread)

        # self.sig_measure.connect(self.ni_worker.run)
        # self.sig_measure_stop.connect(self.ni_worker.stop)

        # self.ni_workerThread.start()

    def savicar(self):
        if not self.measurement_pause:
            self.measure_save()
        QtCore.QTimer.singleShot(self.p.param("Measurements","Storage",'Saving interval').value()*1000, self.savicar)

    def measure_start(self):
        print('measure_start')

        if self.newstores == True:
            # self.pltR_pi.clear()
            # self.pltG_pi.clear()
            self.initplot()
            self.init_stores()
            self.newstores = False

        self.measurement_pause = False


    def measure_stop(self):
        self.measurement_pause = True
        self.newstores = True
        # self.sig_measure_stop.emit(500)
        # self.sig_dht_measure_stop.emit(500)
        # try:
        #     self.ni_store.clear()
        #     self.ni_buff.clear()
        # except:
        #     print( 'Error clearing ni_store' )
        #     print( sys.exc_info() )
        # try:
        #     # self.dht_store.clear()
        #     # self.dht_buff.clear()
        #     pass
        # except:
        #     print( 'Error clearing dht_store' )
        #     print( sys.exc_info() )


    def measure_save(self):
        self.ni_store.save_data()
        self.dht_store.save_data()
        self.log_store.save_data()
        self.p.param("Measurements","Storage",'Last saved').setValue(self.timer.elapsed()/1000 )
        # return

    def init_dht_plot(self):
        self.dht_pi = self.plotFrame.dhtPlot.getPlotItem()
        self.dht_pi.clear()
        self.dht_pi.addLegend()
        self.dht_pi.enableAutoRange('x', True)
        self.dht_pi.enableAutoRange('y', True)

        self.dht_pi.setLabel('left', u'Hum (%)  -  Temp (\u00b0C)')

        self.dht_pi.showGrid(1,1,0.3)

        self.hplot = pg.PlotDataItem()
        self.tplot = pg.PlotDataItem()
        self.hplot.setPen(color=kelly_colors['vivid_green'])
        self.tplot.setPen(color=kelly_colors['vivid_orange'])
        self.dht_pi.addItem(self.hplot)
        self.dht_pi.addItem(self.tplot)

    def dhticar(self):
        if self.p.param('Plotting', 'Plot DHT').value():
            raw_buffer = self.dht_store.get()

            time = raw_buffer[:,0]
            temp = raw_buffer[:,1]
            humi = raw_buffer[:,2]

            if len(temp) > 10:
                self.p.param("Measurements","Current Data",'Temperature').setValue(temp[-10:].mean())
                self.p.param("Measurements","Current Data",'Humidity').setValue(humi[-10:].mean())

            self.tplot.setData(x=time, y=temp)
            self.hplot.setData(x=time, y=humi)


            if len(temp) > 10:
                self.dht_pi.legend.items = []
                self.dht_pi.legend.addItem(self.tplot, 'Temperature' + ' = ' +  '%.1f ' % temp[-10:].mean() +u"\u00b0"+'C')
                self.dht_pi.legend.addItem(self.hplot, 'Humidity' + ' = ' + '%.1f %%' % humi[-10:].mean())
            else:
                self.dht_pi.legend.items = []
                self.dht_pi.legend.addItem(self.tplot, 'Temperature')
                self.dht_pi.legend.addItem(self.hplot, 'Humidity')

        # if not self.measurement_pause:
        QtCore.QTimer.singleShot(self.p.param('Plotting', 'DHT Timing').value()*1000, self.dhticar)

    def initplot(self):
        # print('initplot')
        start_buffer = np.zeros((1,4))
        time =    start_buffer[:,0]
        current = start_buffer[:,1]
        r2pt =    start_buffer[:,2]
        r4pt =    start_buffer[:,3]

        self.pltG_pi.clear()
        self.pltR_pi.clear()
# (axis, text=None, units=None, unitPrefix=None, **args)
        self.pltR_pi.setLabel('left', 'Resistance', u'\u03a9')
        self.pltG_pi.setLabel('left', 'Conductance', 'S')

        self.pltR_pi.showGrid(1,1,0.3)
        self.pltG_pi.showGrid(1,1,0.3)
        self.plotlist = []


        self.plotlist.append({})
        self.plotlist.append({})

        for n, nme in enumerate(self.plotR_names):
            # print(self.ni_plot_counter, nme)
            # if self.ni_plot_counter == 0:
            #     label = nme
            # else:
            color = kelly_colors[colors[n+1]]
            self.plotlist[-1][nme] = self.pltR_pi.plot(pen = color)
            # color = kelly_colors[colors[n+5]]
            self.plotlist[-2][nme] = self.pltR_pi.plot(pen = color)
        for n, nme in enumerate(self.plotG_names):
            # if self.ni_plot_counter < 0:
            #     label = nme
            # else:
            color = kelly_colors[colors[n+1]]
            self.plotlist[-1][nme] = self.pltG_pi.plot(pen = color)
            # color = kelly_colors[colors[n+5]]
            self.plotlist[-2][nme] = self.pltG_pi.plot(pen = color)

        self.ni_plot_counter = 0


    def graficar(self):
        # print('graficar')
        if not self.measurement_pause:
            if self.p.param('Plotting', 'Enable').value():

                raw_buffer = self.ni_store.get()
                current_buffer = raw_buffer[self.ni_plot_counter:]


                if len(raw_buffer[:,0]) > 100:
                    mc = raw_buffer[-100:,1].mean()
                    mr2 = raw_buffer[-100:,2].mean()
                    mr4 = raw_buffer[-100:,3].mean()

                    self.p.param("Measurements","Current Data",'Current').setValue('%.1f nA' % (mc*1e9))
                    self.p.param("Measurements","Current Data",'R2pt').setValue(u'%.1f k\u03a9' % (mr2*1e-3))
                    self.p.param("Measurements","Current Data",'R4pt').setValue(u'%.1f k\u03a9' % (mr4*1e-3))
                    self.p.param("Measurements","Current Data",'G2pt').setValue(u'%.1f \u00b5S' % ((1.0/mr2)*1e6))
                    self.p.param("Measurements","Current Data",'G4pt').setValue(u'%.1f \u00b5S' % ((1.0/mr4)*1e6))

                    self.pltR_pi.legend.items = []
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['Current1'], 'Current' + ' = ' + '%.1f nA' % (mc*1e9))
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['R2pt'], 'R2pt' + ' = ' + u'%.1f k\u03a9' % (mr2*1e-3))
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['R4pt'], 'R4pt' + ' = ' + u'%.1f k\u03a9' % (mr4*1e-3))

                    self.pltG_pi.legend.items = []
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['Current2'], 'Current' + ' = ' + '%.1f nA' % (mc*1e9))
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['G2pt'], 'G2pt' + ' = ' + u'%.1f \u00b5S' % ((1.0/mr2)*1e6))
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['G4pt'], 'G4pt' + ' = ' + u'%.1f \u00b5S' % ((1.0/mr4)*1e6))
                else:
                    self.p.param("Measurements","Current Data",'Current').setValue('')
                    self.p.param("Measurements","Current Data",'R2pt').setValue('')
                    self.p.param("Measurements","Current Data",'R4pt').setValue('')
                    self.p.param("Measurements","Current Data",'G2pt').setValue('')
                    self.p.param("Measurements","Current Data",'G4pt').setValue('')

                    self.pltR_pi.legend.items = []
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['Current1'], 'Current')
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['R2pt'], 'R2pt')
                    self.pltR_pi.legend.addItem(self.plotlist[-1]['R4pt'], 'R4pt')

                    self.pltG_pi.legend.items = []
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['Current2'], 'Current')
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['G2pt'], 'G2pt')
                    self.pltG_pi.legend.addItem(self.plotlist[-1]['G4pt'], 'G4pt')

                if current_buffer.shape[0] >2:
                    time =    current_buffer[:,0]
                    current = current_buffer[:,1]
                    r2pt =    current_buffer[:,2]
                    r4pt =    current_buffer[:,3]
                    g2pt = 1.0/r2pt
                    g4pt = 1.0/r4pt

                    if self.p.param('Plotting', 'Plot Current').value() == True:
                        n = 1
                        self.plotlist[-1]['Current1'].setData(x=time, y=current)
                        self.plotlist[-1]['Current2'].setData(x=time, y=current)

                    if self.p.param('Plotting', 'Plot 2p').value() == True:
                        n = 2
                        self.plotlist[-1]['R2pt'].setData(x=time, y=r2pt)
                        self.plotlist[-1]['G2pt'].setData(x=time, y=g2pt)

                    if self.p.param('Plotting', 'Plot 4p').value() == True:
                        n = 3
                        self.plotlist[-1]['R4pt'].setData(x=time, y=r4pt)
                        self.plotlist[-1]['G4pt'].setData(x=time, y=g4pt)

                    if current_buffer.shape[0] > self.ni_stepper:
                        self.ni_plot_counter += current_buffer.shape[0]-3
                        # self.initplot()
                        # print('newplot')
                        time =    raw_buffer[:,0]
                        current = raw_buffer[:,1]
                        r2pt =    raw_buffer[:,2]
                        r4pt =    raw_buffer[:,3]
                        g2pt = 1.0/r2pt
                        g4pt = 1.0/r4pt

                        if self.p.param('Plotting', 'Plot Current').value() == True:
                            n = 1
                            self.plotlist[-2]['Current1'].setData(x=time, y=current)
                            self.plotlist[-2]['Current2'].setData(x=time, y=current)

                        if self.p.param('Plotting', 'Plot 2p').value() == True:
                            n = 2
                            self.plotlist[-2]['R2pt'].setData(x=time, y=r2pt)
                            self.plotlist[-2]['G2pt'].setData(x=time, y=g2pt)

                        if self.p.param('Plotting', 'Plot 4p').value() == True:
                            n = 3
                            self.plotlist[-2]['R4pt'].setData(x=time, y=r4pt)
                            self.plotlist[-2]['G4pt'].setData(x=time, y=g4pt)

        # if self.measurement_pause:
        #     print('******', self.ni_store.get().shape)
        #     for i in self.plotlist:
        #         print(i)
        #         for nme in i.keys():
        #             i[nme].setData(x=[0],y=[0])

        # if not self.measurement_pause:
        QtCore.QTimer.singleShot(self.p.param('Plotting', 'Plot Timing').value()*1000 , self.graficar)


if __name__ == '__main__':
    argv = sys.argv[1:]
    time = None
    try:
        opts, args = getopt.getopt(argv,"t:",["time="])
    except getopt.GetoptError:
        pass
    for opt, arg in opts:
        if opt in ("-t", "--time"):
            time = arg

    app = QtGui.QApplication(sys.argv)
    window = MainWindow(time=time)
    # window.show()
    sys.exit(app.exec_())
