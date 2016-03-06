import numpy as np

import multiprocessing as mp
from multiprocessing import Queue
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime

import time

import sys, os
import serial

demo = False



class dht_Worker(QtCore.QObject):

    terminate = pyqtSignal()

    def __init__(self, serial, dht_buffer, timer=None, parent=None):

        super(dht_Worker, self).__init__(parent)
        self.serial = serial
        self.dht_buffer = dht_buffer
        self.timer = timer
        self.running = True
        if self.serial != None:
            print( "Monitoring serial port " + self.serial.name )
            self.running = True

    def run(self):
        data = ''
        while (self.running == True):
            if (self.serial == None):
                time.sleep(3)
            else:
                try:
                    self.serial.write('READ:HUM:TEMP')
                    ch = self.serial.readline()
                    if len(ch) != 0:
                        data = ch
                        if data.startswith('DHT:'):
                            data = data.split()
                            humidity = float(data[1])
                            temperature = float(data[2])
                            if (humidity>9) and (temperature>9 ):
                                tdelta = self.timer.elapsed()/1000.0
                                self.dht_buffer.append(np.array([tdelta, temperature, humidity]))
                                # print(np.array([tdelta, temperature, humidity]))
                except:
                    pass

    def update(self,settings):
        self.settings = settings
        # self.running = False
        # if self.serial != None:
        #     print( "Monitoring serial port " + self.serial.name )
            # self.running = True


    def stop(self):
        self.running = False
        try:
            self.serial.close()
        except:
            pass





# class DhtRunner(QtCore.QObject):

#     new_data = QtCore.pyqtSignal(object)

#     def __init__(self, start_signal, stopMeasEvent, port, timer=None, parent=None):
#         super(DhtRunner, self).__init__(parent)
#         self.stopMeasEvent = stopMeasEvent
#         self.queue = Queue()
#         self.timer = timer
#         self.port = port
#         start_signal.connect(self._run)

#     def _run(self):
#         self.stopMeasEvent.clear()
#         self.p = dht_Worker(self.queue, self.stopMeasEvent, timer=self.timer, port=self.port)
#         self.p.start()
#         self.get()

#     def get(self):
#         # print('inget')
#         if self.stopMeasEvent.is_set():
#             self.p.join()
#             print('Measurement Process ended')
#         else:
#             msg = self.queue.get()
#             self.new_data.emit(msg)
#             QtCore.QTimer.singleShot(0, self.get)




# class dht_Worker(QtCore.QObject):

#     terminate = pyqtSignal()

#     def __init__(self, settings, parent=None):

#         super(dht_Worker, self).__init__(parent)
#         self.settings = settings
#         self.running = True
#         if self.serial != None:
#             print( "Monitoring serial port " + self.serial.name )
#             self.running = True

    # def run(self):
        #

    # def update(self,settings):
    #     self.settings = settings
    #     # self.running = False
    #     # if self.serial != None:
    #     #     print( "Monitoring serial port " + self.serial.name )
    #         # self.running = True


    # def stop(self):
    #     self.running = False
    #     try:
    #         self.serial.close()
    #     except:
    #         pass



# class dht_Worker(mp.Process):
#     def __init__(self, resultQueue, stopMeasEvent, port, timer=None):
#         super(dht_Worker, self).__init__()
#         if timer is None:
#             timer = QTime.currentTime()
#             timer.start()
#         self.timer = timer
#         self.port = port
#         self.serial = None



#         try:
#             self.serial = serial.Serial(self.port-1, baudrate=115200, timeout=5) # opens, too.
#         except:
#             print( 'dht failed' )
#             self.serial = None

#         print(self.serial)


#         self.resultQueue = resultQueue
#         self.stopMeasEvent = stopMeasEvent
#         print("initializing DHT-process")

#         self.nChannels = 2
#         self.data = np.zeros(self.nChannels+1)
#         # self.initSerial()

#     def run(self):
#         if demo:
#             while not self.stopMeasEvent.is_set():
#                 time.sleep(0.04)
#                 self.data[0] = self.timer.elapsed()/1000.0
#                 self.data[1:] = np.random.rand(self.nChannels)
#                 self.resultQueue.put(self.data)
#             return

