#!/usr/bin/env python
demo = 1
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
    # def __init__(self, parent = None):
    #     QtGui.QGraphicsWidget.__init__(self)

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled


    def createEditor(self, parent, option, index):
        '''
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        '''
        return None

    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''
        checked = bool(index.model().data(index, QtCore.Qt.EditRole))
        # print(checked)
        check_box_style_option = QtGui.QStyleOptionButton()

        # if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
        #     check_box_style_option.state |= QtGui.QStyle.State_Enabled
        # else:
        #     check_box_style_option.state |= QtGui.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtGui.QStyle.State_On
        else:
            check_box_style_option.state |= QtGui.QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        # this will not run - hasFlag does not exist
        #if not index.model().hasFlag(index, QtCore.Qt.ItemIsEditable):
            #check_box_style_option.state |= QtGui.QStyle.State_ReadOnly

        check_box_style_option.state |= QtGui.QStyle.State_Enabled

        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox, check_box_style_option, painter)

    def editorEvent(self, event, model, option, index):
        # print( 'Check Box editor Event detected : ')
        # if not (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
        #     return False

        # print ('Check Box edior Event detected : passed first check')
        # Do not change the checkbox-state
        if event.type() != QtCore.QEvent.MouseButtonRelease:
            return False

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        # print( 'SetModelData')
        newValue = not model.data(index, QtCore.Qt.EditRole)
        # print(not newValue, newValue)
        model.setData(index, newValue, QtCore.Qt.EditRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QtGui.QStyleOptionButton()
        check_box_rect = QtGui.QApplication.style().subElementRect(QtGui.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint (option.rect.x() +
                             option.rect.width() / 2 -
                             check_box_rect.width() / 2,
                             option.rect.y() +
                             option.rect.height() / 2 -
                             check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())


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
        model.setData(index, color,QtCore.Qt.EditRole)

    @QtCore.pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.editor)
        self.closeEditor.emit(self.editor,QtGui.QAbstractItemDelegate.NoHint) #EditNextItem, EditPreviousItem, NoHint
        print('Include full disabling of checkbox thing')
        self.editor.close()
        self.commitData.emit(self.sender())

    @QtCore.pyqtSlot()
    def pressed(self):
        print('Include full disabling of checkbox thing')

    def paint(self, parent, option, index):
        # data = index.model().data(index, QtCore.Qt.DecorationRole)
        color = index.model().data(index, QtCore.Qt.DisplayRole)

        pixmap = QtGui.QPixmap(QtCore.QSize(option.decorationSize))
        pixmap.fill(QtGui.QColor(*color))
        w = option.decorationSize.width()
        h = option.decorationSize.height()
        iconRect = QtCore.QRect(option.rect.x(), option.rect.y(), w, h)

        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor(0,0,0))
        painter.drawRect(0,0, w-1, h-1)
        del painter

        viewCenter = option.rect.center()
        iconRect.moveCenter(viewCenter)
        parent.drawPixmap(iconRect, pixmap)

class TreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.color = (255,255,255)
        self.is_closed = False
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.show = False
        self.entity = None
        self.pltHandle = []
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
        if self.type == 'LAYER':
            self.name = self.entity.dxf.name
            self.show = self.entity.is_on()
        else:
            self.name  = self.entity.dxf.handle
            self.color = (255,0,255)
            # self.color = self.entity.get_rgb_color()

        self.is_closed = False
        if self.entity.dxftype()=='POLYLINE':
            data = np.array(list(self.entity.points()))
            if(all(data[0] == data[-1])):
                self.is_closed = True
        if self.entity.dxftype()=='LINE':
            self.is_closed = False
            # data = np.array([self.entity.dxf.start, self.entity.dxf.end])


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

    def index(self):
        index = self.model.createIndex(self.parentItem.childNumber(), 0, self.parentItem)
        return index

    def setCheckState(self, value):
        if value == 2:
            self.checkState = QtCore.Qt.Checked
        elif value == 1:
            self.checkState = QtCore.Qt.PartiallyChecked
        else:
            self.checkState = QtCore.Qt.Unchecked
        return self.checkState

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

    def redraw(self):
        return


    def setData(self, column, value, index=None):
        if column < 0 or column >= len(self.itemData):
            return False

