import sys, os
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from copy import deepcopy
import pickle as cPickle

class TreeItem(object):
    def __init__(self, name, parent=None):

        self.name = str(name)
        self.parent = parent
        self.children = []
        self.setParent(parent)

    def setParent(self, parent):
        if parent != None:
            self.parent = parent
            self.parent.appendChild(self)
        else:     self.parent = None

    def appendChild(self, child):
        self.children.append(child)

    def childAtRow(self, row):
        if len(self.children)>row:
            return self.children[row]

    def rowOfChild(self, child):
        for i, item in enumerate(self.children):
            if item == child:  return i
        return -1

    def removeChild(self, row):
        value = self.children[row]
        self.children.remove(value)
        return True

    def __len__(self):
        return len(self.children)

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self):

        QtCore.QAbstractItemModel.__init__(self)

        self.columns = 1
        self.clickedItem=None

        self.root = TreeItem('root', None)
        levelA = TreeItem('levelA', self.root)
        levelB = TreeItem('levelB', levelA)
        levelC1 = TreeItem('levelC1', levelB)
        levelC2 = TreeItem('levelC2', levelB)
        levelC3 = TreeItem('levelC3', levelB)
        levelD = TreeItem('levelD', levelC3)

        levelE = TreeItem('levelE', levelD)
        levelF = TreeItem('levelF', levelE)

    def nodeFromIndex(self, index):
        return index.internalPointer() if index.isValid() else self.root

    def index(self, row, column, parent):
        node = self.nodeFromIndex(parent)
        return self.createIndex(row, column, node.childAtRow(row))

    def parent(self, child):
        # print ('\n parent(child)', child  # PyQt4.QtCore.QModelIndex)
        if not child.isValid():  return QModelIndex()
        node = self.nodeFromIndex(child)
        if node is None:   return QModelIndex()
        parent = node.parent
        if parent is None:      return QModelIndex()
        grandparent = parent.parent

        if grandparent==None:    return QModelIndex()

        row = grandparent.rowOfChild(parent)
        assert row != - 1

        return self.createIndex(row, 0, parent)

    def rowCount(self, parent):
        node = self.nodeFromIndex(parent)
        if node is None: return 0
        return len(node)

    def columnCount(self, parent):
        return self.columns

    def data(self, index, role):
        if role == Qt.DecorationRole:
            return
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignTop | Qt.AlignLeft)
        if role != Qt.DisplayRole:
            return
        node = self.nodeFromIndex(index)
        if index.column() == 0:
            return str(node.name)
        elif index.column() == 1:
            return str(node.state)
        elif index.column() == 2:
            return str(node.description)
        else:   return str()

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)
        if index.isValid():  return Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | defaultFlags
        else:   return Qt.ItemIsDropEnabled | defaultFlags

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if value.toString() and len(value.toString())>0:
                self.nodeFromIndex(index).name = value.toString()
                self.dataChanged.emit(index, index)
            return True

    def mimeTypes(self):
        return ['bstream', 'text/xml']

    def mimeData(self, indexes):

        mimedata = QtCore.QMimeData()
        bstream = cPickle.dumps(self.nodeFromIndex(indexes[0]))
        mimedata.setData('bstream', bstream)
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parentIndex):

        if action == Qt.IgnoreAction: return True

        droppedNode=cPickle.loads(str(mimedata.data('bstream')))

        droppedIndex = self.createIndex(row, column, droppedNode)

        parentNode = self.nodeFromIndex(parentIndex)

        newNode = deepcopy(droppedNode)
        newNode.setParent(parentNode)

        self.insertRow(len(parentNode)-1, parentIndex)

        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), parentIndex, parentIndex)

        return True

    def insertRow(self, row, parent):
        return self.insertRows(row, 1, parent)
    def insertRows(self, row, count, parent):
        self.beginInsertRows(parent, row, (row + (count - 1)))
        self.endInsertRows()
        return True

    def removeRow(self, row, parentIndex):
        return self.removeRows(row, 1, parentIndex)

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row)
        node = self.nodeFromIndex(parentIndex)
        node.removeChild(row)
        self.endRemoveRows()
        return True


