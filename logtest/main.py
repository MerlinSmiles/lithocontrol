#!/usr/bin/python

import logging
import custom_logger
from PyQt4 import QtCore, QtGui
import submodule
# import colorer

log = logging.getLogger('root')
log.setLevel('DEBUG')


log.addHandler(custom_logger.QtHandler())
log.addHandler(custom_logger.MyHandler())


class tDialog(QtGui.QDialog):
    def __init__( self, parent = None ):
        super(tDialog, self).__init__(parent)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self._button  = QtGui.QPushButton(self)
        self._button.setText('Test Me')
        layout.addWidget(self._button)
        self._button.clicked.connect(self.test)

    def test( self ):
        # a = submodule.SubClass() # this should produce a log message
        # a.SomeMethod()           # so should this
        log.debug('Adebug message')
        log.info('Ainfo message')
        log.warning('Awarning message')
        log.error('Aerror message')
        print ('AOld school hand made print message')
        # print(blah)


class LogDialog(QtGui.QWidget):
    def __init__( self, parent = None ):
        super(LogDialog, self).__init__(parent)
        font = QtGui.QFont("Monospace",8)
        font.setStyleHint(QtGui.QFont.TypeWriter);
        self._console = QtGui.QTextBrowser(self)
        self._console.setCurrentFont(font)

        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self._console)
        self.setLayout(layout)

        custom_logger.LogStream.stdout().messageWritten.connect( self.insertText2 )
        custom_logger.LogStream.stderr().messageWritten.connect( self.insertText )

    def insertText(self, text):
        color = QtCore.Qt.darkMagenta
        fm = self._console.currentCharFormat()
        fm.setForeground(color)
        self._console.setCurrentCharFormat(fm)
        self._console.insertPlainText(text)

    def insertText2(self, text):
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

    def test( self ):
        a = submodule.SubClass() # this should produce a log message
        a.SomeMethod()           # so should this
        log.debug('debug message')
        log.info('info message')
        log.warning('warning message')
        log.error('error message')
        print ('Old school hand made print message')
        # print(blah)


if ( __name__ == '__main__' ):
    app = None
    if ( not QtGui.QApplication.instance() ):
        app = QtGui.QApplication([])
    dlgx = tDialog()
    dlg = LogDialog()
    dlg.show()
    dlgx.show()
    dlgx.test()
    if ( app ):
        app.exec_()
