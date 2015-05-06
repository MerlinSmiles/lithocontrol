import numpy as np

class IncBuffer(object):
    def __init__(self, no_rows, no_columns, dtype=float):
        """initialization"""
        self._no_columns = no_coulumns
        self._no_rows = no_rows
        self._index = 0

        self._data = np.empty((self._no_rows, self._no_columns), dtype=dtype)
        self._data.fill(np.NAN)
        print self._data
        self.size = 0

    def append(self, value):
        """append an element"""
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

    # def set_size_max(self, size_max):

    #     self.size_max = size_max
    #     if self.size > self.size_max:
    #         self._data = self._data[-self.size_max:]

    # def __len__(self):
    #     return(self.size)

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
