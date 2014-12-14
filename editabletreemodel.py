#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic


import pyqtgraph as pg

# %load_ext autoreload
# %autoreload 2

# import sys
# import os
# import time
import operator
# import dxfgrabber
# from collections import Counter
import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
# from scipy.interpolate import interp1d
from source.helpers import *
from source.dxf2shape import *
filename = './dxfTest.dxf'




import editabletreemodel_rc
from ui_mainwindow import Ui_MainWindow


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.ss = 'ss'
        self.dxfData = None

    def setDxfData(self, data):
        self.dxfData = data

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

    def data(self, column):
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self)
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

        self.itemData[column] = value

        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.checks = {}

        rootData = [header for header in headers] # Header Names
        self.rootItem = TreeItem(rootData)
        self.setupModelData(data, self.rootItem)

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
        while index.isValid():
            if index in self.checks:
                return self.checks[index]
            index = index.parent()
        return QtCore.Qt.Unchecked

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
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

    def are_parent_and_child(self, parent, child):
        while child.isValid():
            if child == parent:
                return True
            child = child.parent()
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if (role == QtCore.Qt.CheckStateRole and index.column() == 0):
            # self.checks[index] = value
            # item = self.getItem(index).items()
            # print index
            # print value
            self.layoutAboutToBeChanged.emit()
            for i, v in self.checks.items():
                if self.are_parent_and_child(index, i):
                    self.checks.pop(i)
            self.checks[index] = value
            self.layoutChanged.emit()

            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
                # self.setData( self.getItem(index).child(i), value, role)
                # print self.getItem(i)
                # child = self.index(i,0, index)
                # print child
            return True

        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

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


    def setupModelData(self, data, parent):
        columns = self.getColumns()
        parents = [parent]
        indentations = [0]

        number = 0
        layers = {}
        parent_dict = {}
        while number < len(data.entities):
            entity = data.entities[number]
            if entity.dxftype not in ['POLYLINE']:
                number +=1
                continue
            layer = entity.layer
            parent = parents[-1]
            columnData = ['Name', 'Type']
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
                    # print columnData[column], layers[layer][columnData[column]]

            parent = parent_dict[layer]

            parent.insertChildren(parent.childCount(), 1,
                                self.rootItem.columnCount())

            thisChild = parent.child(parent.childCount() -1)
            print thisChild

            entity.is_closed = True
            thisChild.setDxfData(dxf2shape(entity, fill_step = 0.01, fill_angle=np.random.random()*360))

            # print self.headerData(0,QtCore.Qt.Horizontal)


            # print str(np.shape(thisChild.dxfData[0]))

            # print str(entity.is_closed)
            item_data = {'Name': 'Name', 'Type': entity.dxftype, 'Closed': entity.is_closed, 'Voltage': '0'}
            # print columnData
            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
                    thisChild.setData(column, item_data[key])

            number += 1



# class dxf(object): # (this could be a tree or list view class
#     dxf.add_shape(entity, volt=None, speed=None, parent=Layer)  # None takes parameters from global
#     dxf.layer(id=None) # None returns all layers, else the ID is a list with the layer ids, returns list with layers
#     dxf.shape(id=None) # None returns all shapes, else the ID is a list with the shape ids, returns list with shapes

# class shape(object):
#     shape.volt = None
#     shape.speed = None
#     shape.type = None # [VirtualElectrode, line, area]


# class sketch(object): # this could be a list view, that could make a schedule list :) with drag and drop and stuff
#                       # Maybe there could be a drag and drop from the dxf tree to the schedule
#     sketch.add( shape, volt, speed )
#     sketch.remove( que_id )
#     sketch.queue()
#     sketch.run()
#     sketch.abort()
#     sketch.status()
#     sketch.save_queue()



# dxf = dxfgrabber.readfile(filename)
# shapes = []
# for i in dxf.entities:
#     if i.dxftype not in ['POLYLINE']:
#         continue
# #     print i.layer
#     i.is_closed = True

#     shapes.append( shape(i) )
#     collection = dxf2shape(i, fill_step = 0.01, fill_angle=np.random.random()*360)

