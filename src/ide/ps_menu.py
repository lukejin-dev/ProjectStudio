import wx

from wx.lib.agw.flatmenu import *
from wx.lib.agw.artmanager import ArtManager

import ps_auiex

class PSMenuBar(FlatMenuBar):
    MENUBAR_NAME    = "PSMenuBar"
 
    def __init__(self, parent, id=wx.ID_ANY):
        FlatMenuBar.__init__(self, parent, id, 16, 2, FM_OPT_IS_LCD)
        #ArtManager.Get().SetMenuTheme(Style2007)
        ArtManager.Get().SetMenuTheme(StyleXP)
        # list of menu title
        self._menuTitles = []
        self._genericMenuTitles = []
        
    def GetPaneInfo(self):
        pn = ps_auiex.AuiPaneInfo()
        xx = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)

        # We add our menu bar as a toolbar, with the following settings

        pn.Name(self.MENUBAR_NAME)
        pn.Caption("Menu Bar")
        pn.Top()
        pn.MinSize(wx.Size(xx/2, self._barHeight))
        pn.LeftDockable(False)
        pn.RightDockable(False)
        pn.ToolbarPane()
        pn.PaneBorder(False)
        pn.BestSize(wx.Size(xx, self._barHeight))
        pn.Gripper(False)
        pn.Resizable(False)
        return pn
        
    def GetMenuCount(self):
        return len(self._items)
    
    def GetMenuTitle(self, menuIdx):
        if menuIdx >= len(self._items) or menuIdx < 0:
            return None
        return self._items[menuIdx].GetTitle()
    
    def GetMenuTitles(self):
        count = self.GetMenuCount()
        titles = []
        for x in xrange(count):
            titles.append(self.GetMenuTitle(x))
        return titles
    
class PSMenu(FlatMenu):
    def __init__(self, parent=None):
        FlatMenu.__init__(self, parent)
        self._itemHeight = 16
        self._marginHeight = 16
        self.SetSize(wx.Size(self._menuWidth, self._itemHeight+1))
                     
class PSMenuItem(FlatMenuItem):
    pass