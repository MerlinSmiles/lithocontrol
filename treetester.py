#!/usr/bin/env python
demo = 0
print('\n\n')
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import numpy as np
from pprint import pprint


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg

import ezdxf

import sys

sys.path.append(".\\source")

filename = './test.dxf'

import os

from source.treeclass3 import *



colors = ['vivid_yellow','strong_purple','vivid_orange','very_light_blue','vivid_red','grayish_yellow','medium_gray','vivid_green','strong_purplish_pink','strong_blue','strong_yellowish_pink','strong_violet','vivid_orange_yellow','strong_purplish_red','vivid_greenish_yellow','strong_reddish_brown','vivid_yellowish_green','deep_yellowish_brown','vivid_reddish_orange','dark_olive_green']
kelly_colors = dict(vivid_yellow=(255, 179, 0),
            strong_purple=(128, 62, 117),
            vivid_orange=(255, 104, 0),
            very_light_blue=(166, 189, 215),
            vivid_red=(193, 0, 32),
            grayish_yellow=(206, 162, 98),
            medium_gray=(129, 112, 102),
            vivid_green=(0, 125, 52),
            strong_purplish_pink=(246, 118, 142),
            strong_blue=(0, 83, 138),
            strong_yellowish_pink=(255, 122, 92),
            strong_violet=(83, 55, 122),
            vivid_orange_yellow=(255, 142, 0),
            strong_purplish_red=(179, 40, 81),
            vivid_greenish_yellow=(244, 200, 0),
            strong_reddish_brown=(127, 24, 13),
            vivid_yellowish_green=(147, 170, 0),
            deep_yellowish_brown=(89, 51, 21),
            vivid_reddish_orange=(241, 58, 19),
            dark_olive_green=(35, 44, 22))

# mkPen for selected
selectPen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
sketchPen = pg.mkPen(color='FF0000',width=3)  #, style=QtCore.Qt.DotLine
movePen = pg.mkPen(color='1E4193',width=2, style=QtCore.Qt.DotLine)  #, style=QtCore.Qt.DotLine
showPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine , width=



class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)

        self.tree_file = QtGui.QTreeView()
        self.setCentralWidget(self.tree_file)
        self.show()

        self.dxffileName = filename

        self.headers = ('Name', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Closed', 'Type', 'Color', 'Show')

        self.model = TreeModel(self.headers, self.dxf, parent=self)

        self.tree_file.setModel(self.model)
        self.tree_file.expandAll()
        # self.tree_file.setDragEnabled( True )
        # self.tree_file.setAcceptDrops( True )
        self.tree_file.setDragDropMode( QtGui.QAbstractItemView.InternalMove )

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)

        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(int(screen.width()/3), int(screen.height()/3), screen.width()/2, screen.height()/2)

        for col in [self.headers.index(col) for col in ['Voltage', 'Rate', 'Angle', 'Step']]:
            self.tree_file.setItemDelegateForColumn(col,DoubleSpinBoxDelegate(self))
        for col in [self.headers.index(col) for col in ['Color']]:
            self.tree_file.setItemDelegateForColumn(col,ColorDelegate(self))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())
