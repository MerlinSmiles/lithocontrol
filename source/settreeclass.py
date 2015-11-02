#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic
import itertools
import sys

from collections import Iterable
def flatten(foo):
    for x in foo:
        if hasattr(x, '__iter__'):
            for y in flatten(x):
                yield y
        else:
            yield x


class SetTreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.parentKeys = []

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column=None):
        if column == None:
            return self.itemData[:]
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = SetTreeItem(data, self, self.model)
            self.childItems.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.insert(position, None)

        for child in self.childItems:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True

    def setData(self, column, value):
        self.itemData[column] = value
        return True

    def appendKeys(self, value):
        # for i in value:
        self.parentKeys.append(value)
        self.parentKeys = list(flatten(self.parentKeys))
        # x = self.parentKeys

        # self.parentKeys = x
        # self.parentKeys = list(itertools.chain.from_iterable(self.parentKeys))


class SetTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(SetTreeModel, self).__init__(parent)
        self.checks = {}

        self.rootData = [header for header in headers] # Header Names
        self.rootItem = SetTreeItem(self.rootData, model=self)
        self.rootDict = data
        self.iterDict(data, self.rootItem)
        self.display()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = self.getItem(index)
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def checkState(self, index):
        return self.getItem(index).checkState

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column=0, parent=QtCore.QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def insertColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows,
                self.rootItem.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def childCount(self, parent=QtCore.QModelIndex()):
        return self.rowCount(parent)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False
        if index.column() != 1:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:
            self.emit(QtCore.SIGNAL('settingsChanged(QModelIndex)'), index)
            return True
        return False

    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole or orientation != QtCore.Qt.Horizontal:
            return False

        result = self.rootItem.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def getColumns(self):
        columns = []
        for i in range(self.columnCount()):
            columns.append(self.headerData(i,QtCore.Qt.Horizontal))
        return columns

    def getRows(self):
        rows = []
        for i in range(self.rowCount()):
            rows.append(self.getItem(self.index(i)))
        return rows

    def clearData(self):
        self.rootItem = SetTreeItem(self.rootData, model=self)

    def display(self):
        return self.g_dict(self.rootItem)[self.rootItem.data(0)]

    def g_dict(self, item):
        data = {}
        if item.childCount() > 0:
            data[item.data(0)]= {}
            for i in item.childItems:
                p = self.g_dict(i)
                key = i.data(0)
                for key in p.keys():
                    data[item.data(0)][key] = p[key]
        else:
            key = item.data(0)
            value = item.data(1)
            data[key] = value
        return data

    def iterDict(self, data, parent):
        for x in data:
            if not data[x]:
                continue
            if type(data[x]) == dict:
                parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
                thisChild = parent.child(parent.childCount() -1)
                thisChild.setData(0, x)
                thisChild.appendKeys(parent.parentKeys)
                thisChild.appendKeys(x)
                self.iterDict(data[x], thisChild)
            elif type(data[x]) in [float, int, str, bool, list]:
                value =  data[x]
                parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
                thisChild = parent.child(parent.childCount() -1)

                thisChild.appendKeys(parent.parentKeys)
                thisChild.appendKeys(x)
                thisChild.setData(0, x)
                thisChild.setData(1, value)
                thisChild.setData(2, type(value).__name__)


class Example(QtGui.QWidget):

    def __init__(self):

        super(Example, self).__init__()

        self.data = {}
        self.data['settings'] = {}
        self.data['settings']['buffer_size'] = 10000000
        self.data['settings']['acq_rate'] = 30000          # samples/second
        self.data['settings']['acq_samples'] = 1000        # every n samples
        self.data['settings']['device_input'] = "PCI-6251"
        self.data['settings']['SR_sensitivity'] = 100e-9
        self.data['settings']['PAR_sensitivity'] = 1e-3
        self.data['settings']['plot_2pt'] = True
        self.data['settings']['plot_4pt'] = True
        self.data['settings']['plot_current'] = True
        self.data['settings']['plotR'] = True
        self.data['settings']['DHTport'] = 6

        self.data['in'] = {}
        ch0 = self.data['in']['ch0'] = {}
        ch0['channel'] = "ai0"
        ch0['name'] = 'Current'
        ch0['curr_amp'] = '0'
        ch0['amplitude'] = 1e-3
        ch0['min'] = -10 # +/- 100 mV is the minimum bipolar range
        ch0['max'] = 10
        ch0['plot_raw'] = True
        ch0['freq_chan'] = '0'
        ch1 = self.data['in']['ch1'] = {}
        ch1['channel'] = "ai1"
        ch1['name'] = 'A-B'
        ch1['amplitude'] = 1*1e-3
        ch1['min'] = -10
        ch1['max'] = 10
        ch1['plot_raw'] = True
        ch1['freq_chan'] = '0'
        ch1['curr_amp'] = '0'


        # Layout
        self.settings_tree = QtGui.QTreeView()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.settings_tree)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 600, 400)

        # Tree view
        self.settings_model = SetTreeModel(['Parameter', 'Value', 'type'], self.data)
        self.settings_tree.setModel(self.settings_model)
        self.settings_tree.setAlternatingRowColors(True)
        self.settings_tree.setSortingEnabled(True)
        self.settings_tree.setHeaderHidden(False)

        self.settings_tree.expandAll()

        for column in range(self.settings_model.columnCount()):
            self.settings_tree.resizeColumnToContents(column)

        print( self.settings_model.display() )


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())
