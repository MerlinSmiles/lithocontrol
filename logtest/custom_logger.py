import logging
import logging.handlers
import os
import sys
from PyQt4 import QtCore, QtGui


def getLogger(name='root', loglevel='INFO'):
  logger = logging.getLogger(name)

  # if logger 'name' already exists, return it to avoid logging duplicate
  # messages by attaching multiple handlers of the same type
  if logger.handlers:
    return logger
  # if logger 'name' does not already exist, create it and attach handlers
  else:
    # set logLevel to loglevel or to INFO if requested level is incorrect
    loglevel = getattr(logging, loglevel.upper(), logging.INFO)
    logger.setLevel(loglevel)
    fmt = '%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s'
    fmt_date = '%Y-%m-%dT%T%Z'
    formatter = logging.Formatter(fmt, fmt_date)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if logger.name == 'root':
      logger.warning('Running: %s %s',
                     os.path.basename(sys.argv[0]),
                     ' '.join(sys.argv[1:]))
    return logger

class MyHandler(logging.StreamHandler):

    def __init__(self):
        logging.StreamHandler.__init__(self)
        fmt = '%(asctime)s %(filename)-15s %(levelname)-8s: %(message)s'
        fmt_date = '%Y-%m-%dT%T%Z'
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)


class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))

    def emit(self, record):
        record = self.format(record)
        # # color = 'black'
        # try:
        #     if record.levelname == 'DEBUG':
        #         color = 'red'
        # except:
        #     color = 'black'
        if record: LogStream.stdout().write("{}\n".format(record))#"{}\n".format(record))#"%s\n"%record)

        # if record: LogStream.stdout().write("%s\n"%record)
        # originally: LogStream.stdout().write("{}\n".format(record))


class LogStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(msg)
    @staticmethod
    def stdout():
        if ( not LogStream._stdout ):
            LogStream._stdout = LogStream()
            sys.stdout = LogStream._stdout
        return LogStream._stdout
    @staticmethod
    def stderr():
        if ( not LogStream._stderr ):
            LogStream._stderr = LogStream()
            sys.stderr = LogStream._stderr
        return LogStream._stderr
