import numpy as np
class Buffer():
    def __init__(self, length, cols = 1):
        self.length = length
        self.columns = cols
        self._data = np.empty((self.length, self.columns), dtype='f')
        self.size = 0
        self.full = False

    def append(self, x):
        "adds array x to ring buffer"
        # print(x.shape)
        self._data[self.size] = x
        self.size += 1

        if self.size >= self.length:
            print('buffer full')
            # self.size += x.shape[0]
            # if self.size >= self.length:
            #     self.size = self.length
                # self.__class__  = RingBufferFull2

    def get(self):
        return self._data[:self.size]
