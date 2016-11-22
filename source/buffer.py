import numpy as np
import pandas as pd


class Buffer():
    def __init__(self, length, cols=['data'], filename=''):
        self.filename = filename
        self.length = length
        self.cols = cols
        self._num_cols = len(self.cols)
        self._data = np.empty((self.length, self._num_cols), dtype='f')
        self.size = 0
        self.full = False
        self.data_store_index = 0

    def append(self, x):
        "adds array x to ring buffer"
        # print(x.shape)
        self._data[self.size] = x
        self.size += 1

        if self.size >= self.length:
            self.save_data()
            print('buffer full')
            step = max(int(self.length / 10), min(self.length, 10))
            print(step)
            np.roll(self._data, step)
            self.size -= step
            self.data_store_index -= step
            # self.size += x.shape[0]
            # if self.size >= self.length:
            #     self.size = self.length
            # self.__class__  = RingBufferFull2

    def clear(self):
        self.__init__(self.length, self.cols, self.filename)

    def get(self):
        return self._data[:self.size]

    def save_data(self):
        size = self.size
        if (self.filename != '') and (self.data_store_index < size):
            # self.saving = True
            # print( 'saving store: ' + self.filename )
            # print( self.data_store_index, self.cols )
            # try:
            # .reshape((-1,self._num_cols))
            data = self.get()[self.data_store_index:]
            df = pd.DataFrame(data, columns=self.cols)

            # print(df.head())
            # print(df.tail())
            # print(self.size, self.data_store_index)

            self.data_store = pd.HDFStore(self.filename)
            self.data_store.append('data', df, append=True, ignore_index=True)
            self.data_store.close()
            # self.data_store_index = 0
            self.data_store_index = self.size
            # self.saving = False
