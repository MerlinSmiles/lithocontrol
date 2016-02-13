import numpy as np
class Buffer():
    def __init__(self, length, cols = 1):
        self.length = length
        self.columns = cols
        self._data = np.empty((self.length, self.columns), dtype='f')
        self.index = 0
        self.full = False

    def append(self, x):
        "adds array x to ring buffer"
        # print(x.shape)
        self._data[self.index] = x
        self.index += 1

        if self.index >= self.length:
            print('buffer full')
            # self.size += x.shape[0]
            # if self.size >= self.length:
            #     self.size = self.length
                # self.__class__  = RingBufferFull2

    def get(self):
        return self._data[:self.index]
