import numpy as np

class RingBuffer(object):
    def __init__(self, size_max, default_value=0.0, dtype=float):
        """initialization"""
        self._dimensions = np.size(size_max)
        if self._dimensions == 1:
            self.size_max = (1,size_max)
        else:
            self.size_max = size_max
        print self._dimensions , self.size_max
        self._data = np.empty(self.size_max, dtype=dtype)
        print np.shape(self._data)
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
            return(self.get_all()[0][-self.size:])
        return(self.get_all()[-self.size:])

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

class RingBufferFull(RingBuffer):
    def append(self, value):
        """append an element when buffer is full"""
        value = np.reshape(value,(self.size_max[0],-1))
        lenvalue = np.shape(value)[self._dimensions-1]
        self._data = np.roll(self._data, -lenvalue)
        self._data[:,-lenvalue:] = value

