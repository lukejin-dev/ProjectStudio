import core.plugin
import wx
import plugins.ProjectPlugin.projectmain as projectmain

class ProjectExtensionPlugin(core.plugin.IGeneralPlugin):
    def IGetExtension(self):
        """ Need to be overide by extension"""
        return ProjectExtension
        
    def Install(self):
        ret = core.plugin.IGeneralPlugin.Install(self)
        if ret != core.plugin.Plugin.PLUGIN_INSTALL_FAILURE:
            pm = self.GetPluginManager()
            pp = pm.GetPluginByName('Project')
            ps = pp.GetServiceInstance()
            if ps == None:
                return core.plugin.Plugin.PLUGIN_INSTALL_FAILURE
            ps.RegisterProjectExtension(self.IGetExtension()())
        return ret
    
class ProjectExtension:
    def __init__(self):
        self._projectPath    = None
    
    def GetService(self):
        service = wx.GetApp().GetService(projectmain.ProjectService)
        return service
        
    def IGetProjectPath(self):
        return self._projectPath
        
    def IGetName(self):
        """This interface need be overide by extension plugin"""
        return 'Default Project Externsion'
        
    def IGetProjectName(self):
        return 'Default Project Name'
        
    def IProperties(self):
        wx.MessageBox("%s project extension does not provide IProperties interface!" % self.IGetName())
        return None
        
    def INewProject(self):
        wx.MessageBox("%s project extension does not provide INewProject interface!" % self.IGetName())
        """This interface need be overide by extension plugin"""
        return None
    
    def ICloseProject(self):
        wx.MessageBox("%s project extension does not provide ICloseProject interface!" % self.IGetName())
            
    def ILoadExtension(self, dom):
        """This interface need be overide by extension plugin"""
        return True
        
    def ISaveExtension(self, root, dom):
        return True
        
    def ICreateProjectNavigateView(self, docview, serviceview):
        """This interface need be overide by extension plugin"""
        serviceview.DestroyChildren()
        sizer = wx.BoxSizer(wx.VERTICAL)
        #treectl = wx.TreeCtrl(view, -1)
        treectl = wx.TreeCtrl(serviceview, -1)
        sizer.Add(treectl, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 2)
        serviceview.SetSizer(sizer)
        serviceview.Layout()
        serviceview.SetAutoLayout(True)
        serviceview.Activate()
        
        
           