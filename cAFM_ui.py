#!/usr/bin/env python

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, uic

import pyqtgraph as pg
import pyqtgraph.exporters

# %load_ext autoreload
# %autoreload 2

import sys

if sys.platform.startswith('darwin'):
    parentos = 'OSX'
    afmImageFolder = './AFMimages/'

elif sys.platform.startswith('win32'):
    parentos = 'WIN'
    from convertAFM import convertAFM
    # afmfile = './data.npz'
    afmFile = './stomilling.002'
    afmImageFolder = 'D:/lithography/AFMimages/'


filename = './dxfTest.dxf'

import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
# import operator
# import dxfgrabber
# from collections import Counter
# import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
# from scipy.interpolate import interp1d
from source.helpers import *
from source.dxf2shape import *

# mkPen for selected
orangePen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
bluePen = pg.mkPen(color='0000FF')  #, style=QtCore.Qt.DotLine
greenPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine

class MyHandler(PatternMatchingEventHandler):
    def __init__(self, parent = None):
        super( MyHandler, self ).__init__()
        self.parent = parent
        patterns = ["*.*"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        # print event.src_path, event.event_type  # print now only for degug

        self.parent.emit(QtCore.SIGNAL("AFMimage(QString)"), event.src_path)

    # def on_modified(self, event):
    #     self.process(event)

    def on_created(self, event):
        self.process(event)

class AFMWorker(QtCore.QThread):

    def __init__(self, parent = None):

        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.foldername = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def monitor(self, foldername):
        self.exiting = False
        self.foldername = foldername
        self.start()

    def stop(self):
        self.exiting = True
        self.wait()

    def run(self):
        observer = Observer()
        observer.schedule(MyHandler(self), path=self.foldername)
        observer.start()
        while True and not self.exiting:
            time.sleep(3)
        observer.stop()
        observer.join()

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
        self.fillStep = 0.05
        self.volt = 10
        self.speed = 1
#     shape.type = None # [VirtualElectrode, line, area]

    def redraw(self):
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
        if len(self.dxfData)>0:
            self.pltData = []
            for k in self.dxfData:
                self.pltData.append(k.reshape((-1,2)))

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
            self.fillAngle = value
            self.redraw()
        elif self.model.rootData[column] == 'Step':
            self.fillStep = value
            self.redraw()
        elif self.model.rootData[column] == 'Closed':
            self.entity.is_closed = value
            self.redraw()

        self.itemData[column] = value
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
                for i in range(cc):
                    if item.child(i).checkState == 2:
                        no_checked+=1
                if no_checked == cc:
                    item.setCheckState(2)
                elif no_checked > 0:
                    item.setCheckState(1)
                else:
                    item.setCheckState(0)
                # self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index.parent())

            self.layoutChanged.emit()
            return True

        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            # if self.rootData[index.column()] == 'Angle':
            #     item.redraw()

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


    def setupModelData(self, data, parent):
        columns = self.getColumns()
        parents = [parent]
        indentations = [0]

        number = 0
        layers = {}
        parent_dict = {}
        while number < len(data.entities):
            entity = data.entities[number]
            print entity.is_closed
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
            # print thisChild

            # entity.is_closed = True
            thisChild.setEntity(entity)

            # print self.headerData(0,QtCore.Qt.Horizontal)

            # print str(entity.is_closed)
            item_data = {'Name': 'Name', 'Type': entity.dxftype,
                         'Closed': entity.is_closed,
                         'Voltage': thisChild.volt,
                         'Angle': thisChild.fillAngle,
                         'Speed': thisChild.speed,
                         'Step': thisChild.fillStep}
            # print columnData
            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
                    thisChild.setData(column, item_data[key])

            number += 1


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('mainwindow2.ui', self)
        self.actionExit.triggered.connect(QtGui.qApp.quit)
        self.outDir = './'
        self.inFile = ''
        self.sketchFile = ''
        self.freerate = 2.0
        self.afminfo = {}
        self.fileOut.setText(self.outDir)
        self.centerCoord = np.array([0,0])

        self.dxffileName = filename

        self.headers = ('Name', 'Voltage', 'Speed', 'Angle', 'Step', 'Closed', 'Type')

        QtCore.QObject.connect(self.loadFile, QtCore.SIGNAL('clicked()'), self.pickFile)
        QtCore.QObject.connect(self.saveDirectory, QtCore.SIGNAL('clicked()'), self.pickDirectory)
        QtCore.QObject.connect(self.sketchThis, QtCore.SIGNAL('clicked()'), self.sketchNow)
        QtCore.QObject.connect(self.fileOut, QtCore.SIGNAL('returnPressed()'), self.updateDirText)
        QtCore.QObject.connect(self.fileIn, QtCore.SIGNAL('returnPressed()'), self.updateFileText)

        self.readFile()
        print ''
        print ''

        self.AFMthread = AFMWorker()
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("finished()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("terminated()"), self.updateAFM)
        QtCore.QObject.connect(self.AFMthread, QtCore.SIGNAL("AFMimage(QString)"), self.AFMimage)

        self.AFMthread.monitor(afmImageFolder)

        # self.tree_file.selectionModel().selectionChanged.connect(self.updateActions)
        # self.tree_file.model().dataChanged.connect(self.clicked)

        # self.actionsMenu.aboutToShow.connect(self.updateActions)
        # self.insertRowAction.triggered.connect(self.insertRow)
        # self.insertColumnAction.triggered.connect(self.insertColumn)
        # self.removeRowAction.triggered.connect(self.removeRow)
        # self.removeColumnAction.triggered.connect(self.removeColumn)
        # self.insertChildAction.triggered.connect(self.insertChild)

    @QtCore.pyqtSlot("QString")
    def AFMimage(self, filename=None):
        print filename

    def updateAFM(self):
        print 'updateAFM'

    def sketchNow(self, index=None):
        self.sketchFile = ''
        if index == None:
            index = self.model
        nfile = False
        print "here I will sketch the file"
        for i in range(index.rowCount()):
            # print '- ', i
            item = index.getItem(index.index(i))
            if item.checkState == 0:
                continue
            chitems = item.childItems
            # if item.data(6) == 'Layer':
            self.sAdd('')
            self.sComment(item.data())
                # continue
            # print '- ' ,
            if len(chitems) != 0:
                nfile = True
                for child in item.childItems:
                    if child.checkState == 0:
                        continue
                    self.sAdd('')
                    self.sComment(child.data())
                    if child.checkState == 2:
                        for path in child.pltData:
                            x,y = np.add(path[0],-self.centerCoord)
                            self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                            self.sAdd('vtip\t%f' %(child.data(1)))
                            r = child.data(2)
                            for x,y in np.add(path,-self.centerCoord):
                            # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                                self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                            self.sAdd('vtip\t%f' %(0.0))
        if nfile:
            self.writeFile(self.sketchFile)

    def sComment(self, stuff):
        adding = ''
        adding += '# '
        for i in stuff:
            adding += str(i)+ '\t'
        adding += '\n'
        self.sketchFile += adding
        print adding

    def sAdd(self, data):
        self.sketchFile += data
        self.sketchFile += '\n'
        print data


    def writeFile(self, data):
        fname = self.outDir + 'out.tmp'
        f = open(fname, 'w')
        f.write(data)
        f.close()
        os.rename(fname, fname[:-3] + 'txt')
        print  fname[:-3] + 'txt'


    def pickFile(self):
        # http://stackoverflow.com/questions/20928023/how-to-use-qfiledialog-options-and-retreive-savefilename
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Select design file', self.inFile, selectedFilter='*.dxf')
        if filename:
            self.dxffileName = str(filename)
            self.readFile()

    def pickDirectory(self):
        outDir = QtGui.QFileDialog.getExistingDirectory(self, 'Select output Directory', self.outDir)
        if outDir:
            self.outDir = outDir
            self.fileOut.setText(self.outDir)

    def updateDirText(self):
        self.outDir = str(self.fileOut.text())
        self.fileOut.setText(self.outDir)

    def updateFileText(self):
        self.inFile = str(self.fileIn.text())
        self.fileIn.setText(self.inFile)


    def readFile(self):
        self.fileIn.setText(self.dxffileName)
        self.dxf = dxfgrabber.readfile(self.dxffileName)

        self.model = TreeModel(self.headers, self.dxf)

        self.tree_file.setModel(self.model)
        self.tree_file.expandAll()
        self.tree_schedule.setModel(self.model)
        self.tree_schedule.expandAll()

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)
            self.tree_schedule.resizeColumnToContents(column)



        self.pi = self.plot1.getPlotItem()
        self.pi.clear()
        self.pi.enableAutoRange('x', True)
        self.pi.enableAutoRange('y', True)
        self.pi.setAspectLocked(lock=True, ratio=1)
        self.pi.showGrid(x=1, y=1, alpha=0.8)

        if parentos == 'WIN':

            afmData, self.afminfo = convertAFM(afmFile)

            img = pg.ImageItem(afmData)
            img.setZValue(-1000)  # make sure image is behind other data
            img.setRect(pg.QtCore.QRectF(0, 0, self.afminfo['xreal'], self.afminfo['yreal']))

            self.centerCoord = np.array([self.afminfo['xreal'], self.afminfo['yreal']]/2.0)

            self.pi.addItem(img)

        QtCore.QObject.connect(self.tree_file.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        QtCore.QObject.connect(self.tree_schedule.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('checkChanged(QModelIndex)'), self.checked)
        QtCore.QObject.connect(self.model, QtCore.SIGNAL('redraw(QModelIndex)'), self.redraw)

        self.updateActions()


    @QtCore.pyqtSlot("QModelIndex")
    def redraw(self, index):
        model = self.model
        item = model.getItem(index)
        checked = item.checkState
        if not checked == 0:
            # clear plot from item
            for i in item.pltHandle:
                self.pi.removeItem(i)
            item.pltHandle = []

            data = model.getItem(index).pltData
            if data:
                for i in data:
                    pdi = self.pi.plot(i, pen = greenPen)
                    item.pltHandle.append(pdi)

            self.updateActions()


    @QtCore.pyqtSlot("QModelIndex")
    def checked(self, index):
        model = self.model
        item = model.getItem(index)
        checked = item.checkState

        # clear plot from item
        for i in item.pltHandle:
            self.pi.removeItem(i)
        item.pltHandle = []

        if checked == 0:
            # hide item if unchecked
            self.tree_schedule.setRowHidden(index.row(),index.parent(), True)
        else:
            self.tree_schedule.setRowHidden(index.row(),index.parent(), False)
            data = model.getItem(index).pltData
            if data:
                for i in data:
                    pdi = self.pi.plot(i, pen = greenPen)
                    item.pltHandle.append(pdi)

        self.updateActions()


    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def update_plot(self, selected, deselected):
        index = selected.indexes()
        self.tree_file.setCurrentIndex(index[0])
        self.tree_schedule.setCurrentIndex(index[0])
        deindex = deselected.indexes()
        model = self.tree_file.model()
        # print 'bb', index[0], model.getItem(index[0])
        for idx in index:
            item = model.getItem(idx)
            for i in item.pltHandle:
                i.setPen(orangePen)
        for idx in deindex:
            item = model.getItem(idx)
            for i in item.pltHandle:
                i.setPen(greenPen)


        self.updateActions()


    def insertChild(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

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

        self.tree_file.selectionModel().setCurrentIndex(model.index(0, 0, index),
                QtGui.QItemSelectionModel.ClearAndSelect)
        self.updateActions()

    def insertColumn(self):
        model = self.tree_file.model()
        column = self.tree_file.selectionModel().currentIndex().column()

        changed = model.insertColumn(column + 1)
        if changed:
            model.setHeaderData(column + 1, QtCore.Qt.Horizontal,
                    "[No header]", QtCore.Qt.EditRole)

        self.updateActions()

        return changed

    def insertRow(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

        if not model.insertRow(index.row()+1, index.parent()):
            return

        self.updateActions()

        for column in range(model.columnCount(index.parent())):
            child = model.index(index.row()+1, column, index.parent())
            model.setData(child, "[No data]", QtCore.Qt.EditRole)

    def removeColumn(self):
        model = self.tree_file.model()
        column = self.tree_file.selectionModel().currentIndex().column()

        changed = model.removeColumn(column)
        if changed:
            self.updateActions()

        return changed

    def removeRow(self):
        index = self.tree_file.selectionModel().currentIndex()
        model = self.tree_file.model()

        if (model.removeRow(index.row(), index.parent())):
            self.updateActions()

    def updateActions(self):
        hasSelection = not self.tree_file.selectionModel().selection().isEmpty()
        self.removeRowAction.setEnabled(hasSelection)
        self.removeColumnAction.setEnabled(hasSelection)

        hasCurrent = self.tree_file.selectionModel().currentIndex().isValid()
        self.insertRowAction.setEnabled(hasCurrent)
        self.insertColumnAction.setEnabled(hasCurrent)

        if hasCurrent:
            self.tree_file.closePersistentEditor(self.tree_file.selectionModel().currentIndex())

            row = self.tree_file.selectionModel().currentIndex().row()
            column = self.tree_file.selectionModel().currentIndex().column()
            if self.tree_file.selectionModel().currentIndex().parent().isValid():
                self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
            else:
                self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
