import sys
import logging

log = logging.getLogger('root')

class SubClass(object):

    def __init__(self):
         log.info('message from SubClass / __init__')

    def SomeMethod(self):
        log.info('message from SubClass / SomeMethod')