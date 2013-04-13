'''
Created on Nov 10, 2012

@author: Mahdi Ben Jelloul
'''

import time

class Timer(object):
    
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()
        
    def __exit__(self, type, value, traceback):
        if self.name:
            print '[%s]' % self.name,
        print 'Elapsed: %s' % (time.time() - self.tstart)

def side_by_side(*objs, **kwds):
    # http://stackoverflow.com/questions/13030245/how-to-shift-a-pandas-multiindex-series
    from pandas.core.common import adjoin
    space = kwds.get('space', 4)
    reprs = [repr(obj).split('\n') for obj in objs]
    print adjoin(space, *reprs)



if __name__ == '__main__':
    pass