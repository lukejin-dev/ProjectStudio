"""@file
	This module provide base plugin class, template/service/general plugin
	class inherited from base plugin class, plugin manager class and exception
	class.
	There are three types plugin supported by PIS:
		- Template plugin: plugin provide document template for PIS, generally, 
		                   this template is inherited from wx.lib.docview.DocTemplate
		- Service plugin: plugin provide document service for PIS, this service
						  is inherited from core.service.PISService
		- General plugin: plugin provide customized functionality.
"""
import wx.lib.docview as docview
import wx.lib.pydocview as pydocview
import core.debug
import core.service
import wx.lib.newevent
from version import *
from config import *
from util.constant import *
from wx.lib.mixins.listctrl import CheckListCtrlMixin

class Plugin(object):
    """Base plugin class, decsribe basic interface for a PIS plugin.
    """
    PLUGIN_INSTALL_SUCCESS = 0
    PLUGIN_INSTALL_FAILURE = 1
    PLUGIN_INSTALL_ALREADY = 2
    
    def __init__(self, name, author=None, version=None, minversion=None, 
                 description=None, dir=None, dependencies=None):
        self._is_activated = False
        self._is_installed = False
        self._name         = name
        self._author       = author
        self._version      = version
        self._minversion   = minversion
        self._description  = description
        self._dependencies = dependencies
        
        self._dir          = dir
        self._config       = None
        
        
    def GetMinVersion(self):
        """Override in subclasses to return the minimum version of PIS that
        the plugin is compatible with. By default it will return the current
        version of Editra.
        @return: version str

        """
        return VERSION
    
    def IsInstallAtStartup(self):
        return True
    
    def CreateProfile(self):
        self._config = core.config.PluginConfig(self._name)
        self._config.Set('author', self._author)
        self._config.Set('version', self._version)
        
    def GetConfig(self):
        return self._config
    
    def GetName(self):
        return self._name
    
    def GetAuthor(self):
        return self._author
    
    def GetVersion(self):
        return self._version

    def GetPluginManager(self):
    	return PluginManager()
    	
    def GetDependencis(self):
    	return self._dependencies
    	
    def IsInstalled(self):
    	"""Whether plugin is installed"""
    	return self._is_installed
    	
    def Install (self):
    	# Check whether this plugin is installed
    	if self.IsInstalled(): return self.PLUGIN_INSTALL_ALREADY
    	
    	# Check whether it can be installed?
    	is_install = self.GetConfig().GetBoolean('InstallAtStartup', self.IsInstallAtStartup())
    	if not is_install:
    		self._is_installed = False
    		return self.PLUGIN_INSTALL_FAILURE
    		
    	# install dependent plugins
        deps = self.GetDependencis()
        for dep in deps:
        	parent = self.GetPluginManager().GetPluginByName(dep)
        	if parent == None:
        		wx.MessageBox("Plugin %s install Error: can not find dependency plugin %s" %
        		              (self.GetName(), dep))
        		return self.PLUGIN_INSTALL_FAILURE
        		
        	try:
        		ret = parent.Install()
	         	if ret == self.PLUGIN_INSTALL_FAILURE:
	         		wx.MessageBox("Plugin %s install Error: Fail to install dependent plugin %s" %
	                              (self.GetName(), dep))
	         		return ret
	        except core.plugin.PluginException, e:
	            GetPluginLogger().error(e.GetMessage())
	            wx.MessageDialog(None, e.GetMessage(), 
	                             "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
	            wx.MessageBox("Plugin %s install Error: Fail to install dependent plugin %s" %
	                          (self.GetName(), dep))
	            return self.PLUGIN_INSTALL_FAILURE
	        except:
	            ETrace()
	            wx.MessageDialog(None, 'Fail to activate service plugin: %s' % instance.__class__.__name__, 
	                             "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
	            return self.PLUGIN_INSTALL_FAILURE
	            
        self._is_installed = True
        return self.PLUGIN_INSTALL_SUCCESS
        
    def UnInstall (self):
        """UnInstall this plugin"""
        self._is_installed = False
        
    def GetLogger(self):
        return core.debug.GetPluginLogger()
    
    def GetDescription(self):
        return self._description
    
    def GetDir(self):
        return self._dir
    
class PluginException(Exception):
    def __init__(self, message):
        self._message = message
        
    def GetMessage(self):
        return '[Plugin Failure]: %s' %self._message
    
class ITemplatePlugin(Plugin):
    def __init__(self, name, author=None, version=None, minversion=None, description=None, dir=None, dependencies=None):
        Plugin.__init__(self, name, author, version, minversion, description, dir, dependencies)
        self._template = None
        
    def IGetDescription(self):
        """Interface for child class provide template decription
        """
        return 'Template Description'
    
    def IGetDocumentClass(self):
        """Interface for child class provide document class
        """
        return None
    
    def IGetViewClass(self):
        """Interface for child class provide view class
        """
        return None
    
    def IGetFilter(self):
        """Interface for child class provide template's filter string
        """
        return ''
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return ''
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return ''
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return docview.TEMPLATE_VISIBLE
        
    def IGetIcon(self):
        """Interface for child class provide template's icon
        """
        return None
    
    def GetDocumentManager(self):
        return wx.GetApp().GetDocumentManager()
    
    def Install(self):
    	ret = Plugin.Install(self)
    	if ret != Plugin.PLUGIN_INSTALL_SUCCESS:
    		return ret
        
        if self.IGetDocumentClass() == None:
            raise PluginException('%s does not implement IGetDocumentClass' % self.__class__.__name__)
        if self.IGetViewClass() == None:
            raise PluginException('%s does not implement IGetViewClass' % self.__class__.__name__)
        
        self._template = docview.DocTemplate(self.GetDocumentManager(),
                                             self.IGetDescription(),
                                             self.IGetFilter(),
                                             self.IGetDir(),
                                             self.IGetExt(),
                                             self.IGetDocumentClass().__name__,
                                             self.IGetViewClass().__name__,
                                             self.IGetDocumentClass(),
                                             self.IGetViewClass(),
                                             self.IGetFlag(),
                                             self.IGetIcon())
        self.GetDocumentManager().AssociateTemplate(self._template)
        self.GetLogger().info('Install template %s' % self.__class__.__name__)
        return Plugin.PLUGIN_INSTALL_SUCCESS
        
    def UnInstall(self):
        Plugin.UnInstall(self)
        if self._template != None:
            self.GetDocumentManager().DisassociateTemplate(self._template)
            self._template = None
            
class IServicePlugin(Plugin):
    def __init__(self, name, author=None, version=None, minversion=None, 
                 description=None, dir=None, dependencies=None):
        Plugin.__init__(self, name, author, version, minversion, description, dir, dependencies)
        self._service = None
        
    def IGetClass(self):
        """Interface for child class provide service class
        """
        return None
        
    def IGetName(self):
        """Interface for child class provide service's name
        """
        return 'ServicePlugin'

    def Install(self):
    	ret = Plugin.Install(self)
    	if ret != Plugin.PLUGIN_INSTALL_SUCCESS:
    		return ret
    	
        if self._service != None:
            raise PluginException('Plugin %s has been started!' % self.__class__.__name__)
        
        Plugin.Install(self)
        cls = self.IGetClass()
        if cls is None:
            raise PluginException ('%s does not implement IGetClass!' % self.__class__.__name__ )
        
        if not issubclass(cls, core.service.PISService):
            raise PluginException ('%s is not inherited from PISService!' % cls.__name__ )
        
        # create service instance 
        service = cls()
        self._service = service
        
        # push logger and config object into service's instance
        service.SetLogger(self.GetLogger())
        service.SetConfig(self.GetConfig())
        setattr(service, '_plugin', self)
        
        # install service to application's service database
        wx.GetApp().InstallService(service)
        
        frame = wx.GetApp().GetTopWindow()
        service.SetFrame(frame)
        service.Activate()
                
        frame.GetAuiManager().Update()
        self.GetLogger().info('Install service %s' % self.IGetClass().__name__)
        return Plugin.PLUGIN_INSTALL_SUCCESS
        
    def UnInstall(self):
        """
        Service can not be deactivated 
        """
        if self._service != None:
        	self._service.DeActivate()
        	
        Plugin.UnInstall(self)

    def GetServiceInstance(self):
        return self._service
    
class IGeneralPlugin(Plugin):
    def Install(self):
    	ret = Plugin.Install(self)
    	if ret != Plugin.PLUGIN_INSTALL_SUCCESS:
    		return ret
    	
    	self.GetLogger().info('Install plugin %s' % self.__class__.__name__)
    	return Plugin.PLUGIN_INSTALL_SUCCESS

PM_MENU_ID = wx.NewId()
class PluginManager(object):
    _instance = None
    _plugins  = []
    
    def __new__(cls, *args, **kwargs):
        """Maintain only a single instance of this object
        @return: instance of this class

        """
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance
    
    def GetLogger(self):
        return GetPluginLogger()
    
    def AddPlugin(self, info, dir, cls):
        """Add plugin to dict including plugin-data, plugin-class
        """
        # maybe many plugin share same plugin info, so use plugin name + plugin class name as 
        # plugin name
        name         = info.get('name', 'NoNamePlugin')
        author       = info.get('author', 'Lu, Ken') # :-)
        version      = info.get('version', '1.0')
        minversion   = info.get('minversion', '0.0.1')
        description  = info.get('description', 'No Description')
        dependencies = info.get('dependencies', [])
        instance     = cls(name, author, version, minversion, description, dir, dependencies)
        instance.CreateProfile()
        self._plugins.append(instance)
        
    def GetPluginByName(self, name):
    	for p in self._plugins:
    		if p.GetName() == name:
    			return p
    	return None
    	
    def GetPlugins(self, cls):
        ret = []
        for p in self._plugins:
            if issubclass(p.__class__, cls):
                ret.append(p)
        
        return ret
    
    def GetPlugin(self, name):
        for p in self._plugins:
            if p.GetName().lower() == name.lower():
                return p
        return None

    #def GetPlugin(self, name):
    #    for p in self._plugins:
    #        pName = p.GetName().split('.')
    def LoadPlugin(self): 
        """Load and install plugin from directory in config file."""
        
        """
        path = os.path.dirname(sys.argv[0])
        if path == None or len(path) == 0:
        	path = os.getcwd()
        else:
        	if os.path.exists(os.path.join(os.getcwd(), path)):
        		path = os.path.join(os.getcwd(), path)
        """
        path = GetPISDir()
        if not os.path.exists(path):
        	wx.MessageBox("Fail to locate plugin directory %s" % path)
        	return
        
        oldpath = os.getcwd()
        self.GetLogger().info('Load plugin from path %s' % path)
        os.chdir(path)
        dirs = AppConfig().Get('PluginDirs', 'plugins').split(';')
        for dir in dirs:
            if not os.path.exists(os.path.join(path, dir)):
                self.GetLogger().error('Invalid plugin path %s in config file' % path)
                continue
            modules = self.SearchModules(dir)
            
            for module in modules:
                if not module.__dict__.has_key('_plugin_module_info_'):
                    continue
                
                # search list of _plugin_module_info_ in module context
                pminfo = getattr(module, '_plugin_module_info_')
                if type(pminfo) != list:
                    self.GetLogger().error('_plugin_module_info_ in module %s should be list type!' % module.__name__)
                    continue
                
                if len(pminfo) == 0:
                    continue
                
                for info in pminfo:
                    clsName = info.get('class', '')
                    if len(clsName) == 0:
                        self.GetLogger().error('Plugin module %s does not provide plugin class in _plugin_module_info' % module.__name__)
                        continue
                    
                    if not module.__dict__.has_key(clsName):
                        self.GetLogger().error('Plugin class %s can not be found in plugin module %s' % (clsName, module.__name__))
                        continue
                    
                    cls = getattr(module, clsName)
                    if not issubclass(cls, core.plugin.Plugin):
                        self.GetLogger().error('Plugin class %s is not inherrited from core.plugin.Plugin class, can not be loaded!' % clsName)
                        continue
                    
                    self.AddPlugin(info, dir, cls)
        os.chdir(oldpath)
        
    def SearchModules(self, path):
        modules = []
        names   = []
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if dir.lower() in IGNORE_DIRS:
                    dirs.remove(dir) 
            for file in files:
                f, ext = os.path.splitext(file)
                if ext != '.py' and ext != '.pyc': continue
                
                # skip init file.
                if file.find('__init__') != -1: continue
                
                mPath = os.path.join(root, file).replace(os.sep, '.')

                # names list to avoid duplicate import module for .py/.pyc module.
                if mPath[:mPath.rfind('.')].lower() in names:
                    continue
                names.append(mPath[:mPath.rfind('.')].lower())
                
                # skip file postfix name
                mPath = mPath.split('.')[:-1]
                try:
                    mod   = __import__('.'.join(mPath))
                except ImportError, e:
                    self.GetLogger().exception('Fail to import module %s' % mPath)
                    continue
                except:
                    self.GetLogger().exception('Fail to import module %s' % mPath)
                    continue
                
                for comp in mPath[1:]:
                    try:
                        mod = getattr(mod, comp)
                    except:
                        self.GetLogger().error('Fail to get attribute %s' % comp)
                        break
                
                if mod not in modules:
                    modules.append(mod)
        return modules
    
    def Install(self, frame):
        menubar = frame.GetMenuBar()
        toolmenu = menubar.GetMenu(menubar.FindMenu('Tools'))
        item = wx.MenuItem(toolmenu, PM_MENU_ID, 'Plugin Manager', 'Manage all plugins')
        item.SetBitmap(wx.GetApp().GetArtProvider().GetBitmap(wx.ART_REPORT_VIEW))
        wx.EVT_MENU(frame, PM_MENU_ID, self.OnPluginManager)
        toolmenu.InsertItem(0, item)
        toolmenu.InsertSeparator(1)
        
    def OnPluginManager(self, event):
        dlg = PluginDialog(wx.GetApp().GetTopWindow())
        dlg.ShowModal()
        dlg.Destroy()
        
    def InstallGeneralPlugins(self):
        plugins = self.GetPlugins(core.plugin.IGeneralPlugin)
        for instance in plugins:
            try:
                instance.Install()   
            except core.plugin.PluginException, e:
                GetPluginLogger().error(e.GetMessage())
                wx.MessageDialog(None, e.GetMessage(), 
                                "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
            except:
                ETrace()
                wx.MessageDialog(None, 'Fail to activate service plugin: %s' % instance.__class__.__name__, 
                                "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
    	
                
class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent, columns, style):
        wx.ListCtrl.__init__(self, parent, -1, style=style)
        CheckListCtrlMixin.__init__(self)

        for i in range(len(columns)):
            if columns[i][2] == 'left':
                position = wx.LIST_FORMAT_LEFT
            elif columns[i][2] == 'right':
                position = wx.LIST_FORMAT_RIGHT
            else:
                position = wx.LIST_FORMAT_CENTER
                
            self.InsertColumn(i, columns[i][0], position)
            self.SetColumnWidth(i, columns[i][1])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)


    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)


class PluginDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'Plugin Manage', size=(600, 300))

        box = wx.BoxSizer(wx.VERTICAL)
        self._list = CheckListCtrl(self, columns=[
                ("Name", 120, 'left'),
                ("Description", 250, 'left'),
                ("Author", 80, 'right'),
                ("Version", 40, 'right'),
                ], style=wx.LC_REPORT | wx.SUNKEN_BORDER)
