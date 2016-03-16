#!/usr/bin/env python
# -*- coding: latin1 -*-

"""
Basic use of the QScintilla2 widget

Note : name this file "qt4_sci_test.py"
"""

import sys
import os
from PyQt4.QtGui import QApplication
from PyQt4 import QtCore, QtGui, Qsci
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerPython

class editorWidget(QtGui.QWidget):
    def __init__( self, parent = None ):
        super(editorWidget, self).__init__(parent)
        self.editor = QsciScintilla()

        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self.editor)
        self.setLayout(layout)

        ## define the font to use
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setFixedPitch(True)
        font.setPointSize(10)
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
        self.editor.setMarginLineNumbers(0, True)

        ## Edge Mode shows a red vetical bar at 80 chars
        self.editor.setEdgeMode(QsciScintilla.EdgeLine)
        self.editor.setEdgeColumn(80)
        self.editor.setEdgeColor(QtGui.QColor("#FFAAAA"))

        ## Folding visual : we will use boxes
        self.editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)

        ## Braces matching
        self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        ## Editing line color
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#DDDDDD"))

        ## Margins colors
        # line numbers margin
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#AAAAAA"))
        self.editor.setMarginsForegroundColor(QtGui.QColor("#000000"))

        # folding margin colors (foreground,background)
        self.editor.setFoldMarginColors(QtGui.QColor("#999999"),QtGui.QColor("#FFFFFF"))

        ## Choose a lexer
        lexer = QsciLexerPython(self)
        lexer.setDefaultFont(font)


        api = Qsci.QsciAPIs(lexer)
        # path = 'C:/Anaconda/Lib/site-packages/PyQt4/qsci/api/python/Python-3.4.api'
        # with open(path, 'r') as f:
        #     read_data = f.read()
        # for i in read_data.split():
        #     api.add(i)
        # Add autocompletion strings
        api.add("aLongString")
        api.add("aLongerString")
        api.add("aDifferentString")
        api.add("sOmethingElse")
        ## Compile the api for use in the lexer
        api.prepare()

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
        self.editor.show()
        self.setGeometry(100,100,900,800)
        ## Show this file in the editor
        self.editor.setText(open("test_editor.py").read())

if ( __name__ == '__main__' ):
    app = QtGui.QApplication(sys.argv)

    window = editorWidget()
    window.show()

    sys.exit(app.exec_())