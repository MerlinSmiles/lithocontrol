
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
        self.measureDock = pg_dock.Dock("Measuring R", size=(500,200))
        self.mConductanceDock = pg_dock.Dock("Measuring G", size=(500,200))
        self.dhtDock = pg_dock.Dock("DHT", size=(500,500))


        self.area.addDock(self.dhtDock, 'top')
        self.area.addDock(self.sketchDock, 'above', self.dhtDock)
        self.area.addDock(self.measureDock, 'bottom')
        self.area.addDock(self.mConductanceDock, 'bottom')


        data = pg.gaussianFilter(np.random.normal(size=(256, 256)), (20, 20))
        self.afmIm = pg.ImageItem(data)
        self.afmIm.setRect(pg.QtCore.QRectF(-20,-20,40,40))
        self.afmIm.setZValue(-1000)
        self.afmOffset = [0,0]
        self.afmAngle = 0
        self.afmX = 20
        self.afmY = 20

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

        self.mConductancePlot = pg.PlotWidget()
        self.mConductanceDock.addWidget(self.mConductancePlot)

        self.dhtPlot = pg.PlotWidget()
        self.dhtDock.addWidget(self.dhtPlot)

    def setAfmImage(self, image_data= None, x= None, y=None, offset=None, angle=None):
        if not (image_data is None):
            self.afmIm.clear()
            self.afmIm.setImage(image_data)
            self.image_shape = image_data.shape
        if not (offset == None):
            self.afmOffset = offset
        if not (angle == None):
            self.afmAngle = angle
        if not (x==None):
            self.afmX = x
        if not (y == None):
            self.afmY = y

        X = self.afmX
        Y = self.afmY
        dx,dy = self.afmOffset

        rect = [(-X/2.0)+dx,(-Y/2.0)+dy,X,Y]

        self.afmIm.setRect(pg.QtCore.QRectF(*rect))
        # print(image_data.shape)
        self.afmIm.setTransformOriginPoint(self.image_shape[0]/2.0,self.image_shape[1]/2.0)
        self.afmIm.setRotation(self.afmAngle)
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