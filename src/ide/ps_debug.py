""" Debug related utilities.

    Lu, Ken (tech.ken.lu@gmail.com)
"""

import os, sys
import logging, logging.handlers

from functools import update_wrapper

def PSFuncTrace(func):
    def _hookFunc(*args, **kwds):
        logging.getLogger().debug("calling %s with args %s, %s" % (func.__name__, args, kwds))
        return func(*args, **kwds)
    return update_wrapper(_hookFunc, func)
    
class PSLog(object):
    """
    PSLog provide a wrapper based on python's logging. PSIDEApp will hold an instance.
    """
    
    _instance = None
    _format   = '%(asctime)-20s %(name)-8s %(levelname)-8s %(message)s'
    
    def __init__(self, path, level=logging.DEBUG):
        """
        Constructor function.
        @param    path    application absolute path
        @param    level   log level
        """
        self._logFilePath = None
        self._logLevel    = level
        self._logArea     = [""]
        self._logHandlers = []
        
            
        # set up default console message for running from source
        if not hasattr(sys, "frozen"):
            logging.basicConfig(level=level, format=self._format)
        
        # add default file log handler
        if path != None:
            self._logFilePath = path + os.sep + "log.txt"
            self.AddHandler(logging.handlers.RotatingFileHandler (self._logFilePath, "w", 1024 * 1024))
           
    def __del__(self):
        """
        Destructor function, flush all log handler and shutdown logging system.
        """
        for handler in self._logHandlers:
            handler.flush()
            handler.close()
        logging.shutdown()
        
    def GetLogger(self, area=""):
        """
        Get a logger object based on area name. If the area name is new, the new area instance will be
        created and current level and existing handler will be applied to this area instance.
        """
        logobj = logging.getLogger(area)
        
        if area not in self._logArea:
            self._logArea.append(area)
            logobj.setLevel(self._logLevel)
            for handler in self._logHandlers:
                logobj.addHandler(handler)
            
        return logobj
    
    def GetLogFilePath(self):
        """
        Get default log file path.
        """
        return self._logFilePath
            
    def GetLoggerAreas(self):
        return self._logArea
            
    def SetLevel(self, level, area=None):
        """
        Set error level for all existing area.
        """
        if area == None:
            for logarea in self._logArea:
                self.GetLogger(logarea).setLevel(level)
        else:
            self.GetLogger(area).setLevel(level)
            
    def RemoveHandler(self, handler):
        if handler not in self._logHandlers:
            return
        self._logHandlers.remove(handler)
        handler.flush()
        handler.close()
        
    def SetLoggerArea(self, area):
        if area not in self.GetLoggerAreas():
            return
        for a in self.GetLoggerAreas():
            if area != "" and a != area:
                self.GetLogger(a).setLevel(logging.CRITICAL)
            else:
                self.GetLogger(a).setLevel(logging.DEBUG)
                
    def AddHandler(self, handler):
        """
        Add a handler to logging system, and all existing log area instance will also be applied to this handler.
        """
        assert handler != None, "Parameter handler should not be None object!"
        assert issubclass(handler.__class__, logging.Handler), "Fail to set the log hanlder which should be child class of logging.Handler"
        
        # set handler level and formatter and append to internal handler list
        handler.setLevel(self._logLevel)
        handler.setFormatter(logging.Formatter(self._format))
        self._logHandlers.append(handler)
        
        # register handler to all area instance
        logging.getLogger().addHandler(handler)
        # Need not to add handler for each area
        #for area in self._logArea:
        #    print area
        #    logging.getLogger(area).addHandler(handler)
   