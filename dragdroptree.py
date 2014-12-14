import sys
import sip
from PyQt4 import QtGui
from PyQt4 import QtCore



################################################################################
class Branch(object):
    """
    Basic branch/leaf node.
    """

    #---------------------------------------------------------------------------
    def __init__(self, name, value, parent=None):
        """
        Constructor.
        """
        super(Branch, self).__init__()

        #name and parent are both to be stored directly as variables
        self.name = name
        self.parent = parent
        self.value = value

        #store sub-objects (usually other branches)
        self.objD = dict()
        self.nameL = list()


    #---------------------------------------------------------------------------
    def get_name(self):
        """
        Getter.
        """
        return self.name


    #---------------------------------------------------------------------------
    def get_parent(self):
        """
        Returns the parent of this object.
        """
        return self.parent


    #---------------------------------------------------------------------------
    def set_value(self, value):
        """
        Generic setter for all settings.
        """
        self.value = value


    #---------------------------------------------------------------------------
    def get_value(self):
        """
        Generic getter for all settings. Returns the display value
        """
        return self.value


    #---------------------------------------------------------------------------
    def add_child_obj(self, obj, row=None):
        """
        Adds the param object to the dict and list.
        """
        self.objD[obj.get_name()] = obj
        if row == None:
            self.nameL.append(obj.get_name())
        else:
            self.nameL.insert(row, obj.get_name())

        print "JUST ADDED CHILD AT ROW:", self.nameL.index(obj.get_name())


    #---------------------------------------------------------------------------
    def remove_child_at_row(self, row):
        """
        Removes the param object from the dict and list.
        """
        childName = self.nameL[row]
        del(self.nameL[row])
        del(self.objD[childName])


    #---------------------------------------------------------------------------
    def get_child_count(self):
        """
        Returns the number of children in this branch.
        """
        return len(self.nameL)


    #---------------------------------------------------------------------------
    def get_child_list(self):
        """
        Returns a list of the visible children names.
        """
        return self.nameL


    #---------------------------------------------------------------------------
    def get_child_at_row(self, row):
        """
        Returns a specific child object based on its ordinal (only consider
        visible children).
        """
        childName = self.nameL[row]
        return self.objD[childName]


    #---------------------------------------------------------------------------
    def get_child_by_name(self, childName):
        """
        Returns a specific child object based on its name.
        """
        return self.objD[childName]


    #---------------------------------------------------------------------------
    def get_index(self):
        """
        Returns this object's index position with regard to its siblings.
        """
        siblingsL = self.parent.get_child_list()
        return siblingsL.index(self.get_name())




################################################################################
class MyTreeView(QtGui.QTreeView):
    """
    Overrides the QTreeView to handle keypress events.
    """

    #---------------------------------------------------------------------------
    def __init__(self, model, parent=None):
        """
        Constructor for the TreeView class.
        """
        super(MyTreeView, self).__init__(parent)
        self.setModel(model)




