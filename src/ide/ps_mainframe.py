"""This module provide main frame management.

Lu, Ken (tech.ken.lu@gmail.com)
"""
import os
import wx

import ps_auiex as auiex
import ps_art
import ps_scene
import ps_menu 
import ps_childframe
import ps_viewframe
import ps_error
import interfaces.core
import interfaces.event
from ps_debug import *
from ps_viewframe import PSSingleViewFrame
 
_MAINFRAME_SETTING_X      = "MainFrameX"
_MAINFRAME_SETTING_Y      = "MainFrameY"
_MAINFRAME_SETTING_WIDTH  = "MainFrameWidth"
_MAINFRAME_SETTING_HEIGHT = "MainFrameHeight"
_MAINFRAME_SETTING_ISMAX  = "MainFrameIsMax"

ID_MENU_FILE_NEW      = wx.NewId()
ID_MENU_FILE_OPEN     = wx.NewId()
ID_MENU_FILE_SAVE     = wx.NewId()
ID_MENU_FILE_SAVE_AS  = wx.NewId()
ID_MENU_FILE_SAVEALL  = wx.NewId()
ID_MENU_WINDOW_VIEWS  = wx.NewId()
ID_MENU_LASTEST_OPEN  = wx.NewId()

ID_MENU_UNDO = wx.NewId()
ID_MENU_REDO = wx.NewId()
ID_MENU_COPY = wx.NewId()
ID_MENU_CUT  = wx.NewId()
ID_MENU_PASTE = wx.NewId()

ID_LANG_CHINESE  = wx.NewId()
ID_LANG_ENGLISH  = wx.NewId()
ID_LANG_JAPANESE = wx.NewId()

_=wx.GetTranslation

MENU_TITLE_FILE       = "&File"
MENU_TITLE_EDIT       = "&Edit"
MENU_TITLE_WINDOW     = "&Window"
MENU_TITLE_HELP       = "&Help"
TOOLBAR_NAME_GENERAL  = "GeneralTools"

