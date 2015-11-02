#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic
import socket
import time

class SocketWorker(QtCore.QThread):

    def __init__(self, parent = None):

        QtCore.QThread.__init__(self, parent)
        self.exiting = False

        self.host = 'nanoman'
        self.remote_ip = None
        self.port = 12345
        self.sock = None
        self.init = False
        self.connected = False

        self.initSocket()
        self.connectSocket()

    def __del__(self):
        self.stop()

    def initSocket(self):
        try:
            #create an AF_INET, STREAM socket (TCP)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            print( 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1] )
            self.init =  False

        try:
            self.remote_ip = socket.gethostbyname( self.host )
        except socket.gaierror:
            #could not resolve
            print( 'Hostname could not be resolved. Exiting' )
            self.init =  False
        self.init =  True

    def connectSocket(self):
        #Connect to remote server
        if not self.init:
            self.initSocket()
        if self.connected:
            self.disconnectSocket()
        try:
            self.sock.connect((self.remote_ip , self.port))
            print( 'Socket Connected to ' + self.host + ' on ip ' + self.remote_ip )
            self.connected = True
        except:
            self.connected = False
            pass

    def disconnectSocket(self):
        try:
            self.sock.close()
            print( 'Socket disconnected' )
            self.connected = False
        except:
            pass

    def send_message(self, message):
        if not self.connected:
            self.connectSocket()
        try :
            #Set the whole string
            self.sock.sendall(message.encode())
            # print( 'sending message' )
        except socket.error:
            #Send failed
            print( 'Send failed trying again with reconnect' )
            self.initSocket()
            self.connectSocket()
            try :
                #Set the whole string
                # print( 'sending message' )
                self.sock.sendall(message.encode())
            except socket.error:
                #Send failed
                print( 'Send failed: Serious error' )

    def recv_message(self, timeout =0, buf = 4096):
        if not self.connected:
            self.connectSocket()
        try:
            self.sock.settimeout(timeout)
            msg = self.sock.recv(buf)
            return msg
        except socket.error as e:
            return False
        else:
            print( 'got a message, do something :)' )
            pass

    def monitor(self):
        self.exiting = False
        self.start()

    def stop(self):
        self.exiting = True
        self.init = False
        self.connected = False
        self.disconnectSocket()

    def run(self):
        self.exiting = False
        if not self.connected:
            self.connectSocket()

        while not self.exiting:
            time.sleep(1)
            msg = self.recv_message(timeout = 0.05)
            if msg:
                lines = msg.splitlines()
                for line in lines:
                    # self.statusBar().showMessage(line)
                    self.emit(QtCore.SIGNAL("AFMStatus(QString)"), line)

