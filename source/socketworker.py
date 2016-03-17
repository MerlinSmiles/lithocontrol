#!/usr/bin/env python

import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

from PyQt4 import QtCore, QtGui, uic
import socket
import time

import logging
log = logging.getLogger('root')

class SocketWorker(QtCore.QThread):

    new_data = QtCore.pyqtSignal(object)

    def __init__(self, host, port, demo = False, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.demo = demo
        self.host = host
        self.port = port
        self.remote_ip = None
        self.sock = None
        self.init = False
        self.connected = False
        log.debug('SOCKET: Init')
        if not demo:
            self.initSocket()
            self.connectSocket()

    def __del__(self):
        self.stop()

    def initSocket(self):
        try:
            #create an AF_INET, STREAM socket (TCP)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            log.warning('SOCKET: Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1] )
            self.init =  False

        try:
            self.remote_ip = socket.gethostbyname( self.host )
        except socket.gaierror:
            #could not resolve
            log.warning( 'SOCKET: Hostname could not be resolved. Exiting' )
            self.init =  False
        self.init =  True

    def connectSocket(self):
        #Connect to remote server
        if self.demo:
            return
        if not self.init:
            self.initSocket()
        if self.connected:
            self.disconnectSocket()
        try:
            self.sock.connect((self.remote_ip , self.port))
            log.info( 'SOCKET: Connected to ' + self.host + ' on ip ' + self.remote_ip )
            self.connected = True
        except:
            self.connected = False
            # log.debug( 'Socket NOT Connected to ' + self.host + ' on ip ' + self.remote_ip )
            pass

    def disconnectSocket(self):
        if self.demo:
            return
        try:
            self.sock.close()
            log.info( 'SOCKET: disconnected from ' + self.host + ' on ip ' + self.remote_ip )
            self.connected = False
            self.init =  False
        except:
            log.warning( 'SOCKET: disconnect FAILED from ' + self.host + ' on ip ' + self.remote_ip )
            pass

    def send_message(self, message):
        if self.demo:
            return
        if not self.connected:
            log.info('SOCKET: not connected')
            self.connectSocket()
        try :
            #Set the whole string
            # log.info('SOCKET: send: ' +message)
            self.sock.sendall(message.encode())
            # print( 'sending message' )
        except socket.error:
            #Send failed
            log.info( 'SOCKET: Send failed trying again with reconnect' )
            # self.disconnectSocket()
            # self.initSocket()
            self.connectSocket()
            try :
                #Set the whole string
                # print( 'sending message' )
                self.sock.sendall(message.encode())
            except socket.error:
                #Send failed
                log.warning( 'SOCKET: Send failed: Serious error' )
                # self.disconnectSocket()

    def recv_message(self, timeout =0, buf = 4096):
        if self.demo:
            return
        if not self.connected:
            time.sleep(0.2)
            self.connectSocket()
        else:
            try:
                self.sock.settimeout(timeout)
                msg = self.sock.recv(buf)
                return msg
            except socket.error as e:
                return False

    def monitor(self):
        self.exiting = False
        self.start()

    def stop(self):
        self.exiting = True
        self.init = False
        self.connected = False
        self.disconnectSocket()

    def run(self):
        while self.demo:
            time.sleep(0.1)
        self.exiting = False
        if not self.connected:
            self.connectSocket()

        while not self.exiting:
            # time.sleep(0.0001)
            msg = self.recv_message(timeout = 0.05)
            if msg:
                lines = msg.splitlines()
                for line in lines:
                    # print(line)
                    # self.statusBar().showMessage(line)
                    self.new_data.emit(line)
                    # self.emit(QtCore.SIGNAL("AFMStatus(QString)"), line)

