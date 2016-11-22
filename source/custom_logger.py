import logging
import logging.handlers
import os
import sys
import traceback
from PyQt4 import QtCore, QtGui



def getLogger(name='root', loglevel='INFO', handler=None):
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
    logger.propagate = False

    logger.addHandler(QtHandler())
    # logger.addHandler(MyHandler())
    # logger.addHandler(consoleHandler(sys.stdout))

    if logger.name == 'root':
      logger.warning('Running: %s %s',
                     os.path.basename(sys.argv[0]),
                     ' '.join(sys.argv[1:]))

    def my_handler(type, value, tb):
        logger.exception("Uncaught exception: {0}\n{1}".format(str(value),str(traceback.print_tb(tb))))

    # Install exception handler
    # sys.excepthook = my_handler
    return logger

class CustomFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(CustomFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        r = record

        # FORMAT = "%-7s [%-15s : %-4s - %15s() ] %s"%(r.levelname,r.filename,r.lineno,r.funcName,r.message)
        # filename = r.filename
        file = '{}({})'.format(r.filename,r.lineno)
        levelname = '{}:'.format(r.levelname)
        FORMAT = "{:8} [{:25}: {:>15}() ] {:}".format(levelname,file,r.funcName,r.getMessage())
        return FORMAT
    #     # if record.levelno in (logging.WARNING,
    #     #                       logging.ERROR,
    #     #                       logging.CRITICAL):
    #     #     record.msg = '[%s] %s' % (record.levelname, record.msg)
    #     # return super(CustomFormatter , self).format(record)


    # logging.FileHandler('logfile.log')

class RotateHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super(RotateHandler, self).__init__(*args, **kwargs)
        # self.doRollover()
        # FORMAT = "%(levelname)s [%(filename)-15s : %(lineno)-4s - %(funcName)15s() ] %(message)s"
        FORMAT = "%(asctime)s\t%(filename)s\t%(lineno)s\t%(funcName)s()\t%(levelname)s\t%(message)s"
        # formatter = CustomFormatter()
        # self.setFormatter(formatter)
        self.setFormatter(logging.Formatter(FORMAT))


class consoleHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super(consoleHandler, self).__init__(*args, **kwargs)
        self.setLevel(logging.ERROR)

class MyHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        # FORMAT = "[%(asctime)s %(filename)s (%(lineno)s) - %(funcName)s() ] %(levelname)s: %(message)s"
        FORMAT = "%(levelname)-7s [%(filename)-15s : %(lineno)-4s - %(funcName)15s() ] %(message)s"
        # fmt = '%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s'
        # formatter = logging.Formatter(FORMAT)
        formatter = CustomFormatter()
        self.setFormatter(formatter)


class QtHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(QtHandler, self).__init__(*args, **kwargs)
    # def __init__(self):
    #     logging.Handler.__init__(self)
        # FORMAT = "%(levelname)-8s '%(filename)-15s' %(message)s"
        # FORMAT = "%(levelname)-7s [%(filename)-15s : %(lineno)-4s - %(funcName)15s() ] %(message)s"
        # self.setFormatter(logging.Formatter(FORMAT))

        formatter = CustomFormatter()
        self.setFormatter(formatter)

    def emit(self, record):
        record = self.format(record)
        if record:
            LogStream.stdout().write("{}\n".format(record))


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
