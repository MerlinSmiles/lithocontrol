
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import numpy as np

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.dockarea as pg_dock


class niPlotFrame(QtGui.QWidget):
    def __init__( self, parent=None):
        super(niPlotFrame, self).__init__(parent)
        self.area = pg_dock.DockArea()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.area)
        self.setLayout(layout)

        self.mResistanceDock = pg_dock.Dock("Measuring R", size=(2000,400))
        self.mConductanceDock = pg_dock.Dock("Measuring G", size=(2000,400))
        self.dhtDock = pg_dock.Dock("DHT", size=(2000,200))


        self.area.addDock(self.mResistanceDock, 'top')
        self.area.addDock(self.mConductanceDock, 'bottom')
        self.area.addDock(self.dhtDock, 'bottom')


        self.mResistanceeasurePlot = pg.PlotWidget()
        self.mResistanceeasurePlot.setClipToView(True)
        self.mResistanceDock.addWidget(self.mResistanceeasurePlot)

        self.mConductancePlot = pg.PlotWidget()
        self.mConductancePlot.setClipToView(True)
        self.mConductanceDock.addWidget(self.mConductancePlot)

        self.dhtPlot = pg.PlotWidget()
        self.dhtDock.addWidget(self.dhtPlot)

    def savePlot(self, fileName):
        # create an exporter instance, as an argument give it
        # the item you wish to export
        exporter = pg.exporters.ImageExporter(self.sketchPlot.getPlotItem())

        # set export parameters if needed
        exporter.parameters()['width'] = 2048

        # save to file
        exporter.export(fileName)