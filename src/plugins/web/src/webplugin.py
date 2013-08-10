import os, sys, locale
import wx
import wx.html
import wx.webkit
import interfaces.core
from interfaces.docview import *
 
_=wx.GetTranslation

class WebDocument(IDocument):
    def __init__(self, provider, path):
        IDocument.__init__(self, provider, path)
        
    def GetViewClasses(self):
        return [WebView]

    def LoadObject(self):
        return True
    
    def SaveObject(self, path):
        return True   
            
class WebView(IDocView):
    def __init__(self, doc=None):
        IDocView.__init__(self, doc)
        EVT_VIEW_CREATING(self, self.OnCreate)
        
    def OnCreate(self, event):
        frame = self.GetFrame()
        frame.Freeze()
        size = wx.BoxSizer(wx.VERTICAL)
        self._webctrl = wx.html.HtmlWindow(frame, -1)
        size.Add(self._webctrl, 1, wx.EXPAND|wx.ALL, 0)
        frame.SetSizer(size)
        frame.Layout()
        frame.Thaw()        
        self._webctrl.LoadPage("http://www.intel.com")
        
def __extension_main__(pluginInfo):
    global logger
    logger = wx.GetApp().GetLogger("Web")
    
    global config
    config = wx.GetApp().GetConfig("Web")
    
    bitmap = wx.Bitmap(os.path.join(pluginInfo.GetPath(), "icons", "web.bmp"))
    docmgr = wx.GetApp().GetDocManager()
    docmgr.RegisterDocumentProvider("WebPage", _("WebPage"), ["html"], WebDocument, bitmap, False)
    
    