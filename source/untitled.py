def LinesIntersect(a,b,c,d):
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
        print pp = a + t*r
    # si =

    return (t>=0.0) and (t<=1.0) and (u>=0.0) and (u<=1.0)
