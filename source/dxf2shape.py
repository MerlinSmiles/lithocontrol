# import sys
# import os
# import time
import dxfgrabber
# from collections import Counter
import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
# from scipy.interpolate import interp1d
from source.helpers import *

def get_points(entity, threshold = 1e-9):
    if entity.dxftype == 'LINE':
        pts = np.array([entity.start[:-1], entity.end[:-1]])
        return pts
    pts = entity.points
    pts = np.array(pts)[:,:2]

    doubles = np.all((abs(pts - np.roll(pts,1,0))<threshold) == True,axis=1)

    pts = np.delete(pts,np.where(doubles),axis = 0)

    return pts

def Rotate2D(pts,angle=0):
    theta = (angle/180.) * np.pi
    rotMatrix = np.array([[np.cos(theta), -np.sin(theta)],
                          [np.sin(theta),  np.cos(theta)]])
    return np.dot(pts, rotMatrix)

def dxf2shape(i, threshold = 1e-9, fill_step = 0.1, fill_angle = 0, path_direction = 1):
    if path_direction not in [-1,1]:
        print( 'Path direction must be -1 or 1!' )
        return 0
    pts  = get_points(i)[::path_direction]
    if not i.is_closed:
        return np.array([pts])
    else:
        pts = np.append(pts,[pts[0]],axis = 0)
    if fill_step<=0 :
        self.error('Tools diameter must be greater than 0!', 'error')


    pts = Rotate2D(pts,-fill_angle)
    ll = []
    bounds = [min(pts[:,0]), min(pts[:,1]), max(pts[:,0]), max(pts[:,1])]
    line_x = bounds[0]-fill_step/2.0
    top = True
    while (line_x<=bounds[2]+fill_step) :
        if top :
            ll.append([[line_x,line_x], [bounds[1],bounds[3]]])
        else :
            ll.append([[line_x,line_x], [bounds[3],bounds[1]]])
        line_x += fill_step
        top = not top

    # plt.plot(pts[:,0],pts[:,1],'-')
    # for u in ll:
    #     pass
    #     plt.plot(u[0], u[1])
    lines = []
    ll = np.array(ll)
    # print( pts[:,1] )
    for i in ll:
        a1 = np.array([i[0][0], i[1][0]])
        a2 = np.array([i[0][1], i[1][1]])
        b1 = pts[0]
        ints = []
        for b2 in pts[1:]:
            inter = intersect( a1,a2, b1, b2 )

            # print( a1,a2, b1, b2 )
            if inter != 0:
                ints.append(inter)
                # print( inter,  a1,a2, b1, b2 )
            b1 = b2
        # print( ints )
        if ints != []:
            ints = np.array(ints)
            ints.view('float32,float32').sort(order=['f1'], axis=0)
            # it actually might happen, that there is an uneven number of points, so if there are two points very close
            if len(ints)%2 !=0:
                pt = 0
                for j, i in enumerate(ints):
                    if j>0:
                        if abs(ints[j-1,1] - i[1]) <= threshold:
                            pt = j
                if pt != 0:
                    ints = np.delete(ints,pt,0)
            for i in np.arange(0,len(ints),2):
                lines.append( np.array([ints[i],ints[i+1]]) )

    lines = lines
    collection = []
    npath = []
    while len(lines)>0:
        if len(npath) == 0:
            npath.append(lines[0])
            lines = np.delete(lines,0,0)
        a,b,l = get_nearest_point(lines,npath[-1][1])

        last_line = npath[-1]
        this_line = lines[b][::1-(2*a)]

        if abs(last_line[0][0] - this_line[0][0]) > (fill_step+1e-9):
            collection.append(np.array(npath))
            npath = []

        npath.append(this_line)
        lines = np.delete(lines,b,0)

    collection.append(np.array(npath))
    collection = np.array(collection)

    for i in range(len(collection)):
        collection[i] = Rotate2D(collection[i], fill_angle)

    return collection


