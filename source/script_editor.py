import sys
import os
from PyQt4.QtGui import QApplication
from PyQt4 import QtCore, QtGui, Qsci
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerPython

class editorWidget(QtGui.QWidget):
    def __init__( self, file = None, parent = None ):
        super(editorWidget, self).__init__(parent)
        self.defautFile = file

        self.toolbar = QtGui.QToolBar()
        self.editor = QsciScintilla()
        # self.editor.installEventFilter(self)
        self.statusBar = QtGui.QStatusBar()


        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.editor)
        layout.addWidget(self.statusBar)
        self.setLayout(layout)

        self.addToolbars()
        ## define the font to use
        font = QtGui.QFont("Consolas",10)
        font.setStyleHint(QtGui.QFont.TypeWriter)

        font.setFixedPitch(True)
        # font.setPointSize(8)
        # the font metrics here will help
        # building the margin width later
        fm = QtGui.QFontMetrics(font)

        ## set the default font of the editor
        ## and take the same font for line numbers
        self.editor.setFont(font)
        self.editor.setMarginsFont(font)

        ## Line numbers
        # conventionnaly, margin 0 is for line numbers
        self.editor.setMarginWidth(0, fm.width( "000" ) + 5)

        ## Edge Mode shows a red vetical bar at 80 chars
        self.editor.setEdgeMode(QsciScintilla.EdgeLine)
        self.editor.setEdgeColumn(80)
        self.editor.setEdgeColor(QtGui.QColor("#FFAAAA"))

        ## Braces matching
        self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        ## Editing line color
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#DDDDDD"))

        ## Margins colors
        # line numbers margin
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#BBBBBB"))

        # folding margin colors (foreground,background)
        # self.editor.setFoldMarginColors(QtGui.QColor("#999999"),QtGui.QColor("#FFFFFF"))

        ## Choose a lexer
        lexer = QsciLexerPython(self)
        lexer.setDefaultFont(font)
        lexer.setFont(font)


        # api = Qsci.QsciAPIs(lexer)
        # # path = 'C:/Anaconda/Lib/site-packages/PyQt4/qsci/api/python/Python-3.4.api'
        # # with open(path, 'r') as f:
        # #     read_data = f.read()
        # # for i in read_data.split():
        # #     api.add(i)
        # # Add autocompletion strings
        # api.add("aLongString")
        # api.add("aLongerString")
        # api.add("aDifferentString")
        # api.add("sOmethingElse")
        # ## Compile the api for use in the lexer
        # api.prepare()

        self.editor.setLexer(lexer)

        self.editor.setAutoIndent(True)
        self.editor.setTabIndents(True)
        self.editor.setTabWidth(4)
        ## Set the length of the string before the editor tries to autocomplete
        ## In practise this would be higher than 1
        ## But its set lower here to make the autocompletion more obvious
        self.editor.setAutoCompletionThreshold(1)
        ## Tell the editor we are using a QsciAPI for the autocompletion
        self.editor.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        ## Render on screen
        # self.editor.show()
        # self.setGeometry(100,100,900,800)
        ## Show this file in the editor
        # self.editor.setText(open("test_editor.py").read())
        self.readFile(0)


    # def test():
    #     print('self, widget, event')

    # def eventFilter(self, widget, event):
    #     print(event.type())
    #     if (event.type() == QtCore.QEvent.ShortcutOverride and widget is self.editor):
    #         # print('ShortcutOverride')
    #         event.accept()
    #         return True
    #     return QtGui.QWidget.eventFilter(self, widget, event)

    def addToolbars(self):
        scriptFolderAction    = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_search.png'), 'Select sketch script', self)
        scriptReloadAction    = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_refresh.png'), 'Reload current script', self)
        scriptDefaultAction   = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_deny.png'), 'Clear to default', self)
        scriptSaveAction      = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_accept.png'), 'Save script', self)

        QtCore.QObject.connect(scriptFolderAction, QtCore.SIGNAL('triggered()'), self.pickScript)
        QtCore.QObject.connect(scriptSaveAction, QtCore.SIGNAL('triggered()'), self.saveScript)
        QtCore.QObject.connect(scriptDefaultAction, QtCore.SIGNAL('triggered()'), lambda id = 0: self.readFile(id ))
        QtCore.QObject.connect(scriptReloadAction, QtCore.SIGNAL('triggered()'), lambda id = 1: self.readFile(id ))
        # QtCore.QObject.connect(scriptReloadAction,  QtCore.SIGNAL('triggered()'), self.readDefaultScript )


        iconSize = QtCore.QSize(24,24)
        self.toolbar.setIconSize(iconSize)

        self.toolbar.addAction(scriptFolderAction)
        self.toolbar.addAction(scriptReloadAction)
        self.toolbar.addAction(scriptDefaultAction)
        self.toolbar.addAction(scriptSaveAction)


    def pickScript(self):
        file = QtGui.QFileDialog.getOpenFileName(self, 'Open sketch-script', self.defautFile, filter='*.py')
        if file:
            self.openFile(file)

    def saveScript(self):
        file = QtGui.QFileDialog.getSaveFileName(self, 'Save sketch-script', self.defautFile, filter='*.py')
        # print (file)
        if file:
            with open(file,'w') as f:
                f.write(self.getFile())


    def readFile(self,code):
        if code == 0:
            self.openFile(self.defautFile)
        elif code == 1:
            self.openFile(self.file)

    def openFile(self,file):
        self.file = file
        self.statusBar.showMessage('Current script-file:     %s'%(file))
        if self.file != None:
            with open(file) as f:
                data = f.read()
            self.editor.setText(data)

    def getFile(self):
        text = self.editor.text().replace('\t','    ')
        self.editor.setText(text)
        return text

if ( __name__ == '__main__' ):
    app = QtGui.QApplication(sys.argv)

    window = editorWidget()
    window.show()
    window.openFile(__file__)
    print(window.getFile())

    sys.exit(app.exec_())