class PEMainFrame(wx.Frame, interfaces.core.IMainFrame, ps_scene.PSSceneManager):
    ID_FRAME_DOC_NOTEBOOK = wx.NewId()
    
    def __init__(self):
        self._logger = wx.GetApp().GetLogger("MainFrame")
        self._config = wx.GetApp().GetConfig("MainFrame")
        
        #
        # Restore the size and position in last save as parameter for calling
        # parent's constructor function
        #
        self._savedPos, self._savedSize = self._GetSavedPosSize()
        style = wx.FRAME_EX_METAL|wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.CAPTION
        wx.Frame.__init__(self, None, pos=self._savedPos, size=self._savedSize, style=style)
        self.SetThemeEnabled(True)

        #
        # Determine the maxmize as early as possible.
        #
        if self._config.Get(_MAINFRAME_SETTING_ISMAX, False):
            self.Maximize()
            self.SendSizeEvent()
        self.SetMinSize(wx.Size(600, 400))

        self.SetTitle(wx.GetApp().GetAppName())
        self.CreateStatusBar()
        
        #
        # Create AuiManager object
        #
        self._mgr = auiex.PSAuiManager(self, auiex.AUI_MGR_ALLOW_FLOATING | auiex.AUI_MGR_ALLOW_ACTIVE_PANE)
        self._mgr.SetArtProvider(auiex.PSDockArt())
        self._mgr.GetArtProvider().SetMetric(auiex.AUI_DOCKART_SASH_SIZE, 3)
        self._mgr.GetArtProvider().SetMetric(auiex.AUI_DOCKART_GRADIENT_TYPE, auiex.AUI_GRADIENT_NONE)
        
        #
        # Initialize scene manager and enter scene last opened
        #
        ps_scene.PSSceneManager.__init__(self, self._mgr)
        self.FIXED_MENU_TITLES = [_(MENU_TITLE_FILE), _(MENU_TITLE_EDIT), _(MENU_TITLE_WINDOW), _(MENU_TITLE_HELP)]
        self._menubar = self._CreateMenuBar()
        
        self._InstallGenericMenu()
        
        # toolbar dictionary
        # key    : tool bar's name
        # value  : toolbar object
        self._toolbars = {}
        self._InstallGenericToolBar()
        
        
        self._toolbar = auiex.PSToolbar(self, -1, style=auiex.AUI_TB_OVERFLOW)
        toolbarsize  = wx.Size(16, 16)
        self._toolbar.SetToolBitmapSize(toolbarsize)
        self._toolbar.AddSimpleTool(-1, "Test", wx.ArtProvider.GetBitmap(wx.ART_COPY, size=toolbarsize))
        self._toolbar.Realize()
        self._mgr.AddPane(self._toolbar, auiex.AuiPaneInfo().Name("ToolBar").ToolbarPane().Top().Row(1))
        
        # create center document pane
        self._childframe = self._CreateChildFrame()

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZING,  self.OnSizing)
        self.SetIcon(wx.ArtProvider.GetIcon(ps_art.PS_ART_APP, size=(32, 32)))

        #ps_scene.PSSceneManager.EnterLastBackgroundScene(self)
        self._lastFocus = None
        
    def __del__(self):
        ps_scene.PSSceneManager.__del__(self)
        
    def CreateConfirmDialog(self, message, caption, style, setting=None):
        if setting != None and not wx.GetApp().GetConfig("PromptConfirmDialog").Get(setting, True):
            return None
        return ConfirmDialog(message, caption, style, setting)
    
    def CreateMenu(self):
        menu = ps_menu.PSMenu()
        return menu
    
    def CreateSingleView(self, viewImpClass):
        """Create single float view from IView interface implementation class."""
        viewframe = PSSingleViewFrame(viewImpClass)
        self._mgr.AddPane(viewframe, viewframe.GetDefaultPaneInfo())
        if viewframe.GetBackgroundSceneNames() == None:
            for scene in self.GetBackgroundScenes():
                scene.AddSingleView(viewframe)
        self._AddSingleViewMenu(viewframe)
        return viewframe.GetViewInstance()
    
    def GetChildFrame(self):
        return self._childframe
    
    def GetManager(self):
        return self._mgr

    def GetMenuBar(self):
        return self._menubar
        
    def GetToolBar(self, name=TOOLBAR_NAME_GENERAL):
        """Get PSToolBar object via tool bar's name."""
        if name == None:
            self._config.error("Fail to get tool bar due to None as name!")
            return None
        if not self._toolbars.has_key(name):
            return None
        return self._toolbars[name]
        
    def InstallMenu(self, title, menu, scene="default"):
        """Install menu for given scene. 
        The installed menu will be displayed when scene is actived.
        The menus for default scene will be always displayed.
        
        @param menu     menu being installed
        @param scene    scene name 
        """
        sceneObj = self.GetBackgroundScene(scene)
        if sceneObj == None:
            self._logger.error("Fail to get scene object for %s" % scene)
            return

        if self.GetCurrentBackgroundSceneName() == scene:
            self._logger.info("%s %s" % (title, self.FIXED_MENU_TITLES))
            if title not in self.FIXED_MENU_TITLES:
                pos = self.GetMenuBar().FindMenu(_(MENU_TITLE_WINDOW))
                self.GetMenuBar().Insert(pos, menu, title)
            else:
                self.GetMenuBar().Append(menu, title)
        return sceneObj.AssociateMenu(title, menu)
        
    def OnClose(self, event):
        """
        Event handler for wx.EVT_CLOSE
        """
        for service in wx.GetApp().GetServices():
            wx.GetApp().GetLogger().info("Stoping service %s" % service.GetName())
            service.Stop()
            
        for doc in wx.GetApp().GetDocManager().GetDocs():
            if not wx.GetApp().GetDocManager().CloseDocument(doc):
                event.Veto()
                return 
            
        self._SavePosSize()
        event.Skip()
    
    def OnDropDownToolNew(self, event):
        """Event handler for EVT_AUITOOLBAR_TOOL_DROPDOWN."""
        
        if event.IsDropDownClicked():
            tool = event.GetEventObject()
            tool.SetToolSticky(event.GetId(), True)
            submenu = self._CreateNewSubMenu()
            
            rect = tool.GetToolRect(event.GetId())
            pt = tool.ClientToScreen(rect.GetBottomLeft())

            submenu.Popup(wx.Point(pt.x, pt.y), self)
                        
            tool.SetToolSticky(event.GetId(), False)
    
    def OnEditMenuUpdateUI(self, event):
        id = event.GetId()
        win = self.FindFocus()
        if win == None:
            event.Enable(False)
            return
        
        evt = interfaces.event.QueryFocusEditEvent(id, can=False)
        if not win.ProcessEvent(evt):
            event.Enable(False)
            return
        event.Enable(evt.can)
            
    def OnEditMenuCommand(self, event):
        id = event.GetId()
        win = self.FindFocus()
        if win == None:
            return
        
        evt = interfaces.event.FocusEditEvent(id)
        win.ProcessEvent(evt)
        
    def OnLanguageChanged(self, event):
        """wx.EVT_MENU event for language menu."""
        id = event.GetId()

        if id == ID_LANG_ENGLISH and wx.GetApp().GetLanguageId() != wx.LANGUAGE_ENGLISH:
            ret = ps_error.notifyConfirm(_("Change Language"), "Language is changed to English in next startup!\nDo you want to restart ProjectStudio?")
            wx.GetApp().SetLanguageId(wx.LANGUAGE_ENGLISH)
            if ret:
                self.Close()

        if id == ID_LANG_CHINESE and wx.GetApp().GetLanguageId() != wx.LANGUAGE_CHINESE_SIMPLIFIED:
            ret = ps_error.notifyConfirm(_("Change Language"), "Language is changed to Chinese in next startup!\nDo you want to restart ProjectStudio?")
            wx.GetApp().SetLanguageId(wx.LANGUAGE_CHINESE_SIMPLIFIED)
            if ret:
                self.Close()
            

        if id == ID_LANG_JAPANESE and wx.GetApp().GetLanguageId() != wx.LANGUAGE_JAPANESE:
            ret = ps_error.notifyConfirm(_("Change Language"), "Language is changed to Chinese in next startup!\nDo you want to restart ProjectStudio?")
            wx.GetApp().SetLanguageId(wx.LANGUAGE_JAPANESE)
            if ret:
                self.Close()
        
    def OnMenuQuit(self, event):
        self.Close()
       
    def OnSizing(self, event):
        """Event handler for wx.EVT_SIZING.
        
        Hold the size of changing but not write to configure file directly due to performance consideration.
        """
        if not self.IsMaximized():
            self._savedPos  = (event.Rect[0], event.Rect[1])
            self._savedSize = (event.Rect[2], event.Rect[3])
        
    def OnRestoreLayout(self, event):
        self.EnterBackgroundScene(self.GetCurrentBackgroundSceneName(), True)
    
    def OnSwitchWindow(self, event):
        items = PSSwitcherItems()
        items.AddGroup(_("Working Views"), "docviews")
        
        
        # list working views
        for pane in self._mgr.GetAllPanes():
            if pane.dock_direction == auiex.AUI_DOCK_CENTER:
                childframe = pane.window
                for j in xrange(childframe.GetPageCount()):
                    viewframe = childframe.GetPage(j)
                    win = childframe.GetPage(j)
                    items.AddItem(viewframe.GetDescription(), viewframe.GetDescription(), j, childframe.GetPageBitmap(j)).SetWindow(win)
        
        # list single views
        items.AddGroup(_("Single Views"), "singleviews")
        for pane in self._mgr.GetAllPanes():        
            if not pane.IsShown():
                continue
            if pane.dock_direction == auiex.AUI_DOCK_CENTER:
                continue
            
            if pane.IsNotebookControl():
                notebook = pane.window
                for j in xrange(notebook.GetPageCount()):
                    name = notebook.GetPageText(j)
                    win  = notebook.GetPage(j)
                    items.AddItem(name, name, j, notebook.GetPageBitmap(j)).SetWindow(win)
            elif pane.IsNotebookPage():
                continue
            elif isinstance(pane.window, PSSingleViewFrame):
                items.AddItem(pane.caption, pane.name, -1, pane.window.GetViewBitmap()).SetWindow(pane.window)
                 
        dlg = PSSwitcherDialog(items, self, self._mgr)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK and dlg.GetSelection() != -1:
            item = items.GetItem(dlg.GetSelection())

            if item.GetId() == -1:
                info = self._mgr.GetPane(item.GetName())
                info.Show()
                self._mgr.Update()
                info.window.SetFocus()
            else:
                nb = item.GetWindow().GetParent()
                win = item.GetWindow()
                if isinstance(nb, auiex.AuiNotebook):
                    nb.SetSelection(item.GetId())
                    win.SetFocus()            
    
    def OnUpdateLanguageMenu(self, event):
        """Update the language item's checking status."""
        id = event.GetId()
        langMenu = event.GetEventObject()
        curlangid = wx.GetApp().GetLanguageId()
        if (id == ID_LANG_ENGLISH and curlangid == wx.LANGUAGE_ENGLISH) or \
           (id == ID_LANG_CHINESE and curlangid == wx.LANGUAGE_CHINESE_SIMPLIFIED) or \
           (id == ID_LANG_JAPANESE and curlangid == wx.LANGUAGE_JAPANESE): 
            event.Check(True)
        else:
            event.Check(False)
                
    def OnUpdateViewMenu(self, event):
        """wx.EVT_UPDATE_UI event callback for menu of view list."""
        menu = event.GetEventObject()
        viewid = menu.FindItem(event.GetId())._view_id
        for pane in self._mgr.GetAllPanes():
            win = pane.window
            if win.GetId() == viewid:
                if pane.IsShown():
                    event.Check(True)
                else:
                    event.Check(False)
                return
    
    def OnViewMenu(self, event):
        item = event.GetEventObject().FindItem(event.GetId())
        viewid = item._view_id
        for pane in self._mgr.GetAllPanes():
            if pane.window.GetId() == viewid:
                win = pane.window
                if pane.IsShown():
                    if isinstance(pane.window.GetParent(), auiex.AuiNotebook):
                        notebook = pane.window.GetParent()
                        for index in xrange(notebook.GetPageCount()):
                            page = notebook.GetPage(index)
                            if page == pane.window:
                                notebook.SetSelection(index)
                                break
                    else:
                        pane.window.SetFocus()
                else:
                    pane.Float()
                    self._mgr.ShowPane(pane.window, True)
               
    def OnClickMenuNew(self, event):
        item = event.GetEventObject().FindItem(event.GetId())
        wx.GetApp().GetDocManager().CreateDocument(None, item.GetLabel())

    def ReConstructNewMenu(self):
        newMenuItem = self.GetMenuBar().FindMenuItem(ID_MENU_FILE_NEW)
        newSubMenu  = newMenuItem.GetSubMenu()
        if newSubMenu != None:
            # if submenu exist already, clear all existing items.
            newSubMenu.Clear()
        else:
            # if submenu does not exist, create a new submenu.
            newSubMenu = ps_menu.PSMenu()
            newMenuItem.SetSubMenu(newSubMenu)
            
        providers   = wx.GetApp().GetDocManager().GetProviders()

        for provider in providers.values():
            if provider.IsReadOnly():
                continue
            if not provider.IsActive(self.GetCurrentBackgroundSceneName()):
                continue
            
            menuItem = ps_menu.PSMenuItem(newSubMenu, -1, provider.GetName(), provider.GetDescription(),
                                          wx.ITEM_NORMAL, normalBmp=provider.GetBitmap())
            self.Bind(wx.EVT_MENU, self.OnClickMenuNew, id=menuItem.GetId())
            newSubMenu.AppendItem(menuItem)
                                
    def ResetMenuBar(self):
        """Reset menus in menu bar.
        
        The menu whose name in self._genericMenus will be kept and others will be destroyed.
        """
        menubar = self.GetMenuBar()
        for title in menubar.GetMenuTitles():
            menuIndex = menubar.FindMenu(title)
            if menuIndex != wx.NOT_FOUND:
                menuObj = menubar.Remove(menuIndex)
                del menuObj
        menubar.Refresh()
        
    def ResetToolBar(self):
        """Reset all tool bars.
        
        Only tool bar in "general" name will be kept.
        """
        for barname in self._toolbars.keys():
            if barname != TOOLBAR_NAME_GENERAL:
                barObj = self._toolbars[barname]
                del self._toolbars[barname]
                del barObj
                
    def _CreateChildFrame(self):
        nb    = ps_childframe.PSChildFrame(self, self.ID_FRAME_DOC_NOTEBOOK)
        self._mgr.AddPane(nb, nb.GetPaneInfo())
        return nb

    def _CreateMenuBar(self):
        menubar = ps_menu.PSMenuBar(self)
        self._mgr.AddPane(menubar, menubar.GetPaneInfo())
        return menubar
       
    def _CreateNewSubMenu(self):
        newSubMenu = ps_menu.PSMenu()
        
        providers   = wx.GetApp().GetDocManager().GetProviders()

        for provider in providers.values():
            if provider.IsReadOnly():
                continue
            if not provider.IsActive(self.GetCurrentBackgroundSceneName()):
                continue
            
            menuItem = ps_menu.PSMenuItem(newSubMenu, -1, provider.GetName(), provider.GetDescription(),
                                          wx.ITEM_NORMAL, normalBmp=provider.GetBitmap())
            self.Bind(wx.EVT_MENU, self.OnClickMenuNew, id=menuItem.GetId())
            newSubMenu.AppendItem(menuItem)
            
        return newSubMenu
    
    def _GetSavedPosSize(self):
        """
        Get pos and size information from configure file to initialize the main frame
        """
        defaultwidth  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        defaultheight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        x             = self._config.Get(_MAINFRAME_SETTING_X,      defaultwidth / 6)
        y             = self._config.Get(_MAINFRAME_SETTING_Y,      defaultheight / 6)
        width         = self._config.Get(_MAINFRAME_SETTING_WIDTH,  defaultwidth * 2 / 3)
        height        = self._config.Get(_MAINFRAME_SETTING_HEIGHT, defaultheight * 2 / 3)
        return (x, y), (width, height)
    

    def _CreateLanguageSubMenu(self):
        langSubMenu = ps_menu.PSMenu()
        item = langSubMenu.Append(ID_LANG_ENGLISH,  _("English"), _("English"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnLanguageChanged, id=ID_LANG_ENGLISH)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateLanguageMenu, id=ID_LANG_ENGLISH)

        item = langSubMenu.Append(ID_LANG_CHINESE,  _("Chinese"), "Chinese", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnLanguageChanged, id=ID_LANG_CHINESE)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateLanguageMenu, id=ID_LANG_CHINESE)

        item = langSubMenu.Append(ID_LANG_JAPANESE, _("Japanese"), "Japanese", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnLanguageChanged, id=ID_LANG_JAPANESE)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateLanguageMenu, id=ID_LANG_JAPANESE)

        return langSubMenu
    
    def _AddSingleViewMenu(self, view):
        viewMenuItem = self.GetMenuBar().FindMenuItem(ID_MENU_WINDOW_VIEWS)
        
        viewMenu = viewMenuItem.GetSubMenu()
        item = ps_menu.PSMenuItem(viewMenu, -1, _(view.GetName()), view.GetName(), wx.ITEM_CHECK,
                                  normalBmp=view.GetViewBitmap())
        item._view_id = view.GetId()
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateViewMenu, id=item.GetId())
        self.Bind(wx.EVT_MENU, self.OnViewMenu, id=item.GetId())
        viewMenu.AppendItem(item)
        
    def _InstallGenericMenu(self):
        # Create file menu
        filemenu = ps_menu.PSMenu()
        # The submenu of new menu is construct when background/foreground's scene is switched
        item = ps_menu.PSMenuItem(filemenu, ID_MENU_FILE_NEW, _("&New"), "New", wx.ITEM_NORMAL, 
                                  normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_NEW, size=(16, 16)))
        filemenu.AppendItem(item)
        item = ps_menu.PSMenuItem(filemenu, ID_MENU_FILE_OPEN, _("&Open") + "...\tCtrl+O", "Open", wx.ITEM_NORMAL, 
                                  normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_OPEN, size=(16, 16)))
        filemenu.AppendItem(item)
        
        filemenu.AppendSeparator()

        item = ps_menu.PSMenuItem(filemenu, ID_MENU_FILE_SAVE, _("&Save") + "\tCtrl+S", "Save", wx.ITEM_NORMAL, 
                               normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_SAVE, size=(16, 16)))
        filemenu.AppendItem(item)
        item = ps_menu.PSMenuItem(filemenu, ID_MENU_FILE_SAVE_AS, _("Save As"), "Save As", wx.ITEM_NORMAL) 
        filemenu.AppendItem(item)
        item = ps_menu.PSMenuItem(filemenu, ID_MENU_FILE_SAVEALL, _("Save All"), "Save All", wx.ITEM_NORMAL,
                                  normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_SAVEALL, size=(16, 16)))
        filemenu.AppendItem(item)
        
        item = ps_menu.PSMenuItem(filemenu, ID_MENU_LASTEST_OPEN, _("Latest Opened"), "The documents opened lastest", wx.ITEM_NORMAL)
        filemenu.AppendItem(item)
        
        filemenu.AppendSeparator()
        item = ps_menu.PSMenuItem(filemenu, -1, _("&Quit") + "\tAlt+F4", "Quit", wx.ITEM_NORMAL,\
                               normalBmp=wx.ArtProvider.GetBitmap(wx.ART_QUIT, size=(16, 16)))
        self.Bind(wx.EVT_MENU, self.OnMenuQuit, id=item.GetId())
        filemenu.AppendItem(item)
        
        editmenu = ps_menu.PSMenu()
        item = editmenu.Append(interfaces.event.ID_FOCUS_UNDO, _("&Undo") + "\tCtrl+Z", "Undo last action", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(wx.ART_UNDO, size=(16, 16)))
        wx.EVT_UPDATE_UI(self, interfaces.event.ID_FOCUS_UNDO, self.OnEditMenuUpdateUI)
        wx.EVT_MENU(self, interfaces.event.ID_FOCUS_UNDO, self.OnEditMenuCommand)
        
        item = editmenu.Append(interfaces.event.ID_FOCUS_REDO, _("&Redo") + "\tCtrl+Y", "Redo last action", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(wx.ART_REDO, size=(16, 16)))
        wx.EVT_UPDATE_UI(self, interfaces.event.ID_FOCUS_REDO, self.OnEditMenuUpdateUI)
        wx.EVT_MENU(self, interfaces.event.ID_FOCUS_REDO, self.OnEditMenuCommand)
        
        editmenu.AppendSeparator()
        item = editmenu.Append(interfaces.event.ID_FOCUS_COPY, _("Copy") + "\tCtrl+C", "Copy", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(wx.ART_COPY, size=(16, 16)))
        wx.EVT_UPDATE_UI(self, interfaces.event.ID_FOCUS_COPY, self.OnEditMenuUpdateUI)
        wx.EVT_MENU(self, interfaces.event.ID_FOCUS_COPY, self.OnEditMenuCommand)
        
        item = editmenu.Append(interfaces.event.ID_FOCUS_CUT, _("Cut") + "\tCtrl+X", "Cut", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(wx.ART_CUT, size=(16, 16)))
        wx.EVT_UPDATE_UI(self, interfaces.event.ID_FOCUS_CUT, self.OnEditMenuUpdateUI)
        wx.EVT_MENU(self, interfaces.event.ID_FOCUS_CUT, self.OnEditMenuCommand)
        
        item = editmenu.Append(interfaces.event.ID_FOCUS_PASTE, _("Paste") + "\tCtrl+V", "Cut", wx.ITEM_NORMAL)
        item.SetNormalBitmap(wx.ArtProvider_GetBitmap(wx.ART_PASTE, size=(16, 16)))
        wx.EVT_UPDATE_UI(self, interfaces.event.ID_FOCUS_PASTE, self.OnEditMenuUpdateUI)
        wx.EVT_MENU(self, interfaces.event.ID_FOCUS_PASTE, self.OnEditMenuCommand)
        
        # Create window menu
        winmenu = ps_menu.PSMenu()
        item    = ps_menu.PSMenuItem(winmenu, -1, _("Language"), _("Select language"), wx.ITEM_NORMAL)
        item.SetSubMenu(self._CreateLanguageSubMenu())
        winmenu.AppendItem(item)

        # View's submenu will be created after all plugins is started.
        item = ps_menu.PSMenuItem(winmenu, ID_MENU_WINDOW_VIEWS, _("Views"), "Single views", wx.ITEM_NORMAL,
                                  normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_SINGLE_VIEW_LIST, size=(16, 16)))
        item.SetSubMenu(ps_menu.PSMenu())
        winmenu.AppendItem(item)
        
        item    = ps_menu.PSMenuItem(winmenu, -1, _("Restore Layout"), "Restore current layout for current scene", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.OnRestoreLayout, id=item.GetId())
        winmenu.AppendItem(item)
        
        item    = ps_menu.PSMenuItem(winmenu, -1, _("Switch Window") + "\tCtrl+Tab", "Switch", wx.ITEM_NORMAL,
                                     normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_SWITCHER_WINDOW, size=(16, 16)))
        self.Bind(wx.EVT_MENU, self.OnSwitchWindow, id=item.GetId())
        winmenu.AppendItem(item)
        
        # Create help menu
        helpmenu = ps_menu.PSMenu()
        item     = ps_menu.PSMenuItem(helpmenu, -1, _("About") + " ProjectStudio", "About", wx.ITEM_NORMAL, \
                                  normalBmp=wx.ArtProvider.GetBitmap(ps_art.PS_ART_HELP, size=(16, 16)))
        helpmenu.AppendItem(item)
        
        self.InstallMenu(_(MENU_TITLE_FILE), filemenu)
        self.InstallMenu(_(MENU_TITLE_EDIT), editmenu)
        self.InstallMenu(_(MENU_TITLE_WINDOW), winmenu)
        self.InstallMenu(_(MENU_TITLE_HELP), helpmenu)
        #self.GetMenuBar().Append(filemenu, _(MENU_TITLE_FILE))
        #self.GetMenuBar().Append(editmenu, _(MENU_TITLE_EDIT))
        #self.GetMenuBar().Append(winmenu,  _(MENU_TITLE_WINDOW))
        #self.GetMenuBar().Append(helpmenu, _(MENU_TITLE_HELP))
        
    def _InstallGenericToolBar(self):
        toolbar = auiex.PSToolbar(self, -1, style=auiex.AUI_TB_OVERFLOW)
        toolbar.SetToolBorderPadding(2)
        toolbar.SetToolSeparation(2)
        bitmapsize = wx.Size(16, 16)
        toolbar.SetToolBitmapSize(bitmapsize)
        
        toolbar.AddSimpleTool(ID_MENU_FILE_NEW, "New", wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_NEW, size=bitmapsize))
        toolbar.SetToolDropDown(ID_MENU_FILE_NEW, True)
        self.Bind(auiex.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnDropDownToolNew, id=ID_MENU_FILE_NEW)
        
        toolbar.AddSimpleTool(ID_MENU_FILE_OPEN, "Open", wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_OPEN, size=bitmapsize))
        toolbar.AddSimpleTool(ID_MENU_FILE_SAVE, "Save", wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_SAVE, size=bitmapsize))
        toolbar.AddSimpleTool(ID_MENU_FILE_SAVEALL, "SaveAll", wx.ArtProvider.GetBitmap(ps_art.PS_ART_FILE_SAVEALL, size=bitmapsize))
        toolbar.Realize()
        
        self._mgr.AddPane(toolbar, auiex.AuiPaneInfo().Name(TOOLBAR_NAME_GENERAL).ToolbarPane().Top().Row(1))
        self._toolbars[TOOLBAR_NAME_GENERAL] = toolbar
    
    def _SavePosSize(self):
        """
        Save the pos and size information to configure file when main frame is closing.
        """
        if not self.IsMaximized():
            self._config.Set(_MAINFRAME_SETTING_X,      self._savedPos[0])
            self._config.Set(_MAINFRAME_SETTING_Y,      self._savedPos[1])
            self._config.Set(_MAINFRAME_SETTING_WIDTH,  self._savedSize[0])
            self._config.Set(_MAINFRAME_SETTING_HEIGHT, self._savedSize[1])
            self._config.Set(_MAINFRAME_SETTING_ISMAX,  False)
        else:
            self._config.Set(_MAINFRAME_SETTING_ISMAX,  True)
            
