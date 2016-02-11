
# -*- coding: utf-8 -*-

import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

class mGroupParameterItem(pTypes.GroupParameterItem):
    def __init__(self, param, depth):
        pTypes.GroupParameterItem.__init__(self, param, depth)
    def updateDepth(self, depth):
        ## Change item's appearance based on its depth in the tree
        ## This allows highest-level groups to be displayed more prominently.
        if depth == 0:
            for c in [0,1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(200,200,200)))
                self.setForeground(c, QtGui.QBrush(QtGui.QColor(0,0,0)))
                font = self.font(c)
                font.setBold(True)
                font.setPointSize(font.pointSize()+1)
                self.setFont(c, font)
                # self.setSizeHint(0, QtCore.QSize(0, 25))
        else:
            for c in [0,1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(220,220,220)))
                font = self.font(c)
                font.setBold(True)
                #font.setPointSize(font.pointSize()+1)
                self.setFont(c, font)
                self.setSizeHint(0, QtCore.QSize(0, 20))

class mGroupParameter(Parameter):
    """
    Group parameters are used mainly as a generic parent item that holds (and groups!) a set
    of child parameters.

    It also provides a simple mechanism for displaying a button or combo
    that can be used to add new parameters to the group. To enable this, the group
    must be initialized with the 'addText' option (the text will be displayed on
    a button which, when clicked, will cause addNew() to be called). If the 'addList'
    option is specified as well, then a dropdown-list of addable items will be displayed
    instead of a button.
    """
    itemClass = mGroupParameterItem

    def addNew(self, typ=None):
        """
        This method is called when the user has requested to add a new item to the group.
        """
        raise Exception("Must override this function in subclass.")

    def setAddList(self, vals):
        """Change the list of options available for the user to add to the group."""
        self.setOpts(addList=vals)

registerParameterType('group', mGroupParameter, override=True)

class MainWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        ## Create two ParameterTree widgets, both accessing the same data


        params = [
            {"name": "Plotting", "type": "group", "children": [
                {"name": "Enable", "type": "bool", "value": 1},
                {"name": "Plot Current", "type": "bool", "value": 1},
                {"name": "Plot 2p", "type": "bool", "value": 1},
                {"name": "Plot 4p", "type": "bool", "value": 1},
                {'name': 'Timing', 'type': 'float', 'value': 0.1, 'siPrefix': True, 'suffix': 's', 'step':0.1},
            ]},
          {"name": "Measurements", "type": "group", "children": [
              {"name": "DHT-arduino", "type": "group", "children": [
                    {"name": "Serial Port", "type": "int", "value": 5},
                    {'name': 'Temperature', 'type': 'float', 'value': 20.1, 'siPrefix': True, 'suffix': '\xb0C', 'readonly': True},
                    {'name': 'Humidity', 'type': 'float', 'value': 11.1, 'siPrefix': True, 'suffix': '%', 'readonly': True},
              ]},
            {"name": "LockIns", "type": "group", "expanded": False, "children": [
              {"name": "SR-LockIn", "type": "group", "children": [
                    {"name": "Sensitivity", "type": "float", "value": 10e-09, 'dec': True, 'step': 1, 'siPrefix': True, 'suffix': 'A'},
              ]},
              {"name": "PAR-LockIn", "type": "group", "expanded": False, "children": [
                    {'name': 'Sensitivity', 'type': 'float', 'value': 1.0e-3, 'dec': True, 'step': 1, 'siPrefix': True, 'suffix': 'V'},
              ]},
            ]},
          ]},
        ]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.p.sigTreeStateChanged.connect(self.change)
        # Too lazy for recursion:
        for child in self.p.children():
            child.sigValueChanging.connect(self.valueChanging)
            for ch2 in child.children():
                ch2.sigValueChanging.connect(self.valueChanging)

        self.p.param('Plotting', 'Enable').sigValueChanged.connect(self.test)
        t = ParameterTree()
        t.setParameters(self.p, showTop=False)
        t.setWindowTitle('pyqtgraph example: Parameter Tree')
        t2 = ParameterTree()
        t2.setParameters(self.p, showTop=False)

        win = self
        layout = QtGui.QGridLayout()
        win.setLayout(layout)
        layout.addWidget(QtGui.QLabel("These are two views of the same data. They should always display the same values."), 0,  0, 1, 2)
        layout.addWidget(t, 1, 0, 1, 1)
        layout.addWidget(t2, 1, 1, 1, 1)
        win.show()
        win.resize(800,800)


    def change(self, param, changes):
        print("tree changes:")
        print (self.p.param('Plotting', 'Enable').value())
        print(param.value())
        for param, change, data in changes:
            path = self.p.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
            print('  parameter: %s'% childName)
            print('  change:    %s'% change)
            print('  data:      %s'% str(data))
            print('  ----------')



    def valueChanging(self, param, value):
        return
        print("Value changing (not finalized):", param, value)

    def test(self, param, value):
        # pass
        print("test:", param, value)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())

