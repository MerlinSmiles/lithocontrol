# Updated so a PyQT4 Designer TabWidget can be promoted to a FingerTabWidget

from PyQt4 import QtGui, QtCore
import sys

class FingerTabBarWidget(QtGui.QTabBar):
    def __init__(self, parent=None, *args, **kwargs):
        self.tabSize = QtCore.QSize(kwargs.pop('width',100), kwargs.pop('height',25))
        QtGui.QTabBar.__init__(self, parent, *args, **kwargs)

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()

        # option.palette.setColor(QtGui.QPalette.Window, QtGui.QColor('#FF0000'))

        for index in range(self.count()):
            self.initStyleOption(option, index)
            tabRect = self.tabRect(index)
            tabRect.moveLeft(10)


            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            # painter.fillRect(tabRect, QtGui.QColor('#FF0000'))
            painter.fillRect(tabRect, QtGui.QBrush(QtGui.QColor(128, 128, 255, 128)));
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter |\
                             QtCore.Qt.TextDontClip, \
                             self.tabText(index));
        painter.end()
    def tabSizeHint(self,index):
        return self.tabSize

# Shamelessly stolen from this thread:
#   http://www.riverbankcomputing.com/pipermail/pyqt/2005-December/011724.html
class FingerTabWidget(QtGui.QTabWidget):
    """A QTabWidget equivalent which uses our FingerTabBarWidget"""
    def __init__(self, parent, *args):
        QtGui.QTabWidget.__init__(self, parent, *args)
        self.setTabBar(FingerTabBarWidget(self))



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    tabs = QtGui.QTabWidget()
    tabs.setTabBar(FingerTabBarWidget(width=100,height=25))
    digits = ['Thumb','Pointer','Rude','Ring','Pinky']
    for i,d in enumerate(digits):
        widget =  QtGui.QLabel("Area #%s <br> %s Finger"% (i,d))
        tabs.addTab(widget, d)
    tabs.setTabPosition(QtGui.QTabWidget.West)
    tabs.show()
    sys.exit(app.exec_())