import pickle
import multiprocessing
from multiprocessing import Process, Pipe, Event
import time
import numpy as np
import sys
from source.generator import reader, writer
print('\n\n')

from PyQt4.QtCore import QTime, QTimer, QDate

if __name__=='__main__':
    timer = QTime.currentTime()
    terminate_measurement = Event()
    pipe_read, pipe_write = Pipe()
    tasks = multiprocessing.Queue()
    mgr = multiprocessing.Manager()
    settings = mgr.dict()
    settings['time'] = timer
    settings['kkk'] = 1
    settings['measure'] = False

    reader_p = reader(pipe_read,terminate_measurement,tasks,settings)
    reader_p.daemon = True

    writer_p = writer(pipe_write,terminate_measurement,tasks,settings)
    writer_p.daemon = True

    # del writer_p.context
    # del reader_p.process


    writer_p.start()            # Launch the writer process
    reader_p.start()            # Launch the reader process
    settings['measure'] = True  # Finally starts the measurement

    time.sleep(1)
    tasks.put({'key':5})
    settings['kkk'] = 2
    time.sleep(1)
    # Stop processes
    terminate_measurement.set()
    # Finish and close processes
    writer_p.join()
    reader_p.join()
    pipe_read.close()
    pipe_write.close()

    print ('Finished')
