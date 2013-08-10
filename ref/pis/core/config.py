"""@file
This module hold global configuration and provide interface to
deal with user's setting.

"""

__author__ = "Lu Ken <bluewish.ken.lu@gmail.com>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

import os, ConfigParser

import version

from core.debug import *

_DEFAULT_SECTION_NAME = 'Global'

class Config:
    """
    The configuration file consists of sections, led by a "[section]" header and followed 
    by "name: value" entries, with continuations in the style of RFC 822; "name=value" is 
    also accepted. Note that leading whitespace is removed from values. The optional values 
    can contain format strings which refer to other values in the same section, or values in 
    a special DEFAULT section. Additional defaults can be provided on initialization and retrieval. 
    Lines beginning with "#" or ";" are ignored and may be used to provide comments. 
    """
    _gParser = None
    _gFile   = None
    
    def __init__(self):
        self._logger     = GetGlobalLogger()
        if self._GetParser() == None:
            self._InitParser()
        
    def _GetParser(self):
        return self.__class__._gParser
    
    def _GetFile(self):
        return Config._gFile
    
    def _InitParser(self):
        self.__class__._gParser = ConfigParser.ConfigParser()
        
    def IGetSection(self):
        """Get section name of config instance, need override by child class
        default section's name is 'Global'
        """
        return _DEFAULT_SECTION_NAME
    
    def Load(self, file):
        """Load config file from current working path.
        
        @param file  file name
        """
        if not self._CheckFile(file): return
        
        # hold file name for future set
        self._GetParser().read(self._GetFile())
        
    def Get(self, option, default=None):
        """Get setting, if setting does not exist return default
        given default value and set setting to config database.
        
        @param option     setting
        @param default    default value for this setting. 
        """
        if default == None:
            default = ''
            
        if not self._GetParser().has_section(self.IGetSection()):
            self._GetParser().add_section(self.IGetSection())
        
        if not self._GetParser().has_option(self.IGetSection(), option):
            self._GetParser().set(self.IGetSection(), option, default)
            self._SynFile()
            return default
        
        return self._GetParser().get(self.IGetSection(), option)
            
    def Set(self, option, value):
        if not self._GetParser().has_section(self.IGetSection()):
            self._GetParser().add_section(self.IGetSection())
            
        self._GetParser().set(self.IGetSection(), option, value)
        self._SynFile()
        
    def GetInt(self, option, default=None):
        """Get setting, if setting does not exist return default
        given default value and set setting to config database.
        
        @param option     setting
        @param default    default value for this setting. 
        """
        if default == None:
            default = 0
            
        if not self._GetParser().has_section(self.IGetSection()):
            self._GetParser().add_section(self.IGetSection())
        
        if not self._GetParser().has_option(self.IGetSection(), option):
            self._GetParser().set(self.IGetSection(), option, default)
            self._SynFile()
            return default
        
        try:
            ret = self._GetParser().getint(self.IGetSection(), option)
        except:
            ret = default
        return ret       
    
    def GetBoolean(self, option, default=None):
        """Get setting, if setting does not exist return default
        given default value and set setting to config database.
        
        @param option     setting
        @param default    default value for this setting. 
        """
        if default == None:
            default = False
            
        if not self._GetParser().has_section(self.IGetSection()):
            self._GetParser().add_section(self.IGetSection())
        
        if not self._GetParser().has_option(self.IGetSection(), option):
            self._GetParser().set(self.IGetSection(), option, default)
            self._SynFile()
            return default
        try:
            ret = self._GetParser().getboolean(self.IGetSection(), option)
        except:
            ret = default
        
        return ret
            
    def _SynFile(self):
        if self._GetFile() != None:
            self._GetParser().write(open(self._GetFile(), 'w'))
        
    def _CheckFile(self, file):
        """Check whether config file is existing in working. If not exist, create it.
        
        @param  file    config file name, it is relatived to user's application directory.
        
        @retval True    config file exist
        @retval False   config file does not exist, new file is created.
        """
        # Get config dir from user's application path, please make sure wx.App.SetAppName() is
        # set before invoke the following code.
        dir = GetPISDir()

        self._logger.info('Working path is %s' % dir)
        Config._gFile = os.path.join(dir, file)
        if os.path.exists(Config._gFile):
            return True

        try:
            fd = open(Config._gFile, 'w')
            fd.close()
        except IOError:
            self._logger.error('Fail to create config file %s, some settings maybe lost!' % self._file)
            Config._gFile = None
            return False
            
        self._logger.info('Config file %s does not exist, new file is created at %s!' %
                         (file, dir))
        return True
        
class AppConfig(Config):
    def IGetSection(self):
        return version.PROJECT_NAME
    
class EditorConfig(Config):
    def IGetSection(self):
        return 'Editor'
       
class StyleConfig(Config):
    def IGetSection(self):
        return 'Style'
                    
class PluginConfig(Config):    
    def __init__(self, typeName):
        Config.__init__(self)
        self._typeName = typeName

    def IGetSection(self):
        return "%s.%s" % ('plugin', self._typeName)    

def GetPISDir():
    if os.path.isabs(sys.argv[0]):
        return os.path.dirname(sys.argv[0])
        
    curdir = os.getcwd()
    fname  = sys.argv[0]
    if wx.Platform == '__WXMSW__':
        if fname.lower().find('.py') == -1 and fname.lower().find('.pyw') == -1 and \
           fname.lower().find('.exe') == -1:
            fname = fname + '.exe'
    if os.path.exists(os.path.join(curdir, fname)):
        return os.path.dirname(os.path.join(curdir, fname))
    else:
        envpaths = os.environ.get('path', '')
        if len(envpaths) == 0:
            sys.exit(0)
        arr = envpaths.split(';')
        for item in arr:
            temp = os.path.join(item, fname)
            if os.path.exists(temp):
                return os.path.dirname(temp)
    sys.exit(0)
        