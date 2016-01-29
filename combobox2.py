
# from PyQt4 import QtGui,QtCore
# import sys

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT
import sys


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

class ColorModel(QtCore.QAbstractListModel):
    def __init__(self, *args, **kwargs):
        QtCore.QAbstractListModel.__init__(self, *args, **kwargs)
        self.items=[]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() is True:
            if role == QtCore.Qt.DisplayRole:
                return self.items[index.row()]
            elif role == QtCore.Qt.ItemDataRole:
                return self.items[index.row()]
            elif role==QtCore.Qt.DecorationRole:
                # print(self.items[index.row()])
                k = self.items[index.row()]
                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(QtGui.QColor(*kelly_colors[k]))
                icon = QtGui.QIcon(pixmap)
                return icon
            # print(role)
        return None

    def addColors(self,colors):
        for k in sorted(colors):
            self.addItem(k)

    def addItem(self, item):
        # index=QtCore.QModelIndex()
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.items.append(item)
        self.endInsertRows()



class myMainWindow(QtGui.QMainWindow):
    colorSelected = QtCore.pyqtSignal(str)
    closeColor = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.colorModel = ColorModel()
        self.colorDict = kelly_colors
        self.colorModel.addColors(self.colorDict)

        combo = QtGui.QComboBox()
        combo.setModel(self.colorModel)
        self.setCentralWidget(combo)

        combo.activated[str].connect(self.onActivated)

        self.show()

    def onActivated(self, text):
        print(text)




# def changedFocusSlot(old, now):
#     print(old,now)
#     if (now==None):
#         print ("set focus to the active window")
#         # QtGui.QApplication.activeWindow().setFocus()

def main():
    app      = QtGui.QApplication(sys.argv)
    # QtCore.QObject.connect(app, SIGNAL("focusChanged(QWidget *, QWidget *)"), changedFocusSlot)
    window   = myMainWindow()
    # menu     = ColorMenu()

    #Resize width and height
    # window.resize(250,250)
    window.setWindowTitle('PyQt Context Menu Example')
    window.setContextMenuPolicy(QtCore.Qt.CustomContextMenu);

    window.connect(window,SIGNAL("customContextMenuRequested(QPoint)"),
                    window,SLOT("contextMenuRequested(QPoint)"))
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