#         print(self.model.header[column],column, value)
        if type(column) == int:
            colname = self.model.col(column)
        else:
            colname = column
        if colname == 'Angle':
            value= float(value)
            if self.fillAngle != value:
                self.fillAngle = value
                self.redraw()
        elif colname == 'Rate':
            value= float(value)
            if self.rate != value:
                self.rate = value
                self.calcTime()
        elif colname == 'Step':
            value= float(value)
            if self.fillStep != value:
                self.fillStep = value
                self.redraw()
        elif colname == 'Closed':
            value= bool(value)
            if self.is_closed != value:
                self.is_closed = value
                self.redraw()
        elif colname == 'Show':
            value= bool(value)
            if self.show != value:
                self.show = value
                self.redraw()
        elif colname == 'Time':
            value= float(value)
            if self.sketchTime != value:
                self.sketchTime = value
            if self.parent() == None:
                value = 'Time'
        elif colname == 'Color':
            self.color = value

        self.meta[colname] = value

        self.itemData[column] = value
        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.checks = {}
        self.par = parent

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

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)
        item = self.getItem(index)

        if (role == QtCore.Qt.BackgroundRole) & (index.column() == 0) & (item.childCount()>0):
            return QtGui.QColor(70,70,70,80)

           # if (role == Qt::BackgroundRole)
           # {
           #     if (condition1)
           #        return QColor(Qt::red);
           #     else
           #        return QColor(Qt::green);


        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

        # colname = self.header[index.column()]
        colname = self.col(index)

        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable

        if colname not in ['Name', 'Time', 'Type', 'Closed', 'Show']:
            flags = flags | QtCore.Qt.ItemIsEditable

        item = self.getItem(index)
        if item.childCount() == 0:
            flags = flags | QtCore.Qt.ItemIsDragEnabled
        else:
            flags = flags | QtCore.Qt.ItemIsDropEnabled #| QtCore.Qt.ItemIsDragEnabled

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

            self.layoutChanged.emit()
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

        result = item.setData(index.column(), value, index)
        if result:
            self.emit(QtCore.SIGNAL('redraw(QModelIndex,QModelIndex)'), index,index)
            self.emit(QtCore.SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index,index)

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
        layers = []
        for layer in self.dxf.layers:
            eee = self.layerquery(layer.dxf.name)
            if len(eee.entities) > 0:
                layers.append(layer)
        layers = {layer.dxf.name:{'entity': layer} for layer in layers}
        return layers

    def get_dxf_entity(self, handle):
        return self.dxf.get_dxf_entity(handle)

    def query(self,q):
        return self.dxf.modelspace().query(q)

    def layerquery(self,layer):
        return self.dxf.modelspace().query('*[layer=="%s"]'%layer)

    def setupModelData(self, data, parent):
        self.dxf = data
        layers = self.layers()
        for ll in layers:
            layer = layers[ll]
            entity = layer['entity']
#             print(ll, layer['entity'].is_on(), layer['entity'].is_locked())
            parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
            thisChild = parent.child(parent.childCount() -1)
            thisChild.setEntity(entity)

            # thisChild.initData()
            layer['parent'] = thisChild

        ms = data.modelspace()
        for entity in ms:
            ll = entity.dxf.layer
            # if ll not in layers:
            #     continue
            # print(entity.dxftype())
            if entity.dxftype()=='IMAGE':
                continue

            parent = layers[ll]['parent']
            parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())

            thisChild = parent.child(parent.childCount() -1)
            thisChild.setEntity(entity)
            # thisChild.initData()


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
        # self.emit(QtCore.SIGNAL("dataChanged(QtCore.QModelIndex,QtCore.QModelIndex)"), parentIndex, parentIndex)
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
        self.colors = colors
        for k in sorted(colors):
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


class MainWindow(QtGui.QMainWindow):
    # colorSelected = QtCore.pyqtSignal(str)
    # closeColor = QtCore.pyqtSignal()

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)


        self.setCentralWidget(table)
        self.show()
        self.tree_file = QtGui.QTreeView()
        self.setCentralWidget(self.tree_file)
        self.show()

        self.colorModel = ColorModel()
        self.colorDict = kelly_colors
        self.colorModel.addColors(self.colorDict)


        self.dxffileName = filename

        self.headers = ('Name','Show', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Closed', 'Color', 'Type')

        self.dxf = ezdxf.readfile('/Users/Merlin/Google Drive/Projects/ezdxf/current.dxf')
        self.model = TreeModel(self.headers, self.dxf, parent=self)

        self.tree_file.setModel(self.model)

        self.tree_file.setDragDropMode( QtGui.QAbstractItemView.InternalMove )
        self.tree_file.setSelectionMode( QtGui.QAbstractItemView.ExtendedSelection )

        for col in [self.headers.index(col) for col in ['Closed', 'Show']]:
            self.tree_file.setItemDelegateForColumn(col,CheckBoxDelegate(self))

        for col in [self.headers.index(col) for col in ['Voltage', 'Rate', 'Angle', 'Step']]:
            self.tree_file.setItemDelegateForColumn(col,DoubleSpinBoxDelegate(self))

        self.tree_file.setItemDelegateForColumn(self.model.col('Color'),ColorDelegate(self))

        self.tree_file.expandAll()
        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)

        screen = QtGui.QDesktopWidget().screenGeometry()
        print('(set to minimum expanding?)')
        self.setGeometry(int(screen.width()/2), 0, int(screen.width()/2), screen.height())


        # for col in [self.headers.index(col) for col in ['Color']]:

        self.tree_file.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.tree_file, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.doMenu)
        print('make last column just as wide as needed')


    def clicked(self):
        print('point')

    def doMenu(self, point):
        index=self.tree_file.indexAt(point)
        model = index.model()
        headers = model.header
        column = index.column()
        colname = headers[column]
        item = self.tree_file.model().getItem(index)
        print(colname,item)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.setContextMenuPolicy(QtCore.Qt.CustomContextMenu);
    # window.connect(window,SIGNAL("customContextMenuRequested(QPoint)"),
    #                 window,SLOT("contextMenuRequested(QPoint)"))

    # window.show()
    sys.exit(app.exec_())
