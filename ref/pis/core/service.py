import wx
import wx.lib.pydocview as pydocview

class PISService(pydocview.DocService):
    def __init__(self):
        pydocview.DocService.__init__(self)
        self._config = None
        self._logger = None
        self._view   = None
        self._frame  = None
        self._title  = ''
        self._is_activate = False
        self._frame  = wx.GetApp().GetTopWindow()
        
    def SetFrame(self, frame):
        self._frame = frame
        
    def GetFrame(self):
        return self._frame
    
    def SetLogger(self, logger):
        self._logger = logger
        
    def GetLogger(self):
        if self._logger == None:
            import core.debug
            self._logger = core.debug.GetPluginLogger()
        return self._logger
    
    def SetConfig(self, config):
        self._config = config
        
    def GetPosition(self):
        return 'left'
    
    def GetName(self):
        return self.__class__.__name__
    
    def GetDescription(self):
        return self.GetName()
        
    def GetView(self):
        return self._view
    
    def SetView(self, view):
        self._view = view
        
    def GetViewClass(self):
        return None
    
    def GetPlugin(self):
        if hasattr(self, '_plugin'):
            return self._plugin
        return None
    
    def GetTitle(self):
        return self._title
        
    def SetTitle(self, text):
        self._title = text
        view = self.GetView()
        if view == None: return
        
        if not view.IsVisible(): return
        self._frame.SetPaneTitle(self.GetPosition(), text)
        
    def CreateView(self):
        if self._view == None:
            cls = self.GetViewClass()
            if cls != None:
                #parent = wx.GetApp().GetTopWindow().GetSideParent(self.GetPosition())
                self._view = cls(self._frame, self)
                if self._view != None:
                    setattr(self._view, '_logger', self._logger)
                    setattr(self._view, '_config', self._config)
                    wx.EVT_CLOSE(self._view, self.OnViewClose)
                    self._frame.AddSideWindow(self._view, 
                                              self.GetName(),
                                              self.GetPosition(),
                                              self.GetIcon())
                return self._view
            else:
                return None
        return self._view
    
    def DestroyView(self):
        if self._view == None:
            return
        
        frame = wx.GetApp().GetTopWindow()
        frame.CloseSideWindow(self._view)
        self._view = None
                        
    def OnViewClose(self, event):
        self._view = None
        # skip event to give chance for inherit view class
        event.Skip()
    
    def GetConfig(self):
        return self._config
    
    def GetCustomizeToolBars(self):
        return None
    
    def GetIcon(self):
        return wx.EmptyIcon
        
    def ProcessEvent(self, event):
        if pydocview.DocService.ProcessEvent(self, event):
            return True
        
        if self._view:
            if hasattr(self._view, 'ProcessEvent'):
                if self._view.ProcessEvent(event):
                    return True
        return False
    
    def ProcessUpdateUIEvent(self, event):
        if pydocview.DocService.ProcessUpdateUIEvent(self, event):
            return True
        
        if self._view:
            if hasattr(self._view, 'ProcessUpdateUIEvent'):
                if self._view.ProcessUpdateUIEvent(event):
                    return True
        return False
    
    def OnCloseFrame(self, event):
        self.DeActivate()
        #if self._view:
        #    self._view.Close()
        return pydocview.DocService.OnCloseFrame(self, event)
    
    def Activate(self, show=True):
        """Activate service"""
        if self.IsActivated():
            self.GetLogger().warn("Service has been activated")
            return
        frame = self._frame
        if hasattr(self, 'InstallControls'):
            self.InstallControls(frame, menuBar = frame.GetMenuBar(), toolBar = None, statusBar = None)

        bars = self.GetCustomizeToolBars()
        if bars != None:
            for bar in bars:
                frame.AddToolBar(self.GetName(), 
                                 self.GetDescription(), 
                                 bar)
                                 
        self.CreateView()
        self._is_activate = True
        
    def DeActivate(self):
        if not self._is_activate:
            self.GetLogger().info('Service %s is de-activated more than once!' % self.GetName())
            return 
        self.GetLogger().info('Service %s is de-activated!' % self.GetName())
        """Deactivate service"""
        if self._view != None:
            frame = wx.GetApp().GetTopWindow()
            frame.CloseSideWindow(self._view)
            self._view = None
        self._is_activate = False
        
    def IsActivated(self):
        return self._is_activate
        
class PISServiceView(wx.Panel):
    def __init__(self, parent, service, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Panel'):    
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self._service = service
        
    def GetService(self):
        return self._service
    
    def SetTitle(self, text):
        self.GetService().SetTitle(text)
        
    def IsVisible(self):
        nb = self.GetParent()
        return nb.GetPage(nb.GetSelection()) == self
        
    def Activate(self):
        frame = wx.GetApp().GetTopWindow()
        frame.ActivatePageInSideWindow(self)
        