#        self._list.load(self.getdata)
        self._plugmgr = PluginManager()
        for index in range(len(self._plugmgr._plugins)):
            self._list.InsertStringItem(index, self._plugmgr._plugins[index].GetName())
            self._list.SetStringItem(index, 1, self._plugmgr._plugins[index].GetDescription())
            self._list.SetStringItem(index, 2, self._plugmgr._plugins[index].GetAuthor())
            self._list.SetStringItem(index, 3, self._plugmgr._plugins[index].GetVersion())

            if self._plugmgr._plugins[index].IsInstalled():
                self._list.CheckItem(index)
        box.Add(self._list, 1, wx.EXPAND|wx.ALL, 5)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOK = wx.Button(self, wx.ID_OK, "OK", size=(80, -1))
        self.btnOK.SetDefault()
        box2.Add(self.btnOK, 0, 0, 5)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, "Cancel", size=(80, -1))
        box2.Add(self.btnCancel, 0, 0, 5)
        box.Add(box2, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        wx.EVT_BUTTON(self.btnOK, wx.ID_OK, self.OnOK)
        
        self.SetSizer(box)
        self.SetAutoLayout(True)
        
       
    def OnOK(self, event):
        isModify = False
        for index in range(self._list.GetItemCount()):
            item = self._list.GetItem(index)
            name = item.GetText()
            for plugin in self._plugmgr._plugins:
                if plugin.GetName() == name:
                    if plugin.IsInstalled() != \
                       self._list.IsChecked(index):
                        isModify = True
                        plugin.GetConfig().Set('installatstartup', self._list.IsChecked(index))
        if isModify:
            dlg = wx.MessageDialog(None, 'Some plugin has been modified for startup, please restart Project Insight Service',
                                   'Information', wx.YES_NO|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                wx.GetApp().GetTopWindow().Close()
                sys.exit(1)
            else:
                event.Skip()
        
        self.EndModal(wx.ID_YES)
 
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