import sys
# sys.path.append("C:/Program Files (x86)/Gwyddion/bin")
import gwy, gwyutils, os, re
import numpy as np
import time

import cv2

# Set options in settings...

def convertAFM(filenamex, saveImg = True):
    filename = os.path.abspath(filenamex)
    print 'Loading ', filename
    time.sleep(0.2)
    try:
        c = gwy.gwy_file_load(filename, gwy.RUN_NONINTERACTIVE)
        gwy.gwy_app_data_browser_add(c)
    except:
        return False
    for key in c.keys_by_name():
        if re.match(r'^/0/data$', key):
            field = c[key]
            xres = field.get_xres()
            yres = field.get_yres()
            xreal = (field.get_xreal()*1e6)/2.0
            yreal = (field.get_yreal()*1e6)/2.0

            weights = gwy.DataLine(xres, 1.0, True)
            weights.part_fill(0, xres//3, 1.0)
            filtered = gwy.DataField.new_alike(field, False)
            field.fft_filter_1d(filtered, weights,
                                gwy.ORIENTATION_HORIZONTAL,
                                gwy.INTERPOLATION_ROUND)
            degrees = [1,1]
            field.subtract_polynom(degrees[0],degrees[1],field.fit_polynom(degrees[0],degrees[1]))
            field.data_changed()
            data = gwyutils.data_field_data_as_array(field)
            data = np.array(data)[::,::-1]

            imfilename = False
            if saveImg:
                filename = os.path.abspath('D:/lithography/')
                imfilename = str(filename)+"/current.png"
                print imfilename
                res = saveAFMimg(data, imfilename )
                writeImageMacro( imfilename , [-xreal, -yreal, xreal, yreal])
    info = {'width':xreal*2, 'height':yreal*2, 'imname': imfilename}
    gwy.gwy_app_data_browser_remove(c)
    return data, info

def saveAFMimg(data, filename):
        data = data[:, ::-1].T
        mn = np.min(data)
        data = data-mn
        data = data*(255.0/np.max(data))
        px = np.max(np.shape(data))
        img = np.array(data, dtype = np.uint8)

        # create a CLAHE object (Arguments are optional).
        clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(3,3))
        res = clahe.apply(img)

        cv2.imwrite(filename, res)
        return res[::-1,:].T




def writeImageMacro(filename, position):
    x1 = position[0]
    y1 = position[1]
    x2 = position[2]
    y2 = position[3]
    filestr = ''
    filestr += '>LoadBMP\n'
    filestr += ' {\n'
    filestr += '   <Layer %s\n' %('1') #layer
    filestr += '   <PointXYZ %f,%f,0\n' %(x1,y1)
    filestr += '   <PointXYZ %f,%f,0\n' %(x2,y2)
    filestr += '   <Filename \"%s\"\n' %(str(filename))
    filestr += ' }\n'

    fname = str(filename)[:-3]+'d3m'
    f = open(fname, 'w')
    f.write(filestr)
    f.close()

if __name__ == '__main__':
    afmFile = os.path.abspath('D:/lithography/afmImages/05131739.001')
    afmData, afmimage = convertAFM(afmFile)
    print afmData

    sys.exit()
