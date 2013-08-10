import os
import wx
import wx.lib.newevent
import lib.aui.auibook as auibookex
from ps_auiex import *

import ps_art
from interfaces.core import IService
from interfaces.core import ISingleView
from interfaces.event import *
import interfaces.event

_=wx.GetTranslation

class PSSearchService(IService):
    def __init__(self):
        self._logger = wx.GetApp().GetLogger("Search")
        self._searchDlg = None
        
    def GetName(self):
        return "SearchService"
    
    def Start(self):
        self._InstallSearchMenu()
        frame = wx.GetApp().GetMainFrame()
        self._view = frame.CreateSingleView(PSSearchView)
        
    def Stop(self):
        pass
        
    def _InstallSearchMenu(self):
        frame = wx.GetApp().GetMainFrame()
        searchMenu = frame.CreateMenu()
        item = searchMenu.Append(-1, _("Search") +"\tCtrl+F", "Search in current view", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(ps_art.PS_ART_SEARCH_MENU, size=(16, 16)))
        wx.EVT_UPDATE_UI(frame, item.GetId(), self.OnUpdateMenuSearch)
        wx.EVT_MENU(frame, item.GetId(), self.OnMenuSearch)
        item = searchMenu.Append(-1, _("Search In Files"), "Search in files", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(ps_art.PS_ART_SEARCH_IN_FILES, size=(16, 16)))
        item = searchMenu.Append(-1, _("Replace"), "Replace in current view", wx.ITEM_NORMAL)
        wx.EVT_UPDATE_UI(frame, item.GetId(), self.OnUpdateMenuReplace)
        item = searchMenu.Append(-1, _("Replace In Files"), "Replace in files", wx.ITEM_NORMAL)
        frame.InstallMenu(_("&Search"), searchMenu)
        
    def OnMenuSearch(self, event):
        if not self._IsCurrentViewSupportSearch():
            return
        
        if self._searchDlg == None:
            self._searchDlg = SearchDialog()
        
        if not self._searchDlg.IsShown():
            self._searchDlg.Show()
            
        self._searchDlg.SetFocus()
        
    def OnUpdateMenuSearch(self, event):
        if self._IsCurrentViewSupportSearch():
            event.Enable(True)
        else:
            event.Enable(False)

    def OnUpdateMenuReplace(self, event):
        if self._IsCurrentViewSupportReplace():
            event.Enable(True)
        else:
            event.Enable(False)

    def _IsCurrentViewSupportSearch(self):
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view == None:
            return False
        evt = QueryViewSearchEvent(-1, can=False)
        if not view.ProcessEvent(evt):
            return False
        
        return evt.can
        
    def _IsCurrentViewSupportReplace(self):
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view == None:
            return False
        evt = QueryViewReplaceEvent(-1, can=False)
        if not view.ProcessEvent(evt):
            return False
        
        return evt.can
        
class PSSearchView(ISingleView):
    def __init__(self):
        pass
        
    def GetName(self):
        return "Search"
    
    def GetIconName(self):
        return ps_art.PS_ART_SEARCH
    
    def Create(self, parentWnd):      
        self._searchnb = ResultNotebook(parentWnd)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._searchnb, 1, wx.EXPAND, 2)
        parentWnd.SetSizer(sizer)
    
    def GetDockPosition(self):
        return ISingleView.DOCK_BOTTOM      
    
import wx.lib.flatnotebook as FNB
class ResultNotebook(FNB.FlatNotebook):
    def __init__(self, parent):
        style = wx.NO_BORDER|FNB.FNB_VC71|FNB.FNB_LEFT_ARROW|FNB.FNB_NO_X_BUTTON|FNB.FNB_NO_NAV_BUTTONS|FNB.FNB_NODRAG
        FNB.FlatNotebook.__init__(self, parent, style=style)
        for x in range(4):
            self.AddPage(ResultPage(self), _("Result") + "<%d>" % x)

class ResultPage(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.NO_BORDER)
        