################################################################################
class MyTreeModel(QtCore.QAbstractItemModel):

    """
    My tree view data model
    """

    #---------------------------------------------------------------------------
    def __init__(self, root):
        """
        Constructor for the TreeModel class
        """
        super(MyTreeModel, self).__init__()
        self.root = root
        self.fontSize = 8
        self.selection = None


    #---------------------------------------------------------------------------
    def columnCount(self, index=QtCore.QModelIndex()):
        """
        Returns the number of columns in the treeview.
        """
        return 1


    #---------------------------------------------------------------------------
    def rowCount(self, index=QtCore.QModelIndex()):
        """
        Returns the number of children of the current index obj.
        """
        if index.column() > 0:
            return 0
        if not index.isValid():
            item = self.root
        else:
            item = index.internalPointer()
        if item:
            return item.get_child_count()
        return 0


    #---------------------------------------------------------------------------
    def index(self, row, column, parent):
        """
        Returns a QModelIndex item for the current row, column, and parent.
        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.root
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.get_child_at_row(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()


    #---------------------------------------------------------------------------
    def parent(self, index):
        """
        Returns a QModelIndex item for the parent of the given index.
        """
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        if not childItem:
            return QtCore.QModelIndex()

        parentItem = childItem.get_parent()

        if parentItem == self.root:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.get_index(), 0, parentItem)


    #---------------------------------------------------------------------------
    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Returns the text or formatting for a particular cell, depending on the
        role supplied.
        """
        #invalid indexes return invalid results
        if not index.isValid():
            return QtCore.QVariant()

        #access the underlying referenced object
        item = index.internalPointer()

        #edit role displays the raw values
        if role == QtCore.Qt.EditRole:
            return item.get_value()

        #return the data to display
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return item.get_value()

        return QtCore.QVariant()


    #---------------------------------------------------------------------------
    def headerData(self, index, orientation, role=QtCore.Qt.DisplayRole):
        """
        Returns the text for the horizontal headers (parameter names)
        """

        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                alignment = int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
                return QtCore.QVariant(alignment)
            alignment = int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            return QtCore.QVariant(alignment)

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            if int(index) == 0:
                return "Name"


    #---------------------------------------------------------------------------
    def supportedDropActions(self):
        """
        We allow re-ordering.
        """
        return QtCore.Qt.MoveAction


    #---------------------------------------------------------------------------
    def flags(self, index):
        """
        Returns whether or not the current item is editable/selectable/etc.
        """

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        #by default, you can't do anything
        enabled = QtCore.Qt.ItemIsEnabled
        selectable = QtCore.Qt.ItemIsSelectable
        editable = QtCore.Qt.ItemIsEditable
        draggable = QtCore.Qt.ItemIsDragEnabled
        droppable = QtCore.Qt.ItemIsDropEnabled

        #return our flags.
        return enabled | selectable| editable| draggable| droppable


    #---------------------------------------------------------------------------
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Sets the data.
        """
        #convert the value into a string
        if value:
            item = index.internalPointer()
            item.set_value(value)

            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                                     index, index)
        return True


    #---------------------------------------------------------------------------
    def supportedDropActions(self):
        """
        Only allow moves
        """
        return QtCore.Qt.MoveAction


    #---------------------------------------------------------------------------
    def mimeTypes(self):
        """
        Only accept the internal custom drop type which is plain text
        """
        types = QtCore.QStringList()
        types.append('text/plain')
        return types


    #---------------------------------------------------------------------------
    def mimeData(self, index):
        """
        Wrap the index up as a list of rows and columns of each
        parent/grandparent/etc
        """
        rc = ""
        theIndex = index[0] #<- for testing purposes we only deal with 1st item
        while theIndex.isValid():
            rc = rc + str(theIndex.row()) + ";" + str(theIndex.column())
            theIndex = self.parent(theIndex)
            if theIndex.isValid():
                rc = rc + ","
        mimeData = QtCore.QMimeData()
        mimeData.setText(rc)
        return mimeData


    #---------------------------------------------------------------------------
    def dropMimeData(self, data, action, row, column, parentIndex):
        """
        Extract the whole ancestor list of rows and columns and rebuild the
        index item that was originally dragged
        """
        if action == QtCore.Qt.IgnoreAction:
            return True

        if data.hasText():
            ancestorL = str(data.text()).split(",")
            ancestorL.reverse() #<- stored from the child up, we read from ancestor down
            pIndex = QtCore.QModelIndex()
            for ancestor in ancestorL:
                srcRow = int(ancestor.split(";")[0])
                srcCol = int(ancestor.split(";")[1])
                itemIndex = self.index(srcRow, srcCol, pIndex)
                pIndex = itemIndex

        item = itemIndex.internalPointer()
        parent = parentIndex.internalPointer()

        #modify the row if it is -1 (we want to append to the end of the list)
        if row == -1:
            row = parent.get_child_count()

        self.beginInsertRows(parentIndex, row-1, row)
        print "------------------"
        parentIndex.internalPointer().add_child_obj(item)
        print "------------------"
        self.endInsertRows()
        print "sanity check:"
        print "dragged Node", item.get_name()
        print "parent Node", parent.get_name()
        print "inserted at row",row
        print "inserted Node:",parent.get_child_at_row(row).get_name()
        print row, column
        print "from index():",self.index(row, 0, parentIndex).internalPointer().get_name()
        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                                self.index(row, 0, parentIndex),
                                self.index(row, 0, parentIndex))
        return True


    #---------------------------------------------------------------------------
    def insertRow(self, row, parent):
        print "insertRow"
        return self.insertRows(row, 1, parent)


    #---------------------------------------------------------------------------
    def insertRows(self, row, count, parent):
        print "insertRows"
        self.beginInsertRows(parent, row, (row + (count - 1)))
        self.endInsertRows()
        return True


    #---------------------------------------------------------------------------
    def removeRow(self, row, parentIndex):
        print "removeRow"
        return self.removeRows(row, 1, parentIndex)


    #---------------------------------------------------------------------------
    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row)
        print "about to remove child at row:",row
        print "which is under the parent named:",parentIndex.internalPointer().get_name()
        print "and whose own name is:",parentIndex.internalPointer().get_child_at_row(row).get_name()
        parentIndex.internalPointer().remove_child_at_row(row)
        self.endRemoveRows()
        return True









class Ui_MainWindow(object):

    def printChildren(self, item):
        print item.name
        for child in item.get_child_list():
            self.printChildren(item.get_child_by_name(child))

    def printit(self):
        self.printChildren(self.root)


    def setupUi(self, MainWindow):

        root = Branch("root", "root", QtCore.QVariant)

        item1 = Branch("ITEM1","ITEM1",root)
        item2 = Branch("ITEM2","ITEM2",root)
        item3 = Branch("ITEM3","ITEM3",root)
        root.add_child_obj(item1)
        root.add_child_obj(item2)
        root.add_child_obj(item3)

        item1a = Branch("thinga","thinga",item1)
        item1b = Branch("thingb","thingb",item1)
        item1.add_child_obj(item1a)
        item1.add_child_obj(item1b)

        item2a = Branch("thingc","thingc",item2)
        item2b = Branch("thingd","thingd",item2)
        item2.add_child_obj(item2a)
        item2.add_child_obj(item2b)

        item3a = Branch("thinge","thinge",item3)
        item3b = Branch("thingf","thingf",item3)
        item3.add_child_obj(item3a)
        item3.add_child_obj(item3b)


        item1a1 = Branch("___A","___A",item1a)
        item1a2 = Branch("___B","___B",item1a)
        item1a.add_child_obj(item1a1)
        item1a.add_child_obj(item1a2)

        item1b1 = Branch("___C","___C",item1b)
        item1b2 = Branch("___D","___D",item1b)
        item1b.add_child_obj(item1b1)
        item1b.add_child_obj(item1b2)

        item2a1 = Branch("___E","___E",item2a)
        item2a2 = Branch("___F","___F",item2a)
        item2a.add_child_obj(item2a1)
        item2a.add_child_obj(item2a2)

        item2b1 = Branch("___G","___G",item2b)
        item2b2 = Branch("___H","___H",item2b)
        item2b.add_child_obj(item2b1)
        item2b.add_child_obj(item2b2)

        item3a1 = Branch("___J","___J",item3a)
        item3a2 = Branch("___K","___K",item3a)
        item3a.add_child_obj(item3a1)
        item3a.add_child_obj(item3a2)

        item3b1 = Branch("___L","___L",item3b)
        item3b2 = Branch("___M","___M",item3b)
        item3b.add_child_obj(item3b1)
        item3b.add_child_obj(item3b2)

        self.root = root

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 400)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.myModel = MyTreeModel(root)
        self.treeView = MyTreeView(self.myModel, self.centralwidget)
        self.treeView.setObjectName("treeView")
        self.treeView.dragEnabled()
        self.treeView.acceptDrops()
        self.treeView.showDropIndicator()
        self.treeView.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.treeView.expandAll()
        self.horizontalLayout.addWidget(self.treeView)
        self.btn = QtGui.QPushButton('print', MainWindow)
        MainWindow.connect(self.btn, QtCore.SIGNAL("clicked()"), self.printit)
        self.horizontalLayout.addWidget(self.btn)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 600, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)









    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
