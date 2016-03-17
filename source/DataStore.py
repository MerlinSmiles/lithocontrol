import numpy as np
import pandas as pd

class DataStore(object):
    def __init__(self, filename, columns):
        """initialization"""
        self.filename = filename
        self.columns = columns
        self.data = pd.DataFrame(columns = self.columns)#, dtype=object
        self.data_store_index = 0

    def append(self, value, column):
        """append an element"""
        # print( value, column )
        ds = pd.Series(value, column)#, dtype=object
        # print( ds )
        self.data = self.data.append(ds,ignore_index=True)

    def keys(self):
        return self.data.keys()

    def save_data(self):
        self.data_store = pd.HDFStore(self.filename)

        df = pd.DataFrame(self.data[self.data_store_index:])#, dtype=object

        self.data_store_index += df.shape[0]
        # print(df)
        try:
            self.data_store.append('data',df,append=True, ignore_index=True)
            print('fine')
        except:
            print(dict(df.dtypes))
            print(dict(self.data_store['data'].dtypes))
            print(df)
            print(self.data_store['data'])
            self.data_store.append('data',df,append=True, ignore_index=True)

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
