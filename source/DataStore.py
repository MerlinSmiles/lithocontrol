import numpy as np
import pandas as pd

class DataStore(object):
    def __init__(self, filename):
        """initialization"""
        self.filename = filename
        self.cols = []
        self.data = pd.DataFrame()
        self.data_store_index = 0

    def append(self, value, column):
        """append an element"""
        ds = pd.Series(value, column)
        self.data = self.data.append(ds[pd.notnull(ds)],ignore_index=True)

    def keys(self):
        return self.data.keys()

    def save_data(self):
        print 'saving store: ' + self.filename
        self.data_store = pd.HDFStore(self.filename)

        df = pd.DataFrame(self.data[self.data_store_index:])

        self.data_store_index += df.shape[0]

        try:
            print df['current']
        except:
            pass
        self.data_store.append('data',df,append=True, ignore_index=True)
        self.data_store.close()

    def __repr__(self):
        """return string representation"""
        self.data_store.open()
        s = ''
        s = s + '\nStores:\t\t' + str(self.data_store.keys())
        s = s + '\nColumns:\t' + str(self.data.keys())
        s = s + '\nFile:\t\t' + str(self.filename)
        self.data_store.close()
        return(s)
