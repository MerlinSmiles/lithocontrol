#!/usr/bin/env python
demo = False
try:
    import gwy, gwyutils
except:
    demo = True
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
import json
from copy import deepcopy, copy

with open('./config.json', 'r') as f:
    config = json.load(f)
if demo:
    config['storage'] = config['demo_storage']

print(config['storage'])

def_dxf_file = 'F:/lithography/DesignFiles/current.dxf'
def_dxf_file = config['storage']['def_dxf_file']

from source.treeclass3 import *



colors = ['vivid_yellow','strong_purple','vivid_orange','very_light_blue','vivid_red','grayish_yellow','medium_gray','vivid_green','strong_purplish_pink','strong_blue','strong_yellowish_pink','strong_violet','vivid_orange_yellow','strong_purplish_red','vivid_greenish_yellow','strong_reddish_brown','vivid_yellowish_green','deep_yellowish_brown','vivid_reddish_orange','dark_olive_green']
kelly_colors = dict(vivid_yellow=(255, 179, 0),
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




class MainWindow(QtGui.QMainWindow):
    # colorSelected = QtCore.pyqtSignal(str)
    # closeColor = QtCore.pyqtSignal()

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)

        self.tree_file = QtGui.QTreeView()
        self.setCentralWidget(self.tree_file)
        self.show()

        self.colorModel = ColorModel()
        self.colorDict = kelly_colors
        self.colorModel.addColors(self.colorDict,colors)


        self.dxffileName = filename

        self.headers = ('Name','Show', 'Voltage', 'Rate', 'Angle', 'Step', 'Time', 'Length', 'Closed', 'Color', 'Type')

        self.dxf = ezdxf.readfile(def_dxf_file)
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

        for col in [self.headers.index(col) for col in ['Closed', 'Show']]:
            root = self.tree_file.rootIndex()
            for i in range(0,self.model.rowCount(root)):
                index = self.model.index(i, col)
                self.tree_file.openPersistentEditor(index)
                item = self.model.getItem(index)
                for ch in range(0,item.childCount()):
                    index2 = self.model.index(ch, col,  self.model.index(i))
                    self.tree_file.openPersistentEditor(index2)

        for column in range(self.model.columnCount()):
            self.tree_file.resizeColumnToContents(column)

        screen = QtGui.QDesktopWidget().screenGeometry()
        print('(set to minimum expanding?)')
        self.setGeometry(int(screen.width()/3), int(screen.height()/3), screen.width()/2, screen.height()/2)


        # for col in [self.headers.index(col) for col in ['Color']]:

        self.tree_file.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.tree_file, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.doMenu)
        print('make last column just as wide as needed')
        self.offset_angle = 0
        self.offset_center = [0,0]
        self.sketchFile = ''
        self.sketchList = []
        self.sketchPrepare(self.model.rootItem)
        self.sketchFinish()


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


    def sketchAdd(self, data):
        if isinstance(data, list):
            for i in data:
                pass
        elif isinstance(data, str):
            self.sketchList.append(data+'\n')
        elif isinstance(data, sItem):
            self.prepareItem(data)
            self.sketchList.append(data)

    def sketchFinish(self):
        sketchFile = '# sketching start\n'
        for data in self.sketchList:
            # print(type(data))
            if isinstance(data, str):
                sketchFile += data

            elif isinstance(data, sItem):
                sketchFile += data.sketchData
            else:
                raise TypeError

        x0,y0 = self.offset_center
        sketchFile += 'xyAbs\t%.4f\t%.4f\t%.3f\n' %(-x0,-y0,self.freerate)
        sketchFile += '# sketching end\n'
        print( sketchFile )

    def getItem(self,item):
        return self.model.getItem(model.index(item))

    def sketchPrepare(self, root):
        # Function receives the root Item of the data-tree
        self.offset_center = [0,0]
        self.offset_rotation = 0
        self.freerate = 4

        layers = root.childItems

        # layers = [self.getItem for i in layers]
        for layer in layers:
            # if layer.checkState == 0:
            #     continue
            self.sketchAdd(sItem(layer))

            for child in layer.childItems:
                # if child.checkState == 0:
                #     continue
                # print(child.childItems)
                item = sItem(child)
                # item.is_closed
                # item.fillAngle
                # item.fillStep
                # item.pathOrder
                # item.name
                item.volt+=2
                # item.rate
                # item.offset
                self.sketchAdd(item)




    def s_comment(self, child, *args):
        string = ''
        string += '# '
        for arg in args:
            string += str(arg)+ '\t'
        string = string[:-1]
        string += '\n'
        child.sketchData += string


    def s_instruction(self, child, *args):
        string = ''
        for arg in args:
            string += str(arg)+ '\t'
        string = string[:-1]
        string += '\n'
        child.sketchData += string

    def prepareItem(self, child):
        child.sketchData = ''
        # if child.checkState == 0:
        #     return
        self.s_comment(child, 'start', child.name)
        self.s_comment(child, 'entity', *child.data() )

        data = child.pltData
        if data != []:
            for i in data:
                dta = np.add(i[::child.pathOrder],child.offset)

                path = self.transformData( dta ,direction=1)
                # print(path)
                x,y = path[0]
                self.s_instruction(child, 'vtip', 0.0)
                self.s_instruction(child, 'xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                self.s_instruction(child, 'vtip\t%f' %float(child.volt))
                r = child.rate
                for x,y in path:
                # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                    self.s_instruction(child, 'xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                self.s_instruction(child, 'vtip\t%f' %float(child.volt))
                self.s_instruction(child, 'vtip', 0.0)
                self.s_comment(child, 'end', child.name)

        # creates an empty line
        self.s_instruction(child)





    def transformData(self, data, angle = None, offset = None, direction = 1):
        # print('in transformData')
        c = data
        if angle == None:
            angle = self.offset_angle
        if offset == None:
            offset = self.offset_center
        offset = -np.array(offset)

        theta = direction*(angle/180.) * np.pi
        rotMatrix = np.array([[np.cos(theta), -np.sin(theta)],
                              [np.sin(theta),  np.cos(theta)]])
        if direction == 1:
            c = np.add(c, direction*offset)
            c = np.dot(c, rotMatrix)
        else:
            c = np.dot(c, rotMatrix)
            c = np.add(c, direction*offset)
        return c


class sItem(object):
    def __init__(self, item):
        self.item = item
        self.model = item.model
        self.color = item.color
        self.show = item.show
        self.parentItem = item.parentItem
        self.itemData = item.itemData
        self.childItems = item.childItems
        self.entity = item.entity
        self.pltHandle = item.pltHandle
        self.pltData = item.pltData
        self.checkState = item.checkState
        self.length = item.length
        self.sketchTime = item.sketchTime
        self.type = item.type
        self.meta = item.meta

        self.is_closed = item.is_closed
        self.fillAngle = item.fillAngle
        self.fillStep = item.fillStep
        self.pathOrder = item.pathOrder
        self.name = item.name
        self.parentName = item.parent().name
        self.volt = item.volt
        self.rate = item.rate
        self.offset = [0,0]
        self.sketchData = ''

    def data(self):
        datalist = [self.type,
                    self.name,
                    self.parentName,
                    self.volt,
                    self.rate,
                    self.fillAngle,
                    self.fillStep,
                    self.offset,
                    self.color,
                    self.show,
                    self.checkState,
                    self.length,
                    self.sketchTime,
                    self.is_closed,
                    self.pathOrder]

        return datalist





if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    # window.setContextMenuPolicy(QtCore.Qt.CustomContextMenu);
    # window.connect(window,SIGNAL("customContextMenuRequested(QPoint)"),
    #                 window,SLOT("contextMenuRequested(QPoint)"))

    # window.show()
    sys.exit(app.exec_())


nfile = False

        if self.multi_check.checkState() == 2:
            multiples = self.multi_n.value()
            sleep = self.multi_time.value()
            dx = self.multi_dx.value()
            dy = self.multi_dy.value()
        else:
            multiples = 1
            sleep = 0
            dx = 0
            dy = 0


        self.sComment(['sketching','start'])
        for cpy in range(multiples):

            offset = [cpy*dx,cpy*dy]
            self.sComment(['copy',cpy])

            for i in range(index.rowCount()):
                # print( '- ', i )
                item = index.getItem(index.index(i))
                if item.checkState == 0:
                    continue
                chitems = item.childItems
                # if item.data(6) == 'Layer':
                self.sAdd('')
                # print('*********')
                # print(item.data())
                # logger = item.data()
                # logger[0] = 'Layer '+str(logger[0])
                # print(logger)
                self.sComment(item.data(), 'layer ')

                if len(chitems) != 0:
                    nfile = True
                    for child in item.childItems:
                        if child.checkState == 0:
                            continue
                        self.sAdd('')
                        # child.data()
                        # print('xx',child.data('Volt'),child.data(1),child.data(2),child.data(3))
                        # print('yy',child.volt)
                        # l = [['start'], child.data()]
                        # startline = [item for sublist in l for item in sublist]
                        # self.sComment(startline)
                        self.sComment(['start', child.data('Name')])
                        self.sComment(child.data(), 'entity ')
                        # self.sComment()
                        if child.checkState == 2:

                            data = child.pltData
                            if data != []:
                                for i in data:
                                    # print (np.array(i).shape)
                                    # dta = self.transformData(i[::item.pathOrder])
                                    dta = np.add(i[::child.pathOrder],offset)
                                    # pdi = self.pi.plot(dta, pen = showPen)

                            # for chpath in child.pltData[::child.pathOrder]:
                                # dta = chpath[::child.pathOrder]

                                    path = self.transformData( dta ,direction=1)
                                    # print(path)
                                    x,y = path[0]
                                    self.sAdd('vtip\t%f' %(0.0))
                                    self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,self.freerate))
                                    self.sAdd('vtip\t%f' %float(child.data('Volt')))
                                    r = child.data('Rate')
                                    for x,y in path:
                                    # Maybe go from [1:] but going to the startpoint twice should reduce vtip lag
                                        self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(x,y,r))

                                    self.sAdd('vtip\t%f' %(0.0))
                                    self.sComment(['end',child.data('Name')])

            x0,y0 = self.offset_center
            self.sAdd('xyAbs\t%.4f\t%.4f\t%.3f' %(-x0,-y0,self.freerate))
            # self.sAdd('vtip\t%f' %(0.0))
            # time.sleep(sleep)
            self.sAdd('pause\t%.1f' %(sleep))
        self.sComment(['sketching','end'])


        if nfile: