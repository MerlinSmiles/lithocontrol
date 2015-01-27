from PyQt4 import QtCore, QtGui
import cPickle


import sip
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


class TreeItem( object ):
    def __init__( self, data=[], name = 'Name',parent=None):
        '''Instantiates a new tree item.'''
        self.name = QtCore.QString(name)
        self.setParent(parent)
        self.children = []
        self.itemData = data
        self.dxfData = None

    # @property
    # def displayName( self ):
    #     '''Returns the wrapped PyNode's name.'''
    #     return self.name

    # @displayName.setter
    # def displayName( self, name ):
    #     '''Renames the wrapped PyNode.'''
    #     self.name = str( name )

    def columnCount(self):
        if self.itemData== None:
            return 0
        return len(self.itemData)

    def setDxfData(self, data):
        self.dxfData = data

    def name(self):
        return self.name

    def data(self, column):
        return self.itemData[column]

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        if parent != None:
            self.parent = parent
            self.parent.addChild(self)
        else:
            self.parent = None

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value

        return True

    def addChild( self, child ):
        '''Adds a given item as a child of this item.'''
        if child not in self.children:
            self.children.append( child )
        if child.parent != self:
            child.setParent( self )

    def numChildren( self ):
        '''Returns the number of child items.'''
        return len( self.children )

    def removeChildAtRow( self, row ):
        '''Removes an item at the given index from the list of children.'''
        self.children.pop( row )

    def childAtRow( self, row ):
        '''Retrieves the item at the given index from the list of children.'''
        return self.children[row]

    def row( self ):
        '''Get this item's index in its parent item's child list.'''
        if self.parent:
            return self.parent.children.index( self )
        return 0

    def log( self, level=-1 ):
        '''Returns a textual representation of an item's hierarchy.'''
        level += 1

        output = ''
        for i in range( level ):
            output += '\t'

        output += self.name if self.name is not None else 'Root'
        output += '\n'

        for child in self.children:
            output += child.log( level )

        level -= 1

        return output

    def __len__(self):
        return len(self.children)


    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True









class TreeModel( QtCore.QAbstractItemModel ):
    '''A drag and drop enabled, editable, hierarchical item model.'''

    def __init__( self, data, headers, parent=None ):
        '''Instantiates the model with a root item.'''
        super( TreeModel, self ).__init__(parent)
        self.checks = {}
        rootData = [header for header in headers] # Header Names
        # self.root = root
        self.root = TreeItem(rootData)

        self.setupModelData(data, self.root)

    def itemFromIndex( self, index ):
        '''Returns the TreeItem instance from a QModelIndex.'''
        return index.internalPointer() if index.isValid() else self.root

    def rowCount( self, index ):
        '''Returns the number of children for the given QModelIndex.'''
        item = self.itemFromIndex( index )
        return item.numChildren()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.root.columnCount()

    def flags( self, index ):
        '''Valid items are selectable, editable, and drag and drop enabled. Invalid indices (open space in the view)
        are also drop enabled, so you can drop items onto the top level.
        '''
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsDragEnabled |\
               QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
    def supportedDropActions( self ):
        '''Items can be moved and copied (but we only provide an interface for moving items in this example.'''
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction

    def headerData( self, section, orientation, role ):
        '''Return the header title.'''
        if section == 0 and orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return 'Joints'
        return QtCore.QVariant()

    def data( self, index, role ):
        '''Return the display name of the PyNode from the item at the given index.'''
        if not index.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                return self.checkState(index)

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None
        item = self.getItem(index)
        return item.data(index.column())

    def checkState(self, index):
        while index.isValid():
            if index in self.checks:
                return self.checks[index]
            index = index.parent()
        return QtCore.Qt.Unchecked

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.root.data(section)
        return None

    def setData( self, index, value, role =QtCore.Qt.EditRole):
        '''Set the name of the PyNode from the item being edited.'''
        if (role == QtCore.Qt.CheckStateRole and index.column() == 0):
            self.layoutAboutToBeChanged.emit()
            for i, v in self.checks.items():
                if self.are_parent_and_child(index, i):
                    self.checks.pop(i)
            self.checks[index] = value
            self.layoutChanged.emit()

            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            return True

        if role != QtCore.Qt.EditRole:
            return False
        item = self.itemFromIndex( index )
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result
        self.dataChanged.emit( QtCore.QModelIndex(), QtCore.QModelIndex() )
        return True

    def index( self, row, column, parentIndex ):
        '''Creates a QModelIndex for the given row, column, and parent.'''
        if not self.hasIndex( row, column, parentIndex ):
            return QtCore.QModelIndex()

        parent = self.itemFromIndex( parentIndex )
        return self.createIndex( row, column, parent.childAtRow( row ) )

    def parent( self, index ):
        '''Returns a QMoelIndex for the parent of the item at the given index.'''
        item = self.itemFromIndex( index )
        parent = item.parent
        if parent == self.root:
            return QtCore.QModelIndex()
        return self.createIndex( parent.row(), 0, parent )

    def insertRows( self, row, count, parentIndex ):
        '''Add a number of rows to the model at the given row and parent.'''
        self.beginInsertRows( parentIndex, row, row+count-1 )
        self.endInsertRows()
        return True

    def insertColumns(self, col, count, parentIndex):
        self.beginInsertColumns(parentIndex, col, col+count-1)
        self.endInsertColumns()
        return True

    def removeRows( self, row, count, parentIndex ):
        '''Remove a number of rows from the model at the given row and parent.'''
        self.beginRemoveRows( parentIndex, row, row+count-1 )
        parent = self.itemFromIndex( parentIndex )
        for x in range( count ):
            parent.removeChildAtRow( row )
        self.endRemoveRows()
        return True

    def removeColumns(self, col, count, parentIndex):
        '''Remove a number of columns from the model at the given column and parent.'''
        self.beginRemoveColumns(parentIndex, col, col+count-1)
        # success = self.root.removeColumns(col, count)
        self.endRemoveColumns()

        if self.root.columnCount() == 0:
            self.removeRows(0, self.rowCount())
        return True

    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole or orientation != QtCore.Qt.Horizontal:
            return False

        result = self.root.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def getColumns(self):
        columns = []
        for i in range(self.columnCount()):
            columns.append(self.headerData(i,QtCore.Qt.Horizontal))
        return columns

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.root

    def mimeTypes( self ):
        '''The MimeType for the encoded data.'''
        types = QtCore.QStringList( 'application/x-pynode-item-instance' )
        return types

    def mimeData( self, indices ):
        '''Encode serialized data from the item at the given index into a QMimeData object.'''
        data = ''
        item = self.itemFromIndex( indices[0] )
        try:
            data += cPickle.dumps( item )
        except:
            pass
        mimedata = QtCore.QMimeData()
        mimedata.setData( 'application/x-pynode-item-instance', data )
        return mimedata

    def dropMimeData( self, mimedata, action, row, column, parentIndex ):
        '''Handles the dropping of an item onto the model.

        De-serializes the data into a TreeItem instance and inserts it into the model.
        '''
        if not mimedata.hasFormat( 'application/x-pynode-item-instance' ):
            return False
        item = cPickle.loads( str( mimedata.data( 'application/x-pynode-item-instance' ) ) )
        dropParent = self.itemFromIndex( parentIndex )
        dropParent.addChild( item )
        self.insertRows( dropParent.numChildren()-1, 1, parentIndex )
        self.dataChanged.emit( parentIndex, parentIndex )
        return True



    def are_parent_and_child(self, parent, child):
        while child.isValid():
            if child == parent:
                return True
            child = child.parent()
        return False

    def setupModelData(self, data, parent):


        # for iit in range(4):
        #     iitem =  TreeItem(name = 'node_'+str(iit))
        #     for jnt in range(3):
        #         itemx =  TreeItem(name = 'item_'+str(jnt))
        #         iitem.addChild( itemx )
        #     self.root.addChild( iitem )

        # print self.root
        # return self.root


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
                lItem = TreeItem( name = layer , data = columns)

                # self.root.addChild( li)
                self.root.addChild( lItem )

                parent_dict[layer] = lItem
                # thisChild = parent.child(parent.numChildren() -1)

                for column in range(len(columns)):
                    key = columns[column]
                    if key in layers[layer]:
                        lItem.setData(column, layers[layer][key])

                # for column in range(len(columnData)):
                #     lItem.setData(column, layers[layer][columnData[column]])
                #     print columnData[column], layers[layer][columnData[column]]

            parent = parent_dict[layer]

            thisChild = TreeItem(name = 'xx')
            parent.addChild( thisChild )

            # thisChild = parent.child(parent.numChildren() -1)
            # print thisChild

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

