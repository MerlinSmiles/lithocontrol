import sys
# import logging
import custom_logger
from PyQt4 import QtCore, QtGui
# import colorer

# log.setLevel('DEBUG')

class tDialog(QtGui.QDialog):
    def __init__( self, parent = None ):
        super(tDialog, self).__init__(parent)

        self.log = custom_logger.getLogger('root','DEBUG')
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self._button  = QtGui.QPushButton(self)
        self._button.setText('Test Me')
        layout.addWidget(self._button)
        self._button.clicked.connect(self.test)

    def test( self ):
        self.log.debug('Adebug message')
        self.log.info('Ainfo message')
        self.log.warning('Awarning message')
        self.log.error('Aerror message')
        print ('AOld school hand made print message')
        try:
            blah
        except Exception as e:
            self.log.exception(e)


class LogDialog(QtGui.QWidget):
    def __init__( self, parent = None ):
        super(LogDialog, self).__init__(parent)
        self.log = custom_logger.getLogger('root','DEBUG')
        font = QtGui.QFont("Monospace",8)
        font.setStyleHint(QtGui.QFont.TypeWriter);
        self._console = QtGui.QTextBrowser(self)
        self._console.setCurrentFont(font)
        self._combo = QtGui.QComboBox()
        self._combo.addItems(['DEBUG','INFO','WARNING','ERROR'])
        self._combo.currentIndexChanged.connect( self.changed )

        comboLayout = QtGui.QSplitter()
        comboLayout.addWidget(QtGui.QLabel(' Logging level:'))
        comboLayout.addWidget(self._combo)

        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(comboLayout)
        layout.addWidget(self._console)
        self.setLayout(layout)

        custom_logger.LogStream.stdout().messageWritten.connect( self.insertText2 )
        custom_logger.LogStream.stderr().messageWritten.connect( self.insertText )

    def changed(self, index):
        level = self._combo.itemText(index)
        self.log.setLevel(level)
        self.log.info('LOGGING: Level changed to {}'.format(level))
        # print(index, level)

    def insertText(self, text):
        color = QtCore.Qt.darkMagenta
        fm = self._console.currentCharFormat()
        fm.setForeground(color)
        self._console.setCurrentCharFormat(fm)
        self._console.insertPlainText(text)
        self._console.moveCursor(QtGui.QTextCursor.End)
        self._console.ensureCursorVisible()


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
        self._console.moveCursor(QtGui.QTextCursor.End)
        self._console.ensureCursorVisible()


    def test( self ):
        # a = submodule.SubClass() # this should produce a log message
        # a.SomeMethod()           # so should this
        self.log.debug('debug message')
        self.log.info('info message')
        self.log.warning('warning message')
        self.log.error('error message')
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
