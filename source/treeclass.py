#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic
from source.dxf2shape import *
import itertools

class TreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.dxfData = None
        self.pltData = None
        self.entity = None
        self.pltHandle = []
        self.checkState = QtCore.Qt.Unchecked
        self.fillAngle = 0
        self.fillStep = 0.1
        self.volt = 10
        self.rate = 1.0
        self.length = 0.0
        self.sketchTime = 0.0
#     shape.type = None # [VirtualElectrode, line, area]

    def redraw(self):
        if self.entity != None:
            self.setDxfData(dxf2shape(self.entity, fill_step = self.fillStep, fill_angle=self.fillAngle))

    def setCheckState(self, value):
        if value == 2:
            self.checkState = QtCore.Qt.Checked
        elif value == 1:
            self.checkState = QtCore.Qt.PartiallyChecked
        else:
            self.checkState = QtCore.Qt.Unchecked
        return self.checkState

    def setEntity(self, entity):
        self.entity = entity
        self.redraw()

    def setDxfData(self, data):
        self.dxfData = data
        self.pltData = []
        for k in self.dxfData:
            self.pltData.append(k.reshape((-1,2)))
        self.calcTime()

    def calcLength(self):
        try:
            dat = np.concatenate(self.pltData).reshape((-1,2))
        except:
            print 'error calculating length'
            return
        dat_b = np.roll(dat,-2)
        dist = 0
        for k in range(len(dat)-1):
            dist += np.linalg.norm(dat[k]-dat_b[k])

        self.length = dist

    def calcTime(self):
        self.calcLength()
        self.sketchTime = self.length / float(self.rate)

        self.setData(5,round(float(self.sketchTime),1))


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
            item = TreeItem(data, self, self.model)
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
        if column < 0 or column >= len(self.itemData):
            return False
        if self.model.rootData[column] == 'Angle':
            value= float(value)
            if self.fillAngle != value:
                self.fillAngle = value
                self.redraw()
        elif self.model.rootData[column] == 'Rate':
            value= float(value)
            if self.rate != value:
                self.rate = value
                self.calcTime()
        elif self.model.rootData[column] == 'Step':
            value= float(value)
            if self.fillStep != value:
                self.fillStep = value
                self.redraw()
        elif self.model.rootData[column] == 'Closed':
            value= bool(value)
            if self.entity.is_closed != value:
                self.entity.is_closed = value
        elif self.model.rootData[column] == 'Time':
            value= float(value)
            # return True
            if self.sketchTime != value:
                self.sketchTime = value

        self.itemData[column] = value
        if self.model.rootData[column] in  ['Voltage', 'Angle', 'Rate', 'Step']:
            for ch in self.childItems:
                ch.setData(column, value)
        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.checks = {}

        self.rootData = [header for header in headers] # Header Names
        self.rootItem = TreeItem(self.rootData, model=self)
        self.setupModelData(data, self.rootItem)

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

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

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

    def are_parent_and_child(self, parent, child):
        while child.isValid():
            if child == parent:
                return True
            child = child.parent()
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if (role == QtCore.Qt.CheckStateRole and index.column() == 0):
            self.layoutAboutToBeChanged.emit()
            item = self.getItem(index)

            item.setCheckState(value)
            self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index)

            cc = item.childCount()
            if cc > 0:
                for i in range(cc):
                    chindex =  self.createIndex(i, 0, item.child(i))
                    self.setData(chindex,value,role)


            item = self.getItem(index.parent())
            cc = item.childCount()
            no_checked = 0
            if cc > 0:
                item.sketchTime = 0.0
                item.setData(5,item.sketchTime)
                for i in range(cc):
                    if item.child(i).checkState == 2:
                        no_checked+=1

                        item.sketchTime += item.child(i).sketchTime
                        if item.child(i).childCount() == 0:
                            item.setData(5,item.sketchTime)
                if no_checked == cc:
                    item.setCheckState(2)
                elif no_checked > 0:
                    item.setCheckState(1)
                else:
                    item.setCheckState(0)
                # self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index.parent())

            self.layoutChanged.emit()
            return True

        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:
            self.emit(QtCore.SIGNAL('redraw(QModelIndex)'), index)
            self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)
                # , value

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
        self.rootItem = TreeItem(self.rootData, model=self)

    def setupModelData(self, data, parent):
        columns = self.getColumns()
        parents = [parent]
        indentations = [0]

        number = 0
        layers = {}
        parent_dict = {}
        while number < len(data.entities):
            # entities are right in dxf file!!
            entity = data.entities[number]
            if entity.dxftype not in ['POLYLINE','LINE']:
                number +=1
                continue
            if entity.dxftype == 'LINE':
                entity.is_closed = False
            layer = entity.layer
            parent = parents[-1]
            # columnData = ['Name', 'Type']
            if layer not in layers:
                layers[layer] = {'Name': layer, 'Type': 'Layer'}
                parent.insertChildren(parent.childCount(), 1,
                                    self.rootItem.columnCount())

                parent_dict[layer] = parent.child(parent.childCount() -1)
                thisChild = parent.child(parent.childCount() -1)


                for column in range(len(columns)):
                    key = columns[column]
                    if key in layers[layer]:
                        thisChild.setData(column, layers[layer][key])

                # for column in range(len(columnData)):
                    # parent.child(parent.childCount() -1).setData(column, layers[layer][columnData[column]])
                    # columnData[column], layers[layer][columnData[column]]

            parent = parent_dict[layer]

            parent.insertChildren(parent.childCount(), 1,
                                self.rootItem.columnCount())

            thisChild = parent.child(parent.childCount() -1)
            # print thisChild

            # entity.is_closed = True
            thisChild.setEntity(entity)

            # print self.headerData(0,QtCore.Qt.Horizontal)

            # print str(entity.is_closed)
            item_data = {'Name': 'Id'+str(number),
                         'Type': entity.dxftype,
                         'Closed': entity.is_closed,
                         'Voltage': thisChild.volt,
                         'Angle': thisChild.fillAngle,
                         'Rate': thisChild.rate,
                         'Step': thisChild.fillStep,
                         'Time': thisChild.sketchTime}
            # print columnData
            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
                    thisChild.setData(column, item_data[key])

            number += 1

