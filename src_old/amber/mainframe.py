""" This module provide main frame class.

    Main frame also manage all views, There are following view types:
    1) doc view: 
        This type view is shown in editor center's tab windows. It is take
        responsible to display/manage a document's content.
        It is same as original MFC's doc-view framework.
        
    2) side view:
        The side view maybe exist in left/top/bottom/right tab windows. It 
        is associated with a functionality's output/input. side window will
        not block main doc-view's work.
         
    3) popup view:
        A popup view is like a model windows, it is also associated with
        a funcitonality's output/input as side view. The only difference
        with side view, popup view will be displayed front above all other views.

    Amber Editor support multi-layer windows layout, which is also managed by
    main frame. It based on wx.AUI manager.
     
    Copyright (C) 2008 ~ 2012. All Rights Reserved.
    The contents of this file are subject to the Mozilla Public License
    Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS"
    basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
    License for the specific language governing rights and limitations
    under the License.

    Initial Developer: Lu Ken <bluewish.ken.lu@gmail.com>
"""   

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__revision__ = "$Revision: 1 $"

#======================================  External Libraries ========================================
import wx
import wx.aui
import auiex
import os
import wx.lib.flatnotebook as FNB

#======================================  Internal Libraries ========================================
import image
import wx.lib.agw.toasterbox as TB
import app
import art

#============================================== Code ===============================================
ID_MENU_WINDOW_SHOW_VIEWS = wx.NewId()

_general_menu = [('&File', [('New', wx.ID_NEW, 'New', None), 
                           ('Open\tCtrl+O', wx.ID_OPEN, 'Open File', wx.ART_FILE_OPEN), 
                           ('Close', wx.ID_CLOSE, 'Close', None),
                           ('Close All', wx.ID_CLOSE_ALL, 'Close All', None),
                           '-',
                           ('Save\tCtrl+S', wx.ID_SAVE, 'Save', wx.ART_FILE_SAVE),
                           ('Save As', wx.ID_SAVEAS, 'Save As', wx.ART_FILE_SAVE_AS),
                           '-',
                           ('&Exit\tAlt+F4', wx.ID_EXIT, 'Exit', wx.ART_QUIT)]),
                 ('&Window', ),
                 ('&Help', [('About', wx.ID_ABOUT, 'About Amber Editor', wx.ART_HELP)])
                 ]

_=wx.GetTranslation

class AmberEditorFrameDockArt (wx.aui.PyAuiDockArt):
    pass
    #def DrawBorder(*args, **kwargs):
    #    print 'draw border'
    #def DrawGripper(*args, **kwargs):
    #    print 'DrawGripper'
        
