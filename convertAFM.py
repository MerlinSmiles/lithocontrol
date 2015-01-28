import sys
sys.path.append("C:/Program Files (x86)/Gwyddion/bin")
import gwy, gwyutils, os, re
import numpy as np

import cv2

# Set options in settings...

def convertAFM(filename, saveImg = True):
    filename = os.path.abspath(filename)
    c = gwy.gwy_file_load(filename, gwy.RUN_NONINTERACTIVE)
    gwy.gwy_app_data_browser_add(c)
    for key in c.keys_by_name():
        if re.match(r'^/0/data$', key):
            field = c[key]
            xres = field.get_xres()
            yres = field.get_yres()
            xreal = field.get_xreal()*1e6
            yreal = field.get_yreal()*1e6

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

            imfilename = False
            if saveImg:
                imfilename = str(filename)+".png"
                saveAFMimg(data, imfilename )
    info = {'xreal':xreal, 'yreal':yreal, 'imname': imfilename}
    gwy.gwy_app_data_browser_remove(c)
    return data, info

def saveAFMimg(data, filename):
        mn = np.min(data)
        data = data-mn
        data = data*(255.0/np.max(data))
        px = np.max(np.shape(data))
        im = np.array(data, dtype = np.uint8)
        res = cv2.resize(im,(px,px), interpolation = cv2.INTER_CUBIC)
        cv2.imwrite(filename, res)


if __name__ == '__main__':
    afmFile = './stomilling.002'
    afmData, afmimage = convertAFM(afmFile)


    sys.exit()
