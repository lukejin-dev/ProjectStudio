""" This module provide logging system.

    Copyright (C) 2008 ~ 2012. All Rights Reserved.
    The contents of this file are subject to the Mozilla Public License
    Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS"
    basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
    License for the specific language governing rights and limitations
    under the License.

    Initial Developer: Lu Ken <bluewish.ken.lu@gmail.com>
"""   

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__revision__ = "$Revision: 1 $"

#======================================  External Libraries ========================================
import logging

#============================================== Code ===============================================
DEFAULT_LOG_AREA = ['', 'plugin', 'task', 'service']
_LogHandlers     = []

def InitAmberEditorLogger(levelstr='DEBUG', file=None, ipaddr=None):
    """ Initialize logging system for Amber Edtior
    
    Amber Editor support file/network logger, and will create handle for them.
    
    @param level             log level string in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    @param file              user specified log file
    @param ipaddr            remote log service ip address
    """
    LOG_LEVEL = {'NOTSET':logging.NOTSET, 'DEBUG':logging.DEBUG, 'INFO':logging.INFO, 
                 'WARNING':logging.WARNING, 'ERROR':logging.ERROR, 'CRITICAL':logging.CRITICAL}
    if levelstr.upper() in LOG_LEVEL.keys():
        level = LOG_LEVEL[levelstr.upper()]
    else:
        level = logging.NOTSET
        
    if file != None:
        logging.basicConfig(level=level, 
                            format='%(name)-8s %(levelname)-8s %(message)s',
                            filename=file,
                            filemode='w')
    else:
        logging.basicConfig(level=level, 
                            format='%(name)-8s %(levelname)-8s %(message)s')
        
    
    if ipaddr != None:
        socketHandler = logging.handlers.SocketHandler(ipaddr,
                                                       logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        _LogHandlers.append(socketHandler)
    
        # Bind socket handle to all message level.
        for area in DEFAULT_LOG_AREA:
            logger = logging.getLogger(area)
            logger.addHandler(socketHandler)    
            
def GetLogger(name):
    """
    Get logger according to an area name.
    
    @param name    area name
    
    @return logger object.
    """
    logger = logging.getLogger(name)
    if name not in DEFAULT_LOG_AREA:
        for handler in _LogHandlers:
            logger.addHandler(handler)
    return logger