import lib.aui.aui_switcherdialog
class PSSwitcherItems(lib.aui.aui_switcherdialog.SwitcherItems):
    pass

class PSSwitcherDialog(lib.aui.aui_switcherdialog.SwitcherDialog):
    pass

import wx.lib.agw.genericmessagedialog as gmd
class ConfirmDialog(gmd.GenericMessageDialog):
    def __init__(self, message, caption, style, setting=None):
        gmd.GenericMessageDialog.__init__(self, wx.GetApp().GetMainFrame(), message, caption, style)
        
        if setting != None:
            self._setting = setting
            oldsize = self.GetSize()
            self.SetSize((oldsize[0], oldsize[1] + 26))
            sizer = self.GetSizer()
            self._checkbox = wx.CheckBox(self, -1, "Do not prompt this reminder in future?")
            sizer.Add(self._checkbox, 0, wx.LEFT|wx.BOTTOM, 10)
            wx.EVT_CHECKBOX(self, self._checkbox.GetId(), self.OnCheckBox)
        
    def OnCheckBox(self, event):
        if event.IsChecked():
            wx.GetApp().GetConfig("PromptConfirmDialog").Set(self._setting, False)
        else:
            wx.GetApp().GetConfig("PromptConfirmDialog").Set(self._setting, True)