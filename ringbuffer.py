import numpy as np
import pandas as pd

class RingBuffer(object):
    def __init__(self, size_max, default_value=0.0, dtype=float, filename='store.h5', cols=['d_time', 'current', 'r2pt', 'r4pt']):
        """initialization"""
        self.data_store = pd.HDFStore(filename)
        self.cols = cols
        self.data_store_index = 0

        self._dimensions = np.size(size_max)
        if self._dimensions == 1:
            self.size_max = (1,size_max)
        else:
            self.size_max = size_max
        self._data = np.empty(self.size_max, dtype=dtype)
        self._data.fill(default_value)
        self.size = 0

    def append(self, value):
        """append an element"""
        value = np.reshape(value,(self.size_max[0],-1))
        lenvalue = np.shape(value)[self._dimensions-1]
        self._data = np.roll(self._data, -lenvalue)
        self._data[:,-lenvalue:] = value

        self.size += lenvalue
        if self.size >= self.size_max:
            self.size = self.size_max
            self.__class__  = RingBufferFull

    def get_all(self):
        """return a list of elements from the oldest to the newest"""
        if self._dimensions == 1:
            return(self._data[0])
        return(self._data)

    def get_partial(self):
        if self.size == 0:
            return np.ndarray(0)
        if self._dimensions == 1:
            return(self.get_all()[0][:,-self.size:])
        return(self.get_all()[:,-self.size:])

    def get_partial_clear(self):
        if self.size == 0:
            return np.ndarray(0)
        tsize = self.size
        if self._dimensions == 1:
            dat = self.get_all()[0][:,-tsize:]
        else:
            dat = self.get_all()[:,-tsize:]
        self.size = 0
        return dat

    def save_data(self):
        df = pd.DataFrame(self.get_partial()[self.data_store_index:].T, columns = self.cols)
        self.data_store_index = self.size
        self.data_store.append('measurement',df,append=True)


    def __getitem__(self, key):
        """get element"""
        return(self._data[-key])

    def __repr__(self):
        """return string representation"""
        s = self._data.__repr__()
        s = s + '\t' + str(self.size)
        s = s + '\t' + self.get_all()[::-1].__repr__()
        s = s + '\t' + self.get_partial()[::-1].__repr__()
        return(s)

class RingBufferFull(RingBuffer):
    def append(self, value):
        """append an element when buffer is full"""
        value = np.reshape(value,(self.size_max[0],-1))
        lenvalue = np.shape(value)[self._dimensions-1]
        self._data = np.roll(self._data, -lenvalue)
        self._data[:,-lenvalue:] = value

