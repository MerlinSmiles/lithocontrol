from PyQt4 import QtCore, QtGui,uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QTime, QTimer
import pyqtgraph as pg
import numpy as np

import pandas as pd
# import serial
import datetime
from datetime import datetime as dt

import time
from time import sleep

import sys

# https://github.com/clade/PyDAQmx/tree/master/PyDAQmx/example
from numpy import zeros

import ringbuffer as ringbuffer
# import cProfile

# from source.ni_measurement import *

class ni_Worker(QtCore.QObject):

    terminate = pyqtSignal()

    def __init__(self, settings, parent=None):

        super(ni_Worker, self).__init__(parent)
        self.settings = settings
        self.tdelta = 0.0
        self.running = True

    def dodata(self):
        tdelta = self.settings['time'].elapsed()/1000.0
        self.settings['buff'].append(np.array([tdelta,np.random.random(),np.random.random()]))

    def run(self):
        self.settings['time'].start()
        while self.running == True:
            self.dodata()
            time.sleep(0.05)

    def stop(self):
        self.task.StopTask()
        self.running = False
        # self.task.ClearTask()



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


