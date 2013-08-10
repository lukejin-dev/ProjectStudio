from interfaces import *

class IConfig(Interface):
    """Interface for application configure file master class.
    
    Application get/set configure setting from configuration files which
    is consisted by many sections, such as Global, Plugin, Mainframe sections.
    
    An config object master a section in configuration file. 
    """
    
    @interface
    def Get(self, option, default=''):
        """Get config value for given option.
        If the option does not exist, then default value is written into configure
        file, and default value is return.
        """
        pass
    
    @interface
    def Set(self, option, value):
        """Set config value for given option."""
        pass
    
class IApplication(Interface):
    """Interface for application class."""
    
    @interface
    def GetAppPath(self):
        """Get application absolute path."""
        pass
    
    @interface
    def GetConfig(self, area="Global"):
        """Get IConfig object in given area.""" 
        pass
    
    @interface
    def GetLogger(self, area=""):
        pass
    
    @interface
    def GetMainFrame(self):
        pass
    
    @interface
    def GetIfImpClass(self, ifclass):
        """Get interface implement class, if this interface is only implement by one time."""
    
    @interface
    def GetIfImpClasses(self, ifclass):
        """Get interface implement class list if this interface is implement by many times."""
            
class IMainFrame(Interface):
    
    @interface
    def AppendMenu(self, name, title, menu):
        pass
    
    @interface
    def GetManager(self):
        pass
    
class IBackgroundScene(Interface):
    @interface
    def GetName(self):    
        """Return the name of scene which is used as a key."""
        
    @interface
    def GetPerspectiveString(self):
        """Return perspective string contains layout and panes shown in this scene."""
        
class IForegroundScene(Interface):
    
    @interface
    def GetName(self):
        """Return foreground scene's name which is used as a key."""
                
class INewItem(Interface):
    
    @interface
    def GetName(self):
        """Get name displayed in new menu"""
    
    @interface
    def GetDescription(self):
        """Get description for new item which will be displayed at status bar."""
    
    @interface
    def GetBitmap(self):
        """Get icon displayed in new menu."""
    
    @interface
    def OnClick(self, event):
        """Action when click new menu"""
        
    @interface
    def IsActive(self, scene):
        """Whether this new item is active in new menu according to current scene."""
        
class ISingleView(Interface):
    DOCK_FLOAT  = 0
    DOCK_LEFT   = 1
    DOCK_RIGHT  = 2
    DOCK_TOP    = 3
    DOCK_BOTTOM = 4
    
    @interface
    def Create(self, parent):
        """Create the single view instance
        @return view object which is an window object.
        """        
        
    @interface
    def GetName(self):
        """Get name of single view"""
        
    def GetDockPosition(self):
        return self.DOCK_FLOAT
        """Whether this new item is active in new menu according to current scene."""
        
    def GetBackgroundSceneNames(self):
        """Return names list of background scene which this single view exist by default.
        if return None, this view will be added to all background scene.
        """
        return None
    
    def GetIconName(self):
        return ""
    
class IService(Interface):

    @interface
    def Start(self):
        """Start service."""
        
    def Stop(self):
        """Stop service."""
        
class IPlugin(Interface):
    
    @interface
    def GetPath(self):        
        """Return the plugin root directory."""
        
    @interface
    def GetMetaFilePath(self):
        """Return meta file paths."""
        
    @interface
    def GetName(self):
        """Return plugin's name."""
        
class ISearchScope(Interface):
    
    def GetScopeName(self):
        """Return scope's name"""
        
    def GetFileList(self):
        """Return list stored searched file"""