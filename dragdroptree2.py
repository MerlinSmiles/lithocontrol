from PyQt4 import QtCore, QtGui
import cPickle


import sip

class TreeItem( object ):
    def __init__( self, name = 'Node', parent=None):
        '''Instantiates a new tree item.'''
        self.name = QtCore.QString(name)
        self.setParent(parent)
        self.children = []

    @property
    def displayName( self ):
        '''Returns the wrapped PyNode's name.'''
        return self.name

    @displayName.setter
    def displayName( self, name ):
        '''Renames the wrapped PyNode.'''
        self.name = str( name )

    def name(self):
        return self.name

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        if parent != None:
            self.parent = parent
            self.parent.addChild(self)
        else:
            self.parent = None

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






def gatherItems():
    ''' Return a scene hierarchy of top-level joints as TreeItems.'''
    # Create a null TreeItem to serve as the root
    rootItem = TreeItem()

    for iit in range(4):
        iitem =  TreeItem(name = 'node_'+str(iit))
        for jnt in range(3):
            itemx =  TreeItem(name = 'item_'+str(jnt))
            iitem.addChild( itemx )
        rootItem.addChild( iitem )

    return rootItem


class TreeModel( QtCore.QAbstractItemModel ):
    '''A drag and drop enabled, editable, hierarchical item model.'''

    def __init__( self, root, parent=None ):
        '''Instantiates the model with a root item.'''
        super( TreeModel, self ).__init__(parent)
        self.root = root

    def itemFromIndex( self, index ):
        '''Returns the TreeItem instance from a QModelIndex.'''
        return index.internalPointer() if index.isValid() else self.root

    def rowCount( self, index ):
        '''Returns the number of children for the given QModelIndex.'''
        item = self.itemFromIndex( index )
        return item.numChildren()

    def columnCount( self, index ):
        '''This model will have only one column.'''
        return 1

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
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            item = self.itemFromIndex( index )
            return item.displayName

    def setData( self, index, value, role ):
        '''Set the name of the PyNode from the item being edited.'''
        item = self.itemFromIndex( index )
        item.displayName = str( value.toString() )
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

    def removeColumns(self, position, columns, parent=QtCore.QModelIndex()):
        '''Remove a number of columns from the model at the given column and parent.'''
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


class SkeletonOutliner( QtGui.QMainWindow ):
    '''A window containing a tree view set up for drag and drop.'''

    def __init__( self,  parent=None):
        '''Instantiates the window as a child of the Maya main window, sets up the
        QTreeView with an TreeModel, and enables the drag and drop operations.
        '''
        super( SkeletonOutliner, self ).__init__( parent )

        self.tree = QtGui.QTreeView()
        self.TreeModel = TreeModel( gatherItems() )
        self.tree.setModel( self.TreeModel )
        self.tree.setDragEnabled( True )
        self.tree.setAcceptDrops( True )
        self.tree.setDragDropMode( QtGui.QAbstractItemView.InternalMove )

        self.selModel = self.tree.selectionModel()
        # self.selModel.currentChanged.connect( self.selectInScene )

        self.tree.expandAll()

        self.setCentralWidget( self.tree )

        self.show()

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
























# import sys
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
# from copy import deepcopy
# from cPickle import dumps, load, loads
# from cStringIO import StringIO


# class PyMimeData(QMimeData):
#     """ The PyMimeData wraps a Python instance as MIME data.
#     """
#     # The MIME type for instances.
#     MIME_TYPE = QString('application/x-ets-qt4-instance')

#     def __init__(self, data=None):
#         """ Initialise the instance.
#         """
#         QMimeData.__init__(self)

#         # Keep a local reference to be returned if possible.
#         self._local_instance = data

#         if data is not None:
#             # We may not be able to pickle the data.
#             try:
#                 pdata = dumps(data)
#             except:
#                 return

#             # This format (as opposed to using a single sequence) allows the
#             # type to be extracted without unpickling the data itself.
#             self.setData(self.MIME_TYPE, dumps(data.__class__) + pdata)