#         while not self.stopMeasEvent.is_set():
#             time.sleep(0.05)
#             if self.serial == None:
#                 time.sleep(3)
#             else:
#                 # try:
#                 self.serial.write('READ:HUM:TEMP')
#                 response = self.serial.readline()
#                 if len(response) != 0:
#                     data = response
#                     if data.startswith('DHT:'):
#                         data = data.split()
#                         print(data)
#                         humidity = float(data[1])
#                         temperature = float(data[2])
#                         if (humidity>1) and (temperature>1 ):
#                             tdelta = self.settings['time'].elapsed()/1000.0
#                             self.resultQueue.put(np.array([tdelta, temperature, humidity]))

#                             # self.settings['dht_buff'].append()
#                         # print([tdelta, temperature, humidity])
#                 # except:
#                 #     pass

#         self.serial.close()
#         print("DHT-process %s just ended" % os.getpid())
#         return

    # def initSerial(self):
    #     print('serial init called')
    #     # port = self.p.param('Measurements','Instruments','DHT-arduino','Serial Port').value()

    #     try:
    #         self.serial = serial.Serial(self.port-1, baudrate=115200, timeout=5) # opens, too.
    #     except:
    #         print( 'dht failed' )
    #         self.serial = None

    #     print(self.serial)
            # self.settings['measure']['dht_serial'] = None
            # QtCore.QTimer.singleShot(5000, self.initSerial)

        # try:
        # if self.settings['measure']['dht_serial'] != None:
        #     self.run_dht()
        # self.sig_dht_measure.emit(500)
        # except:
        #     print( 'dht failed' )
        #     self.settings['measure']['dht_serial'] = None

# if not demo:
#     class MeasureTask(Task):
#         def __init__(self, resultQueue= None, settings = None, timer = None):
#             Task.__init__(self)
#             self.running = False
#             self.resultQueue = resultQueue
#             self.tdelta = 0.0
#             if timer is None:
#                 timer = QTime.currentTime()
#                 timer.start()
#             self.timer = timer

#             self.acq_samples = settings['acq_samples']

#             self.num_chans = len(settings['channels'])
#             self.ch_out = []

#             self.data = np.zeros(self.num_chans+1)

#             for i in settings['channels']:
#                 chan = settings['device']+ '/ai' + str(i[0])
#                 self.create_chan(chan, i[1], i[2])
#                 # print( 'created ', chan )

#             self.CfgSampClkTiming("", settings['acq_rate'], DAQmx_Val_Rising,
#                                   DAQmx_Val_ContSamps, settings['buffer_size'])
#             self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer,
#                                                 self.acq_samples, 0)
#             self.AutoRegisterDoneEvent(0)

#         def create_chan(self, chan, v_min=-10, v_max=10):
#             self.CreateAIVoltageChan( chan,
#                                       "",
#                                       DAQmx_Val_Diff,
#                                       v_min,
#                                       v_max,
#                                       DAQmx_Val_Volts,
#                                       None)

#         def EveryNCallback(self):
#             read = int32()
#             if self.running:
#                 # This is to have at least some samples in the buffer. else one might read more samples than available, EveryNSamplesEvent is x +- 100 samples!
#                 data = np.zeros(5*self.num_chans*self.acq_samples)
#                 self.ReadAnalogF64(-1,
#                                    -1,
#                                    DAQmx_Val_GroupByChannel,
#                                    data,
#                                    data.size,
#                                    byref(read),
#                                    None)
#             else:
#                 self.running = True
#                 data = np.zeros(10*self.num_chans*self.acq_samples)
#                 self.ReadAnalogF64(-1,
#                                    -1,
#                                    DAQmx_Val_GroupByChannel,
#                                    data,
#                                    data.size,
#                                    byref(read),
#                                    None)
#             meas_data = np.reshape(data[:read.value*self.num_chans],(self.num_chans,-1))

#             av_data = np.mean(meas_data,1)

#             av_data = av_data.reshape((-1,self.num_chans))

#             # print('callback')

#             # tdelta = settings['time'].elapsed()/1000.0
#             # if self.tdelta<=tdelta:
#                 # self.tdelta = tdelta
#             self.data[0] = self.timer.elapsed()/1000.0
#             self.data[1:] = av_data
#             self.resultQueue.put(self.data)
#             # print(np.array([av_data[0],av_data[1]]))
#             # self.resultQueue.append(np.array([av_data[0],av_data[1]]))
#             # settings['buff'].append(np.array([av_data[0],av_data[1]]))
#             return 0  # The function should return an integer

#         def DoneCallback(self, status):
#             # print( "Status", status.value )
#             return 0  # The function should return an integer


