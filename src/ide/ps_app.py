""" IDE application classes.

    Lu, Ken (tech.ken.lu@gmail.com)
"""

import os, sys, logging, locale, time
import wx

import ps_error, ps_debug, ps_config, ps_art, ps_plugin, ps_docview
import interfaces
import interfaces.core  

_=wx.GetTranslation
class PSIDEApp(wx.App, interfaces.core.IApplication):
    """IDE Application class."""
    
    def __init__(self, appPath):
        self._time      = time.clock()
        self._appPath   = appPath
        self._logger    = None
        self._config    = None
        self._services  = [] 
        wx.App.__init__(self, False)
        
    def OnInit(self):
        """
        Initialize the application object, this function is invoked at wx.App.__init__.
        """
        self.SetAppName("ProjectStudio")
        self._logger     = ps_debug.PSLog(self.GetAppPath())
        self._configFile = ps_config.PSConfigFile(self.GetAppName() + ".cfg", self.GetLogger())
        self._config     = self.GetConfig()
        if self._config.Get("Debug", True):
            self._logger.SetLevel(logging.DEBUG)
            self.SetAssertMode(wx.PYAPP_ASSERT_DIALOG)
        else:
            self._logger.SetLevel(logging.ERROR)
            self.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
        
        wx.Locale.AddCatalogLookupPathPrefix('locale')    
        
        id = self._config.Get("LastLanguageId", wx.LANGUAGE_ENGLISH)
        if not wx.Locale.IsAvailable(id):
            ps_error.notifyError("Invalid Language","Language %s is not available on your system!\nLanguage will be set to English!" % wx.Locale.GetLanguageName(id))
            id = wx.LANGUAGE_ENGLISH
            self._config.Set("LastLanguageId", id)
            
        self._locale = wx.Locale(id)
        if self._locale.IsOk():
            self._locale.AddCatalog("psstr")

        self._PrintEnvironment()
        
        wx.ArtProvider.Push(ps_art.PSArtProvider(self.GetLogger("ArtProvider")))
        
        self._ShowMainframe()

        # Load all document templates
        self._docmgr = ps_docview.PSDocManager()

        self._pluginmgr = ps_plugin.PSPluginManager()
        self._pluginmgr.LoadPlugins(os.path.join(self.GetAppPath(), "plugins"))
        self.GetLogger().info('The whole startup duration is %f' % (time.clock() - self._time))
        
        # Start all register services
        servclasses = self.GetIfImpClasses(interfaces.core.IService)
        for serv in servclasses:
            instance = serv()
            self._services.append(instance)
            self.GetLogger().info("Starting service %s" % instance.GetName())
            instance.Start()
        #self._LaunchInspector()
        
        self._frame.EnterLastBackgroundScene()
        
        self.GetLogger().info('The whole startup duration is %f' % (time.clock() - self._time))

        # Show development reminder
        dlg = self._frame.CreateConfirmDialog("This version is development tip!\n", "Project Studio", wx.ICON_ASTERISK|wx.OK, "DevelopmentTip")
        if dlg != None:
            dlg.ShowModal()

        return True
    
    def AddLogHandler(self, handler):
        self._logger.AddHandler(handler)
        
    def GetAppPath(self):
        """
        Return the full path name that ProjectEditor.exe exist.
        """
        return self._appPath

    def GetConfig(self, area="Global"):
        """
        Get config instance for a specific area/section.
        """
        return self.GetIfImpClass(interfaces.core.IConfig)(self._configFile, area)

    def GetDocManager(self):
        return self._docmgr
    
    def GetLanguageId(self):
        return self._locale.GetLanguage()
    
    def SetLanguageId(self, id):
        self._config.Set("LastLanguageId", id)
        
    def GetLogger(self, area=""):
        """
        Get logger instance in given area
        """
        return self._logger.GetLogger(area)
    
    def GetLoggerAreas(self):
        return self._logger.GetLoggerAreas()
    
    def GetMainFrame(self):
        """
        Return main frame object, Do not use GetTopWindow to get main frame, because
        top window maybe is not main frame.
        """
        return self._frame
    
    def GetIfImpClass(self, ifclass):
        """Get interface implement class, if this interface is only implement by one time."""
        clslist = interfaces.getInterfaceImplementClasses(ifclass)
        assert len(clslist) == 1, "Interface %s should not be implemented by more than one time."
        return clslist[0]
        
    def GetIfImpClasses(self, ifclass):
        """Get interface implement class list if this interface is implement by many times."""
        return interfaces.getInterfaceImplementClasses(ifclass)
    
    def GetServices(self):
        return self._services
    
    def IsInterfaceImplement(self, ifclass, impclass):
        """Judge whether a class implement an interface"""
        clslist = self.GetIfImpClasses(ifclass)
        if impclass in clslist:
            return True
        return False
    
    def NotifyError(self, caption, message):
        ps_error.notifyError(caption, message)
        
    def RemoveLoggerHandler(self, handler):
        self._logger.RemoveHandler(handler)

    def SetLoggerArea(self, area):
        self._logger.SetLoggerArea(area)

    def __del__(self):
        """Destructor function."""
        del self._docmgr
        del self._frame
        del self._config
        del self._logger
        wx.App.__del__(self)
        
    def _LaunchInspector(self):
        if self._config.Get("Debug", True):
            from wx.lib.inspection import InspectionTool
            if not InspectionTool().initialized:
                InspectionTool().Init()
            InspectionTool().Show(self.GetMainFrame(), True)
        
    def _PrintEnvironment(self):
        logger = self.GetLogger()
        logger.info("===================================================================================")
        logger.info("Application Path     : %s" % self.GetAppPath())
        logger.info("OS type              : %s" % sys.platform)
        if sys.platform == 'win32':
            logger.info('Windows version      : %d.%d.%d.%s [%s]' % (sys.getwindowsversion()))
        logger.info("Default encoding     : %s" % sys.getdefaultencoding())
        logger.info("Default locale encoding: %s" % locale.getdefaultlocale()[1])
        logger.info("File System encoding : %s" % sys.getfilesystemencoding())
        logger.info("wx encoding          : %s" % wx.GetDefaultPyEncoding())
        logger.info("wx platform info     : %s" % " ".join(wx.PlatformInfo))
        logger.info("Locale encoding      : %s" % self._locale.GetSystemEncodingName())
        logger.info("System language      : %s" % self._locale.GetLanguageName(self._locale.GetSystemLanguage()))
        logger.info("IDE language         : %s" % self._locale.GetLanguageName(self.GetLanguageId()))
        logger.info("===================================================================================")
        
    def _ShowMainframe(self):
        self._frame = self.GetIfImpClass(interfaces.core.IMainFrame)()
        self._frame.Show() 
               
def startIDE(path):
    sys.excepthook = ps_error.hookUnhandleException
    appobj = PSIDEApp(path)
    appobj.MainLoop()

    # Garbage collection
    for key in interfaces.Interface._instances:
        del interfaces.Interface._instances[key][:]
    del appobj
