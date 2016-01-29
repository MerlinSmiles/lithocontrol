import re
import os
import sys
from PyQt4 import QtCore
from PyQt4.QtGui import *
sys.path.append("./style/")
import style_dark_orange



def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

class MyWindow(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        # css = QtCore.QFile('./style/darkorange.css')
        # css.open(QtCore.QIODevice.ReadOnly)
        # if css.isOpen():
        #     self.setStyleSheet(QtCore.QVariant(css.readAll()).toString())
        # css.close()
        # # self.setStyleSheet()

        # create table
        self.var_voltage = [['Virtual Electrodes', 25.0],
                            ['Contacts', 22.0],
                            ['Device', 10.0],
                            ['Erase', -10]]
        table = self.createTable()

        # layout
        layout = QVBoxLayout()
        layout.addWidget(table)
        self.setLayout(layout)


    def createTable(self):
        # create the view
        tv = QTableView()

        # set the table model
        header = ['Variable', 'Value']
        tm = MyTableModel(self.var_voltage, header, self)
        tv.setSortingEnabled(False)
        tv.setModel(tm)

        # set the minimum size
        self.setMinimumSize(400, 300)

        # hide vertical header
        tv.verticalHeader().setVisible(False)
        # set horizontal header properties
        # hh = tv.horizontalHeader()
        # hh.setStretchLastSection(True)

        # set column width to fit contents
        tv.resizeColumnsToContents()

        # # set row height
        # nrows = len(self.var_voltage)
        # for row in xrange(nrows):
        #     tv.setRowHeight(row, 18)

        # enable sorting
        # this doesn't work
        tv.setSortingEnabled(True)

        return tv

class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None, *args):
        super(MyTableModel, self).__init__(parent, *args)
        self.arraydata = datain
        self.headerdata = headerdata
        print('Make Table sorted')
        print('How to add extra lines? maybe the easies is to just add + buttons')

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        # elif role != QtCore.Qt.DisplayRole:
        #     return

        # if (role == QtCore.Qt.BackgroundRole) & (index.column() == 0) & (item.childCount()>0):
        #     return QtGui.QColor(70,70,70,80)

           # if (role == Qt::BackgroundRole)
           # {
           #     if (condition1)
           #        return QColor(Qt::red);
           #     else
           #        return QColor(Qt::green);


        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None
        # if index.row()>=len(self.arraydata):
        #     return[['']*self.columnCount()]
        return self.arraydata[index.row()][index.column()]
        # return item.data(index.column())

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headerdata[col]
        return

    def flags(self, index):
        # if not index.isValid():
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEditable
        # flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        # return flags

if __name__ == "__main__":
    main()
