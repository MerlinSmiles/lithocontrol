#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic
import itertools
import sys

class SetTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.changed = False
        # self.name = data[0]
        # self.value = data[1]

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
            item = SetTreeItem(data, self.parentItem)
            self.childItems.insert(position, item)
        return True

    def appendRow(self, data):

        self.insertChildren(self.childCount, 1, self.columnCount())

        # print data

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
        if column < 0 or column >= len(self.itemData):
            return False
        # if self.set_model.rootData[column] == 'Angle':

        self.itemData[column] = value
        return True


class SetTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(SetTreeModel, self).__init__(parent)

        self.rootData = [header for header in headers] # Header Names
        self.rootItem = SetTreeItem(self.rootData)
        self.data = data
        self.setupModelData(self.data, self.rootItem)

        self._checked=[[False for i in xrange(self.columnCount())] for j in xrange(self.rowCount())]

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = self.getItem(index)
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

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
        success = parentItem.insertChildren(position, rows, self.rootItem.columnCount())
        self.endInsertRows()
        return success

    def appendRow(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows, self.rootItem.columnCount())
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

    def are_parent_and_child(self, parent, child):
        while child.isValid():
            if child == parent:
                return True
            child = child.parent()
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False
        self.layoutAboutToBeChanged.emit()

        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:
            self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)

        self.layoutChanged.emit()
        return result

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
        self.layoutAboutToBeChanged.emit()
        self.rootItem = TreeItem(self.rootData)
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)
        self.layoutChanged.emit()

    def setupModelData(self, data, parent):

        self.iterDict(self.data, parent)


    def iterDict(self, data, parent):
        print data
        for x in data:
            if not data[x]:
                continue
            if type(data[x]) == dict:

                parent.insertChildren(parent.childCount(), 1,self.rootItem.columnCount())

                thisChild = parent.child(parent.childCount() -1)
                node = QtGui.QStandardItem(x)
                node.setFlags(QtCore.Qt.NoItemFlags)
                self.iterDict(data[x], node)
                parent.appendRow(node)
            elif type(data[x]) in [float, int, str, bool]:
                value =  data[x]
                child0 = QtGui.QStandardItem(x)
                child0.setFlags(QtCore.Qt.NoItemFlags | QtCore.Qt.ItemIsEnabled)
                child1 = QtGui.QStandardItem(str(value))
                child1.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | ~ QtCore.Qt.ItemIsSelectable)
                child2 = QtGui.QStandardItem(type(value).__name__)
                child2.setFlags(QtCore.Qt.ItemIsEnabled)

                parent.appendRow([child0, child1, child2])



#     def xxx(self, data, parent):
#         columns = self.getColumns()
#         parents = [parent]
#         indentations = [0]

#         number = 0
#         layers = {}
#         parent_dict = {}
#         while number < len(data.entities):
#             parent = parents[-1]
#             parent.insertChildren(parent.childCount(), 1,self.rootItem.columnCount())

#             thisChild = parent.child(parent.childCount() -1)


#             for column in range(len(columns)):
#                 key = columns[column]
#                 if key in layers[layer]:
#                     thisChild.setData(column, layers[layer][key])

#             parent = parent_dict[layer]

#             parent.insertChildren(parent.childCount(), 1,
#                                 self.rootItem.columnCount())

#             thisChild = parent.child(parent.childCount() -1)

#             for column in range(len(columns)):
#                 if key in item_data:
#                     thisChild.setData(column, item_data[key])

#             number += 1

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
        ch0['curr_amp'] = 0
        ch0['amplitude'] = 1e-3
        ch0['min'] = -10 # +/- 100 mV is the minimum bipolar range
        ch0['max'] = 10
        ch0['plot_raw'] = True
        ch0['freq_chan'] = 0
        ch1 = self.data['in']['ch1'] = {}
        ch1['channel'] = "ai1"
        ch1['name'] = 'A-B'
        ch1['amplitude'] = 1*1e-3
        ch1['min'] = -10
        ch1['max'] = 10
        ch1['plot_raw'] = True
        ch1['freq_chan'] = 0
        ch1['curr_amp'] = 0


        # Layout
        self.tree_settings = QtGui.QTreeView()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tree_settings)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 600, 400)

        # Tree view
        self.set_model = SetTreeModel(['Parameter', 'Value', 'type'], self.data)
        self.tree_settings.setModel(self.set_model)
        self.tree_settings.setAlternatingRowColors(True)
        self.tree_settings.setSortingEnabled(True)
        self.tree_settings.setHeaderHidden(False)
        self.tree_settings.expandAll()

        for column in range(self.set_model.columnCount()):
            self.tree_settings.resizeColumnToContents(column)

        QtCore.QObject.connect(self.set_model, QtCore.SIGNAL('itemChanged(QModelIndex)'), self.test)
        QtCore.QObject.connect(self.tree_settings, QtCore.SIGNAL('valueChanged(QModelIndex)'), self.test)

    @QtCore.pyqtSlot("QModelIndex")
    def test(self, bla =None):
        print bla


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())
