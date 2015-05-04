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


from PyQt4 import QtCore, QtGui,uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime, QTimer
import pyqtgraph as pg
import numpy as np

import pandas as pd

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

class Worker(QtCore.QObject):

    terminate = pyqtSignal()

    def __init__(self, settings, parent=None):

        super(Worker, self).__init__(parent)
        self.settings = settings
        DAQmxResetDevice("PCI-6251")
        self.task = MeasureTask(self.settings)
        self.running = False

    def run(self):
        if self.running == False:
            self.running = True
            self.task.StartTask()

    def stop(self):
        self.task.StopTask()
        self.running = False
        # self.task.ClearTask()

##################################################################


class MeasureTask(Task):
    def __init__(self, settings):
        Task.__init__(self)
        self.running = False
        self.settings = settings

        self.settings['time'].start()
        self.acq_samples = self.settings['acq_samples']

        ###################################
        self.ch_in_list = self.settings['in'].keys()

        self.num_chans = len(self.ch_in_list)
        self.ch_out = []
        self.data_buffer = {}
        for i in self.ch_in_list:
            chan = self.settings['device_input']+ '/' + self.settings['in'][i]['channel']
            self.create_chan(chan, self.settings['in'][i]['min'], self.settings['in'][i]['max'])
            print 'created ', chan

        self.CfgSampClkTiming("", self.settings['acq_rate'], DAQmx_Val_Rising,
                              DAQmx_Val_ContSamps, self.settings['buffer_size'])
        self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer,
                                            self.acq_samples, 0)
        self.AutoRegisterDoneEvent(0)

    def create_chan(self, chan, v_min=-10, v_max=10):
        self.CreateAIVoltageChan( chan,
                                  "",
                                  DAQmx_Val_Diff,
                                  v_min,
                                  v_max,
                                  DAQmx_Val_Volts,
                                  None)

    def EveryNCallback(self):
        read = int32()
        if self.running:
            # This is to have at least some samples in the buffer. else one might read more samples than available, EveryNSamplesEvent is x +- 100 samples!
            data = zeros(5*self.num_chans*self.acq_samples)
            self.ReadAnalogF64(-1,
                               -1,
                               DAQmx_Val_GroupByChannel,
                               data,
                               data.size,
                               byref(read),
                               None)
        else:
            self.running = True
            data = zeros(10*self.num_chans*self.acq_samples)
            self.ReadAnalogF64(-1,
                               -1,
                               DAQmx_Val_GroupByChannel,
                               data,
                               data.size,
                               byref(read),
                               None)
        meas_data = np.reshape(data[:read.value*self.num_chans],(self.num_chans,-1))

        av_data = np.mean(meas_data,1)

        av_data = av_data.reshape((self.num_chans,-1))
        tdelta = self.settings['time'].elapsed()/1000.0
        self.settings['buff'].append([tdelta,av_data[0],av_data[1]])
        return 0  # The function should return an integer

    def DoneCallback(self, status):
        # print "Status", status.value
        return 0  # The function should return an integer


class MeasureData():
    def __init__(self, buffer_size = 10000, columns = ['Data']):
        self.buffer_size = buffer_size
        self.columns = columns
        self.hasfile = False

        tempdata = np.zeros((self.buffer_size,len(self.columns)))
        self.index = 0
        self._buffer = pd.DataFrame(data=tempdata, columns = self.columns)

    def saveData(self):
        if not self.hasfile:
            self._store = self._buffer

    def get(self):
        return self._buffer[:self.index]

    def extend(self, rows):
        tempdata = np.zeros((rows,len(self.columns)))
        data = pd.DataFrame(data=tempdata, columns = self.columns)
        self._buffer = pd.concat([self._buffer, data], axis=0, ignore_index=True)
        self.buffer_size+=rows


    def append(self, value):
        if self.index >= self.buffer_size:
            self.extend(self.extend_num)
        self._buffer.iloc[self.index] = value
        self.index +=1



###############################################################

