# D:\Projects\lithocontrol>python -m cProfile -s cumulative -o profile.pstats NIdaq4.py
# D:\Projects\lithocontrol>gprof2dot -f pstats profile.pstats | dot -Tsvg -o nidaq4.svg


# add:
# - temperature
# - humidity
# - vtip (measure? might be more accurate... test rpc first)
# - sketch-object ( ID, start, end )
# - exact start time from session
# - start and end from sketch object
# - sketch-id (also save everything with that ID: cad, afm image, schedule)
# - cuttng start / cutting end
# - type comments and save them with timing

# - python array for data storage
# - pandas store for storing data every 1 minute?



from PyQt4 import QtCore, QtGui,uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime, QTimer
import pyqtgraph as pg
import numpy as np

import pandas as pd
import serial
import datetime
from datetime import datetime as dt

import time

import sys

# https://github.com/clade/PyDAQmx/tree/master/PyDAQmx/example
from PyDAQmx import *
from PyDAQmx.DAQmxCallBack import *
from numpy import zeros
import scipy.fftpack

from PyDAQmx import Task
import ringbuffer as ringbuffer
# import cProfile

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
###############################################################

class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_measure_stop = pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('daqlayout2.ui', self)
        self.ni_terminate = False

        self.plotlist = []
        self.settings = {}
        self.settings['time'] = QTime()
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

        self.buff = ringbuffer.RingBuffer((len(self.settings['in'])+1, 2000))
        self.settings['buff'] = self.buff
        self.store_columns = ['time', 'current','r2p','r4p']
        self.store = ringbuffer.RingBuffer((len(self.store_columns), 360000), filename='store_data.h5')


        self.dht_buff = ringbuffer.RingBuffer((3, 2000))
        self.settings['dht_buff'] = self.dht_buff

        self.dht_store_columns = ['time', 'temperature', 'humidity']
        self.dht_store = ringbuffer.RingBuffer((len(self.dht_store_columns), 360000), filename='store_dht.h5')


        self.ni_worker = ni_Worker(self.settings)
        self.ni_workerThread = None

        self.dht_Worker = dht_Worker(self.settings)
        self.dht_WorkerThread = None


        self.pi = self.plotView.getPlotItem()
        self.pi.addLegend()
        self.pi_legend = self.pi.legend
        self.pi.enableAutoRange('x', True)
        # self.pi.setXRange(990000, 1000000)
        self.pi.enableAutoRange('y', True)
        # li_data = np.array([[gen_meas_amplitude], [normamplitudes], [normphases], [li_r/1e6], [li_g]])
        self.pi_names = ['ch0','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9',]
        for i in range(5):
            self.plotlist.append({'plot': self.pi.plot(name=self.pi_names[i]), 'channel': i})


        self.resize(800, 700)

    def initSerial(self):
        try:
            self.settings['dht_serial'] = serial.Serial(self.settings['DHTport']-1, baudrate=115200, timeout=5) # opens, too.
            try:
                self.dht_WorkerThread.quit()
            except:
                pass
            self.dht_Worker = dht_Worker(self.settings)
            self.dht_WorkerThread = QtCore.QThread()
            self.dht_Worker.moveToThread(self.dht_WorkerThread)
            self.dht_WorkerThread.start()
            # self.dht_Worker.run()

            self.sig_measure.connect(self.dht_Worker.run)
            self.sig_measure_stop.connect(self.dht_Worker.stop)
        except:
            print 'dht failed'
            self.settings['dht_serial'] = None
            pass

    def closeEvent(self,event):
        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if reply==QtGui.QMessageBox.Yes:
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

        self.btn_measure.clicked.connect(self.measure_start)
        self.btn_measure.clicked.connect(self.graficar)
        self.btn_stop.clicked.connect(self.measure_stop)

        self.check_plot.stateChanged.connect(self.update_plotting)
        self.check_2pt.stateChanged.connect(self.update_plotting)
        self.check_4pt.stateChanged.connect(self.update_plotting)
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
        self.ni_terminate = False
        self.sig_measure.emit(500)

    def measure_stop(self):
        self.store.save_data()
        self.dht_store.save_data()
        self.ni_terminate = True
        self.sig_measure_stop.emit(500)

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

            self.store.append([d_time, current, r2pt, r4pt])

        if self.settings['dht_buff'].size > 0:
            raw_buffer = self.settings['dht_buff'].get_partial_clear()
            a = raw_buffer[0].mean()
            b = raw_buffer[1].mean()
            c = raw_buffer[2].mean()
            self.dht_store.append([a,b,c])
            self.text_temp.setText('Tmp: %.1f\xb0C'%(raw_buffer[1].mean()))
            self.text_hum.setText('Hum: %.1f%%'%(raw_buffer[2].mean()))

        if self.settings['acq_plot']:
            if self.store.size>1:
                n = 0
                self.plot_counter +=1
                raw_buffer = self.store.get_partial()

                d_time = raw_buffer[0]
                current = raw_buffer[1]

                n += 1
                av_len = -10
                if self.plot_counter>11:
                    self.pi_legend.items = []

                if self.settings['plot_current'] == True:
                    if self.plot_counter>11:

                        try:
                            av_curr = np.average(current[av_len:])*1e9
                            self.pi_legend.addItem(self.plotlist[n]['plot'], 'Current' + ' = ' + '%.2f nA' % av_curr)
                        except:
                            self.pi_legend.addItem(self.plotlist[n]['plot'], 'Current')
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
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt' + ' = ' + '%.1f kOhm' % av_2pt)
                            except:
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=r2pt/1000.0)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

                    n += 1
                    if self.settings['plot_4pt'] == True:
                        if self.plot_counter>11:

                            self.plot_counter = 0
                            try:
                                av_4pt = np.average(r4pt[av_len:])/1000.0
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt' + ' = ' + '%.1f kOhm' % av_4pt)
                            except:
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt')
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
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'g2pt' + ' = ' + '%.1f uS' % av_2pt)
                            except:
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'g2pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=g2pt)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

                    n += 1
                    if self.settings['plot_4pt'] == True:
                        if self.plot_counter>11:

                            self.plot_counter = 0
                            try:
                                av_4pt = np.average(g4pt[av_len:])
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'g4pt' + ' = ' + '%.1f uS' % av_4pt)
                            except:
                                self.pi_legend.addItem(self.plotlist[n]['plot'], 'g4pt')
                                pass

                        self.plotlist[n]['plot'].setData(x=d_time, y=g4pt)
                        self.plotlist[n]['plot'].setPen(color=kelly_colors[colors[n]])

        if not self.ni_terminate:
            QtCore.QTimer.singleShot(self.settings['plot_timing'], self.graficar)


def run():
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()

    QtCore.QTimer.singleShot(0, window.run)

    sys.exit(app.exec_())




if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()

    QtCore.QTimer.singleShot(0, window.run)

    sys.exit(app.exec_())