#     @classmethod
#     def coerce(cls, md):
#         """ Coerce a QMimeData instance to a PyMimeData instance if
# possible.
#         """
#         # See if the data is already of the right type.  If it is then
# we know
#         # we are in the same process.
#         if isinstance(md, cls):
#             return md

#         # See if the data type is supported.
#         if not md.hasFormat(cls.MIME_TYPE):
#             return None

#         nmd = cls()
#         nmd.setData(cls.MIME_TYPE, md.data())

#         return nmd

#     def instance(self):
#         """ Return the instance.
#         """
#         if self._local_instance is not None:
#             return self._local_instance

#         io = StringIO(str(self.data(self.MIME_TYPE)))

#         try:
#             # Skip the type.
#             load(io)

#             # Recreate the instance.
#             return load(io)
#         except:
#             pass

#         return None

#     def instanceType(self):
#         """ Return the type of the instance.
#         """
#         if self._local_instance is not None:
#             return self._local_instance.__class__

#         try:
#             return loads(str(self.data(self.MIME_TYPE)))
#         except:
#             pass

#         return None


# class treeNode(object):
#     def __init__(self, name, state, description, parent=None):

#         self.name = QString(name)
#         self.state = QString(state)
#         self.description = QString(description)

#         self.parent = parent
#         self.children = []

#         self.setParent(parent)

#     def setParent(self, parent):
#         if parent != None:
#             self.parent = parent
#             self.parent.addChild(self)
#         else:
#             self.parent = None

#     def addChild(self, child):
#         self.children.append(child)

#     def childAtRow(self, row):
#         return self.children[row]

#     def rowOfChild(self, child):
#         for i, item in enumerate(self.children):
#             if item == child:
#                 return i
#         return -1

#     def removeChild(self, row):
#         value = self.children[row]
#         self.children.remove(value)

#         return True

#     def __len__(self):
#         return len(self.children)


# class myModel(QAbstractItemModel):

#     def __init__(self, parent=None):
#         super(myModel, self).__init__(parent)

#         self.treeView = parent
#         self.headers = ['Item','State','Description']

#         self.columns = 3

#         # Create items
#         self.root = treeNode('root', 'on', 'this is root', None)

#         itemA = treeNode('itemA', 'on', 'this is item A', self.root)
#         itemA1 = treeNode('itemA1', 'on', 'this is item A1', itemA)

#         itemB = treeNode('itemB', 'on', 'this is item B', self.root)
#         itemB1 = treeNode('itemB1', 'on', 'this is item B1', itemB)

#         itemC = treeNode('itemC', 'on', 'this is item C', self.root)
#         itemC1 = treeNode('itemC1', 'on', 'this is item C1', itemC)


#     def supportedDropActions(self):
#         return Qt.CopyAction | Qt.MoveAction


#     def flags(self, index):
#         defaultFlags = QAbstractItemModel.flags(self, index)

#         if index.isValid():
#             return Qt.ItemIsEditable | Qt.ItemIsDragEnabled | \
#                     Qt.ItemIsDropEnabled | defaultFlags

#         else:
#             return Qt.ItemIsDropEnabled | defaultFlags


#     def headerData(self, section, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return QVariant(self.headers[section])
#         return QVariant()

#     def mimeTypes(self):
#         types = QStringList()
#         types.append('application/x-ets-qt4-instance')
#         return types

#     def mimeData(self, index):
#         node = self.nodeFromIndex(index[0])
#         mimeData = PyMimeData(node)
#         return mimeData


#     def dropMimeData(self, mimedata, action, row, column, parentIndex):
#         if action == Qt.IgnoreAction:
#             return True

#         dragNode = mimedata.instance()
#         parentNode = self.nodeFromIndex(parentIndex)

#         # make an copy of the node being moved
#         newNode = deepcopy(dragNode)
#         newNode.setParent(parentNode)
#         self.insertRow(len(parentNode)-1, parentIndex)
#         self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
# parentIndex, parentIndex)
#         return True


#     def insertRow(self, row, parent):
#         return self.insertRows(row, 1, parent)


