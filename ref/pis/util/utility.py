import threading
    
class RunFunctionOnMainApp:
    def __init__(self, app, function):
        self._app       = app
        self._func      = function
        self._condition = threading.Condition()
        self._result    = None
        
    def __call__(self, *args):
        #self._app.GetLogger().info('Call function in main APP thread: %r' % self._func)
        
        self._condition.acquire()
        
        self._app.ForegroundProcess(self._OnMainThread, args)
        
        self._condition.wait()
        self._condition.release()
        
        return self._result
        
    def _OnMainThread(self, *args):
        try:
            self._result = self._func(*args)
        finally:
            pass
            
        self._condition.acquire()
        self._condition.notify()
        self._condition.release()
        