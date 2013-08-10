import time

PS_IGNORE_DIRS = [".svn", "_svn", "cvs"] 
PS_OS_TYPE     = ["win32", "linux32"]

def getTimeStamp():
    return time.asctime(time.localtime(time.time()))


   