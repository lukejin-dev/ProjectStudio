from interfaces.core import ISingleView

from ps_auiex import *

_=wx.GetTranslation
class PSSingleViewFrame(wx.Panel):
    def __init__(self, viewclass):
        # Default parent is main frame 
        wx.Panel.__init__(self, wx.GetApp().GetMainFrame())
        
        assert wx.GetApp().IsInterfaceImplement(ISingleView, viewclass), "view class must implement the ISingleView."
        
        # Create customer view instance
        self._logger = wx.GetApp().GetLogger("SingleView")
        self._view = viewclass()
        self._view.Create(self)
        self.SetName(self._view.GetName())

    def GetDefaultPaneInfo(self):
        paneinfo = AuiPaneInfo().Name(self.GetName()).Caption(_(self.GetName())).MinSize((100, 100)).NotebookDockable().MinimizeButton(True).PinButton(True)
        paneinfo = paneinfo.Caption(_(self.GetName()))
        framesize = wx.GetApp().GetMainFrame().GetSize()
        framepos  = wx.GetApp().GetMainFrame().GetPosition()
        dockpos   = self._view.GetDockPosition()
        if dockpos == ISingleView.DOCK_FLOAT:
            paneinfo = paneinfo.Float()
        elif dockpos == ISingleView.DOCK_LEFT:
            paneinfo = paneinfo.Left()
        elif dockpos == ISingleView.DOCK_RIGHT:
            paneinfo = paneinfo.Right()
        elif dockpos == ISingleView.DOCK_TOP:
            paneinfo = paneinfo.Top()
        elif dockpos == ISingleView.DOCK_BOTTOM:
            paneinfo = paneinfo.Bottom()
        else:
            self._logger.error("Invalid dock position %s for single view" % dockpos)
            paneinfo = paneinfo.Float()
            paneinfo = paneinfo.FloatingPosition((framepos[0] + framesize[0] / 4, framepos[1] + framesize[1] / 4))

        paneinfo = paneinfo.FloatingPosition((framepos[0] + framesize[0] / 4, framepos[1] + framesize[1] / 4))        
        paneinfo  = paneinfo.BestSize((framesize[0] / 2, framesize[1] / 2))
        paneinfo  = paneinfo.MinimizeMode(AUI_MINIMIZE_POS_SMART|AUI_MINIMIZE_CAPT_SMART)
        paneinfo = paneinfo.IconName(self._view.GetIconName())
        return paneinfo
    
    def GetBackgroundSceneNames(self):
        return self._view.GetBackgroundSceneNames()
    
    def GetViewInstance(self):
        return self._view
    
    def GetViewBitmap(self):
        return wx.ArtProvider_GetBitmap(self._view.GetIconName(), size=(16, 16))
    
import ps_auiex    
class PSCenterViewFrame(wx.Panel):
    def __init__(self, owner):
        parent = wx.GetApp().GetMainFrame().GetChildFrame()
        self._owner = owner
        wx.Panel.__init__(self, parent)
        
    def Active(self):
        self.GetParent().ActiveViewFrame(self)
        
    def GetName(self):
        return self._owner.GetName()
    
    def GetDescription(self):
        return self._owner.GetDescription()

    def GetOwner(self):
        return self._owner
    
    def GetTitle(self):
        index = self.GetParent().GetPageIndex(self)
        return self.GetParent().GetPageText(index)
    
    def ProcessViewEvent(self, event):
        self._owner.ProcessEvent(event)
        
    def SetTitle(self, title):
        index = self.GetParent().GetPageIndex(self)
        self.GetParent().SetPageText(index, title)
