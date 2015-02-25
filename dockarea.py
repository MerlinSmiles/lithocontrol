#!/usr/bin/env python

# Set the QT API to PyQt4
import os
os.environ['QT_API'] = 'pyqt'
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)
import sys
from PyQt4 import QtCore, QtGui, uic

import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore, QtGui
# import pyqtgraph.console
import numpy as np

import pyqtgraph.dockarea as pg_dock
# from pyqtgraph.dockarea import *


# Import the console machinery from ipython
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport


style_sheet = ""
with open ("source/style.css", "r") as myfile:
    style_sheet=myfile.read()


orangePen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
bluePen = pg.mkPen(color='0000FF')  #, style=QtCore.Qt.DotLine
greenPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine


class QIPythonWidget(RichIPythonWidget):
    """ Convenience class for a live IPython console widget. We can replace the standard banner using the customBanner argument"""
    def __init__(self,customBanner=None,*args,**kwargs):
        if customBanner!=None: self.banner=customBanner
        super(QIPythonWidget, self).__init__(*args,**kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        """ Given a dictionary containing name / value pairs, push those variables to the IPython console widget """
        self.kernel_manager.kernel.shell.push(variableDict)
    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()
    def printText(self,text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)
    def executeCommand(self,command):
        """ Execute a command in the frame of the console widget """
        self._execute(command,False)


class Test(QtGui.QWidget):
    def __init__( self, parent=None):
        super(Test, self).__init__(parent)
        self.area = pg_dock.DockArea()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.area)
        self.setLayout(layout)

        sketchDock = pg_dock.Dock("Skecthing", size=(500, 300))
        ## d2 = pg_dock.Dock("Measuring", size=(500,300))
        # d3 = pg_dock.Dock("Console", size=(500,300))
        measureDock = pg_dock.Dock("Measuring", size=(500,300))


        self.area.addDock(sketchDock, 'top')
        self.area.addDock(measureDock, 'bottom')



        # w2 = pg.PlotWidget()
        # w2.setBackground("222")
        # w2.plot(np.random.normal(size=100))
        # d2.addWidget(w2)

        # l = QtGui.QGridLayout()
        # cw.setLayout(l)
        # l.setSpacing(0)
        # plt = pg.PlotItem()

        data = pg.gaussianFilter(np.random.normal(size=(256, 256)), (20, 20))
        img = pg.ImageItem(data)
        # v = pg.GraphicsView()
        # vb = pg.ViewBox()
        # vb.setAspectLocked()
        # v.setCentralItem(vb)
        # measureDock.addWidget(v, 0, 0)

        sketchPlot = pg.PlotWidget()
        sketchPlot.enableAutoRange('x', True)
        sketchPlot.enableAutoRange('y', True)
        sketchPlot.setAspectLocked(lock=True, ratio=1)
        sketchPlot.showGrid(x=1, y=1, alpha=0.8)
        sketchDock.addWidget(sketchPlot, 0, 0)

        histWidget = pg.HistogramLUTWidget()
        sketchDock.addWidget(histWidget, 0, 1)
        histWidget.setImageItem(img)


        sketchPlot.addItem(img)
        sketchPlot.plot(np.random.normal(size=100))




        measurePlot = pg.PlotWidget()
        measurePlot.plot(np.random.normal(size=100))
        measureDock.addWidget(measurePlot)
        # vb.addItem(img)
        # vb.autoRange()

        # measureDock.addWidget(v)

        ## d2.hide()

        # w5 = pg.ImageView()
        # w5.setImage(np.random.normal(size=(100,100)))
        # d5.addWidget(w5)

        # w6 = pg.PlotWidget(title="Dock 6 plot")
        # w6.plot(np.random.normal(size=100))
        # d6.addWidget(w6)

