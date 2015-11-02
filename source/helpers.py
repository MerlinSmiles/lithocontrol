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

def samedist(pa, pb, pc):
    if np.isnan(np.sum([pa,pb,pc])) or np.isinf(np.sum([pa,pb,pc])):
        return 0
    td = distsq(pa, pb)
    tp1 = distsq(pa, pc)
    tp2 = distsq(pb, pc)
    if abs(tp1+tp2-td) >= 1e-9:
        return 0
    return 1


# def intersect( a1, a2, b1, b2):
#     def perp(u,v):
#         return u[0] * v[1] - u[1] * v[0]
#     aa1 = np.array(a1)
#     aa2 = np.array(a2)
#     bb1 = np.array(b1)
#     bb2 = np.array(b2)
#     u = aa1 - aa2
#     v = bb1 - bb2
#     w = aa1 - bb1
#     D = perp(u,v)
#     # print( D )
#     sI = perp(v,w) / D

#     pp  = aa1 + sI * u
#     # if not (np.isnan(np.sum([pp])) or np.isinf(abs(np.sum([pp])))):
#     if samedist(aa1,aa2,pp) and samedist(bb1,bb2,pp):
#         print( pp )
#         return pp[0],pp[1]
#     return 0



# def intersect( a1, a2, b1, b2):
#     def perp(u,v):
#         return u[0] * v[1] - u[1] * v[0]
#     aa1 = np.array(a1)
#     aa2 = np.array(a2)
#     bb1 = np.array(b1)
#     bb2 = np.array(b2)
#     u = aa1 - aa2
#     v = bb1 - bb2
#     w = aa1 - bb1
#     D = perp(u,v)

#     sI = perp(v,w) / D
#     pp  = aa1 + sI * u

#     def samedist(pa, pb, pc):
#         td = distsq(pa, pb)
#         tp1 = distsq(pa, pc)
#         tp2 = distsq(pb, pc)

#         if tp1+tp2-td >= 1e-9:
#             return 0
#         return 1

#     if samedist(aa1,aa2,pp) and samedist(bb1,bb2,pp):
#         print( pp )
#         return pp[0],pp[1]
#     return 0

def intersect(a,b,c,d):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    d = np.array(d)
    cc = c-a # w
    r = b-a  # u
    s = d-c  # v

    denom = cc[0] * r[1] - cc[1] * r[0]
    ccxs = cc[0] * s[1] - cc[1] * s[0] # si perp(vw)
    rxs  = r[0] * s[1] - r[1] * s[0]  # D

    if denom == 0.0:
        # Lines are collinear, and so intersect if they have any overlap
        return False
        return (((c[0]-a[0]) < 0) != ((c[0]-b[0]) < 0)) or (((c[1]-a[1]) < 0) != ((c[1]-b[1]) < 0))

    if rxs == 0.0:
        # Lines are parallel
        return False

    rxsr = 1.0/rxs
    t = ccxs * rxsr  #sI
    u = denom * rxsr

    if (t>=0.0) and (t<=1.0) and (u>=0.0) and (u<=1.0):
        pp = a + t*r
        return pp[0],pp[1]
    else:
        return False
    # si =
    # return pp[0],pp[1]
    # return (t>=0.0) and (t<=1.0) and (u>=0.0) and (u<=1.0)