def dxf2shapeX(i, threshold = 1e-9, fill_step = 0.1, fill_angle = 0, path_direction = 1):
    if path_direction not in [-1,1]:
        print( 'Path direction must be -1 or 1!' )
        return 0
    pts  = get_points(i)[::path_direction]
    if not i.is_closed:
        return np.array([pts])
    else:
        pts = np.append(pts,[pts[0]],axis = 0)
    if fill_step<=0 :
        self.error('Tools diameter must be greater than 0!', 'error')


    pts = Rotate2D(pts,-fill_angle)
    ll = []
    bounds = [min(pts[:,0]), min(pts[:,1]), max(pts[:,0]), max(pts[:,1])]
    line_x = bounds[0]-fill_step/2.0
    top = True
    while (line_x<=bounds[2]+fill_step) :
        if top :
            ll.append([[line_x,line_x], [bounds[1],bounds[3]]])
        else :
            ll.append([[line_x,line_x], [bounds[3],bounds[1]]])
        line_x += fill_step
        top = not top

    # plt.plot(pts[:,0],pts[:,1],'-')
    # for u in ll:
    #     pass
    #     plt.plot(u[0], u[1])
    lines = []
    ll = np.array(ll)
    # print( pts[:,1] )
    for i in ll:
        a1 = np.array([i[0][0], i[1][0]])
        a2 = np.array([i[0][1], i[1][1]])
        b1 = pts[0]
        ints = []
        for b2 in pts[1:]:
            inter = intersect( a1,a2, b1, b2 )

            # print( a1,a2, b1, b2 )
            if inter != 0:
                ints.append(inter)
                # print( inter,  a1,a2, b1, b2 )
            b1 = b2
        # print( ints )
        if ints != []:
            ints = np.array(ints)
            ints.view('float32,float32').sort(order=['f1'], axis=0)
            # it actually might happen, that there is an uneven number of points, so if there are two points very close
            if len(ints)%2 !=0:
                pt = 0
                for j, i in enumerate(ints):
                    if j>0:
                        if abs(ints[j-1,1] - i[1]) <= threshold:
                            pt = j
                if pt != 0:
                    ints = np.delete(ints,pt,0)
            for i in np.arange(0,len(ints),2):
                lines.append( np.array([ints[i],ints[i+1]]) )

    lines = lines
    collection = []
    npath = []
    while len(lines)>0:
        if len(npath) == 0:
            npath.append(lines[0])
            lines = np.delete(lines,0,0)
        a,b,l = get_nearest_point(lines,npath[-1][1])

        last_line = npath[-1]
        this_line = lines[b][::1-(2*a)]

        if abs(last_line[0][0] - this_line[0][0]) > (fill_step+1e-9):
            collection.append(np.array(npath))
            npath = []

        npath.append(this_line)
        lines = np.delete(lines,b,0)

    collection.append(np.array(npath))
    collection = np.array(collection)

    for i in range(len(collection)):
        collection[i] = Rotate2D(collection[i], fill_angle)

    return collection

    # sorted_collection = []
    # next_group = [0,1,1e9]
    # while len(collection)<0:
    #     next_group = [0,1,1e9]
    # #     print( len(collection) )
    #     if len(sorted_collection) == 0:
    #         sorted_collection.append(collection[0])
    #         collection = np.delete(collection,0,0)
    #     endpoint = sorted_collection[-1][-1][-1]
    #     for i in range(len(collection)):
    #         dist_firstline = distsq(endpoint, collection[i][0])
    #         dist_lastline = distsq(endpoint, collection[i][-1])
    #         distarr = np.array([dist_firstline, dist_lastline])
    #         closest = distarr.argmin()

    #         if closest < 2:
    #             direction = 1
    #         else:
    #             direction = -1

    #         dist = min(abs(distarr).flatten())
    #         closest = [i, direction, dist]

    #         if closest[2]<next_group[2]:
    #             next_group = closest
    #     sorted_collection.append(collection[next_group[0]][::next_group[1]])
    #     collection = np.delete(collection,next_group[0],0)

    # sorted_collection = np.array(sorted_collection)

    # sorted_collection = collection

    # for i, npath in enumerate(sorted_collection):
    #     pt = npath.flatten()
    #     CS = plt.plot(pt[::2],pt[1::2],'-')
    #     ax.annotate('section '+str(i), xy=(pt[0], pt[1]),  xycoords='data',
    #                 xytext=(-50, 10), textcoords='offset points',
    #                 arrowprops=dict(arrowstyle="->")
    #                 )

    # for j, i in enumerate(sorted_collection):
    #     path = np.array(i)
    #     plt.plot(path[:,0], path[:,1],'-')
