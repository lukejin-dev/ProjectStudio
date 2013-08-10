""" This module provide service manager.

    The service in Amber is a groups of functionalities and can be 
    invoked by other service or task.
    
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

#======================================  Internal Libraries ========================================

#============================================== Code ===============================================
class Service:
    """ Service concept in Amber Editor is a group of functionalities. so:
        1) To achieve a functionality, a task maybe created.
        2) A service maybe manage zero or more side views. 
        3) Should only one service instance.
        4) A service maybe install a tool bar and some menus
    """
    def __init__(self):
        self._isEnable = False
        
    @classmethod
    def Install(cls, isEnable=True):
        """ Install service invoked by amber core.
        
        When Amber create a service instance for a internal service or from a plugin.
        
        """
        self._isEnable = isEnable
        
