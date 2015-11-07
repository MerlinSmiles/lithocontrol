
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


class PlotFrame(QtGui.QWidget):
    def __init__( self, parent=None):
        super(PlotFrame, self).__init__(parent)
        self.area = pg_dock.DockArea()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.area)
        self.setLayout(layout)

        self.sketchDock = pg_dock.Dock("Skecthing", size=(500, 500))     ## give this dock the minimum possible size
        self.measureDock = pg_dock.Dock("Measuring", size=(500,200))
        self.dhtDock = pg_dock.Dock("DHT", size=(500,200))


        self.area.addDock(self.sketchDock, 'top')
        self.area.addDock(self.dhtDock, 'bottom')
        self.area.addDock(self.measureDock, 'above',self.dhtDock)


        data = pg.gaussianFilter(np.random.normal(size=(256, 256)), (20, 20))
        self.afmIm = pg.ImageItem(data)
        self.afmIm.setRect(pg.QtCore.QRectF(-20,-20,40,40))
        self.afmIm.setZValue(-1000)

        self.sketchPlot = pg.PlotWidget()
        self.sketchPlot.enableAutoRange('x', True)
        self.sketchPlot.enableAutoRange('y', True)
        self.sketchPlot.setAspectLocked(lock=True, ratio=1)
        self.sketchPlot.showGrid(x=1, y=1, alpha=0.8)
        self.sketchDock.addWidget(self.sketchPlot, 0, 0)


        self.histWidget = pg.HistogramLUTWidget()
        self.sketchDock.addWidget(self.histWidget, 0, 1)

        self.histWidget.setImageItem(self.afmIm)
        self.sketchPlot.addItem(self.afmIm)

        self.measurePlot = pg.PlotWidget()
        self.measureDock.addWidget(self.measurePlot)

        self.dhtPlot = pg.PlotWidget()
        self.dhtDock.addWidget(self.dhtPlot)

    def setAfmImage(self, image_data, x= None, y=None):
        self.afmIm.clear()
        self.afmIm.setImage(image_data)
        if not (x==None or y == None):
            self.afmIm.setRect(pg.QtCore.QRectF(-x/2.0, -y/2.0, x, y))
        self.histWidget.setImageItem(self.afmIm)

    def clearSketchPlot(self):
        # return
        self.sketchPlot.clear()
        # self.histWidget.setImageItem(self.afmIm)
        self.sketchPlot.addItem(self.afmIm)

    def savePlot(self, fileName):
        # create an exporter instance, as an argument give it
        # the item you wish to export
        exporter = pg.exporters.ImageExporter(self.sketchPlot.getPlotItem())

        # set export parameters if needed
        exporter.parameters()['width'] = 2048

        # save to file
        exporter.export(fileName)