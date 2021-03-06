import sys
from PyQt4 import QtGui, QtCore

class displayItem(QtGui.QWidget):  #A simple widget to display, just centers a digit in a 100x100 widget
    def __init__(self,num):
        QtGui.QWidget.__init__(self)
        self.size=100
        self.resize(self.size,self.size)
        self.setMinimumSize(self.size,self.size)
        self.text = num
    def paintEvent(self,event):
        p = QtGui.QPainter(self)
        p.drawText(self.size//2,self.size//2,str(self.text))

app = QtGui.QApplication(sys.argv)
widget = QtGui.QTreeWidget()
widget.setWindowTitle('simple tree')

#Build the list widgets
treeItem1 = QtGui.QTreeWidgetItem(widget)
treeItem1.setText(0,"TreeWidget Parent")   #Sets the "header" for your [+] box

list1 = QtGui.QListWidget()                #This will contain your icon list
list1.setMovement(QtGui.QListView.Static)  #otherwise the icons are draggable
list1.setResizeMode(QtGui.QListView.Adjust) #Redo layout every time we resize
list1.setViewMode(QtGui.QListView.IconMode) #Layout left-to-right, not top-to-bottom

listItem = QtGui.QListWidgetItem(list1)
listItem.setSizeHint(QtCore.QSize(100,100)) #Or else the widget items will overlap (irritating bug)
list1.setItemWidget(listItem,displayItem(1))

listItem = QtGui.QListWidgetItem(list1)     #Add a few more items
listItem.setSizeHint(QtCore.QSize(100,100))
list1.setItemWidget(listItem,displayItem(2))

listItem = QtGui.QListWidgetItem(list1)
listItem.setSizeHint(QtCore.QSize(100,100))
list1.setItemWidget(listItem,displayItem(3))

list1.setAutoFillBackground(True)                #Required for a widget that will be a QTreeWidgetItem widget
treeSubItem1 = QtGui.QTreeWidgetItem(treeItem1)  #Make a subitem to hold our list
widget.setItemWidget(treeSubItem1,0,list1)       #Assign this list as a tree item

treeItem2 = QtGui.QTreeWidgetItem(widget)        #Make a fake second parent
treeItem2.setText(0,"TreeWidget Parent II")

widget.show()           #kick off the app in standard PyQt4 fashion
sys.exit(app.exec_())