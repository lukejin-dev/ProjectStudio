import os, ConfigParser
import wx
import wx.lib.agw.genericmessagedialog as gmd

from interfaces.core import IConfig

class PSConfigFile:
    """
    Wrapper for ConfigParser class. The setting file is store at user's application folder.
    """
    def __init__(self, filename, logger):
        self._logger = logger
        self._path   = os.path.join (wx.StandardPaths.Get().GetUserDataDir(), filename)
        self._parser = None
        
        if self._CheckFile():
            self._parser = ConfigParser.ConfigParser()
            self._parser.read(self._path)
                    
    def Get(self, section, option, default=''):
        """ 
        Get setting, if setting does not exist return default
        given default value and set setting to config database.
        """
        if self._parser == None: return default
            
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        
        if not self._parser.has_option(section, option):
            return self.Set(section, option, default)
        
        if isinstance(default, bool):
            return self._parser.getboolean(section, option)
        elif isinstance(default, int):
            return self._parser.getint(section, option)
        return self._parser.get(section, option)
            
    def Set(self, section, option, value):
        """ 
        Set setting value. 
        """
        if self._parser == None: return value
        
        if not self._parser.has_section(section):
            self._parser.add_section(section)

        self._parser.set(section, option, str(value))
        self._SynFile()
        return value
        
    def _SynFile(self):
        if self._parser != None:
            self._parser.write(open(self._path, 'w'))
        
    def _CheckFile(self):
        """
        Check whether config file is existing in working. If not exist, create it.
        
        @param  file    config file name, it is relatived to user's application directory.
        
        @retval True    config file exist
        @retval False   config file does not exist, new file is created.
        """
        if os.path.exists(self._path):
            return True

        if not os.path.exists(os.path.dirname(self._path)):
            try:
                os.makedirs(os.path.dirname(self._path))
            except:
                pass
            
        try:
            fd = open(self._path, 'w')
            fd.close()
        except IOError:
            err = 'Fail to create config file %s, some settings maybe lost!' % self._path
            self._logger.error(err)
            dlg = gmd.GenericMessageDialog (None, err, caption="Error", style=wx.ICON_ERROR|wx.OK)
            dlg.ShowModal()
            return False
            
        self._logger.info('Config file %s does not exist, new file is created at %s!' % (file, dir))
        return True
    
class PSConfig(IConfig):
    _configdict = {}
    
    def __new__(cls, fileobj, section):
        if section in cls._configdict.keys():
            return cls._configdict[section]
        
        instance = super(PSConfig, cls).__new__(cls)
        if section not in cls._configdict.keys():
            cls._configdict[section] = instance
        return instance
    
    def __init__(self, fileobj, section):
        assert isinstance(fileobj, PSConfigFile), "Config file object is invalid!"
        self._file      = fileobj
        self._section   = section
        
    def Get(self, option, default=''):
        return self._file.Get(self._section, option, default)
    
    def Set(self, option, value):
        return self._file.Set(self._section, option, value)
    
            