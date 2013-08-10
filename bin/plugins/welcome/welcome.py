import wx
import os
import wx.html
from interfaces.core import IService
from interfaces.docview import *

_=wx.GetTranslation
 
edit from linux
  
class WelcomeView(IDocView):
    def __init__(self, pluginpath, doc=None):
        IDocView.__init__(self, doc)
        self._ctrl = None
        self._pluginpath = pluginpath
        EVT_VIEW_CREATING(self, self.OnCreate)
        
    def OnCreate(self, event):
        """Event handler for EVT_VIEW_CREATING."""
        frame = self.GetFrame()
        frame.Freeze()
        size = wx.BoxSizer(wx.VERTICAL)
        self._ctrl = wx.html.HtmlWindow(frame)
        size.Add(self._ctrl, 1, wx.EXPAND|wx.ALL, 0)
        frame.SetSizer(size)
        frame.Layout()
        frame.Thaw()
        
        try:
            self._ctrl.LoadFile(os.path.join(self._pluginpath, "Welcome.html"))
        except Exception, e:
            logger.error("Fail to load welcome.html")
        
    def GetBitmap(self):
        return wx.Bitmap(os.path.join(self._pluginpath, "welcome.ico"))
                         
    def GetName(self):
        return _("Welcome")
    
    def GetDescription(self):
        return self.GetName()
    
def __extension_main__(pluginInfo):
    logger = wx.GetApp().GetLogger("Plugin")
    filepath = os.path.join(pluginInfo.GetPath(), "Welcome.html")
    if not os.path.exists(filepath):
        logger.error("Fail to find the welcome HTML page file %s" % filepath)
        return
    
    welcomeview = WelcomeView(pluginInfo.GetPath())
    welcomeview.Create()
