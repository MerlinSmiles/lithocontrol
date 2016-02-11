import sys
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtGui import QStandardItem

class MyItem(QStandardItem):
#     def __init__(self, data, *args):
# class SetTreeItem(QStandardItem):
    def __init__(self, data, *args):
        super(MyItem, self).__init__(data)
        # self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.changed = False

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

    # def data(self, role=QtCore.Qt.UserRole+1):
    #     # print role
    #     if role == QtCore.Qt.DisplayRole:
    #         return self.itemData
    #     # return self.itemData
    #     return super().data(role) # Fall back to the default method
    # def data(self, x):
    #     print x
    #     return self.itemData

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False
        for row in range(count):
            self.childItems.pop(position)
        return True

    def setData(self, value, role = None):
        if role == QtCore.Qt.EditRole:
            print value.toPyObject()
            self.itemData = value

        # QItemDelegate.__init__(self, parent, *args)

    # def paint(self, painter, option, index):
    #     painter.save()

    #     # set background color
    #     painter.setPen(QPen(Qt.NoPen))
    #     if option.state & QStyle.State_Selected:
    #         painter.setBrush(QBrush(Qt.red))
    #     else:
    #         painter.setBrush(QBrush(Qt.white))
    #     painter.drawRect(option.rect)

    #     # set text color
    #     painter.setPen(QPen(Qt.black))
    #     value = index.data(Qt.DisplayRole)
    #     if value.isValid():
    #         text = value.toString()
    #         painter.drawText(option.rect, Qt.AlignLeft, text)

    #     painter.restore()
class Example(QtGui.QWidget):

    def __init__(self):

        super(Example, self).__init__()

        self.data = {}
        self.data['settings'] = {}
        self.data['settings']['buffer_size'] = 10000000
        self.data['settings']['acq_rate'] = 30000          # samples/second
        self.data['settings']['acq_samples'] = 1000        # every n samples
        self.data['settings']['device_input'] = "PCI-6251"
        self.data['settings']['SR_sensitivity'] = 100e-9
        self.data['settings']['PAR_sensitivity'] = 1e-3
        self.data['settings']['plot_2pt'] = True
        self.data['settings']['plot_4pt'] = True
        self.data['settings']['plot_current'] = True
        self.data['settings']['plotR'] = True
        self.data['settings']['DHTport'] = 6

        self.data['in'] = {}
        ch0 = self.data['in']['ch0'] = {}
        ch0['channel'] = "ai0"
        ch0['name'] = 'Current'
        ch0['curr_amp'] = 0
        ch0['amplitude'] = 1e-3
        ch0['min'] = -10 # +/- 100 mV is the minimum bipolar range
        ch0['max'] = 10
        ch0['plot_raw'] = True
        ch0['freq_chan'] = 0
        ch1 = self.data['in']['ch1'] = {}
        ch1['channel'] = "ai1"
        ch1['name'] = 'A-B'
        ch1['amplitude'] = 1*1e-3
        ch1['min'] = -10
        ch1['max'] = 10
        ch1['plot_raw'] = True
        ch1['freq_chan'] = 0
        ch1['curr_amp'] = 0


        # Layout
        self.tree = QtGui.QTreeView()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tree)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 600, 400)

        # Tree view
        self.tree.setModel(QtGui.QStandardItemModel())
        self.model = self.tree.model()
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setHeaderHidden(False)

        self.model.setHorizontalHeaderLabels(['Parameter', 'Value', 'type'])

        self.iterDict(self.data, self.model)
        self.tree.expandAll()

        for column in range(self.model.columnCount()):
            self.tree.resizeColumnToContents(column)

        QtCore.QObject.connect(self.model, QtCore.SIGNAL('itemChanged(QModelIndex)'), self.test)
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL('valueChanged(QModelIndex)'), self.test)

    @QtCore.pyqtSlot("QModelIndex")
    def test(self, bla =None):
        print bla

    def iterDict(self, data, parent):
        for x in data:
            if not data[x]:
                continue
            if type(data[x]) == dict:
                node = MyItem(x)
                node.setFlags(QtCore.Qt.NoItemFlags)
                self.iterDict(data[x], node)
                parent.appendRow(node)
            else:
                value =  data[x]
                child0 = MyItem(x)
                child0.setFlags(QtCore.Qt.NoItemFlags | QtCore.Qt.ItemIsEnabled)
                child1 = MyItem(str(value))
                child1.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | ~ QtCore.Qt.ItemIsSelectable)
                child2 = MyItem(type(value).__name__)
                child2.setFlags(QtCore.Qt.ItemIsEnabled)

                parent.appendRow([child0, child1, child2])


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())
