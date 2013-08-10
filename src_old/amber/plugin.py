""" This module provide plug-in manager and maintain all plug-ins.

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
class PluginManager:
    def __init__(self):
        """ Constructor function for PluginManager """
        pass

    def GetPath(self):
        """ Return plugin root path. """
        appPath = wx.GetApp().GetPath()
        return os.path.join(appPath, 'plugins')
        
    def GetLogger(self):
        return wx.GetApp().GetLogger('plugins')
        
    def LoadPlugins(self):
        """ Search plugin meta file under plugin folder and establish plug-in database. """ 
        pass

    def GetPlugin(self, uuid):
        """ Get a loaded plugin instance from database """

class Plugin:
    """ A plugin manage one or more plugin interfaces.
    A plugin inteface is identified by a string name, which should *not* be duplicated in 
    one plugin interface.
    
    """
    def __init__(self, uuid, name='Default Plug-in name', author='Lu, Ken',
                 releaseDate=None, interfaceClasses=None, description=None, version=None):
        if interfaceClasses != None:
            self._interfaceClassesDict = interfaceClasses
        else:
            self._interfaceClassesDict = {}
        self._name          = name
        self._author        = author
        self._description   = description
        self._version       = version
        self._releaseDate   = releaseDate
        
    def GetInterfaceClasses(self):
        """ Retrieve all interfaces class """
        
    def GetAuthor(self):
        return self._author
        
    def GetReleaseData(self):
        return self._releaseDate
        
class PluginInteface:
    """ A plugin interface could be:
    
        1) service
        2) document template
        3) task
    """
    def GetInterfaceName(self):
        return self.__class__.__name__
        
    
class IServicePluginInteface(PluginInteface):
    pass
    
import wx.lib.docview.DocTemplate as DocTemplate
class ITemplatePluginInterface(PluginInteface, DocTemplate):
    pass
    
class ITaskPluginInterface(PluginInteface):
    pass
    