# colors = plt.cm.rainbow(np.linspace(0, 1, len(shapes)))
# for y, c in zip(ys, colors):
#     plt.scatter(x, y, color=c)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('mainwindow.ui', self)

        # self.setupUi(self)

        headers = ('Name', 'Voltage', 'Speed', 'Closed', 'Type')

        # file = QtCore.QFile(':/default.txt')
        # file.open(QtCore.QIODevice.ReadOnly)
        dxf = dxfgrabber.readfile(filename)
        model = TreeModel(headers, dxf)

        # file.close()

        self.view.setModel(model)
        self.view.expandAll()
        for column in range(model.columnCount()):
            self.view.resizeColumnToContents(column)

        self.exitAction.triggered.connect(QtGui.qApp.quit)

        self.view.selectionModel().selectionChanged.connect(self.updateActions)

        self.actionsMenu.aboutToShow.connect(self.updateActions)
        self.insertRowAction.triggered.connect(self.insertRow)
        self.insertColumnAction.triggered.connect(self.insertColumn)
        self.removeRowAction.triggered.connect(self.removeRow)
        self.removeColumnAction.triggered.connect(self.removeColumn)
        self.insertChildAction.triggered.connect(self.insertChild)


        self.pi = self.plotView.getPlotItem()
        self.pi.enableAutoRange('x', True)
        self.pi.enableAutoRange('y', True)
        self.plot = self.pi.plot()

        QtCore.QObject.connect(self.view.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        self.updateActions()

    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def update_plot(self, selected, deselected):
        index = selected.indexes()
        model = self.view.model()
        # child = index.ss
        for idx in index:
            # print idx.row()
            # parent = idx.parent()
            data = model.getItem(idx).dxfData

            # thisChild = parent.child(parent.childCount() -1)

            # print(deselected)

            # self.plotlist = []
            # for i in self.settings['channels']:
                # self.plotlist.append({'plot': pi.plot(), 'channel': i})
            # pl = pi.plot()
            x = []
            y = []
            for i in data:
            # print data
                pt = i.flatten()
                x.append(pt[::2])
                y.append(pt[1::2])
                # self.pi = self.plotView.getPlotItem()
                # self.pi.enableAutoRange('x', True)
                # self.pi.enableAutoRange('y', True)
                # self.plot = self.pi.plot()
                    # CS = plt.plot(pt[::2],pt[1::2],'-',color=c)
            x=np.array(x).flatten()
            y=np.array(y).flatten()
            print x
            self.plot.setData(x=np.array(x),y=np.array(y))
            # print np.shape(data)
            # self.plot.setData(y=data[:,1])
            # self.plot1 = pi.plot()
            # pi.setRange(xRange=(0,self.settings['buffer_size']/10),yRange=(-1.2,1.2))


    def insertChild(self):
        index = self.view.selectionModel().currentIndex()
        model = self.view.model()

        if model.columnCount(index) == 0:
            if not model.insertColumn(0, index):
                return

        if not model.insertRow(0, index):
            return

        for column in range(model.columnCount(index)):
            child = model.index(0, column, index)
            model.setData(child, "[No data]", QtCore.Qt.EditRole)
            if model.headerData(column, QtCore.Qt.Horizontal) is None:
                model.setHeaderData(column, QtCore.Qt.Horizontal,
                        "[No header]", QtCore.Qt.EditRole)

        self.view.selectionModel().setCurrentIndex(model.index(0, 0, index),
                QtGui.QItemSelectionModel.ClearAndSelect)
        self.updateActions()

    def insertColumn(self):
        model = self.view.model()
        column = self.view.selectionModel().currentIndex().column()

        changed = model.insertColumn(column + 1)
        if changed:
            model.setHeaderData(column + 1, QtCore.Qt.Horizontal,
                    "[No header]", QtCore.Qt.EditRole)

        self.updateActions()

        return changed

    def insertRow(self):
        index = self.view.selectionModel().currentIndex()
        model = self.view.model()

        if not model.insertRow(index.row()+1, index.parent()):
            return

        self.updateActions()

        for column in range(model.columnCount(index.parent())):
            child = model.index(index.row()+1, column, index.parent())
            model.setData(child, "[No data]", QtCore.Qt.EditRole)

    def removeColumn(self):
        model = self.view.model()
        column = self.view.selectionModel().currentIndex().column()

        changed = model.removeColumn(column)
        if changed:
            self.updateActions()

        return changed

    def removeRow(self):
        index = self.view.selectionModel().currentIndex()
        model = self.view.model()

        if (model.removeRow(index.row(), index.parent())):
            self.updateActions()

    def updateActions(self):
        hasSelection = not self.view.selectionModel().selection().isEmpty()
        self.removeRowAction.setEnabled(hasSelection)
        self.removeColumnAction.setEnabled(hasSelection)

        hasCurrent = self.view.selectionModel().currentIndex().isValid()
        self.insertRowAction.setEnabled(hasCurrent)
        self.insertColumnAction.setEnabled(hasCurrent)

        if hasCurrent:
            self.view.closePersistentEditor(self.view.selectionModel().currentIndex())

            row = self.view.selectionModel().currentIndex().row()
            column = self.view.selectionModel().currentIndex().column()
            if self.view.selectionModel().currentIndex().parent().isValid():
                self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
            else:
                self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
