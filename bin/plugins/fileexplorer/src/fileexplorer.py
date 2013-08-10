import os
import wx
from interfaces.core import IService
from interfaces.core import ISingleView

class FileExplorer(IService):
    def Start(self):
        frame = wx.GetApp().GetMainFrame()
        self._view = frame.CreateSingleView(FileExplorerView)

class FileExplorerView(ISingleView):  
    def __init__(self):
        self._parent = None
              
    def GetName(self):
        """Implement the ISingleView.GetName() interface."""
        return "FileExplorer"
    
    def GetIconName(self):
        """Implement the ISingleView.GetIconName() interface."""
        return wx.ART_FILE_OPEN
    
    def Create(self, parentWnd):
        self._pathCtrl = wx.ComboBox(parentWnd, -1, choices=self._GetBookmarkPaths(), style=wx.STATIC_BORDER|wx.TE_PROCESS_ENTER)
        self._pathCtrl.Bind(wx.EVT_KEY_DOWN, self.OnPathCtrlKeyDown)
        self._pathCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnPathCtrlEnter)
        self._pathCtrl.Bind(wx.EVT_COMBOBOX, self.OnPathSelected)
        self._dirctrl = wx.GenericDirCtrl(parentWnd, -1, style=wx.STATIC_BORDER)
        self._dirctrl.GetTreeCtrl().Bind(wx.EVT_KEY_UP, self.OnTreeKeyUp)
        self._dirctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnTreeMouseLeftUp)
        self._dirctrl.ShowHidden(config.Get("ShowHiddenFile", True))
        self._bookmark_bt = wx.BitmapButton(parentWnd, -1, size=(20, 20),
                                            bitmap=wx.Bitmap(os.path.join(pi.GetPath(), "icons", "bookmark_path_16.ico")))
        self._bookmark_bt.SetToolTipString("Bookmark current path")
        self._bookmark_bt.Bind(wx.EVT_BUTTON, self.OnBookmarkPath)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        subsizer = wx.BoxSizer(wx.HORIZONTAL)
        subsizer.Add(self._pathCtrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTRE, 2)
        subsizer.Add(self._bookmark_bt, 0, wx.EXPAND|wx.RIGHT, 2)
        sizer.Add(subsizer, 0, wx.EXPAND|wx.TOP, 2)
        sizer.Add(self._dirctrl, 1, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.TOP, 2)
        parentWnd.SetSizer(sizer)
        parentWnd.Bind(wx.EVT_SET_FOCUS, self.OnParentFocus)
        self._parent = parentWnd
        
    def GetDockPosition(self):
        """Implement the ISingleView.GetDockPosition() interface. """
        return ISingleView.DOCK_BOTTOM
    
    def OnPathSelected(self, event):
        path = self._pathCtrl.GetValue()
        if not os.path.exists(path):
            return
        
        self._dirctrl.SetPath(path)
        
    def OnParentFocus(self, event):
        self._pathCtrl.SetFocus()
        
    def OnPathCtrlKeyDown(self, event):
        keycode = event.GetKeyCode()

        if keycode in [wx.WXK_UP, wx.WXK_DOWN]:
            self._dirctrl.GetTreeCtrl().SetFocus()
            return
        if keycode in [wx.WXK_LEFT, wx.WXK_RIGHT]:
            event.Skip()
            return
        
        text = self._pathCtrl.GetValue()
        text = os.path.normpath(text)
        parentPath = os.path.dirname(text)
        if not os.path.exists(parentPath):
            return

        for path in os.listdir(parentPath):
            full = os.path.normpath(os.path.join(parentPath, path))
            if full.lower().find(text.lower()) != -1:
                self._dirctrl.SetPath(full)
                return
            
        self._dirctrl.SetPath(parentPath)

    def OnBookmarkPath(self, event):
        path = self._pathCtrl.GetValue()
        if not os.path.exists(path):
            path = os.path.dirname(path)
            if not os.path.exists(path):
                return
        path = os.path.normpath(path)
        
        list = self._GetBookmarkPaths()
        if path not in list:
            self._pathCtrl.Insert(path, 0)
        
        self._SaveBookmarkPaths()
        
    def OnPathCtrlEnter(self, event):
        self._dirctrl.GetTreeCtrl().SetFocus()
        
    def OnTreeKeyUp(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_TAB:
            self._pathCtrl.SetFocus()
        elif keycode == wx.WXK_RETURN:
            tree = self._dirctrl.GetTreeCtrl()
            if tree.IsExpanded(tree.GetSelection()):
                tree.Collapse(tree.GetSelection())
            else:
                tree.Expand(tree.GetSelection())
        self._pathCtrl.SetValue(self._dirctrl.GetPath())
        
    def OnTreeMouseLeftUp(self, event):
        path = self._dirctrl.GetPath()
        if os.path.isdir(path):
            self._pathCtrl.SetValue(self._dirctrl.GetPath())
        else:
            wx.GetApp().GetDocManager().OpenDocument(path)
        event.Skip()
        
    def _GetBookmarkPaths(self):
        pathlist = config.Get("BookmarkPaths", "").split(";")
        if len(pathlist) == 1 and pathlist[0] == "":
            return []
        return pathlist
    
    def _SaveBookmarkPaths(self):
        config.Set("BookmarkPaths", ";".join(self._pathCtrl.GetStrings()[0:10]))
         
def __extension_main__(pluginInfo):
    global pi
    pi = pluginInfo
    
    global logger
    logger = wx.GetApp().GetLogger("FileExplorer")
    
    global config
    config = wx.GetApp().GetConfig("FileExplorer")
    


