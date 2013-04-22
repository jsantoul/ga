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


def of_import(module = None, classname = None, country = None):
    """
    Returns country specific class found in country module
    
    Parameters
    ----------
    module : str, default None
             name of the module where the object is to be imported
    classname : str, default None
                name of the object or class to import      
    country : str, default None, required to be not None
              name of the country (france, tunisa for the moment)  
    
    """
    
    if module is None:
        module_str = ""
    else:
        module_str = "." + module
    
    if classname is None or country is None:
        raise Exception("classname or country needed")
    
    _temp = __import__('src.countries.' + country + module_str, globals = globals(), locals = locals(), fromlist = [classname], level=-1)

    
    return getattr(_temp, classname, None)



if __name__ == '__main__':
    pass
