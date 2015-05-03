# D:\Projects\lithocontrol>python -m cProfile -s cumulative -o profile.pstats NIdaq4.py
# D:\Projects\lithocontrol>gprof2dot -f pstats profile.pstats | dot -Tsvg -o nidaq4.svg

from PyQt4 import QtCore, QtGui,uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime, QTimer
import pyqtgraph as pg
import numpy as np

import pandas as pd

import datetime
from datetime import datetime as dt

import time

# from functools import partial
from Queue import Queue
# import math
import sys
# import time

# https://github.com/clade/PyDAQmx/tree/master/PyDAQmx/example
from PyDAQmx import *
from PyDAQmx.DAQmxCallBack import *
from numpy import zeros
import scipy.fftpack

from PyDAQmx import Task
import ringbuffer as ringbuffer
import cProfile

def process_data(data, f, fs):
    '''Perform lock-in analysis and save results in memory'''
    phi = 2*numpy.pi*f * numpy.array(range(len(data[0]))) / float(fs)
    sini = (numpy.sin(phi) * data).sum(axis=1)
    cosi = (numpy.cos(phi) * data).sum(axis=1)
    amplitudes = 2 * numpy.sqrt(sini**2 + cosi**2) / float(len(phi))
    # amplitudes[1:] = (amplitudes[1:] / amplitudes[0])
    # amplitudes[0] = amplitudes[0]
    phases = numpy.arctan2(cosi, sini)
    phases[1:] = phases[1:] - phases[0]
    normphases = numpy.mod(phases + numpy.pi, 2 * numpy.pi) - numpy.pi
    return (amplitudes, normphases)


class Worker(QtCore.QObject):

    terminate = pyqtSignal()

    def __init__(self, settings, parent=None):

        super(Worker, self).__init__(parent)
        self.settings = settings
        DAQmxResetDevice("PCI-6251")
        self.task = MeasureTask(self.settings)

    def run(self):
        self.task.StartTask()

    def wave_start(self,val):
        pass

    def settings_update(self, settings):
        pass


##################################################################


class MeasureTask(Task):
    def __init__(self, settings):
        Task.__init__(self)
        self.running = False
        self.settings = settings

        self.settings['time'].start()


        # self.settings['buffer_size'] = 10000000
        # self.settings['acq_rate'] = 50000          # samples/second
        # self.settings['acq_samples'] = 10000        # every n samples

        self.acq_samples = self.settings['acq_samples']

        ###################################
        self.ch_in_list = self.settings['in'].keys()

        self.num_chans = len(self.ch_in_list)
        print self.num_chans
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
        integration_time = 0.1 #seconds
        self.li_buff_length = int(self.settings['acq_rate']*integration_time*self.num_chans)
        self.li_buffer = np.zeros((self.num_chans,1))

        self.freq_buffer = ringbuffer.RingBuffer((1, 31))
        self.freq = 0.0
        self.T =1.0 / self.settings['acq_rate']


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



class DataCollection():
    def __init__(self, buffer_size = 100, num_chans = 1):
        self.settings = settings

        self.buffer = ringbuffer.RingBuffer((num_chans, buffer_size))

    def get_partial(self):
        return self.buffer.get_partial()

    def get_all(self):
        return self.buffer.get_all()

    def append(self,value):
        self.buffer.append(value)


# class MeasureData():
#     def __init__(self, buffer_size = 100000, columns = ['Data'], extend_num = 1000):
#         self.buffer_size = buffer_size
#         self.columns = columns
#         self.extend_num = extend_num

#         tempdata = np.zeros((self.buffer_size,len(self.columns)))
#         self.index = 0
#         self._data = pd.DataFrame(data=tempdata, columns = self.columns, dtype=float)

#     def get(self):
#         return self._data[:self.index]

#     def extend(self, rows):
#         tempdata = np.zeros((rows,len(self.columns)))
#         data = pd.DataFrame(data=tempdata, columns = self.columns, dtype=float)
#         self._data = pd.concat([self._data, data], axis=0, ignore_index=True)
#         self.buffer_size+=rows


#     def append(self, value):
#         if self.index >= self.buffer_size:
#             self.extend(self.extend_num)
#         self._data.iloc[self.index] = value
#         self.index +=1






###############################################################

