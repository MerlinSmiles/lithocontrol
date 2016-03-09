import sys
from PyQt4 import QtCore, QtGui
import logging
# Initialize coloredlogs.
# import coloredlogs
import colorer
# coloredlogs.install(level='DEBUG')




DEBUG_LEVELV_NUM = 25
logging.addLevelName(DEBUG_LEVELV_NUM, "AFMLOG")
def afmlog(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(DEBUG_LEVELV_NUM):
        self._log(DEBUG_LEVELV_NUM, message, args, **kws)
logging.Logger.afmlog = afmlog

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        # level = str(record.levelname)
        record = self.format(record)
        # # color = 'black'

        if record: XStream.stdout().write("{}\n".format(record))#"{}\n".format(record))#"%s\n"%record)
        # originally: XStream.stdout().write("{}\n".format(record))

class MyFormatter(logging.Formatter):
    width = 10
    def format(self, record):
        a = "%s:%s" % (record.filename, record.lineno)
        return "[%s] %s" % (a.ljust(self.width), record.msg)

loglevel = logging.INFO
logger = logging.getLogger(__name__)
handler = QtHandler()
# handler.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(loglevel)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(loglevel)
mformat = '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s'
formatter = logging.Formatter(mformat)
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.basicConfig(format=mformat, filename='example.log',level=logging.DEBUG)

class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit((msg))
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class MyDialog(QtGui.QDialog):
    def __init__( self, parent = None ):
        super(MyDialog, self).__init__(parent)

        self._console = QtGui.QTextBrowser(self)

        font = QtGui.QFont("Monospace",8)
        font.setStyleHint(QtGui.QFont.TypeWriter);

        self._console.setCurrentFont(font)

        self._button  = QtGui.QPushButton(self)
        self._button.setText('Test Me')

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._console)
        layout.addWidget(self._button)
        self.setLayout(layout)

        XStream.stdout().messageWritten.connect( self.insertText2 )
        XStream.stderr().messageWritten.connect( self.insertText )

        self._button.clicked.connect(self.test)

    def insertText(self, text):
        # print()
        color = QtCore.Qt.darkMagenta

        fm = self._console.currentCharFormat()
        fm.setForeground(color)
        self._console.setCurrentCharFormat(fm)
        self._console.insertPlainText(text)

    def insertText2(self, text):
        # print()
        if text.startswith('DEBUG'):
            color = QtCore.Qt.darkRed
        elif text.startswith('INFO'):
            color = QtCore.Qt.darkYellow
        elif text.startswith('AFMLOG'):
            color = QtCore.Qt.darkGreen
        elif text.startswith('WARNING'):
            color = QtCore.Qt.darkBlue
        elif text.startswith('ERROR'):
            color = QtCore.Qt.red
        else:
            color = QtCore.Qt.darkGray
        fm = self._console.currentCharFormat()
        fm.setForeground(color)
        self._console.setCurrentCharFormat(fm)
        self._console.insertPlainText(text)
        # self._console.insertPlainText(t)
        # print()
        # self._console.insertPlainText(text)


        # XStream.stdout().messageWritten.connect( self._console.insertPlainText )
        # XStream.stderr().messageWritten.connect( self._console.insertPlainText )
    def test( self ):
        logger.debug('debug message')
        logger.afmlog('afmlog message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')
        print ('Old school hand made print message')
        print(blah)

if ( __name__ == '__main__' ):
    app = None
    if ( not QtGui.QApplication.instance() ):
        app = QtGui.QApplication([])
    dlg = MyDialog()
    dlg.show()
    if ( app ):
        app.exec_()
