#!/usr/bin/env python
demo = False
import sys
sys.path.append(".\\source")

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

import json

with open('config.json', 'r') as f:
    config = json.load(f)
if demo:
    config['storage'] = config['demo_storage']
print(config['storage'])

import multiprocessing as mp
from source.ni_measurement2 import *
from source.buffer import *
from source.ringbuffer2 import *

import os
import time
from time import sleep
import socket

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

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)
        self.timer = QTime.currentTime()
        self.timer.start()

        splash_pix = QtGui.QPixmap(r'./source/splash2.png')
        self.splash = QtGui.QSplashScreen(splash_pix)
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
        self.s_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))

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

        self.cnt = 0
############

        # self.init_measurement()

        self.splash.showMessage("Initialize Plot",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.init_dht_plot()

        self.log('log', 'init')

        # sleep(2)
        self.splash.showMessage("Showing GUI",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        # self.showMaximized()

        frameGm = self.frameGeometry()
        # screen = QtGui.QApplication.desktop().screenNumber(2)
        centerPoint = QtGui.QApplication.desktop().screenGeometry(0).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
        self.showMaximized()

        # self.show()
        self.splash.showMessage("Starting Program",alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.run()
        self.splash.finish(self)

        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        # exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        menubar = self.menuBar()
        mainMenu = menubar.addMenu('&Main')
        mainMenu.addAction(exitAction)

        # self.splitter.setStretchFactor(3,2)




    def initParamTree(self):
        params = [
            {'name': 'Plotting', 'type': 'group', 'children': [
                {'name': 'Enable', 'type': 'bool', 'value': 1},
                {'name': 'Plot Current', 'type': 'bool', 'value': 1},
                {'name': 'Plot 2p', 'type': 'bool', 'value': 1},
                {'name': 'Plot 4p', 'type': 'bool', 'value': 1},
                {'name': 'Plot Timing', 'type': 'float', 'value': 0.15, 'siPrefix': True, 'suffix': 's', 'step':0.05, 'limits': (0, 999.99)},
                {'name': 'Plot DHT', 'type': 'bool', 'value': 1},
                {'name': 'DHT Timing', 'type': 'float', 'value': 0.4, 'siPrefix': True, 'suffix': 's', 'step':0.05, 'limits': (0, 999.99)},
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
              {'name': 'Storage', 'type': 'group', 'expanded': False, 'children': [
                    {'name': 'Folder', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'Subfolder', 'type': 'str', 'value': '', 'readonly': True},
                    {'name': 'Log Prefix', 'type': 'str', 'value': '', 'readonly': True},
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
        pass
        # print('tree changes:')
        # print(param, changes)
        # for param, change, data in changes:
        #     path = self.p.childPath(param)
        #     if path is not None:
        #         childName = '.'.join(path)
        #     else:
        #         childName = param.name()
        #     print('  parameter: %s'% childName)
        #     print('  change:    %s'% change)
        #     print('  data:      %s'% str(data))
        #     print('  ----------')



    def valueChanging(self, param, value):
        return
        print("Value changing (not finalized):", param, value)

    @QtCore.pyqtSlot("QModelIndex")
    def test(self, bla =None):
        print( bla )

    def init_stores(self):
        # c_time = str(QDate.currentDate().toString('yyyy-MM-dd_') + QTime.currentTime().toString('HH-mm-ss'))
        c_time = str(int(self.timer.elapsed()/1000.0))
        # tdelta = self.settings['measure']['time'].elapsed()/1000.0

        self.p.param("Measurements","Storage",'Log Prefix').setValue(c_time)
        if not os.path.exists(self.storeFolder):
            os.makedirs(self.storeFolder)

        nifile = self.storeFolder+c_time +'_ni_data.h5'
        dhtfile = self.storeFolder+c_time +'_dht_data.h5'
        logname = self.storeFolder+c_time +'_logging.h5'

        self.log_store = DataStore(filename=logname)

        self.ni_store_columns = ['time', 'current','r2p','r4p']
        self.ni_store = Buffer(1000000, cols=self.ni_store_columns, filename=nifile)
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

        columns = len(self.dht_store_columns)
        self.dht_buff = RingBuffer(10000, cols = columns)
        self.settings['measure']['dht_buff'] = self.dht_buff

        self.initSerial()

        if not demo:
            self.dht_Worker = dht_Worker(self.settings['measure'])
            self.dht_WorkerThread = None

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

        self.measure_terminate = False
        self.initplot()

    # def start_runner(self):

    def quit_runner(self):
        print('ending')
        self.stopMeasEvent.set()
        self.ni_runner_thread.exit()
        self.ni_runner_thread.wait()
        # print(self.ni_runner_thread.isRunning())

    def handle_msg(self, msg):
        if self.measure_terminate:
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

    @QtCore.pyqtSlot("QString")
    def updateStatus(self,line):
        line = str(line)
        self.statusBar().showMessage(line)


    def addToolbars(self):
        measureAction         = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'New Measurement', self)
        acceptMeasureAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save Measurement', self)
        favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite', self)
        stopMeasureAction     = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measure', self)

        # QtCore.QObject.connect(closeConnectionAction, QtCore.SIGNAL('triggered()'), self.shutLithoNow )


        QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.measure_start )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.start_runner )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.graficar )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.dhticar )
        # QtCore.QObject.connect(measureAction,          QtCore.SIGNAL('triggered()'), self.savicar )
        QtCore.QObject.connect(favoriteMeasureAction,  QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(acceptMeasureAction,    QtCore.SIGNAL('triggered()'), self.measure_save )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.measure_stop )
        QtCore.QObject.connect(stopMeasureAction,      QtCore.SIGNAL('triggered()'), self.quit_runner )


        iconSize = QtCore.QSize(32,32)
        # toolbar = self.addToolBar('Exit')
        # toolbar.setIconSize(iconSize)

        plttoolbar = self.addToolBar('Measurement')
        plttoolbar.addAction(measureAction)
        plttoolbar.addAction(favoriteMeasureAction)
        plttoolbar.addAction(acceptMeasureAction)
        plttoolbar.addAction(stopMeasureAction)


    def measure(self):
        print('in measrue thing')
        pass

    def initSerial(self):
        print('serial init called')
        try:
            print(self.settings['measure']['dht_serial'])
        except:
            pass
        try:
            port = self.p.param('Measurements','Instruments','DHT-arduino','Serial Port').value()
            self.settings['measure']['dht_serial'] = serial.Serial(port-1, baudrate=115200, timeout=5) # opens, too.
            if self.settings['measure']['dht_serial'] != None:
                self.run_dht()
            self.sig_dht_measure.emit(500)

        except:
            print( 'dht failed' )
            self.settings['measure']['dht_serial'] = None
            # QtCore.QTimer.singleShot(5000, self.initSerial)

    def closeEvent(self,event):
        self.quit_runner()
        # self.ni_workerThread.quit()
        if demo:
            event.accept()
            return

        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes | QtGui.QMessageBox.No , QtGui.QMessageBox.Yes)
        if reply==QtGui.QMessageBox.Yes:
            # self.SocketThread.send_message('ClientClose\n')
            # sleep(1)
            # self.SocketThread.stop()

            self.measure_save()
            self.measure_stop()

            try:
                self.ni_workerThread.quit()
            except:
                pass
            try:
                self.dht_WorkerThread.quit()
            except:
                pass
            try:
                self.settings['measure']['dht_serial'].close()
            except:
                pass
            event.accept()
        else:
            event.ignore()


    def run(self):
        self.run_ni()

    def run_dht(self):
        if not demo:
            self.dht_WorkerThread = QtCore.QThread()
            self.dht_Worker.moveToThread(self.dht_WorkerThread)

            self.sig_dht_measure.connect(self.dht_Worker.run)
            self.sig_dht_measure.connect(self.dhticar)
            self.sig_dht_measure_stop.connect(self.dht_Worker.stop)

            self.dht_WorkerThread.start()

    def run_ni(self):
        return
        # if not demo:
        # self.ni_workerThread = QtCore.QThread()
        # self.ni_worker.moveToThread(self.ni_workerThread)

        # self.sig_measure.connect(self.ni_worker.run)
        # self.sig_measure_stop.connect(self.ni_worker.stop)

        # self.ni_workerThread.start()

    def savicar(self):
        if not self.measure_terminate:
            self.measure_save()
        QtCore.QTimer.singleShot(5000, self.savicar)

    def measure_start(self):
        print('measure_start')

        self.ni_runner_thread.start()

        if self.newstores == True:
            self.init_stores()
            self.newstores = False

        # if self.settings['measure']['dht_serial'] == None:
        #     self.initSerial()

        self.init_measurement()

        self.sig_measure.emit(500)
        self.sig_dht_measure.emit(500)

        # self.measure_terminate = True


    def measure_stop(self):
        self.measure_terminate = True
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
        # return

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
        if self.settings['measure']['dht_buff'].size > 0 and not self.measure_terminate:
            raw_buffer = self.settings['measure']['dht_buff'].get_partial_clear()
            # dtime = time
            # raw_buffer[1] = raw_buffer[1]
            # raw_buffer[2] = raw_buffer[2]
            self.dht_store.append(raw_buffer[0:2])

            self.p.param("Measurements","Current Data",'Temperature').setValue(raw_buffer[1].mean())
            self.p.param("Measurements","Current Data",'Humidity').setValue(raw_buffer[2].mean())

            self.tplot.setData(x=self.dht_store.get_partial()[0], y=self.dht_store.get_partial()[1])
            self.hplot.setData(x=self.dht_store.get_partial()[0], y=self.dht_store.get_partial()[2])


            self.dht_pi.legend.items = []
            self.dht_pi.legend.addItem(self.hplot, 'Humidity' + ' = ' + '%.1f %%RH' % raw_buffer[2].mean())
            self.dht_pi.legend.addItem(self.tplot, 'Temperature' + ' = ' + '%.1f ' % raw_buffer[1].mean() +u"\u00b0"+'C')

        # if not self.measure_terminate:
        QtCore.QTimer.singleShot(self.p.param('Plotting', 'DHT Timing').value()*1000, self.dhticar)

    def initplot(self):
        print('initplot')
        start_buffer = np.zeros((1,4))
        time =    start_buffer[:,0]
        current = start_buffer[:,1]
        r2pt =    start_buffer[:,2]
        r4pt =    start_buffer[:,3]

        self.pltG_pi.clear()
        self.pltR_pi.clear()

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
        # n = 1
        # self.plotlist[-1]['Current1'].setData(x=time, y=current)
        # # self.plotlist[-1]['Current1'].setPen(color=kelly_colors[colors[n]])
        # self.plotlist[-1]['Current2'].setData(x=time, y=current)
        # # self.plotlist[-1]['Current2'].setPen(color=kelly_colors[colors[n]])

        # n = 2
        # self.plotlist[-1]['R2pt'].setData(x=time, y=r2pt)
        # self.plotlist[-1]['R2pt'].setPen(color=kelly_colors[colors[n]])

        # n = 3
        # self.plotlist[-1]['R4pt'].setData(x=time, y=r4pt)
        # self.plotlist[-1]['R4pt'].setPen(color=kelly_colors[colors[n]])

        # g2pt = 1.0/r2pt
        # g4pt = 1.0/r4pt

        # n = 2
        # self.plotlist[-1]['G2pt'].setData(x=time, y=g2pt)
        # self.plotlist[-1]['G2pt'].setPen(color=kelly_colors[colors[n]])
        # n = 4
        # self.plotlist[-1]['G4pt'].setData(x=time, y=g4pt)
        # self.plotlist[-1]['G4pt'].setPen(color=kelly_colors[colors[n]])

        # for c in self.plotlist:
        #     for nme in self.plotR_names:
        #         print(c[nme].data.shape)


    def graficar(self):

        if self.p.param('Plotting', 'Enable').value() and not self.measure_terminate:

            raw_buffer = self.ni_store.get()
            current_buffer = raw_buffer[self.ni_plot_counter:]


            mc = raw_buffer[-100:,1].mean()
            mr2 = raw_buffer[-100:,2].mean()
            mr4 = raw_buffer[-100:,3].mean()

            self.p.param("Measurements","Current Data",'Current').setValue('%.1f nA' % (mc*1e9))
            self.p.param("Measurements","Current Data",'R2pt').setValue('%.1f kOhm' % (mr2*1e-3))
            self.p.param("Measurements","Current Data",'R4pt').setValue('%.1f kOhm' % (mr4*1e-3))
            self.p.param("Measurements","Current Data",'G2pt').setValue('%.1f uS' % ((1.0/mr2)*1e6))
            self.p.param("Measurements","Current Data",'G4pt').setValue('%.1f uS' % ((1.0/mr4)*1e6))


                        # self.p.param("Measurements","Current Data",'Humidity').setValue(raw_buffer[2].mean())

            self.pltR_pi.legend.items = []
            self.pltR_pi.legend.addItem(self.plotlist[-1]['Current1'], 'Current' + ' = ' + '%.1f nA' % (mc*1e9))
            self.pltR_pi.legend.addItem(self.plotlist[-1]['R2pt'], 'R2pt' + ' = ' + '%.1f kOhm' % (mr2*1e-3))
            self.pltR_pi.legend.addItem(self.plotlist[-1]['R4pt'], 'R4pt' + ' = ' + '%.1f kOhm' % (mr4*1e-3))

            self.pltG_pi.legend.items = []
            self.pltG_pi.legend.addItem(self.plotlist[-1]['Current2'], 'Current' + ' = ' + '%.1f nA' % (mc*1e9))
            self.pltG_pi.legend.addItem(self.plotlist[-1]['G2pt'], 'G2pt' + ' = ' + '%.1f uS' % ((1.0/mr2)*1e6))
            self.pltG_pi.legend.addItem(self.plotlist[-1]['G4pt'], 'G4pt' + ' = ' + '%.1f uS' % ((1.0/mr4)*1e6))

            if current_buffer.shape[0] >2:
                time =    current_buffer[:,0]
                # self.pltR_pi.set
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
                    # self.pltR_pi.set
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

        QtCore.QTimer.singleShot(self.p.param('Plotting', 'Plot Timing').value()*1000 , self.graficar)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())