class MainWindow(QtGui.QMainWindow):

    sig_measure = pyqtSignal(int)
    sig_wave_start = pyqtSignal(int)
    sig_settings_update = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('daqlayout2.ui', self)
        self.terminate = False
        self.actionExit.triggered.connect(QtGui.qApp.quit)

        self.settings = {}
        self.settings['time'] = QTime()
        # self.settings['acq_plot'] = True
        # self.settings['li_plot'] = True
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
        ch0['lockin'] = False
        ch0['plot_raw'] = True
        ch0['li_tc'] = 0.1
        ch0['li_buffer'] = ringbuffer.RingBuffer((4, self.settings['buffer_size']/10))
        ch0['fft_arr'] = np.array([])
        ch0['freq_chan'] = 0

        ch1['channel'] = "ai1"
        ch1['name'] = 'A-B'
        ch1['amplitude'] = 1*1e-3
        amplification = 0.001/10.0
        ch1['multiplier'] = amplification
        ch1['min'] = -10
        ch1['max'] = 10
        ch1['lockin'] = False
        ch1['plot_raw'] = True
        ch1['li_tc'] = 0.1
        ch1['li_buffer'] = ringbuffer.RingBuffer((4, self.settings['buffer_size']/10))
        ch1['fft_arr'] = np.array([])
        ch1['freq_chan'] = 0
        ch1['curr_amp'] = 0

        # ch2['channel'] = "ai2"
        # ch2['name'] = 'Current'
        # ch2['curr_amp'] = -8
        # ch2['multiplier'] = 10**ch2['curr_amp']
        # ch2['min'] = -10
        # ch2['max'] = 10
        # ch2['lockin'] = True
        # ch2['plot_raw'] = True
        # ch2['li_tc'] = 0.1
        # ch2['li_buffer'] = ringbuffer.RingBuffer((4, self.settings['buffer_size']/100))
        # ch2['fft_arr'] = np.array([])
        # ch2['freq_chan'] = 0

        # ch3['channel'] = "ai3"
        # ch3['min'] = -10
        # ch3['max'] = 10
        # ch3['lockin'] = True
        # ch3['plot_raw'] = False
        # ch3['li_tc'] = 0.1
        # ch3['li_buffer'] = ringbuffer.RingBuffer((3, self.settings['buffer_size']/100))
        # ch3['fft_arr'] = np.array([])
        # ch3['freq_chan'] = 0
        # ch3['curr_amp'] = ch1['curr_amp']


        self.freqSpinBox.setValue(self.settings['out'][0]['freq'])
        self.amplSpinBox.setValue(self.settings['out'][0]['ampl'])
        self.cAmpSpinBox.setValue(self.settings['in'][0]['curr_amp'])
        p = MeasureData(3,['time','A','B'],3)
        # (self._gen_meas_amplitude, self._normamplitudes, self._normphases)
        self.li_buff = ringbuffer.RingBuffer((5, self.settings['buffer_size']/1000))

        self.buff = ringbuffer.RingBuffer((len(self.settings['in'])+1, 36000))
        self.settings['buff'] = self.buff
        self.settings['li_buff'] = self.li_buff

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

    def makeDataset(self):
        pass

    def run(self):
        self.workerThread = QtCore.QThread()
        self.worker.terminate.connect(self.setterminate)
        self.worker.moveToThread(self.workerThread)
        self.btn_measure.clicked.connect(self.measure_start)
        self.btn_measure.clicked.connect(self.graficar)
        self.btn_stop.clicked.connect(self.measure_stop)

        self.check_lockin.stateChanged.connect(self.update_plotting)
        self.check_rawdata.stateChanged.connect(self.update_plotting)
        self.plot_update_time.valueChanged.connect(self.update_plotting)

        self.freqSpinBox.valueChanged.connect(self.settings_update)
        self.amplSpinBox.valueChanged.connect(self.settings_update)
        self.cAmpSpinBox.valueChanged.connect(self.settings_update)

        self.sig_measure.connect(self.worker.run)
        self.sig_settings_update.connect(self.worker.settings_update)

        self.workerThread.start()

        self.show()

    def update_plotting(self):
        if self.check_lockin.checkState() == 2:
            self.settings['li_plot'] = True
        else:
            self.settings['li_plot'] = False
        if self.check_rawdata.checkState() == 2:
            self.settings['acq_plot'] = True
        else:
            self.settings['acq_plot'] = False
        self.settings['plot_timing'] = self.plot_update_time.value()

    def settings_update(self):
        freq = self.freqSpinBox.value()
        ampl = self.amplSpinBox.value()
        cAmp = self.cAmpSpinBox.value()
        self.settings['out'][0]['freq'] = freq
        self.settings['out'][0]['ampl'] = ampl
        self.settings['in'][1]['curr_amp']= cAmp
        self.sig_settings_update.emit(self.settings)

    def measure_start(self):
        self.terminate = False
        self.sig_measure.emit(500)

    def measure_stop(self):
        self.terminate = True

    def setterminate(self):
        self.terminate = True

    def graficar(self):


        if True:
            self.plot_counter +=1


            raw_buffer = self.settings['buff'].get_partial()

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
