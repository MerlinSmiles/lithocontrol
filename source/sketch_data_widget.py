import sys
from PyQt4 import QtCore, QtGui

class SketchDataDialog(QtGui.QWidget):
    def __init__( self, parent = None ):
        super(SketchDataDialog, self).__init__(parent)

        font = QtGui.QFont("Consolas",8)
        font.setStyleHint(QtGui.QFont.TypeWriter);
        fm = QtGui.QFontMetrics(font)
        pixels = fm.width('M' * 6)

        self._console = QtGui.QTextBrowser(self)
        self._console.setCurrentFont(font)
        self._console.setTabStopWidth(pixels)

        # self._combo = QtGui.QComboBox()
        # self._combo.addItems(['DEBUG','INFO','WARNING','ERROR'])
        # self._combo.currentIndexChanged.connect( self.changed )

        # comboLayout = QtGui.QSplitter()
        # comboLayout.addWidget(QtGui.QLabel(' Logging level:'))
        # comboLayout.addWidget(self._combo)

        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        # layout.addWidget(comboLayout)
        layout.addWidget(self._console)
        self.setLayout(layout)

        # custom_logger.LogStream.stderr().messageWritten.connect( self.insertText )


    def insertText(self, text):
        # color = QtCore.Qt.darkMagenta
        # fm = self._console.currentCharFormat()
        # fm.setForeground(color)
        # self._console.setCurrentCharFormat(fm)
        self._console.clear()
        self._console.insertPlainText(text)
        # self._console.moveCursor(QtGui.QTextCursor.End)
        # self._console.ensureCursorVisible()



if ( __name__ == '__main__' ):
    app = None
    if ( not QtGui.QApplication.instance() ):
        app = QtGui.QApplication([])
    # dlgx = tDialog()
    dlg = SketchDataDialog()
    dlg.show()
    dlg.insertText('a\tb\tc\td')
    dlg.insertText('a\tb\tc\td')
    # dlgx.show()
    # dlgx.test()
    if ( app ):
        app.exec_()
