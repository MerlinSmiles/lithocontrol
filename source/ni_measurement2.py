import numpy as np

import multiprocessing as mp
from multiprocessing import Queue
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime

import time

import sys, os

demo = False
try:
    # https://github.com/clade/PyDAQmx/tree/master/PyDAQmx/example
    from PyDAQmx import *
    # from PyDAQmx import Task
    from PyDAQmx.DAQmxCallBack import *
except:
    print('DAQmx Demo')
    demo = True


class Runner(QtCore.QObject):

    new_data = QtCore.pyqtSignal(object)

    def __init__(self, start_signal, stopMeasEvent, timer=None, parent=None):
        super(Runner, self).__init__(parent)
        self.stopMeasEvent = stopMeasEvent
        self.queue = Queue()
        self.timer = timer
        start_signal.connect(self._run)

    def _run(self):
        self.stopMeasEvent.clear()
        self.p = ni_Worker(self.queue, self.stopMeasEvent, timer=self.timer)
        self.p.start()
        self.get()

    def get(self):
        # print('inget')
        if self.stopMeasEvent.is_set():
            self.p.join()
            print('Measurement Process ended')
        else:
            msg = self.queue.get()
            self.new_data.emit(msg)
            QtCore.QTimer.singleShot(0, self.get)

class ni_Worker(mp.Process):
    def __init__(self, resultQueue, stopMeasEvent, timer=None):
        super(ni_Worker, self).__init__()
        if timer is None:
            timer = QTime.currentTime()
            timer.start()
        self.timer = timer

        print(timer.elapsed())

        self.resultQueue = resultQueue
        self.stopMeasEvent = stopMeasEvent
        print("initializing DAQ-process")

        self.settings = {}
        self.settings['buffer_size'] = 10000000
        self.settings['acq_rate'] = 50000          # samples/second
        self.settings['acq_samples'] = 1000        # every n samples
        self.settings['device'] = "PCI-6251"
        self.settings['channels'] = [[0,-10,10],[1,-10,10],[2,-10,10],[3,-10,10]]
        self.nChannels = len(self.settings['channels'])
        self.data = np.zeros(self.nChannels+1)

    def run(self):
        if demo:
            while not self.stopMeasEvent.is_set():
                time.sleep(0.04)
                self.data[0] = self.timer.elapsed()/1000.0
                self.data[1:] = np.random.rand(self.nChannels)
                # print('xx', self.data)
                self.resultQueue.put(self.data)
            return

        DAQmxResetDevice("PCI-6251")
        self.task = MeasureTask( self.resultQueue , self.settings )
        self.task.StartTask()

        while not self.stopMeasEvent.is_set():
            time.sleep(1)
            # commandQueue.get() to update settings
            # self.resultQueue.put('m')

        self.task.StopTask()
        self.task.ClearTask()
        print("DAQ-process %s jsut ended" % os.getpid())
        return

if not demo:
    class MeasureTask(Task):
        def __init__(self, resultQueue= None, settings = None):
            Task.__init__(self)
            self.running = False
            self.resultQueue = resultQueue
            self.tdelta = 0.0


            self.acq_samples = settings['acq_samples']

            self.num_chans = len(settings['channels'])
            self.ch_out = []

            for i in settings['channels']:
                chan = settings['device']+ '/ai' + str(i[0])
                self.create_chan(chan, i[1], i[2])
                # print( 'created ', chan )

            self.CfgSampClkTiming("", settings['acq_rate'], DAQmx_Val_Rising,
                                  DAQmx_Val_ContSamps, settings['buffer_size'])
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
                data = np.zeros(5*self.num_chans*self.acq_samples)
                self.ReadAnalogF64(-1,
                                   -1,
                                   DAQmx_Val_GroupByChannel,
                                   data,
                                   data.size,
                                   byref(read),
                                   None)
            else:
                self.running = True
                data = np.zeros(10*self.num_chans*self.acq_samples)
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

            # print('callback')

            # tdelta = settings['time'].elapsed()/1000.0
            # if self.tdelta<=tdelta:
                # self.tdelta = tdelta
            self.resultQueue.put(av_data)
            # print(np.array([av_data[0],av_data[1]]))
            # self.resultQueue.append(np.array([av_data[0],av_data[1]]))
            # settings['buff'].append(np.array([av_data[0],av_data[1]]))
            return 0  # The function should return an integer

        def DoneCallback(self, status):
            # print( "Status", status.value )
            return 0  # The function should return an integer


class dht_Worker(QtCore.QObject):

    terminate = pyqtSignal()

    def __init__(self, settings, parent=None):

        super(dht_Worker, self).__init__(parent)
        self.settings = settings
        self.running = True
        if self.settings['dht_serial'] != None:
            print( "Monitoring serial port " + self.settings['dht_serial'].name )
            self.running = True

    def run(self):
        data = ''
        while (self.running == True):
            if (self.settings['dht_serial'] == None):
                sleep(3)
            else:
                try:
                    self.settings['dht_serial'].write('READ:HUM:TEMP')
                    ch = self.settings['dht_serial'].readline()
                    if len(ch) != 0:
                        data = ch
                        if data.startswith('DHT:'):
                            data = data.split()
                            humidity = float(data[1])
                            temperature = float(data[2])
                            if (humidity>9) and (temperature>9 ):
                                tdelta = self.settings['time'].elapsed()/1000.0
                                self.settings['dht_buff'].append([tdelta, temperature, humidity])
                except:
                    pass

    def update(self,settings):
        self.settings = settings
        # self.running = False
        # if self.settings['dht_serial'] != None:
        #     print( "Monitoring serial port " + self.settings['dht_serial'].name )
            # self.running = True


    def stop(self):
        self.running = False
        try:
            self.settings['dht_serial'].close()
        except:
            pass




##################################################################




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

