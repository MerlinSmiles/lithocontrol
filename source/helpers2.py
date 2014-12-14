# import sys
# import os
# import time
import dxfgrabber
# from collections import Counter
# import matplotlib.pyplot as plt
# %matplotlib inline
import numpy as np
# from scipy.interpolate import interp1d

def print_layers(counter):
    print("used Layers: {}".format(len(counter)))
    for item in sorted(counter.items()):
        print("Layer: {} has {} entities".format(*item))
def get_nearest_point(data,pt):
    nearesta = []
    for j, i in enumerate(data):
        d = distsq(i[0],pt)
        if d>1e-9:
            nearesta.append(np.array([j, d]))
    nearesta = np.array(nearesta)
    nearestb = []
    for j, i in enumerate(data):
        d = distsq(i[1],pt)
        if d>1e-9:
            nearestb.append(np.array([j, d]))
    nearestb = np.array(nearestb)

    if min(nearesta[:,1]) < (min(nearestb[:,1])):
        p = nearesta[:,1].argmin()
        j = nearesta[p,0]
        return 0, int(j), np.sqrt(nearesta[p,1])
    else:
        p = nearestb[:,1].argmin()
        j = nearestb[p,0]
        return 1, int(j), np.sqrt(nearestb[p,1])


def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return np.where(array==array[idx])

def distsq( a, b ):
    return  (b[0] - a[0])**2 + (b[1] - a[1])**2

def intersect( a1, a2, b1, b2):
    def perp(u,v):
        return u[0] * v[1] - u[1] * v[0]
    aa1 = np.array(a1)
    aa2 = np.array(a2)
    bb1 = np.array(b1)
    bb2 = np.array(b2)
    u = aa1 - aa2
    v = bb1 - bb2
    w = aa1 - bb1
    D = perp(u,v)

    sI = perp(v,w) / D
    pp  = aa1 + sI * u

    def samedist(pa, pb, pc):
        td = distsq(pa, pb)
        tp1 = distsq(pa, pc)
        tp2 = distsq(pb, pc)

        if tp1+tp2-td >= 1e-9:
            return 0
        return 1

    if samedist(aa1,aa2,pp) and samedist(bb1,bb2,pp):
        print pe
        return pp[0],pp[1]
    return 0
