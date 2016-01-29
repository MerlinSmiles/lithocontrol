#!/usr/bin/env python
import numpy as np
#!/usr/bin/env python

import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

from PyQt4 import QtCore, QtGui, uic
# from source.dxf2shape import *
import itertools

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

class ColorDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        color_dialog = QtGui.QColorDialog(parent)
        color_dialog.setCurrentColor(QtGui.QColor(255,255,255))
        color_dialog.setOption(color_dialog.DontUseNativeDialog,True)
        color_dialog.setOption(color_dialog.ShowAlphaChannel,True)

        changed = color_dialog.exec_()
        if changed:
            color = list(color_dialog.currentColor().getRgb())[:-1]
            index.model().setData(index, color, QtCore.Qt.EditRole)



class TreeItem(object):
    def __init__(self, data, parent=None, model=None):
        self.model = model
        self.color = (255,255,255)
        self.is_closed = False
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.dxfData = None
        self.pltData = None
        self.show = False
        self.handle = None
        self.entity = None
        self.pltHandle = []
        self.checkState = QtCore.Qt.Unchecked
        self.fillAngle = 0
        self.fillStep = 0.1
        self.volt = 20.0
        self.rate = 1.0
        self.length = 0.0
        self.sketchTime = 0.0
#     shape.type = None # [VirtualElectrode, line, area]
    def index(self):
        index = self.model.createIndex(self.parentItem.childNumber(), 0, self.parentItem)
        return index

    def redraw(self):
        if self.entity != None:
            self.setDxfData(dxf2shape(self.entity, fill_step = self.fillStep, fill_angle=self.fillAngle))

    def setColor(self,color):
        self.color=color

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
            # print 'error calculating length'
            return
        dat_b = np.roll(dat,-2)
        dist = 0
        for k in range(len(dat)-1):
            dist += np.linalg.norm(dat[k]-dat_b[k])

        self.length = dist

    def calcTime(self):
        if self.childCount() == 0:
            self.calcLength()
            self.sketchTime = self.length / float(self.rate)
        else:
            self.sketchTime = 0.0
            # self.setData(5,self.sketchTime)
            for i in range(self.childCount()):
                if self.child(i).checkState == 2:
                    self.sketchTime += self.child(i).sketchTime
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
        self.calcTime()
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

    def setData(self, column, value, index=None):
        if column < 0 or column >= len(self.itemData):
            return False

#         print(self.model.rootData[column],column, value)
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
            if self.is_closed != value:
                self.is_closed = value
                self.redraw()
        elif self.model.rootData[column] == 'Time':
            value= float(value)
            if self.sketchTime != value:
                self.sketchTime = value
            if self.parent() == None:
                value = 'Time'
        elif self.model.rootData[column] == 'Color':
            self.color = value

        self.itemData[column] = value
        return True


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.checks = {}

        self.rootData = [header for header in headers] # Header Names
        self.rootItem = TreeItem(self.rootData, model=self)
        self.setupModelData(data, self.rootItem)

        self._checked=[[False for i in range(self.columnCount())] for j in range(self.rowCount())]

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def getSpinVars(self,index):
        column = index.column()
        # range decimals steps
        if self.rootData[column] == 'Angle':
            return [(-3600,3600), 1, 1.0]
        elif self.rootData[column] == 'Voltage':
            return [(-210,210), 1, 0.1]
        elif self.rootData[column] == 'Step':
            return [(0.001,1000), 3, 0.01]
        elif self.rootData[column] == 'Rate':
            return [(0.01,1000), 2, 0.1]
        else:
            return False

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)
            if index.column() == 6:
                item = self.getItem(index)
                try:
                    return item.entity.is_closed
                except:
                    pass

        item = self.getItem(index)

        if (role == QtCore.Qt.BackgroundRole) & (self.rootData[index.column()] == 'Color'):
            return QtGui.QColor(*item.color)


        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

        colname = self.rootData[index.column()]
        if colname in ['Name', 'Time', 'Type']:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsDropEnabled |QtCore.Qt.ItemIsDragEnabled

    def supportedDropActions( self ):
        '''Items can be moved and copied (but we only provide an interface for moving items in this example.'''
        # print('supportedDropActions')
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
                # item.sketchTime = 0.0
                # item.setData(5,item.sketchTime)
                for i in range(cc):
                    if item.child(i).checkState == 2:
                        no_checked+=1

                        # item.sketchTime += item.child(i).sketchTime
                        # if item.child(i).childCount() == 0:
                        #     item.setData(5,item.sketchTime)
                if no_checked == cc:
                    item.setCheckState(2)
                elif no_checked > 0:
                    item.setCheckState(1)
                else:
                    item.setCheckState(0)
                # self.emit(QtCore.SIGNAL('checkChanged(QModelIndex)'), index.parent())

            self.layoutChanged.emit()
            return True

        # self.emit(QtCore.SIGNAL('dataChanged(QModelIndex)'), index)
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        # print(item)
        colname = self.rootData[index.column()]
        if colname in ['Voltage', 'Angle', 'Rate', 'Step', 'Color']:
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
        self.rootItem = TreeItem(self.rootData, model=self)


    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        mimedata = QtCore.QMimeData()
        mimedata.setData('application/x-qabstractitemmodeldatalist', 'mimeData')
        return mimedata

    # def dropMimeData(self, data, action, row, column, parent):
        # print ('dropMimeData %s %s %s %s' % (data.data('text/xml'), action, row, parent))
        # return True


    def dropMimeData(self, data, action, row, column, parent):

        print(data, action, row, column, parent)

        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            bytearray = data.data('application/x-qabstractitemmodeldatalist')
            data_items = self.decode_data (bytearray)

            # Assuming that we get at least one item, and that it defines
            # text that we can display.
            text = data_items[0][QtCore.Qt.DisplayRole].toString()

            for row in range(self.rowCount()):
                name = self.item(row, 0).text()
                if name == text:
                    number_item = self.item(row, 1)
                    number = int(number_item.text())
                    number_item.setText(str(number + 1))
                    break
            else:
                name_item = QtCore.QStandardItem(text)
                number_item = QtCore.QStandardItem("1")
                self.appendRow([name_item, number_item])

            return True
        else:
            return QtCore.QStandardItemModel.dropMimeData(self, data, action, row, column, parent)

    def decode_data(self, bytearray):

        data = []
        item = {}

        ds = QtCore.QDataStream(bytearray)
        while not ds.atEnd():

            row = ds.readInt32()
            column = ds.readInt32()

            map_items = ds.readInt32()
            for i in range(map_items):

                key = ds.readInt32()

                value = ""
                ds >> value
                item[QtCore.Qt.ItemDataRole(key)] = value

            data.append(item)

        return data

    def setupModelData(self, data, parent):
        layers = {layer.dxf.name:{'entity': layer} for layer in data.layers if layer.dxf.name!='0'}
