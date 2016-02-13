import numpy as np
class RingBuffer():
    def __init__(self, length, cols = 1):
        self.length = length
        self.columns = cols
        self.data = np.zeros((self.length, self.columns), dtype='f')
#         print(self.data.shape)
        self.index = 0
        self.size = 0
        self.full = False

    def append(self, x):
        "adds array x to ring buffer"
        x_index = (self.index + np.arange(x.shape[0])) % self.data.shape[0]
        self.data[x_index] = x
        self.index = x_index[-1] + 1

        if not self.full:
            self.size += x.shape[0]
            if self.size >= self.length:
                self.size = self.length
                self.__class__  = RingBufferFull2

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.data.shape[0])) %self.data.shape[0]
        return self.data[idx]

    def get_partial(self):
        "Returns the first-in-first-out data in the ring buffer"
        if self.size == 0:
            return np.ndarray(0)
        idx = (self.index + np.arange(self.data.shape[0])) %self.data.shape[0]
        return self.data[idx][-self.size:,:]

    def get_partial_clear(self):
        if self.size == 0:
            return np.ndarray(0)
        tsize = self.size
        dat = self.get()[-tsize:,:]
        self.size = 0
        return dat

class RingBufferFull2(RingBuffer):
    def append(self, value):
        """append an element when buffer is full"""
        x_index = (self.index + np.arange(x.shape[0])) % self.data.shape[0]
        self.data[x_index] = x
        self.index = x_index[-1] + 1
#         if self.data_store_index >= self.size_max:
#             self.save_data()