SizeAdjustEvent, EVT_SIZE_ADJUST_EVENT = NewEvent()        
class SearchDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, wx.GetApp().GetMainFrame(), -1)  
        style = wx.NO_BORDER|FNB.FNB_VC71|FNB.FNB_LEFT_ARROW|FNB.FNB_NO_X_BUTTON|FNB.FNB_NO_NAV_BUTTONS|FNB.FNB_NODRAG
        self._nb = FNB.FlatNotebook(self, -1, style=style)
        self._findPage = FindPage(self)
        self._nb.AddPage(self._findPage, _("Find"))
        self._replacePage = ReplacePage(self)
        self._nb.AddPage(self._replacePage, _("Replace"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._nb, 1, wx.EXPAND, 5)
        self.SetSizer(sizer)
        EVT_SIZE_ADJUST_EVENT(self, self.OnSizeAdjust)
    
        self.ProcessEvent(SizeAdjustEvent())
        wx.CallAfter(self.Centre)
        
    def OnSizeAdjust(self, event):
        page = self._nb.GetCurrentPage()
        self.SetSize((400, page.CaculateHeight()))
        self.Layout()
        
import wx.lib.agw.foldpanelbar as fpb        
class FindOptionsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self._fpb = fpb.FoldPanelBar(self, -1, style=fpb.FPB_DEFAULT_STYLE)
        
        self._searchFilterItem = self._fpb.AddFoldPanel(_("Search Filter"), collapsed=True)
        self._inFolderCheckCtrl = wx.CheckBox(self._searchFilterItem, -1, "Search in subfolder")
        self._fpb.AddFoldPanelWindow(self._searchFilterItem, self._inFolderCheckCtrl, fpb.FPB_ALIGN_WIDTH)
        self._fpb.AddFoldPanelWindow(self._searchFilterItem, wx.StaticText(self._searchFilterItem, -1, "File Types:"), fpb.FPB_ALIGN_LEFT) 
        self._fileTypesEditCtrl = wx.ComboBox(self._searchFilterItem, -1)
        self._fpb.AddFoldPanelWindow(self._searchFilterItem, self._fileTypesEditCtrl, fpb.FPB_ALIGN_WIDTH, Spacing=2)
        self._fpb.AddFoldPanelWindow(self._searchFilterItem, wx.StaticText(self._searchFilterItem, -1, "Exclude Folders:"), fpb.FPB_ALIGN_LEFT)
        self._excludefoldersCtrl = wx.ComboBox(self._searchFilterItem, -1)
        self._fpb.AddFoldPanelWindow(self._searchFilterItem, self._excludefoldersCtrl, fpb.FPB_ALIGN_WIDTH, Spacing=2)
        
        self._searchFlagItem = self._fpb.AddFoldPanel(_("Search Options"), collapsed=True)
        self._caseCheckCtrl = wx.CheckBox(self._searchFlagItem, -1, ("Match Case"))
        self._fpb.AddFoldPanelWindow(self._searchFlagItem, self._caseCheckCtrl, fpb.FPB_ALIGN_LEFT)
        self._wholeCheckCtrl = wx.CheckBox(self._searchFlagItem, -1, _("Match Whole World"))
        self._fpb.AddFoldPanelWindow(self._searchFlagItem, self._wholeCheckCtrl, fpb.FPB_ALIGN_LEFT)
        self._backwardCheckCtrl = wx.CheckBox(self._searchFlagItem, -1, _("Search Backward"))
        self._fpb.AddFoldPanelWindow(self._searchFlagItem, self._backwardCheckCtrl, fpb.FPB_ALIGN_LEFT)
        self._wrapperSearchCtrl = wx.CheckBox(self._searchFlagItem, -1, _("Wrapper Search"))
        self._fpb.AddFoldPanelWindow(self._searchFlagItem, self._wrapperSearchCtrl, fpb.FPB_ALIGN_LEFT)
        
        self._resultFlagItem = self._fpb.AddFoldPanel("Result Options", collapsed=True)
        self._fpb.AddFoldPanelWindow(self._resultFlagItem, wx.StaticText(self._resultFlagItem, -1, "Output result in:"), fpb.FPB_ALIGN_LEFT)
        self._resultIndexCtrl = wx.ComboBox(self._resultFlagItem, -1, choices=["<Result 0>", "<Result 1>", "<Result 2>", "<Result 3>"])
        self._fpb.AddFoldPanelWindow(self._resultFlagItem, self._resultIndexCtrl, fpb.FPB_ALIGN_WIDTH)
        self._resultAppendCtrl = wx.CheckBox(self._resultFlagItem, -1, _("Append to result"))
        self._fpb.AddFoldPanelWindow(self._resultFlagItem, self._resultAppendCtrl, fpb.FPB_ALIGN_LEFT)
        
        fpb.EVT_CAPTIONBAR(self._fpb, self.OnCaptionBar)
        size = self.GetParent().GetParent().GetClientSize()
        self._fpb.SetSize((size[0], self.CaculateHeight()))
       
    def CaculateHeight(self):
        height = 0
        if self._searchFilterItem.IsExpanded():
            height += 140
        else:
            height += 20
        if self._searchFlagItem.IsExpanded():
            height += 120
        else:
            height += 20
        if self._resultFlagItem.IsExpanded():
            height += 100
        else:
            height += 20
        return height

    def OnCaptionBar(self, event):
        event.Skip()
        wx.PostEvent(self.GetParent().GetParent().GetParent(), SizeAdjustEvent())
        size = self.GetParent().GetParent().GetClientSize()
        self._fpb.SetSize((size[0], 400))

class FindPage(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._config = wx.GetApp().GetConfig("Search")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._searchCtrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self._scopeEditCtrl = wx.ComboBox(self, -1)
        self._scopeBtn = wx.BitmapButton(self, -1, size=(20,20), bitmap=wx.ArtProvider_GetBitmap(ps_art.PS_ART_SEARCH_SCOPE_FOLDER, size=(16, 16)))
        self._optionCtrl = FindOptionsPanel(self)
        self._okBtn = wx.Button(self, -1, _("Find"), style=wx.NO_BORDER)
        self._cancelBtn = wx.Button(self, -1, _("Cancel"), style=wx.NO_BORDER)
        
        scopesizer = wx.BoxSizer(wx.HORIZONTAL)
        scopesizer.Add(self._scopeEditCtrl, 1, wx.EXPAND)
        scopesizer.Add(self._scopeBtn, 0, wx.EXPAND|wx.LEFT, 3)
        
        btsizer = wx.BoxSizer(wx.HORIZONTAL)
        btsizer.Add(self._okBtn, 0, wx.EXPAND|wx.ALL, 2)
        btsizer.Add(self._cancelBtn, 0, wx.EXPAND|wx.ALL, 2)
        
        sizer.Add(wx.StaticText(self, -1, _("Search for:")), 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self._searchCtrl, 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(wx.StaticText(self, -1, _("Look in:")), 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(scopesizer, 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self._optionCtrl, 1, wx.EXPAND|wx.ALL, 0)
        sizer.Add(btsizer, 0, wx.EXPAND|wx.ALIGN_CENTRE, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
        self._initControl()
        
    def CaculateHeight(self):
        return 180 + self._optionCtrl.CaculateHeight()

    def _initControl(self):
        # append history key into search control
        self._searchCtrl.SetDescriptiveText("Input search keywords")
        self.Bind(wx.EVT_TEXT_ENTER, self.OnStartSearch, self._searchCtrl)
        
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectSearchScope, self._scopeEditCtrl)
        self._scopeEditCtrl.Append("<Current Document>")
        
    def _refreshSearchMenu(self, key):
        menu = self._searchCtrl.GetMenu()
        if menu == None:
            menu = wx.Menu()
            self._searchCtrl.SetMenu(menu)
        for item in menu.GetMenuItems():
            if item.GetText() == key:
                menu.RemoveItem(item)
        item = menu.Insert(0, -1, key)
        wx.EVT_MENU(self, item.GetId(), self.OnMenuSearchKey)
        
    def OnMenuSearchKey(self, event):
        menu = event.GetEventObject()
        item = menu.FindItemById(event.GetId())
        self._searchCtrl.SetValue(item.GetText())
        
    def OnSelectSearchScope(self, event):
        print self._scopeEditCtrl.GetSelection()
        event.Skip()
    def OnStartSearch(self, event):
        key = self._searchCtrl.GetValue()
        self._refreshSearchMenu(key)
        
class ReplacePage(wx.Panel):
    def __init__(self, parent):        
        wx.Panel.__init__(self, parent)   