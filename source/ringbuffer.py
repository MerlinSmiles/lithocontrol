import numpy as np
import pandas as pd
import os

class RingBuffer(object):
    def __init__(self, size_max, default_value=0.0, dtype=float, filename='', cols=['d_time', 'current', 'r2pt', 'r4pt']):
        """initialization"""
        self.size_max = size_max
        self.default_value = default_value
        self.dtype = dtype
        self.filename = filename
        self.cols = cols
        self._num_cols = len(self.cols)

        if self.filename != '':
            # os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError:
                pass
            self.data_store = pd.HDFStore(self.filename)
        #     for i in self.data_store.keys():
        #         self.data_store.remove(i)

        self._data = np.empty((self._num_cols,self.size_max), dtype=dtype)
        self._data.fill(default_value)
        self.size = 0
        self.data_store_index = 0
        self.saving = False

    def append(self, value):
        """append an element"""

        if self.saving:
            return False

        value = np.reshape(value,(self._num_cols,-1))
        lenvalue = np.shape(value)[1]
        self._data = np.roll(self._data, -lenvalue)
        self._data[:,-lenvalue:] = value

        self.data_store_index += lenvalue
        self.size += lenvalue
        if self.data_store_index >= self.size_max:
            self.save_data()
        if self.size >= self.size_max:
            self.size = self.size_max
            self.__class__  = RingBufferFull

    def get_all(self):
        """return a list of elements from the oldest to the newest"""
        return(self._data)

    def get_partial(self):
        if self.size == 0:
            return np.ndarray(0)
        return(self.get_all()[:,-self.size:])

    def get_partial_clear(self):
        if self.size == 0:
            return np.ndarray(0)
        tsize = self.size
        dat = self.get_all()[:,-tsize:]
        self.size = 0
        return dat

    def save_data(self):
        if self.filename != '':
            self.saving = True
            print 'save ' + self.filename
            df = pd.DataFrame(self.get_partial()[:,-self.data_store_index:].T, columns = self.cols)
            self.data_store_index = 0
            if not self.data_store.is_open:
                self.data_store.open()
            self.data_store.append('measurement',df,append=True, ignore_index=True)
            self.saving = False

    def close(self):
        if self.filename != '':
            self.data_store.close()

    def clear(self):
        self.close()
        self.__class__  = RingBuffer
        self.__init__(size_max = self.size_max, default_value = self.default_value, dtype = self.dtype, filename = self.filename, cols = self.cols)

    def __getitem__(self, key):
        """get element"""
        return(self._data[-key])

    def __repr__(self):
        """return string representation"""
        s = ''
        s = s + 'Size:\t\t' + str(self.size)
        s = s + '\nColumns:\t' + str(self.cols)
        s = s + '\nFile:\t\t' + str(self.filename)
        s = s + '\n' + self.get_partial().__repr__()
        return(s)

class RingBufferFull(RingBuffer):
    def append(self, value):
        """append an element when buffer is full"""
        value = np.reshape(value,(self._num_cols,-1))
        lenvalue = np.shape(value)[1]
        self._data = np.roll(self._data, -lenvalue)
        self.data_store_index += lenvalue
        self._data[:,-lenvalue:] = value
        if self.data_store_index >= self.size_max:
            self.save_data()

