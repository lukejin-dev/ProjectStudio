import wx, os
import core.service

class OutlineService(core.service.PISService):
    def __init__(self):
        core.service.PISService.__init__(self)
        self._outview          = None
        self._InitTreeCallback = None
        self._SelectCallback   = None
        
    def ResigterCallbacks(self, init=None, sel=None):
        self._InitTreeCallback = init
        self._SelectCallback   = sel
        
    def GetPosition(self):
        return 'right'
    
    def GetName(self):
        return 'Outline'
    
    def GetViewClass(self):
        return OutlineView
    
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        pass

    def GetIcon(self):
        return wx.GetApp().GetArtProvider().GetIcon(wx.ART_LIST_VIEW)
    
    def Load(self, outview):
        if self._outview != None and self._outview == view:
            return
        
        # create view if not exists
        view = self.GetView()
        if view == None:
            view = self.CreateView()
            
        view.Freeze()
        if self._outview != None:
            view.ClearTree()
        self._outview = outview
        sel = self._SelectCallback
        self._SelectCallback = None
        if self._InitTreeCallback != None:
            self._InitTreeCallback(self._outview, 
                                   view.GetTreeCtrl())
            view.GetTreeCtrl().SortAllChildren()
        view.Thaw()
        self._SelectCallback = sel
        
    def UnLoad(self):
        if self.GetView() != None:
            self.GetView().ClearTree()
        self._outview          = None
        self._InitTreeCallback = None
        self._SelectCallback   = None        
        #self.DeActivate()
        
    def GetTargetView(self):
        return self._outview
        
    def Clear(self):
        if self.GetView() != None:
            self.GetView().ClearTree()
            self._outview = None
        
class OutlineView(core.service.PISServiceView):
    """
    the view of outline service is in a right side window
    """
    def __init__(self, parent, service,id=-1, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Outline'):
        core.service.PISServiceView.__init__(self, parent, service, id, pos, size, style, name)
        
        # create view's ctrl
        self._sizer = wx.BoxSizer(wx.VERTICAL) 
        self._treectrl = OutlineTreeCtrl(self, -1)
        self._sizer.Add(self._treectrl, 1, wx.EXPAND)
        self.SetSizer(self._sizer)
        self.SetAutoLayout(True)
        
        wx.EVT_TREE_ITEM_ACTIVATED(self._treectrl, self._treectrl.GetId(), self.DoSelection)
        
    def GetTreeCtrl(self):
        return self._treectrl
        
    def ClearTree(self):
        self.Freeze()
        self._treectrl.DeleteAllItems()
        self.Thaw()
        
    def DoSelection(self, event):
        item = event.GetItem()
        pydate = self._treectrl.GetPyData(item)
        service = self.GetService()
        if service._SelectCallback != None and service.GetTargetView() != None:
            service._SelectCallback(service.GetTargetView(),
                                    pydate)
                
class OutlineTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT ):
        wx.TreeCtrl.__init__(self, parent, id, style = style)
        
    def SortAllChildren(self, parentItem=None):
        if parentItem == None:
            parentItem = self.GetRootItem()
            
        if parentItem and self.GetChildrenCount(parentItem, False):
            self.SortChildren(parentItem)
            (child, cookie) = self.GetFirstChild(parentItem)
            while child.IsOk():
                self.SortAllChildren(child)
                (child, cookie) = self.GetNextChild(parentItem, cookie)        