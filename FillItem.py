from PyQt4 import QtGui
import pyqtgraph as pg

class FillItem(QtGui.QGraphicsPathItem):
    """
    GraphicsItem filling the space between two PlotDataItems.
    """
    def __init__(self, curve1=None, curve2=None, brush=None):
        QtGui.QGraphicsPathItem.__init__(self)
        self.curves = None
        if curve1 is not None and curve2 is not None:
            self.setCurves(curve1, curve2)
        elif curve1 is not None or curve2 is not None:
            raise Exception("Must specify two curves to fill between.")

        if brush is not None:
            self.setBrush(pg.mkBrush(brush))
        self.updatePath()

    def setCurves(self, curve1, curve2):
        """Set the curves to fill between.

        Arguments must be instances of PlotDataItem or PlotCurveItem.

        Added in version 0.9.9
        """

        if self.curves is not None:
            for c in self.curves:
                try:
                    c.sigPlotChanged.disconnect(self.curveChanged)
                except (TypeError, RuntimeError):
                    pass

        curves = [curve1, curve2]
        for c in curves:
            if not isinstance(c, pg.PlotDataItem) and not isinstance(c, pg.PlotCurveItem):
                raise TypeError("Curves must be PlotDataItem or PlotCurveItem.")
        self.curves = curves
        curve1.sigPlotChanged.connect(self.curveChanged)
        curve2.sigPlotChanged.connect(self.curveChanged)
        self.setZValue(min(curve1.zValue(), curve2.zValue())-1)
        self.curveChanged()

    def setBrush(self, *args, **kwds):
        """Change the fill brush. Acceps the same arguments as pg.mkBrush()"""
        QtGui.QGraphicsPathItem.setBrush(self, pg.mkBrush(*args, **kwds))

    def curveChanged(self):
        self.updatePath()

    def updatePath(self):
        if self.curves is None:
            self.setPath(QtGui.QPainterPath())
            return
        paths = []
        for c in self.curves:
            if isinstance(c, pg.PlotDataItem):
                paths.append(c.curve.getPath())
            elif isinstance(c, pg.PlotCurveItem):
                paths.append(c.getPath())

        path = QtGui.QPainterPath()
        p1 = paths[0].toSubpathPolygons()
        p2 = paths[1].toReversed().toSubpathPolygons()
        if len(p1) == 0 or len(p2) == 0:
            self.setPath(QtGui.QPainterPath())
            return

        path.addPolygon(p1[0] + p2[0])
        self.setPath(path)