def gatherItems():
    ''' Return a scene hierarchy of top-level joints as TreeItems.'''
    # Create a null TreeItem to serve as the root
    root = TreeItem()

    for iit in range(4):
        iitem =  TreeItem(name = 'node_'+str(iit))
        for jnt in range(3):
            itemx =  TreeItem(name = 'item_'+str(jnt))
            iitem.addChild( itemx )
        root.addChild( iitem )

    return root


class SkeletonOutliner( QtGui.QMainWindow ):
    '''A window containing a tree view set up for drag and drop.'''

    def __init__( self,  parent=None):
        '''Instantiates the window as a child of the Maya main window, sets up the
        QTreeView with an TreeModel, and enables the drag and drop operations.
        '''
        super( SkeletonOutliner, self ).__init__( parent )

        headers = ('Name', 'Voltage', 'Speed', 'Closed', 'Type')
        dxf = dxfgrabber.readfile(filename)

        self.tree = QtGui.QTreeView()
        self.TreeModel = TreeModel( dxf, headers)
        self.tree.setModel( self.TreeModel )

        self.tree.setDragEnabled( True )
        self.tree.setAcceptDrops( True )
        self.tree.setDragDropMode( QtGui.QAbstractItemView.InternalMove )


        self.selModel = self.tree.selectionModel()
        # self.selModel.currentChanged.connect( self.selectInScene )

        self.tree.expandAll()
        for column in range(self.TreeModel.columnCount()):
            self.tree.resizeColumnToContents(column)

        # self.exitAction.triggered.connect(QtGui.qApp.quit)

        self.setCentralWidget( self.tree )

        self.show()
        # self.tree.expandAll()
        # for column in range(self.TreeModel.columnCount()):
        #     self.tree.resizeColumnToContents(column)
        # self.selModel = self.tree.selectionModel()
        # self.selModel.currentChanged.connect( self.selectInScene )
        # self.tree.selectionModel().selectionChanged.connect(self.updateActions)

        # self.tree.expandAll()

        # QtCore.QObject.connect(self.tree.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.update_plot)
        # self.updateActions()

        # self.setCentralWidget( self.tree )

    # def selectInScene( self, current, previous ):
        # '''Callback for selecting the PyNode in the maya scene when the outliner selection changes.'''
        # pynode = self.TreeModel.itemFromIndex( current ).node
        # select( pynode, r=True )






if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = SkeletonOutliner()
    window.show()
    sys.exit(app.exec_())



