class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_measure_stop = pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('daqlayout2.ui', self)
        self.terminate = False

        self.settings = {}
        self.settings['time'] = QTime()
        self.update_plotting()
        self.plot_counter = 0

        self.settings['buffer_size'] = 10000000
        self.settings['acq_rate'] = 30000          # samples/second
        self.settings['acq_samples'] = 1000        # every n samples
        self.settings['device_input'] = "PCI-6251"

        self.settings['in'] = {}
        ch0 = self.settings['in'][0] = {}
        ch1 = self.settings['in'][1] = {}
        # ch2 = self.settings['in'][2] = {}
        # ch3 = self.settings['in'][3] = {}

        # ch2['curr_amp'] = -8


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


        self.cAmpSpinBox.setValue(self.settings['in'][0]['curr_amp'])
        # (self._gen_meas_amplitude, self._normamplitudes, self._normphases)

        self.buff = ringbuffer.RingBuffer((len(self.settings['in'])+1, 2000))
        self.settings['buff'] = self.buff
        self.store_columns = ['time', 'current','r2p','r4p']
        self.store = ringbuffer.RingBuffer((len(self.store_columns), 360000))


        self.worker = Worker(self.settings)

        self.workerThread = None


        self.pi = self.plotView.getPlotItem()
        self.pi.addLegend()
        self.pi_legend = self.pi.legend
        self.pi.enableAutoRange('x', True)
        # self.pi.setXRange(990000, 1000000)
        self.pi.enableAutoRange('y', True)
        self.plotlist = []
        # li_data = np.array([[gen_meas_amplitude], [normamplitudes], [normphases], [li_r/1e6], [li_g]])
        self.pi_names = ['ch0','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9',]
        for i in range(5):
            self.plotlist.append({'plot': self.pi.plot(name=self.pi_names[i]), 'channel': i})

        self.colors = ['vivid_yellow','strong_purple','vivid_orange','very_light_blue','vivid_red','grayish_yellow','medium_gray','vivid_green','strong_purplish_pink','strong_blue','strong_yellowish_pink','strong_violet','vivid_orange_yellow','strong_purplish_red','vivid_greenish_yellow','strong_reddish_brown','vivid_yellowish_green','deep_yellowish_brown','vivid_reddish_orange','dark_olive_green']
        self.kelly_colors = dict(vivid_yellow=(255, 179, 0),
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

        self.resize(800, 700)

    def closeEvent(self,event):
        reply=QtGui.QMessageBox.question(self,'Message',"Are you sure to quit?",QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if reply==QtGui.QMessageBox.Yes:
            self.measure_stop()
            self.workerThread.quit()

            event.accept()
        else:
            event.ignore()

    def makeDataset(self):
        pass

    def run(self):
        self.workerThread = QtCore.QThread()
        self.worker.terminate.connect(self.setterminate)
        self.worker.moveToThread(self.workerThread)
        self.btn_measure.clicked.connect(self.measure_start)
        self.btn_measure.clicked.connect(self.graficar)
        self.btn_stop.clicked.connect(self.measure_stop)

        self.check_rawdata.stateChanged.connect(self.update_plotting)
        self.plot_update_time.valueChanged.connect(self.update_plotting)


        self.sig_measure.connect(self.worker.run)
        self.sig_measure_stop.connect(self.worker.stop)

        self.workerThread.start()

        self.show()

    def update_plotting(self):
        if self.check_rawdata.checkState() == 2:
            self.settings['acq_plot'] = True
        else:
            self.settings['acq_plot'] = False
        self.settings['plot_timing'] = self.plot_update_time.value()

    def measure_start(self):
        self.terminate = False
        self.sig_measure.emit(500)

    def measure_stop(self):
        self.terminate = True
        self.sig_measure_stop.emit(500)

    def setterminate(self):
        self.terminate = True


    def daticar(self):
        raw_buffer = self.settings['buff'].get_partial_clear()

        if raw_buffer.size > 0:

            d_time = raw_buffer[0]
            d_ch0 = raw_buffer[1]
            d_ch1 = raw_buffer[2]

            current = np.abs(d_ch0*self.settings['in'][0]['multiplier'])
            r2pt = np.abs(self.settings['in'][0]['amplitude'] / current)
            g2pt = 1.0/r2pt


            a_b = d_ch1*self.settings['in'][1]['multiplier']
            r4pt = np.abs(a_b / current)
            g4pt = 1.0/r4pt

            self.store.append([d_time, current, r2pt, r4pt])



    if not self.terminate:
        QtCore.QTimer.singleShot(self.settings['plot_timing'], self.daticar)

    def graficar(self):


        if True:
            self.plot_counter +=1


            raw_buffer = self.store.get_partial()

            if raw_buffer.size > 10:

                d_time = raw_buffer[0]
                d_ch0 = raw_buffer[1]
                d_ch1 = raw_buffer[2]

                current = np.abs(d_ch0*self.settings['in'][0]['multiplier'])
                r2pt = np.abs(self.settings['in'][0]['amplitude'] / current)
                g2pt = 1.0/r2pt


                a_b = d_ch1*self.settings['in'][1]['multiplier']
                r4pt = np.abs(a_b / current)
                g4pt = 1.0/r4pt

                n=0
                # for n in range(len(self.settings['in'].keys())):
                #     if self.settings['in'][n]['plot_raw']:

                #         self.pi_legend.addItem(self.plotlist[n]['plot'], 'ai' + str(n) + ' = ' + '%.2e' % np.average(raw_buffer[n][-20:]))

                #         self.plotlist[n]['plot'].setData(y=av_data[n], name=self.settings['in'][n]['name'])
                #         self.plotlist[n]['plot'].setPen(color=self.kelly_colors[self.colors[n]])

                n += 1
                av_len = -10
                if self.plot_counter>11:
                    self.pi_legend.items = []

                    try:
                        av_curr = np.average(current[av_len:])*1e9
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'Current' + ' = ' + '%.2f nA' % av_curr)
                    except:
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'Current')
                        pass

                self.plotlist[n]['plot'].setData(x=d_time, y=current*1e9)
                self.plotlist[n]['plot'].setPen(color=self.kelly_colors[self.colors[n]])
                n += 1
                if self.plot_counter>11:
                    try:
                        av_2pt = np.average(r2pt[av_len:])/1000.0
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt' + ' = ' + '%.1f kOhm' % av_2pt)
                    except:
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'R2pt')
                        pass

                self.plotlist[n]['plot'].setData(x=d_time, y=r2pt/1000.0)
                self.plotlist[n]['plot'].setPen(color=self.kelly_colors[self.colors[n]])

                n += 1
                if self.plot_counter>11:

                    self.plot_counter = 0
                    try:
                        av_4pt = np.average(r4pt[av_len:])/1000.0
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt' + ' = ' + '%.1f kOhm' % av_4pt)
                    except:
                        self.pi_legend.addItem(self.plotlist[n]['plot'], 'R4pt')
                        pass

                self.plotlist[n]['plot'].setData(x=d_time, y=r4pt/1000.0)
                self.plotlist[n]['plot'].setPen(color=self.kelly_colors[self.colors[n]])

        if not self.terminate:
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
