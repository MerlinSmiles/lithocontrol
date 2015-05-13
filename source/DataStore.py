import numpy as np
import pandas as pd
import os

class DataStore(object):
    def __init__(self, filename=''):
        """initialization"""
        self.filename = filename
        self.cols = []
        if self.filename != '':
            # os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError:
                pass
            self.data_store = pd.HDFStore(self.filename)
        self.data = pd.DataFrame()
        self.data_store_index = 0


    def append(self, value, column):
        """append an element"""
        df = pd.Series(value, column)
        self.data = self.data.append(df,ignore_index=True)

    def get_all(self):
        """return a list of elements from the oldest to the newest"""
        return(self.data)

    def save_data(self):
        if self.filename != '':
            self.saving = True
            print 'save ' + self.filename
            if not self.data_store.is_open:
                self.data_store.open()
            if len(self.data[self.data_store_index:]) >0:
                self.data_store.append('logging',self.data[self.data_store_index:],append=True)
            self.data_store_index = len(self.data)
            self.saving = False

    def close(self):
        if self.filename != '':
            self.data_store.close()

    def clear(self):
        self.close()
        self.__init__(filename = self.filename)

    def __repr__(self):
        """return string representation"""
        s = ''
        s = s + '\nColumns:\t' + str(self.data_store.keys)
        s = s + '\nFile:\t\t' + str(self.filename)
        return(s)