#         print([layer.dxf.name for layer in data.layers if layer.dxf.name!='0'])
        columns = self.getColumns()
        for ll in layers:
            nchildren = len(data.modelspace().query('*[layer=="%s"]'%ll).entities)
            if nchildren == 0:
                continue
            layer = layers[ll]
            entity = layer['entity']
#             print(ll, layer['entity'].is_on(), layer['entity'].is_locked())
            parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
            thisChild = parent.child(parent.childCount() -1)
            thisChild.handle = layer
            layer['parent'] = thisChild


            item_data = {'Name': ll,
                         'Type': entity.dxftype(),
                         'Closed': 0,
                         'Voltage': thisChild.volt,
                         'show': layer['entity'].is_on(),
                         'Angle': thisChild.fillAngle,
                         'Rate': thisChild.rate,
                         'Step': thisChild.fillStep,
                         'Time': thisChild.sketchTime}

            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
#                     print(column, item_data[key])
                    thisChild.setData(column, item_data[key])

        ms = data.modelspace()
        cnt = -1
        for entity in ms:
            cnt+=1
            ll = entity.dxf.layer
            if ll not in layers:
                continue
#             print(entity.dxftype())
            if entity.dxftype()=='IMAGE':
                continue
            thisChild.is_closed = False
            if entity.dxftype()=='POLYLINE':
                data = np.array(list(entity.points()))
                if(all(data[0] == data[-1])):
                    thisChild.is_closed = True
            if entity.dxftype()=='LINE':
                thisChild.is_closed = False
                data = np.array([entity.dxf.start, entity.dxf.end])


            parent = layers[ll]['parent']
            parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())

            thisChild = parent.child(parent.childCount() -1)
            thisChild.handle = entity
            thisChild.color = entity.get_rgb_color()


            item_data = {'Name': entity.dxf.handle,
                         'Type': entity.dxftype(),
                         'Closed': thisChild.is_closed,
                         'Voltage': thisChild.volt,
                         'show': thisChild.show,
                         'Angle': thisChild.fillAngle,
                         'Rate': thisChild.rate,
                         'Step': thisChild.fillStep,
                         'Time': thisChild.sketchTime,
                         'Color': entity.get_rgb_color()}
            # print columnData
            for column in range(len(columns)):
                key = columns[column]
                if key in item_data:
#                     print(column, item_data[key])
                    thisChild.setData(column, item_data[key])