#     def insertRows(self, row, count, parent):
#         self.beginInsertRows(parent, row, (row + (count - 1)))
#         self.endInsertRows()
#         return True


#     def removeRow(self, row, parentIndex):
#         return self.removeRows(row, 1, parentIndex)


#     def removeRows(self, row, count, parentIndex):
#         self.beginRemoveRows(parentIndex, row, row)
#         node = self.nodeFromIndex(parentIndex)
#         node.removeChild(row)
#         self.endRemoveRows()

#         return True


#     def index(self, row, column, parent):
#         node = self.nodeFromIndex(parent)
#         return self.createIndex(row, column, node.childAtRow(row))


#     def data(self, index, role):
#         if role == Qt.DecorationRole:
#             return QVariant()

#         if role == Qt.TextAlignmentRole:
#             return QVariant(int(Qt.AlignTop | Qt.AlignLeft))

#         if role != Qt.DisplayRole:
#             return QVariant()

#         node = self.nodeFromIndex(index)

#         if index.column() == 0:
#             return QVariant(node.name)

#         elif index.column() == 1:
#             return QVariant(node.state)

#         elif index.column() == 2:
#             return QVariant(node.description)
#         else:
#             return QVariant()


#     def columnCount(self, parent):
#         return self.columns


#     def rowCount(self, parent):
#         node = self.nodeFromIndex(parent)
#         if node is None:
#             return 0
#         return len(node)


#     def parent(self, child):
#         if not child.isValid():
#             return QModelIndex()

#         node = self.nodeFromIndex(child)

#         if node is None:
#             return QModelIndex()

#         parent = node.parent

#         if parent is None:
#             return QModelIndex()

#         grandparent = parent.parent
#         if grandparent is None:
#             return QModelIndex()
#         row = grandparent.rowOfChild(parent)

#         assert row != - 1
#         return self.createIndex(row, 0, parent)


#     def nodeFromIndex(self, index):
#         return index.internalPointer() if index.isValid() else self.root



# class myTreeView(QTreeView):

#     def __init__(self, parent=None):
#         super(myTreeView, self).__init__(parent)

#         self.myModel = myModel()
#         self.setModel(self.myModel)

#         self.dragEnabled()
#         self.acceptDrops()
#         self.showDropIndicator()
#         self.setDragDropMode(QAbstractItemView.InternalMove)

#         self.connect(self.model(),
# SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self.change)
#         self.expandAll()

#     def change(self, topLeftIndex, bottomRightIndex):
#         self.update(topLeftIndex)
#         self.expandAll()
#         self.expanded()

#     def expanded(self):
#         for column in range(self.model().columnCount(QModelIndex())):
#             self.resizeColumnToContents(column)



# class Ui_MainWindow(object):
#     def setupUi(self, MainWindow):
#         MainWindow.setObjectName("MainWindow")
#         MainWindow.resize(600, 400)
#         self.centralwidget = QWidget(MainWindow)
#         self.centralwidget.setObjectName("centralwidget")
#         self.horizontalLayout = QHBoxLayout(self.centralwidget)
#         self.horizontalLayout.setObjectName("horizontalLayout")
#         self.treeView = myTreeView(self.centralwidget)
#         self.treeView.setObjectName("treeView")
#         self.horizontalLayout.addWidget(self.treeView)
#         MainWindow.setCentralWidget(self.centralwidget)
#         self.menubar = QMenuBar(MainWindow)
#         self.menubar.setGeometry(QRect(0, 0, 600, 22))
#         self.menubar.setObjectName("menubar")
#         MainWindow.setMenuBar(self.menubar)
#         self.statusbar = QStatusBar(MainWindow)
#         self.statusbar.setObjectName("statusbar")
#         MainWindow.setStatusBar(self.statusbar)

#         self.retranslateUi(MainWindow)
#         QMetaObject.connectSlotsByName(MainWindow)

#     def retranslateUi(self, MainWindow):
#         MainWindow.setWindowTitle(QApplication.translate("MainWindow",
# "MainWindow", None, QApplication.UnicodeUTF8))


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     MainWindow = QMainWindow()
#     ui = Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec_())