class AmberEditorFrame(wx.Frame):
    """Main frame class for Amber Editor.
    
    It use wx.AuiManager to manager all side window and document windows.
    """
    def __init__(self, parent):
        """Constructor function for AmberEditorFrame."""
        wx.Frame.__init__(self, parent)

        # set application as default mainframe's title
        self.SetTitle(wx.GetApp().GetAppName())
        self.SetIcon(wx.ArtProvider_GetIcon(art.ART_AMBER_APP_ICON, size=(16, 16)))

       
        # main frame is managed by AuiManager
        self._auiMgr = auiex.AuiExManager(self)
        auiArt = AmberEditorFrameDockArt()
        print auiArt.GetFont(0)
        #self._auiMgr.SetArtProvider(auiArt)
        
        self._SetAuiManagerFlags()
        
        # initialization works should be taken firstly.
        self._InitializeMenuBar()
        statusbar = AmberEditorStatusBar(self)
        self.SetStatusBar(statusbar)
        self.SetStatusBarPane(statusbar.STATUSBAR_GENERAL_MESSAGE_INDEX)
        self._InitializeToolBar()
        
        # restore main frame's size and position as last opened
        self._RestoreMainFrameSize()
        self._auiMgr.Update()
        
        self._sideviews         = []
        self._menuViewMapping   = {}
        
        # welcome to amber editor
        self.PlayTextToasterBox(_('Welcome to Amber Editor! Current version is %s' % app.APP_VERSION))
        
        # event mapping for main frame
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        # Load perspective? how to create real pane?
        #self._auiMgr.LoadPerspective(wx.GetApp().ConfigRead('MainFramePerspective', ''))
        nb = wx.aui.AuiNotebook(self, -1)
        nb.AddPage(wx.TextCtrl(self, -1), '22')
        self._auiMgr.AddPane(nb, wx.aui.AuiPaneInfo().Name('document').CenterPane())
        self._auiMgr.Update()
        
        self._count = 0
        
    # ====================================   Event Handling =======================================
    def OnFileExit(self, event):
        """Callback function for wx.ID_EXIT menu. """
        #
        # Uninitializes the framework and should be called before a managed frame or window 
        # is destroyed. UnInit() is usually called in the managed wxFrame's destructor. It is 
        # necessary to call this function before the managed frame or window is destroyed, 
        # otherwise the manager cannot remove its custom event handlers from a window.
        #        
        perspective = self._auiMgr.SavePerspective()
        wx.GetApp().ConfigWrite('MainFramePerspective', perspective)
        self._auiMgr.UnInit()
        self.Close()
        
    def OnFileNew(self, event):
        #win = wx.GenericDirCtrl(self, -1)
        win = wx.TextCtrl(self, -1)
        self._count += 1
        if self._count != 2:
            #self.AddSideView(win, 'bottom')
            #self._auiMgr.AddPane(win, wx.aui.AuiPaneInfo().Float(), 'test float')
            self._auiMgr.AddPane(win, wx.aui.AuiPaneInfo().Dockable(True).Bottom().\
                                 Caption("test")) 
            self._auiMgr.Update()           
        else:
            self._auiMgr.AddPane(win, wx.aui.AuiPaneInfo().Float(), 'test float')
            self._auiMgr.Update()
        
    def OnMenuShowViews(self, event):
        """Callback for wx.EVT_MENU for menu Window->Show Views."""
        view = self._menuViewMapping[event.GetId()]
        self.ActiveSideView(view)
        
    def OnMouseEvents(self, event):
        """Active document pane"""
        pass
        
    def OnMove(self, event):
        """Callback function for wx.EVT_MOVE event.
        
        Once window is moved to new position, it should be saved for next open.
        """
        pos  = self.GetPosition()
        wx.GetApp().ConfigWriteInt('MainFrameX', pos.x)
        wx.GetApp().ConfigWriteInt('MainFrameY', pos.y)
        
    def OnSize(self, event):
        """Callback function for wx.EVT_SIZE event.
        
        Once size is changed of main frame, all size and aui pane information should be 
        saved to user profile.
        """
        size = self.GetSize()
        pos  = self.GetPosition()
        if not self.IsMaximized():
            wx.GetApp().ConfigWriteInt('MainFrameWidth', size.width)
            wx.GetApp().ConfigWriteInt('MainFrameHeight', size.height)
            wx.GetApp().ConfigWriteInt('MainFrameX', pos.x)
            wx.GetApp().ConfigWriteInt('MainFrameY', pos.y)
            wx.GetApp().ConfigWriteInt('MainFrameIsMaximized', 0)
        else:
            wx.GetApp().ConfigWriteInt('MainFrameIsMaximized', 1)
        
    # ====================================   layer window management interface =======================================
    def ActiveSideView(self, view):
        """ Active a given side view. """
        pane = self.GetSidePaneByView(view)
        if pane == None:
            wx.GetApp().GetLogger().error("Fail to active side view %s" % view.GetLabel())
            return
        if not pane.IsShown():
            pane.Show()
            self._auiMgr.Update()
        nb = pane.window
        for index in range(nb.GetPageCount()):
            page = nb.GetPage(index)
            if page == view: 
                nb.SetSelection(index)
                
    def AddSideView(self, win, position='bottom', layer=0, pos=0, row=0):
        """ Add a side window to main frame
        
        @param win          side window 
        @param position     position string in ['left', 'right', 'bottom', 'top']
        """
        if self.GetSidePaneByView(win) != None:
            return
        dirMap = {'left':4, 'right':2, 'top':1, 'bottom':3}
        assert position.lower() in dirMap.keys(), 'Fatal Error: Wrong side window position!'
        panes = self._auiMgr.GetAllPanes()
        foundPanes = []
        for pane in panes:
            if pane.dock_direction == dirMap[position] and pane.dock_layer == layer and \
               pane.dock_row == row and pane.dock_pos == pos:
                foundPanes.append(pane)
        assert len(foundPanes) <= 1, 'Fatal Error: Found two different panes in position %s' % position
        if len(foundPanes) == 0:
            nb = AmberEditorSideViewNoteBook(self, -1, style=FNB.FNB_BACKGROUND_GRADIENT|FNB.FNB_BOTTOM|FNB.FNB_X_ON_TAB|\
                                                             FNB.FNB_HIDE_ON_SINGLE_TAB|FNB.FNB_NO_X_BUTTON|FNB.FNB_DROPDOWN_TABS_LIST|\
                                                             FNB.FNB_NO_NAV_BUTTONS|FNB.FNB_ALLOW_FOREIGN_DND)
            nb.AddPage(win, win.GetLabel())
            framesize = self.GetSize()
            if position in ['left', 'right']:
                minsize = (framesize.width/6, framesize.height/4)
                maxsize = (framesize.width/3, framesize.height/2)
            else:
                minsize = (framesize.width/4, framesize.height/6)
                maxsize = (framesize.width/2, framesize.height/3)
            self._auiMgr.AddPane(nb, wx.aui.AuiPaneInfo().Dockable(True).Direction(dirMap[position]).\
                                 Caption(win.GetLabel()).MinSize(minsize).MaxSize(maxsize).\
                                 FloatingSize(maxsize).DestroyOnClose(False).MaximizeButton(True))
        else:
            nb = foundPanes[0].window
            nb.AddPage(win, win.GetLabel())
            foundPanes[0].Show()
        
        self._auiMgr.Update()
        if win not in self._sideviews:
            self._sideviews.append(win)
            viewsMenu = self.GetMenuBar().FindItemById(ID_MENU_WINDOW_SHOW_VIEWS)
            item = viewsMenu.GetSubMenu().Append(-1, win.GetName())
            wx.EVT_MENU(self, item.GetId(), self.OnMenuShowViews)
            self._menuViewMapping[item.GetId()] = win
            
    def GetSidePaneByView(self, view):
        """ Get side pane info for given side view. """
        panes     = self._auiMgr.GetAllPanes()
        for pane in panes:
            if pane.IsToolbar() or pane.name == 'document': continue
            nb = pane.window
            assert issubclass(nb.__class__, FNB.FlatNotebook), "Fatal Error: Side pane should be FlatNotebook class"
            for index in range(nb.GetPageCount()):
                page = nb.GetPage(index)
                if page == view:
                    return pane
        return None
            
    def GetSideViews(self):
        """ Get all side windows belong to given layer. """
        return self._sideviews
    
    def RemoveSideView(self, win):
        """ Remove a side window belong to given layer.
        
        @param  win      side window object
        """
        # find the side view's pane
        panes     = self._auiMgr.GetAllPanes()
        for pane in panes:
            nb = pane.window
            assert issubclass(nb.__class__, FNB.FlatNotebook), "Fatal Error: Side pane should be FlatNotebook class"
            for index in range(nb.GetPageCount()):
                page = nb.GetPage(index)
                if page == win:
                    nb.RemovePage(index)
                    self._auiMgr.Update()
                    return True
                
        wx.GetApp().GetLogger().error('Fail to find the side view in all panes!')
        return False

    # ====================================   document tab window management interface =======================================    
        
    # ====================================   toaster box management  interface =======================================
    def PlayTextToasterBox(self, text, size=None):
        """ Play a simple toaster box with text message. 
        @param  text     message in toaster box
        @param  size     toaster box's size
        """
        tb = TB.ToasterBox(self, TB.TB_SIMPLE, TB.DEFAULT_TB_STYLE, TB.TB_ONTIME|TB.TB_ONCLICK)
        tb.SetPopupText(text)
        self.PlayToasterBox(tb, size)
        
    def PlayToasterBox(self, tb, size=None):
        """ Play a toaster box.
        @param tb     toaster box object maybe contains text or complex controls.
        @param size   the size of toaster box
        """
        screenWidth  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        #tb.SetPopupBitmap(image.getToasterBoxbackgroundBitmap())        
        if size == None:
            size = (200, 100)
        tb.SetPopupSize(size)
        tb.SetPopupPosition((screenWidth - size[0] - 5, screenHeight - size[1] - 10))
        tb.SetPopupPauseTime(500)
        tb.Play()
        
    # ====================================   Internal Methods =======================================
    def _CreateSideNoteBook(self, layer=0):
        """ Internal function to create notebook control for a side window. It is called when AddSideWindow and 
            that side has not been initialized.
        """
        
    def _InitializeMenuBar(self):
        """ Install menu bar and add general menu. """
        menubar = wx.MenuBar()
        
        # Install all general menu items used by document manager, editor, service.
        for menudata in _general_menu:
            menu = wx.Menu()
            menubar.Append(menu, menudata[0])
            if len(menudata) == 1:
                continue
            for itemdata in menudata[1]:
                if itemdata == '-':
                    menu.AppendSeparator()
                else:
                    if len(itemdata) <= 3 or itemdata[3] == None:
                        menu.Append(itemdata[1], itemdata[0], itemdata[2])
                    else:
                        menuitem = wx.MenuItem(menu, itemdata[1], itemdata[0], itemdata[2])
                        menuitem.SetBitmap(wx.ArtProvider_GetBitmap(itemdata[3], wx.ART_MENU))
                        menu.AppendItem(menuitem)
                        
        # set menu bar to frame object
        self.SetMenuBar(menubar)
        
        winmenu = menubar.GetMenu(menubar.FindMenu('&Window'))
        viewmenu = wx.Menu()
        winmenu.AppendMenu(ID_MENU_WINDOW_SHOW_VIEWS, "Show Views", viewmenu)
        
        
        # Binding menu event
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnFileExit)
        wx.EVT_MENU(self, wx.ID_NEW, self.OnFileNew)
        
    def _InitializeToolBar(self):
        """ Initialize tool bars manager.
        
            1, main frame manage more than one tool bar.
            2, a general tool bar will created for general menu.  
        """
        toolbar = wx.ToolBar(self, -1,  wx.DefaultPosition, wx.DefaultSize, wx.TB_FLAT | wx.TB_NODIVIDER)
        toolbar.SetToolBitmapSize(wx.Size(16, 16))
        toolbar.AddLabelTool(wx.ID_NEW,  'New',  wx.ArtProvider_GetBitmap(wx.ART_NEW, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_OPEN, 'Open', wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_SAVE, 'Save', wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, size=(16, 16)))
        toolbar.AddSeparator()
        toolbar.AddLabelTool(wx.ID_CUT,  'Cut',  wx.ArtProvider_GetBitmap(wx.ART_CUT, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_COPY, 'Copy', wx.ArtProvider_GetBitmap(wx.ART_COPY, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_PASTE, 'Paste', wx.ArtProvider_GetBitmap(wx.ART_PASTE, size=(16, 16)))
        toolbar.AddSeparator()
        toolbar.AddLabelTool(wx.ID_UNDO,     'Undo', wx.ArtProvider_GetBitmap(wx.ART_UNDO, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_REDO,     'Redo', wx.ArtProvider_GetBitmap(wx.ART_REDO, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_BACKWARD, 'Back', wx.ArtProvider_GetBitmap(wx.ART_GO_BACK, size=(16, 16)))
        toolbar.AddLabelTool(wx.ID_FORWARD,  'Forward', wx.ArtProvider_GetBitmap(wx.ART_GO_FORWARD, size=(16, 16)))
        
        toolbar.Realize()
        self._auiMgr.AddPane(toolbar, wx.aui.AuiPaneInfo().ToolbarPane().Top().
                             Row(1).Name('General').LeftDockable(False).RightDockable(False))
        
    def _RestoreMainFrameSize(self):
        screenWidth  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)        
        isMaximized  = wx.GetApp().ConfigReadInt('MainFrameIsMaximized', 0)
        width        = wx.GetApp().ConfigReadInt('MainFrameWidth',  screenWidth/2)
        height       = wx.GetApp().ConfigReadInt('MainFrameHeight', screenHeight/2)
        x            = wx.GetApp().ConfigReadInt('MainFrameX', screenWidth/4)
        y            = wx.GetApp().ConfigReadInt('MainFrameY', screenHeight/4)
        self.SetPosition((x,y))
        self.SetSize((width, height))
        self.Maximize((isMaximized == 1))
    
    def _SetAuiManagerFlags(self):
        flags = self._auiMgr.GetFlags()
        flags &= ~wx.aui.AUI_MGR_TRANSPARENT_HINT
        flags &= ~wx.aui.AUI_MGR_VENETIAN_BLINDS_HINT
        flags &= ~wx.aui.AUI_MGR_RECTANGLE_HINT
        
        flags ^= wx.aui.AUI_MGR_RECTANGLE_HINT
        self._auiMgr.SetFlags(flags)     
           
class TestSideWindow(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnClose(self, event):
        print 'close'

class AmberEditorSideViewNoteBook(FNB.FlatNotebook):
    def DeletePage(self, page):
        """Override the DeletePage interface for FlatNotebook, Amber will do view destroy for all side view.""" 
        self.RemovePage(page)
        
class AmberEditorStatusBar(wx.StatusBar):
    """ Amber Editor's status bar contains following area:
    
        1, side window navigator which display a list for all available side windows.
        2, general information area.
        3, editor information.
        4, active task progress information area.
        5, active task progress bar 
    
    """
    
    STATUSBAR_VIEW_BUTTON_INDEX       = 0
    STATUSBAR_GENERAL_MESSAGE_INDEX   = 1
    STATUSBAR_DOC_INSET_INDEX         = 2
    STATUSBAR_DOC_LINE_INDEX          = 3
    STATUSBAR_DOC_COL_INDEX           = 4
    STATUSBAR_TASK_GAUGE_INDEX        = 5
    STATUSBAR_TASK_TEXT_INDEX         = 6
    STATUSBAR_MAX_INDEX               = 7         
    
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, style=0)    # style should be 0, wxST_SIZEGRIP is not good enough
        
        
        # initialize the field areas and size
        self.SetFieldsCount(self.STATUSBAR_MAX_INDEX)
        self.SetStatusStyles([wx.SB_FLAT, wx.SB_FLAT, wx.SB_NORMAL, wx.SB_NORMAL, wx.SB_NORMAL, wx.SB_FLAT, wx.SB_NORMAL])    
        self.SetStatusWidths([20, -1, 40, 30, 30, 80, 150])
        #self.SetMinHeight(30)

        # create task gauge control
        rect  = self.GetFieldRect(self.STATUSBAR_TASK_GAUGE_INDEX)
        self._gauge = wx.Gauge(self, -1, 50, pos=(rect.x, rect.y), size=(rect.width, rect.height))

        # create view list button
        rect = self.GetFieldRect(self.STATUSBAR_VIEW_BUTTON_INDEX)
        self._btViewBook = wx.BitmapButton(self, -1, wx.ArtProvider_GetBitmap(art.ART_AMBER_VIEW_SIDE_WINDOW, size=(16, 16)),
                                           pos = (rect.x, rect.y), size=(16, 16))
        self._btViewBook.Bind(wx.EVT_BUTTON, self.OnListSideViews)
        
        # Set default values
        self.SetInsertStatus()

        
        self._isParentClose   = False
        self.Bind(wx.EVT_SIZE, self.OnSize)
        # work around for avoiding size event is triggered after main frame is closed.
        parent.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self._viewMenuMapping = {} 
        
    def OnSize(self, event):
        """ Callback function for event wx.EVT_SIZE
        """
        # work around for avoiding size event is triggered after main frame is closed.
        if self._isParentClose: return 

        # update position and size for task gauge
        rect  = self.GetFieldRect(self.STATUSBAR_TASK_GAUGE_INDEX)
        self._gauge.SetPosition((rect.x, rect.y + 1))
        self._gauge.SetSize((rect.width, rect.height -2))
        
        # update view book buttion size
        rect = self.GetFieldRect(self.STATUSBAR_VIEW_BUTTON_INDEX)
        self._btViewBook.SetPosition((rect.x, rect.y))
        self._btViewBook.SetSize((rect.width, rect.height))
        
    def OnClose(self, event):
        """ Callback function for event wx.EVT_CLOSE
            This callback is used for working around the issue that size event is triggered
            after parent is closed.
        """
        self._isParentClose = True
        event.Skip()
        
    def OnListSideViews(self, event):
        """ Callback function for event wx.EVT_BUTTON """
        # clear all mapping relation ship
        self._viewMenuMapping.clear()
        menu = wx.Menu()
        for view in self.GetParent().GetSideViews():
            menuid = wx.NewId() 
            self._viewMenuMapping[menuid] = view
            menu.Append(menuid, view.GetName())
            wx.EVT_MENU(self.GetParent(), menuid, self.OnMenuSelectSideView)
        self.PopupMenu(menu)
        
    def OnMenuSelectSideView(self, event):
        """ Callback function for event wx.EVT_MENU """
        view = self._viewMenuMapping[event.GetId()]
        frame = wx.GetApp().GetTopWindow()
        if frame.GetSidePaneByView(view) == None:
            frame.AddSideView(view)
        frame.ActiveSideView(view)
        
    def SetInsertStatus(self, bInsert=True):
        if bInsert:
            self.SetStatusText('INS', self.STATUSBAR_DOC_INSET_INDEX)
        else:
            self.SetStatusText('OW', self.STATUSBAR_DOC_INSET_INDEX) 
            
    def SetLineStatus(self, value=0):
        self.SetStatusText('%d' % value, self.STATUSBAR_DOC_LINE_INDEX)
        
    def SetColumnStatus(self, value=0):
        self.SetStatusText('%d' % value, self.STATUSBAR_DOC_COL_INDEX)
        
    def GetLineStatus(self):
        return ord(self.GetStatusText(self.STATUSBAR_DOC_LINE_INDEX))
    
    def GetColumnStatus(self):
        return ord(self.GetStatusText(self.STATUSBAR_DOC_COL_INDEX))
    
    def SetTaskMessage(self, name=''):
        if self._isParentClose: return
        self.SetStatusText(name, self.STATUSBAR_TASK_TEXT_INDEX)
        
    def SetTaskProgress(self, value):
        if self._isParentClose: return
        self._gauge.SetValue(value * self._gauge.GetRange() / 100)   