class GUI(QtGui.QDialog):
    def build(self, myWindow):
        myWindow.resize(600, 400)
        self.myWidget = QWidget(myWindow)
        self.boxLayout = QtGui.QVBoxLayout(self.myWidget)

        self.treeView = QtGui.QTreeView()

        self.treeModel = TreeModel()
        self.treeView.setModel(self.treeModel)
        self.treeView.expandAll()
        self.treeView.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.treeView.connect(self.treeView.model(), SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self.onDataChanged)
        QtCore.QObject.connect(self.treeView, QtCore.SIGNAL("clicked (QModelIndex)"),  self.treeItemClicked)
        self.boxLayout.addWidget(self.treeView)


        self.PrintButton= QtGui.QPushButton("Print")
        self.PrintButton.clicked.connect(self.PrintOut)
        self.boxLayout.addWidget(self.PrintButton)

        self.DeleteButton= QtGui.QPushButton("Delete")
        self.DeleteButton.clicked.connect(self.DeleteLevel)
        self.boxLayout.addWidget(self.DeleteButton)

        self.insertButton= QtGui.QPushButton("Insert")
        self.insertButton.clicked.connect(self.insertLevel)
        self.boxLayout.addWidget(self.insertButton)

        self.duplicateButton= QtGui.QPushButton("Duplicate")
        self.duplicateButton.clicked.connect(self.duplicateLevel)
        self.boxLayout.addWidget(self.duplicateButton)

        myWindow.setCentralWidget(self.myWidget)


    def make_dirs_from_dict(self, dirDict, current_dir='/'):
        for key, val in dirDict.items():
            #os.mkdir(os.path.join(current_dir, key))
            print ("\t\t Creating directory: ", os.path.join(current_dir, key))
            if type(val) == dict:
                self.make_dirs_from_dict(val, os.path.join(current_dir, key))

    def PrintOut(self):
        result_dict = {}
        for a1 in self.treeView.model().root.children:
            result_dict[str(a1.name)]={}
            for a2 in a1.children:
                result_dict[str(a1.name)][str(a2.name)]={}
                for a3 in a2.children:
                    result_dict[str(a1.name)][str(a2.name)][str(a3.name)]={}
                    for a4 in a3.children:
                        result_dict[ str(a1.name)][str(a2.name)][str(a3.name)][str(a4.name)]={}
                        for a5 in a4.children:
                            result_dict[ str(a1.name)][str(a2.name)][str(a3.name)][str(a4.name)][str(a5.name)]={}
                            for a6 in a5.children:
                                result_dict[str(a1.name)][str(a2.name)][str(a3.name)][str(a4.name)][str(a5.name)][str(a6.name)]={}
                                for a7 in a6.children:
                                    result_dict[str(a1.name)][str(a2.name)][str(a3.name)][str(a4.name)][str(a5.name)][str(a6.name)][str(a7.name)]={}


        self.make_dirs_from_dict(result_dict)


    def DeleteLevel(self):
        if len(self.treeView.selectedIndexes())==0: return

        currentIndex = self.treeView.selectedIndexes()[0]
        currentRow=currentIndex.row()
        currentColumn=currentIndex.column()
        currentNode = currentIndex.internalPointer()

        parentNode = currentNode.parent
        parentIndex = self.treeView.model().createIndex(currentRow, currentColumn, parentNode)
        print ('\n\t\t\t CurrentNode:', currentNode.name, ', ParentNode:', currentNode.parent.name, ', currentColumn:', currentColumn, ', currentRow:', currentRow)

        # self.treeView.model().removeRow(len(parentNode)-1, parentIndex)

        self.treeView.model().removeRows(currentRow, 1, parentIndex )

        #self.treeView.model().removeRow(len(parentNode), parentIndex)
        #self.treeView.model().emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), parentIndex, parentIndex)

    def insertLevel(self):
        if len(self.treeView.selectedIndexes())==0: return

        currentIndex = self.treeView.selectedIndexes()[0]
        currentNode = currentIndex.internalPointer()
        newItem = TreeItem('Brand New', currentNode)
        self.treeView.model().insertRow(len(currentNode)-1, currentIndex)
        self.treeView.model().emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), currentIndex, currentIndex)

    def duplicateLevel(self):
        if len(self.treeView.selectedIndexes())==0: return

        currentIndex = self.treeView.selectedIndexes()[0]
        currentRow=currentIndex.row()
        currentColumn=currentIndex.column()
        currentNode=currentIndex.internalPointer()

        parentNode=currentNode.parent
        parentIndex=self.treeView.model().createIndex(currentRow, currentColumn, parentNode)
        parentRow=parentIndex.row()
        parentColumn=parentIndex.column()

        newNode = deepcopy(currentNode)
        newNode.setParent(parentNode)

        self.treeView.model().insertRow(len(parentNode)-1, parentIndex)
        self.treeView.model().emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), parentIndex, parentIndex)

        print ('\n\t\t\t CurrentNode:', currentNode.name, ', ParentNode:', parentNode.name, ', currentColumn:', currentColumn, ', currentRow:', currentRow, ', parentColumn:', parentColumn, ', parentRow:', parentRow)
        self.treeView.update()
        self.treeView.expandAll()


    def treeItemClicked(self, index):
        print ("\n clicked item ----------->", index.internalPointer().name)

    def onDataChanged(self, indexA, indexB):
        print ("\n onDataChanged NEVER TRIGGERED! ####################### \n ", index.internalPointer().name)
        self.treeView.update(indexA)
        self.treeView.expandAll()
        self.treeView.expanded()



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    myWindow = QMainWindow()
    myGui = GUI()
    myGui.build(myWindow)
    myWindow.show()
    sys.exit(app.exec_())
