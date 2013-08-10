"""This module provides child frame related class.

Child frame is center pane in main frame. Typically, child frame is a notebook control.
Each view in child frame is a notebook page.

Lu, Ken (tech.ken.lu@gmail.com)
"""
from ps_menu import *
from ps_auiex import *
from ps_viewframe import PSCenterViewFrame
from interfaces.docview import *

_= wx.GetTranslation
class PSChildFrameTabArt(VC71TabArt):
    def __init__(self):
        VC71TabArt.__init__(self)
        self.SetCustomButton(AUI_BUTTON_CLOSE, AUI_BUTTON_STATE_NORMAL, wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)))
        self.SetCustomButton(AUI_BUTTON_WINDOWLIST, AUI_BUTTON_STATE_NORMAL, wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)))
        
class PSChildFrame(AuiNotebook):
    PANE_NAME = "ChildFrame"
    
    def __init__(self, parent, id):
        style = AUI_NB_TOP|AUI_NB_CLOSE_ON_ACTIVE_TAB|AUI_NB_TAB_FIXED_WIDTH|wx.NO_BORDER|\
                AUI_NB_SMART_TABS|AUI_NB_WINDOWLIST_BUTTON|AUI_NB_SCROLL_BUTTONS|AUI_NB_USE_IMAGES_DROPDOWN|AUI_NB_TAB_SPLIT|AUI_NB_TAB_MOVE
        AuiNotebook.__init__(self, parent, id, style=style)
        art = PSChildFrameTabArt()
        art.SetCustomButton(AUI_BUTTON_CLOSE, AUI_BUTTON_STATE_NORMAL, wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)))
        art.SetCustomButton(AUI_BUTTON_WINDOWLIST, AUI_BUTTON_STATE_NORMAL, wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)))
        self.SetArtProvider(art)
        self.SetTabCtrlHeight(23)
        
        self.Bind(EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnPageClose)
        self.Bind(EVT_AUINOTEBOOK_TAB_RIGHT_UP, self.OnTabRightUp)
        
    def ActiveViewFrame(self, viewframe):
        self.SetSelectionToWindow(viewframe)
        
    def CloseView(self, view):
        viewframe = view.GetFrame()
        index = self.GetPageIndex(viewframe)
        
        e = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSE, self.GetId())
        e.SetSelection(index)
        e.SetOldSelection(index)
        e.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(e)
        if not e.IsAllowed():
            return
        
        self.DeletePage(index)

        # notify owner that the tab has been closed
        e2 = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSED, self.GetId())
        e2.SetSelection(index)
        e2.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(e2)

        if self.GetPageCount() == 0:
            mgr = self.GetAuiManager()
            win = mgr.GetManagedWindow()
            win.SendSizeEvent()
    
    def CreateViewFrame(self, owner):
        viewframe = PSCenterViewFrame(owner)
        self.AddPage(viewframe, viewframe.GetName(), True, owner.GetBitmap())
        return viewframe

    def GetActiveView(self):
        if self.GetSelection() == -1:
            return None
        return self.GetPage(self.GetSelection()).GetOwner()
    
    def GetPaneInfo(self):
        paneinfo = AuiPaneInfo().Name(self.PANE_NAME).CenterPane().PaneBorder(False)
        return paneinfo
    
    def OnPageChanged(self, event):
        oldsel = event.GetOldSelection()
        if oldsel != -1:
            viewframe = self.GetPage(oldsel)
            viewframe.ProcessViewEvent(ViewActiveEvent(active=False))
                         
        viewframe = self.GetPage(event.GetSelection())
        viewframe.ProcessViewEvent(ViewActiveEvent(active=True))

        wx.GetApp().GetMainFrame().SetTitle(viewframe.GetDescription() + " - " + wx.GetApp().GetAppName())
                
    def OnPageClose(self, event):
        index = event.GetSelection()
        view  = self.GetPage(index)
        e = ViewCloseEvent()
        view.ProcessViewEvent(e)
        if not e.IsAllowed():
            event.Veto()

    def OnTabMenuClose(self, event):
        index = self.GetSelection()
        viewframe = self.GetPage(self.GetSelection())
        
        e = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSE, self.GetId())
        e.SetSelection(self.GetSelection())
        e.SetOldSelection(self.GetSelection())
        e.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(e)
        if not e.IsAllowed():
            return
        self.DeletePage(self.GetSelection())

        # notify owner that the tab has been closed
        e2 = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSED, self.GetId())
        e2.SetSelection(index)
        e2.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(e2)

        if self.GetPageCount() == 0:
            mgr = self.GetAuiManager()
            win = mgr.GetManagedWindow()
            win.SendSizeEvent()
        
    def OnTabMenuCloseOthers(self, event):
        existing = self.GetPage(self.GetSelection())
        finish = False
        while True:
            if self.GetPageCount() == 1 and self.GetPage(0) == existing:
                break
            if self.GetPage(0) == existing:
                closeview = self.GetPage(1)
            else:
                closeview = self.GetPage(0)
            
            index = self.GetPageIndex(closeview)
            self.SetSelection(index)
            
            e = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSE, self.GetId())
            e.SetSelection(index)
            e.SetOldSelection(index)
            e.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(e)
            if not e.IsAllowed():
                return
            self.DeletePage(index)
    
            # notify owner that the tab has been closed
            e2 = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSED, self.GetId())
            e2.SetSelection(index)
            e2.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(e2)
        
    def OnTabMenuCloseAll(self, event):
        while True:
            if self.GetPageCount() ==0:
                break

            closeview = self.GetPage(0)
            index = self.GetPageIndex(closeview)
            self.SetSelection(index)
            
            e = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSE, self.GetId())
            e.SetSelection(index)
            e.SetOldSelection(index)
            e.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(e)
            if not e.IsAllowed():
                return
            self.DeletePage(index)
    
            # notify owner that the tab has been closed
            e2 = AuiNotebookEvent(wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSED, self.GetId())
            e2.SetSelection(index)
            e2.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(e2)

        mgr = self.GetAuiManager()
        win = mgr.GetManagedWindow()
        win.SendSizeEvent()
        
    def OnTabMenuCopyFilename(self, event):
        view = self.GetPage(self.GetSelection()).GetOwner()
        textObj = wx.TextDataObject()
        textObj.SetText(view.GetDoc().GetFilename())
        # Copy text object to clipboard
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(textObj)
        wx.TheClipboard.Close()   
                
    def OnTabRightUp(self, event):
        self.SetSelection(event.GetSelection())
        
        view = self.GetPage(self.GetSelection()).GetOwner()
        popupMenu = PSMenu()
        
        menuItem = PSMenuItem(popupMenu, -1, _("Close"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, menuItem.GetId(), self.OnTabMenuClose)
        popupMenu.AppendItem(menuItem)
        menuItem = PSMenuItem(popupMenu, -1, _("Close Others"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, menuItem.GetId(), self.OnTabMenuCloseOthers)        
        popupMenu.AppendItem(menuItem)
        menuItem = PSMenuItem(popupMenu, -1, _("Close All"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, menuItem.GetId(), self.OnTabMenuCloseAll)
        popupMenu.AppendItem(menuItem)
        
        if view.GetDoc() != None and view.GetDoc().GetFilename() != None:
            popupMenu.AppendSeparator()
            menuItem = PSMenuItem(popupMenu, -1, _("Copy Filename"), wx.ITEM_NORMAL)
            wx.EVT_MENU(self, menuItem.GetId(), self.OnTabMenuCopyFilename)
            popupMenu.AppendItem(menuItem)
            
        #popupMenu.Append 
        pt = wx.Point(event.X, event.Y)
        popupMenu.Popup(self.ClientToScreen(pt), self)
        del popupMenu
        
