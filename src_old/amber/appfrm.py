
import wx
import auiex

import wx._aui
class AuiExToolBar(wx.aui.AuiToolBar):
    
class AEFrame(wx.Frame):
    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)
        
        self._auiexmgr = auiex.AuiExManager(self)
        import wx._aui
        toolbar = wx.aui.AuiToolBar(self, -1)
        toolbar.Realize()
        self._auiexmgr.AddPane (toolbar, wx.aui.AuiPaneInfo().ToolbarPane().Top().Name("testtoolbar"))
        self._auiexmgr.Update()
        
    def Show(self, bShow=True):
        wx.Frame.Show(self, bShow)
        childrens = self.GetChildren()
        print childrens
        