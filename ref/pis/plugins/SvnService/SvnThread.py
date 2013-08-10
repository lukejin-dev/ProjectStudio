import threading
import pysvn
import time
class SVNThread(threading.Thread):
    def __init__(self, service):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self._running = True
        self._work_semaphore = threading.Semaphore(0)
        self._work_queue      = []
        self._work_queue_lock = threading.Lock()
        self._is_busy  = False
        self._service = service
        
    def IsBusy(self):
        return self._is_busy
        
    def run(self):
        while self._running:
            self._is_busy = False
            # wait for new svn command
            self._work_semaphore.acquire()
            
            # dequeue
            self._work_queue_lock.acquire()
            function = self._work_queue.pop(0)
            self._work_queue_lock.release()  
            
            self._is_busy = True
            # run the function
            function()

        self._is_busy = False  
        try:
            self._service.GetLogger().info('SVN threading is shutdown!')
        except:
            pass
        
    def AddWork(self, function, args):
        self._addWork(ThreadingFunction(self._service, function, args))
        
    def _addWork(self, function):
        # queue the function
        self._work_queue_lock.acquire()
        self._work_queue.append(function)
        self._work_queue_lock.release()

        # count one more piece of work
        self._work_semaphore.release()
                
    def Shutdown(self):
        self._addWork(self._shutdown)
        
    def _shutdown(self):
        self._running = False   
        
class ThreadingFunction:
    def __init__(self, service, function, args):
        self._func = function
        self._args = args
        self._service = service
        
    def __call__(self):
        #try:
        self._func(*self._args)
        #except:
        #    self._service.GetLogger().error('Fail to execute %r' % self._func)

                    