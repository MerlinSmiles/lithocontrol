#!/usr/bin/env python

print('\n\n')
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import numpy as np
from pprint import pprint


from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate
from PyQt4.QtCore import pyqtSignal

import pyqtgraph as pg

import ezdxf

import sys

sys.path.append(".\\source")

filename = './test.dxf'

from dxf2shape_tst import *
import os
import pickle as pickle

colors = ['vivid_yellow','strong_purple','vivid_orange','very_light_blue','vivid_red','grayish_yellow','medium_gray','vivid_green','strong_purplish_pink','strong_blue','strong_yellowish_pink','strong_violet','vivid_orange_yellow','strong_purplish_red','vivid_greenish_yellow','strong_reddish_brown','vivid_yellowish_green','deep_yellowish_brown','vivid_reddish_orange','dark_olive_green']
kelly_colors = dict(
            black=(0, 0, 0),
            white=(255, 255, 255),
            vivid_yellow=(255, 179, 0),
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
accols = [(0  , 0  , 0),(255, 0  , 0),(255, 255, 0),(0  , 255, 0),(0  , 255, 255),(0  , 0  , 255),(255, 0  , 255),(255, 255, 255),(65 , 65 , 65),(128, 128, 128),(255, 0  , 0),(255, 170, 170),(189, 0  , 0),(189, 126, 126),(129, 0  , 0),(129, 86 , 86),(104, 0  , 0),(104, 69 , 69),(79 , 0  , 0),(79 , 53 , 53),(255, 63 , 0),(255, 191, 170),(189, 46 , 0),(189, 141, 126),(129, 31 , 0),(129, 96 , 86),(104, 25 , 0),(104, 78 , 69),(79 , 19 , 0),(79 , 59 , 53),(255, 127, 0),(255, 212, 170),(189, 94 , 0),(189, 157, 126),(129, 64 , 0),(129, 107, 86),(104, 52 , 0),(104, 86 , 69),(79 , 39 , 0),(79 , 66 , 53),(255, 191, 0),(255, 234, 170),(189, 141, 0),(189, 173, 126),(129, 96 , 0),(129, 118, 86),(104, 78 , 0),(104, 95 , 69),(79 , 59 , 0),(79 , 73 , 53),(255, 255, 0),(255, 255, 170),(189, 189, 0),(189, 189, 126),(129, 129, 0),(129, 129, 86),(104, 104, 0),(104, 104, 69),(79 , 79 , 0),(79 , 79 , 53),(191, 255, 0),(234, 255, 170),(141, 189, 0),(173, 189, 126),(96 , 129, 0),(118, 129, 86),(78 , 104, 0),(95 , 104, 69),(59 , 79 , 0),(73 , 79 , 53),(127, 255, 0),(212, 255, 170),(94 , 189, 0),(157, 189, 126),(64 , 129, 0),(107, 129, 86),(52 , 104, 0),(86 , 104, 69),(39 , 79 , 0),(66 , 79 , 53),(63 , 255, 0),(191, 255, 170),(46 , 189, 0),(141, 189, 126),(31 , 129, 0),(96 , 129, 86),(25 , 104, 0),(78 , 104, 69),(19 , 79 , 0),(59 , 79 , 53),(0  , 255, 0),(170, 255, 170),(0  , 189, 0),(126, 189, 126),(0  , 129, 0),(86 , 129, 86),(0  , 104, 0),(69 , 104, 69),(0  , 79 , 0),(53 , 79 , 53),(0  , 255, 63),(170, 255, 191),(0  , 189, 46),(126, 189, 141),(0  , 129, 31),(86 , 129, 96),(0  , 104, 25),(69 , 104, 78),(0  , 79 , 19),(53 , 79 , 59),(0  , 255, 127),(170, 255, 212),(0  , 189, 94),(126, 189, 157),(0  , 129, 64),(86 , 129, 107),(0  , 104, 52),(69 , 104, 86),(0  , 79 , 39),(53 , 79 , 66),(0  , 255, 191),(170, 255, 234),(0  , 189, 141),(126, 189, 173),(0  , 129, 96),(86 , 129, 118),(0  , 104, 78),(69 , 104, 95),(0  , 79 , 59),(53 , 79 , 73),(0  , 255, 255),(170, 255, 255),(0  , 189, 189),(126, 189, 189),(0  , 129, 129),(86 , 129, 129),(0  , 104, 104),(69 , 104, 104),(0  , 79 , 79),(53 , 79 , 79),(0  , 191, 255),(170, 234, 255),(0  , 141, 189),(126, 173, 189),(0  , 96 , 129),(86 , 118, 129),(0  , 78 , 104),(69 , 95 , 104),(0  , 59 , 79),(53 , 73 , 79),(0  , 127, 255),(170, 212, 255),(0  , 94 , 189),(126, 157, 189),(0  , 64 , 129),(86 , 107, 129),(0  , 52 , 104),(69 , 86 , 104),(0  , 39 , 79),(53 , 66 , 79),(0  , 63 , 255),(170, 191, 255),(0  , 46 , 189),(126, 141, 189),(0  , 31 , 129),(86 , 96 , 129),(0  , 25 , 104),(69 , 78 , 104),(0  , 19 , 79),(53 , 59 , 79),(0  , 0  , 255),(170, 170, 255),(0  , 0  , 189),(126, 126, 189),(0  , 0  , 129),(86 , 86 , 129),(0  , 0  , 104),(69 , 69 , 104),(0  , 0  , 79),(53 , 53 , 79),(63 , 0  , 255),(191, 170, 255),(46 , 0  , 189),(141, 126, 189),(31 , 0  , 129),(96 , 86 , 129),(25 , 0  , 104),(78 , 69 , 104),(19 , 0  , 79),(59 , 53 , 79),(127, 0  , 255),(212, 170, 255),(94 , 0  , 189),(157, 126, 189),(64 , 0  , 129),(107, 86 , 129),(52 , 0  , 104),(86 , 69 , 104),(39 , 0  , 79),(66 , 53 , 79),(191, 0  , 255),(234, 170, 255),(141, 0  , 189),(173, 126, 189),(96 , 0  , 129),(118, 86 , 129),(78 , 0  , 104),(95 , 69 , 104),(59 , 0  , 79),(73 , 53 , 79),(255, 0  , 255),(255, 170, 255),(189, 0  , 189),(189, 126, 189),(129, 0  , 129),(129, 86 , 129),(104, 0  , 104),(104, 69 , 104),(79 , 0  , 79),(79 , 53 , 79),(255, 0  , 191),(255, 170, 234),(189, 0  , 141),(189, 126, 173),(129, 0  , 96),(129, 86 , 118),(104, 0  , 78),(104, 69 , 95),(79 , 0  , 59),(79 , 53 , 73),(255, 0  , 127),(255, 170, 212),(189, 0  , 94),(189, 126, 157),(129, 0  , 64),(129, 86 , 107),(104, 0  , 52),(104, 69 , 86),(79 , 0  , 39),(79 , 53 , 66),(255, 0  , 63),(255, 170, 191),(189, 0  , 46),(189, 126, 141),(129, 0  , 31),(129, 86 , 96),(104, 0  , 25),(104, 69 , 78),(79 , 0  , 19),(79 , 53 , 59),(51 , 51 , 51),(80 , 80 , 80),(105, 105, 105),(130, 130, 130),(190, 190, 190),(255, 255, 255)]
# mkPen for selected
selectPen = pg.mkPen(color='FF750A')  #, style=QtCore.Qt.DotLine
sketchPen = pg.mkPen(color='FF0000',width=3)  #, style=QtCore.Qt.DotLine
movePen = pg.mkPen(color='1E4193',width=2, style=QtCore.Qt.DotLine)  #, style=QtCore.Qt.DotLine
showPen = pg.mkPen(color='00FF00')  #, style=QtCore.Qt.DotLine , width=


import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)


class DoubleSpinBoxDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtGui.QDoubleSpinBox(parent)
        editor.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

        spin_vars = index.model().getSpinVars(index)
        if spin_vars != False:
            spin_range = spin_vars[0]
            spin_decimals = spin_vars[1]
            spin_steps = spin_vars[2]
            editor.setDecimals(spin_decimals)
            editor.setRange(*spin_range)
            editor.setSingleStep(spin_steps)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        try:
            spinBox.setValue(value)
        except:
            pass
            spinBox.clear()

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class CheckBoxDelegate(QtGui.QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        # self.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        # self.model = parent.model

    # def paint(self, painter, option, index):
    #     return None

    def createEditor(self, parent, option, index):
        cbox = QtGui.QCheckBox(parent)
        cbox.setCheckState(1)
        self.item = index.model().getItem(index)

        if self.item.childCount() > 0:
            cbox.setTristate(False)
            print('fix checkbox so that it checks for children, or maybe if a child changed that it updates its parent...')
        else:
            cbox.setTristate(False)

        self.connect(cbox, QtCore.SIGNAL("stateChanged(int)"), self, QtCore.SLOT("stateChanged(int)"))
        # self.connect(cbox, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        return cbox

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setCheckState(int(index.model().data(index, QtCore.Qt.EditRole)))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.isChecked())
        # newValue = not model.data(index, QtCore.Qt.EditRole)
        # print(not newValue, newValue)
        # model.setData(index, newValue, QtCore.Qt.EditRole)
        return


    # def editorEvent(self, event, model, option, index):
    #     # print( 'Check Box editor Event detected : ')
    #     # if not (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
    #     #     return False

    #     # print ('Check Box edior Event detected : passed first check')
    #     # Do not change the checkbox-state
    #     if event.type() != QtCore.QEvent.MouseButtonRelease:
    #         return False

    #     # Change the checkbox-state
    #     self.setModelData(None, model, index)
    #     return True

    def paint(self, painter, option, index):
        item = index.model().getItem(index)
        if item.childCount()==0:
            return
        # painter.save()
        color = index.model().data(index, QtCore.Qt.BackgroundRole)
        if color == None:
            return
            # color = QtCore.Qt.green
        # set background color
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        # if option.state & QtGui.QStyle.State_Selected:
        painter.setBrush(QtGui.QBrush(color))
        # else:
            # painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.drawRect(option.rect)

        # set text color
        # painter.setPen(QtGui.QPen(QtCore.Qt.black))

        # painter.restore()

    @QtCore.pyqtSlot('int')
    def stateChanged(self, cc):
        self.commitData.emit(self.sender())
        # print('changed', cc , cbox.isChecked())
        # self.item.setData( item.col())
        # self.setModelData(None, model, index)
        # model.setData(index, newValue, QtCore.Qt.EditRole)
        # self.commitData.emit(self.sender())


class ColorDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        # print()
        self.editor = QtGui.QComboBox(parent)
        model = index.model().par.colorModel
        self.editor.setModel(model)

        # self.editor.showPopup()
        QtCore.QTimer.singleShot(100,self.editor.showPopup)
        self.connect(self.editor, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        self.connect(self.editor, QtCore.SIGNAL("hideEvent()"), self, QtCore.SLOT("pressed()"))
        return self.editor

    def setModelData(self, editor, model, index):
        color = editor.model().getColor(editor.currentIndex())[1]
        # print(color)
        model.setData(index, color,QtCore.Qt.EditRole)

    @QtCore.pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.editor)
        self.closeEditor.emit(self.editor,QtGui.QAbstractItemDelegate.NoHint) #EditNextItem, EditPreviousItem, NoHint
        # print('D Include full disabling of checkbox thing')
        self.editor.close()
        self.commitData.emit(self.sender())

    @QtCore.pyqtSlot()
    def pressed(self):
        # print('Include full disabling of checkbox thing')
        pass

    def paint(self, painter, option, index):
        # data = index.model().data(index, QtCore.Qt.DecorationRole)
        color = index.model().data(index, QtCore.Qt.DisplayRole)
        bgcolor = index.model().data(index, QtCore.Qt.BackgroundRole)

        pixmap = QtGui.QPixmap(QtCore.QSize(option.decorationSize))
        pixmap.fill(QtGui.QColor(*color))
        w = option.decorationSize.width()
        h = option.decorationSize.height()
        iconRect = QtCore.QRect(option.rect.x(), option.rect.y(), w, h)

        rect_painter = QtGui.QPainter(pixmap)

        item = index.model().getItem(index)
        if item.childCount()>0:
            # return
            # # rect_painter.save()
            # color = index.model().data(index, QtCore.Qt.BackgroundRole)
            # if color == None:
            #     return
            #     # color = QtCore.Qt.green
            # # set background color
            painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            # # if option.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtGui.QBrush(bgcolor))
            # # else:
            #     # rect_painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
            painter.drawRect(option.rect)


        rect_painter.setPen(QtGui.QColor(0,0,0))
        rect_painter.drawRect(0,0, w-1, h-1)
        del rect_painter


        viewCenter = option.rect.center()
        iconRect.moveCenter(viewCenter)
        painter.drawPixmap(iconRect, pixmap)

class TreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.color = (255,200,255)
        self.is_closed = 0
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.show = False
        self.entity = None
        self.pltHandle = []
        self.pltData = []
        self.checkState = QtCore.Qt.Unchecked
        self.fillAngle = 0
        self.fillStep = 0.1
        self.volt = 20.0
        self.rate = 1.0
        self.length = 0.0
        self.sketchTime = 0.0
        self.name = 'Item'
        self.type = 'Dummy'
        self.meta = {}

#     shape.type = None # [VirtualElectrode, line, area]

    def setEntity(self, entity):
        self.entity = entity
        self.initData()

    def initData(self):
        # 'Name', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Closed', 'Type', 'Color', 'Show'
        self.type = self.entity.dxftype()

        self.color = (999,999,999)

        if self.type == 'LAYER':
            self.name = self.entity.dxf.name
            self.show = self.entity.is_on()
        else:
            self.name  = self.entity.dxf.handle
        try:
            self.color = accols[self.entity.dxf.color]
        except:
            if self.parentItem != None:
                self.color = self.parentItem.color
        if self.color == (999,999,999):
            self.color = (255,0,255)


        self.is_closed = 0
        if self.entity.dxftype()=='POLYLINE':
            data = np.array(list(self.entity.points()))
            if(all(data[0] == data[-1])):
                self.is_closed = 2
        if self.entity.dxftype()=='LINE':
            self.is_closed = 0
            self.entity.points = np.array([self.entity.dxf.start, self.entity.dxf.end])

        # print('ininit')

        item_data = {'Color':        self.color,
                     'Closed':       self.is_closed,
                     'parentItem':   self.parentItem,
                     'itemData':     self.itemData,
                     'childItems':   self.childItems,
                     'Show':         self.show,
                     'entity':       self.entity,
                     'pltHandle':    self.pltHandle,
                     'checkState':   self.checkState,
                     'Angle':        self.fillAngle,
                     'Step':         self.fillStep,
                     'Voltage':      self.volt,
                     'Rate':         self.rate,
                     'length':       self.length,
                     'Time':         self.sketchTime,
                     'Name':         self.name,
                     'Type':         self.type}
        self.loadMetaData(item_data)

    def loadMetaData(self, meta):
        for column, key in enumerate(self.model.header):
            if key in meta:
                self.setData(column, meta[key])

    def index(self, column=0):
        index = self.model.createIndex(self.parentItem.childNumber(), column, self.parentItem)
        return index

    def setCheckState(self, value):
        if value == 2:
            self.checkState = QtCore.Qt.Checked
        elif value == 1:
            self.checkState = QtCore.Qt.PartiallyChecked
        else:
            self.checkState = QtCore.Qt.Unchecked

        # self.model.emit(QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), self.index(), self.index())

        if self.parentItem != None:
            self.parentItem.calcTime()


        return self.checkState

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    # def childIndex(self):
    #     if self.parentItem != None:
    #         return self.parentItem.childItems.index(self)
    #     return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column=None):
        if column == None:
            return self.itemData[:]
        if type(column) == str:
            column = self.col(column)

        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        # print('insertChildren')
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
        # print('removeChildren')
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


    # def index( row, column=0, parent=QtCore.QModelIndex()):
    #     if parent.isValid() and parent.column() != 0:
    #         return QtCore.QModelIndex()

    #     parentItem = self.getItem(parent)
    #     childItem = parentItem.child(row)
    #     if childItem:
    #         return self.createIndex(row, column, childItem)
    #     else:
    #         return QtCore.QModelIndex()

    # def parent(self, index):
    #     if not index.isValid():
    #         return QtCore.QModelIndex()

    #     childItem = self.getItem(index)
    #     parentItem = childItem.parent()

    #     if parentItem == self.rootItem:
    #         return QtCore.QModelIndex()
    #     try:
    #         self.createIndex(parentItem.childNumber(), 0, parentItem)
    #     except:
    #         return QtCore.QModelIndex()

    #     return self.createIndex(parentItem.childNumber(), 0, parentItem)




    def calcLength(self):
        if self.childCount() == 0:
            try:
                dat = np.concatenate(self.pltData).reshape((-1,2))
            except:
                # self.setData('Length', 0.0)
                print('error calculating length')
                self.setData('Length', 0)
                return
            dat_b = np.roll(dat,-2)
            self.length = 0.0
            for k in range(len(dat)-1):
                self.length += np.linalg.norm(dat[k]-dat_b[k])
            self.parentItem.calcLength()
        else:
            self.length = 0.0
            for i in range(self.childCount()):
                # print(i)
                if self.child(i).checkState == 2:
                    # self.child(i).calcLength()
                    # print('chd',self.child(i).length)
                    self.length += self.child(i).length
            # print('par', self.length)
        self.setData('Length', round(float(self.length),1))

    def calcTime(self):
        if self.childCount() == 0:
            self.calcLength()
            self.sketchTime = self.length / float(self.rate)
            # col = self.col('Time')
            # print(col)

            self.parentItem.calcTime()
        else:
            self.sketchTime = 0.0
            # self.setData(5,self.sketchTime)
            for i in range(self.childCount()):
                if self.child(i).checkState == 2:
                    self.sketchTime += self.child(i).sketchTime
        self.setData('Time',round(float(self.sketchTime),1))

    def col(self, column):
        if type(column) == int:
            if column < 0 or column >= len(self.itemData):
                return None
            colname = self.model.col(column)
            return colname
        if type(column) == str:
            colnum = self.model.col(column)
            return colnum
        return None

    def setData(self, column, value, index=None):
        if type(column) == int:
            if column < 0 or column >= len(self.itemData):
                return False
            colname = self.model.col(column)
        else:
            colname = column
            column = self.model.col(column)

        # recalc = False
        replot = False

        if colname == 'Angle':
            value= float(value)
            if self.fillAngle != value:
                self.fillAngle = value
                # self.recalc()
                self.model.recalc(self, index)
        elif colname == 'Voltage':
            value= float(value)
            if self.volt != value:
                self.volt = value
        elif colname == 'Rate':
            value= float(value)
            if self.rate != value:
                self.rate = value
                self.calcTime()
        elif colname == 'Step':
            value= float(value)
            if self.fillStep != value:
                self.fillStep = value
                # self.recalc()
                self.model.recalc(self, index)
        elif colname == 'Closed':
            if value == True:
                value = 2
            elif value == False:
                value = 0
            value= int(value)
            # print(column,colname,value,index)
            if self.is_closed != value:
                self.is_closed = value
                # self.recalc()
                self.model.recalc(self, index)
                col = self.model.col('Time')
                self.model.emit(QtCore.SIGNAL('dataChanged(QModelIndex,QModelIndex)'), self.index(col), self.index(col+1))
        elif colname == 'Show':
            if value == True:
                value = 2
            elif value == False:
                value = 0
            value= int(value)
            if self.show != value:
                self.show = value
                replot = True
        elif colname == 'Time':
            value= float(value)
            if self.sketchTime != value:
                self.sketchTime = value
                # print(value)
            if self.parent() == None:
                value = 'Time'

        elif colname == 'Length':
            value= float(value)
            if self.length != value:
                self.length = value
            if self.parent() == None:
                value = 'Length'
        elif colname == 'Color':
            self.color = value
            replot = True

        self.meta[colname] = value
        self.itemData[column] = value


        # if colname in ['Closed']:
        #     cc = self.childCount()
        #     if cc > 0:
        #         for i in range(cc):
        #             chindex =  self.createIndex(i, index.column(), self.child(i))
        #             self.setData(chindex,value,role)
        #             if colname == 'Closed':
        # if (index != None) and (recalc):
        #     self.model.emit(QtCore.SIGNAL('recalc(QModelIndex,QModelIndex)'), index,index)
        #     self.model.emit(QtCore.SIGNAL('recalc(QModelIndex.QModelIndex)'), self.index(), self.index())

        if (index != None) and (replot):
            self.model.emit(QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), index,index)


        if colname in  ['Closed']:
            for ch in self.childItems:
                ch.setData(column, value)
                # print('X closed')
        # if (self.childCount() != 0) and (column != (0 or 5)):
            # self.itemData[column] = ''
        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        # print(parent)
        self.checks = {}
        self.par = parent
        # print(self.par)

        self.header = [header for header in headers] # Header Names
        self.rootItem = TreeItem(self.header, model=self)
        self.dxf = data
        self.setupModelData(data, self.rootItem)


        self._checked=[[False for i in range(self.columnCount())] for j in range(self.rowCount())]

    def col(self,request):
        if type(request) == QtCore.QModelIndex:
            return self.header[request.column()]
        if type(request) == str:
            return self.header.index(request)
        if type(request) == int:
            return self.header[request]
        return None


    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def getSpinVars(self,index):
        colname = self.col(index)
        if colname == 'Angle':
            return [(-3600,3600), 1, 1.0]
        elif colname == 'Voltage':
            return [(-210,210), 1, 0.1]
        elif colname == 'Step':
            return [(0.001,1000), 3, 0.01]
        elif colname == 'Rate':
            return [(0.01,1000), 2, 0.1]
        else:
            return False

    def recalc(self, item, index):
        # print(item,index, item.name)
        if item.entity.dxftype() in ['POLYLINE','LINE','SPLINE']:
            dxf2shape(item, fill_step = item.fillStep, fill_angle = item.fillAngle)


        item.calcTime()

    # def index(item, row, column=0, parent=QtCore.QModelIndex()):
        # print(item.childNumber())
        # try:
        #     index2 = item.model.index(item.childNumber(), 0, item.ParentItem)
        #     print('nnn', index2, item.model.getItem(index2).name)
        # except:
        #     pass
        self.emit(QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), index, index)



    def data(self, index, role):
        if not index.isValid():
            return None


        # if role == QtCore.Qt.AlignmentRole:
        #     print(index.column() , self.col('Closed'))
        #     if index.column() == self.col('Closed'):
        #         print('yo')
        #         return QtCore.Qt.AlignCenter

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)
        item = self.getItem(index)

        if (role == QtCore.Qt.BackgroundRole) & (item.childCount()>0):
            return QtGui.QColor(70,70,70,80)

           # if (role == Qt::BackgroundRole)
           # {
           #     if (condition1)
           #        return QColor(Qt::red);
           #     else
           #        return QColor(Qt::green);


        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        colname = self.col(index.column())
        # print(column, self.col(column), self.itemData[column])

        if colname in ['Time', 'Length']:
            if (item.childCount() > 0) and (item.parentItem != None):
                val = 0
                for i in range(item.childCount()):
                    if item.child(i).checkState == 2:
                        # item.child(i).calcLength()
                        # print('chd',item.child(i).length)
                        vv = item.child(i).data(colname)
                        if vv == None:
                            continue
                        val += vv
                # print(colname,val)
                if val == 0.0:
                    return ' '

                return val

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

        # colname = self.header[index.column()]
        colname = self.col(index)

        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable

        if colname not in ['Name', 'Time', 'Type', 'Show', 'Length']:
            flags = flags | QtCore.Qt.ItemIsEditable

        # dragdrop kills other things :/
        # item = self.getItem(index)
        # if item.childCount() == 0:
        #     flags = flags | QtCore.Qt.ItemIsDragEnabled
        # else:
        #     flags = flags | QtCore.Qt.ItemIsDropEnabled #| QtCore.Qt.ItemIsDragEnabled

        return  flags

    def supportedDropActions( self ):
        return QtCore.Qt.MoveAction # | QtCore.Qt.CopyAction

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
        # print('insert rows')
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
        try:
            self.createIndex(parentItem.childNumber(), 0, parentItem)
        except:
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
        # print('remove rows')
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

            self.layoutChanged.emit()
            # print('checkstate', index)
            # self.emit(QtCore.SIGNAL('checkChanged(QModelIndex, QModelIndex)'), index, index)
            self.emit(QtCore.SIGNAL('replot(QModelIndex, QModelIndex)'), index, index)
            return True

        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        colname = self.col(index)
        if colname in ['Voltage', 'Angle', 'Rate', 'Step', 'Color', 'Closed', 'Show']:
            cc = item.childCount()
            if cc > 0:
                for i in range(cc):
                    chindex =  self.createIndex(i, index.column(), item.child(i))
                    self.setData(chindex,value,role)
                    # if colname == 'Closed':
                    #     print('closed')

        # if colname in ['Angle', 'Rate', 'Step', 'Color', 'Closed', 'Show']:
        #     print('I have to recalc', item)
            # self.emit(QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), index,index)

        result = item.setData(index.column(), value, index)
        # if result:
            # self.emit(QtCore.SIGNAL('replot(QModelIndex,QModelIndex)'), index,index)

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
        self.rootItem = TreeItem(self.header, model=self)

    def layers(self):
        if self.dxf == None:
            return []
        # for layer in self.dxf.layers:
        layers = []
        for layer in self.dxf.layers:
            # print(layer.dxf.name)
            eee = self.layerquery(layer.dxf.name)
            if len(eee.entities) > 0:
                layers.append(layer)

        # layers = {layer.dxf.name:{'entity': layer} for layer in layers}
        # print(layers)
        return layers

    def get_dxf_entity(self, handle):
        return self.dxf.get_dxf_entity(handle)

    def query(self,q):
        return self.dxf.modelspace().query(q)

    def layerquery(self,layer):
        return self.dxf.modelspace().query('*[layer=="%s"]'%layer)

    def setupModelData(self, data, parent):
        self.dxf = data

        for layer in self.dxf.layers:
            # print(layer.dxf.name)
            query = self.layerquery(layer.dxf.name)

            parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
            thisLayer = parent.child(parent.childCount() -1)
            thisLayer.setEntity(layer)

            for entity in query:
                if entity.dxftype() in ['IMAGE', 'SPLINE']:
                    continue

                thisLayer.insertChildren(thisLayer.childCount(), 1, self.rootItem.columnCount())

                thisChild = thisLayer.child(thisLayer.childCount() -1)
                thisChild.setEntity(entity)

                self.recalc(thisChild, thisChild.index())

            if thisLayer.childCount() == 0:
                self.removeRows(parent.childCount()-1,1)

    def mimeTypes(self):
        # types = QtCore.QStringList()
        types = ['QByteArray']
        return types

    def mimeData(self, index):
        # print(index)
        item = [self.getItem(i) for i in index]
        dxfentity = []
        metalist  = []
        for i in item:
            handle = i.entity.dxf.handle
            if handle not in dxfentity:
                dxfentity.append(handle)
                metalist.append(i.meta)

        mimedata = QtCore.QMimeData()
        mimedata.setData('QByteArray', QtCore.QByteArray(pickle.dumps([dxfentity,metalist])))
        # mimedata.setData('text/plain', pickle.dump(dxfhandle))
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parentIndex):
        # print (mimedata, action, row, column, parentIndex)
        # print(action,row,column,parentIndex)
        if action == QtCore.Qt.IgnoreAction:
            return True
        data, meta = pickle.loads(mimedata.data('QByteArray').data())

        entities = [self.get_dxf_entity(dd) for dd in data]
        # metas = [dd for dd in data]
        if row == -1:
            row = 0
        # print(entities[0].childCount(), row)
        # print(dd.dxftype)
        for key, entity in enumerate(entities[::-1]):
            # print(self.getItem(parentIndex))
            # print(self.parent(parentIndex))
            # parentNode = self.nodeFromIndex(parentIndex)

            # newNode.setParent(parentNode)
            parent = self.getItem(parentIndex)

            self.insertRow(row, parentIndex)
            # parent.insertChildren(row, 1, self.rootItem.columnCount())
            thisChild = parent.child(row)
            thisChild.setEntity(entity)
            # thisChild.initData()
            dct = meta[-key]
            thisChild.loadMetaData(dct)

            # for k in dct:
            #     thisChild.setData(k,dct[k])
            #     print(k,dct[k])
        print('make moved item selected, treeitem to reimplement thisChild.setSelected()')
        # self.par.tree_file.setSelection(thisChild)
        return True










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
            elif role == QtCore.Qt. ItemDataRole:
                return self.items[index.row()]
            elif role==QtCore.Qt.DecorationRole:
                # print(self.items[index.row()])
                k = self.items[index.row()]
                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(QtGui.QColor(*self.colors[k]))
                icon = QtGui.QIcon(pixmap)
                return icon
            # print(role)
        return None

    def addColors(self,clist,colors):
        self.colors = colors
        for k in clist:
            self.addItem(k)

    def getColor(self, index):
        if type(index) == int:
            cname = self.items[index]
            return [cname, self.colors[cname]]
        if type(index) == str:
            return [index, self.colors[index]]

    def addItem(self, item):
        # index=QtCore.QModelIndex()
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.items.append(item)
        self.endInsertRows()