def print_process_id():
    print 'Process ID is:', os.getpid()

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('mainwindow3.ui', self)
        self.setWindowTitle('Merlins AFM sketching tool')
        self.setGeometry(1200,100,1000,800)
        self.addToolbars()



        self.plotSplitter.addWidget(Test())





    def addToolbars(self):

        spacer = QtGui.QWidget()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        exitAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_delete.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        captureAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0006_capture.png'), 'Capture', self)
        captureAction.triggered.connect(self.capture)
        capture_abortAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0008_capture_abort.png'), 'Capture Abort', self)
        capture_abortAction.triggered.connect(self.capture_abort)
        capture_forceAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0007_capture_force.png'), 'Capture Force', self)
        capture_forceAction.triggered.connect(self.capture_force)
        frame_downAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0004_frame_down.png'), 'Frame Down', self)
        frame_downAction.triggered.connect(self.frame_down)
        frame_upAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0003_frame_up.png'), 'Frame Up', self)
        frame_upAction.triggered.connect(self.frame_up)

        engageAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0005_engage.png'), 'Engage', self)
        engageAction.triggered.connect(self.engage)
        withdrawAction = QtGui.QAction(QtGui.QIcon('icons/afm/a_0000_withdraw.png'), 'Withdraw', self)
        withdrawAction.triggered.connect(self.withdraw)

        measureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_merlin.png'), 'Measure', self)
        measureAction.triggered.connect(self.measure)
        acceptMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_accept_merlin.png'), 'Save and Clear', self)
        acceptMeasureAction.triggered.connect(self.measure)
        favoriteMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_favourite_merlin.png'), 'Save as Favorite and Clear', self)
        favoriteMeasureAction.triggered.connect(self.measure)
        stopMeasureAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/photo_deny.png'), 'Stop Measure', self)
        stopMeasureAction.triggered.connect(self.measure)

        sketchAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_accept.png'), 'Sketch Now', self)
        sketchAction.triggered.connect(self.measure)
        abortSketchAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/bullet_deny.png'), 'Sketch Now', self)
        abortSketchAction.triggered.connect(self.measure)
        afmfolderAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_search.png'), 'AFM Image Folder', self)
        afmfolderAction.triggered.connect(self.measure)
        afmfolderReloadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/folder_reload.png'), 'Reload AFM Image Folder', self)
        afmfolderReloadAction.triggered.connect(self.measure)
        dxfLoadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_add.png'), 'Load dxf', self)
        dxfLoadAction.triggered.connect(self.measure)
        dxfReloadAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_refresh.png'), 'Reload dxf', self)
        dxfReloadAction.triggered.connect(self.measure)
        dxfClearAction = QtGui.QAction(QtGui.QIcon('icons/Hand Drawn Web Icon Set/note_deny.png'), 'Clear dxf', self)
        dxfClearAction.triggered.connect(self.measure)


        iconSize = QtCore.QSize(32,32)
        toolbar = self.addToolBar('Exit')
        toolbar.setIconSize(iconSize)
        toolbar.addAction(exitAction)

        plttoolbar = self.addToolBar('Sketching')
        plttoolbar.setIconSize(iconSize)
        plttoolbar.addAction(sketchAction)
        plttoolbar.addAction(abortSketchAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(afmfolderAction)
        plttoolbar.addAction(afmfolderReloadAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(dxfLoadAction)
        plttoolbar.addAction(dxfReloadAction)
        plttoolbar.addAction(dxfClearAction)
        plttoolbar.addSeparator()
        plttoolbar.addAction(measureAction)
        plttoolbar.addAction(favoriteMeasureAction)
        plttoolbar.addAction(acceptMeasureAction)
        plttoolbar.addAction(stopMeasureAction)

        afmToolbar = self.addToolBar('AFM')
        afmToolbar.setIconSize(iconSize)
        afmToolbar.addAction(engageAction)
        afmToolbar.addAction(withdrawAction)
        afmToolbar.addSeparator()
        afmToolbar.addAction(captureAction)
        afmToolbar.addAction(capture_forceAction)
        afmToolbar.addAction(capture_abortAction)
        afmToolbar.addSeparator()
        afmToolbar.addAction(frame_downAction)
        afmToolbar.addAction(frame_upAction)


    def measure(self):
        pass
    def engage(self):
        pass
    def withdraw(self):
        pass
    def frame_down(self):
        pass
    def frame_up(self):
        pass
    def capture(self):
        pass
    def capture_force(self):
        pass
    def capture_abort(self):
        pass



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    app.setStyle("plastique")
    window.setStyleSheet(style_sheet)

    # window.resize(1000,600)
    window.show()
    sys.exit(app.exec_())
