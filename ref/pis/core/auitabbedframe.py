import wx, wx.lib.pydocview as pydocview
import wx.aui
import wx.lib.flatnotebook as fnb
import string
from core.config import *
import core.art
import core.plugin
import core.images
import version
import images
import libs.ToasterBox as TB

if wx.Platform == '__WXMSW__':
    import _winreg
    
__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__svnid__    = "$Id$"
__revision__ = "$Revision$"

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------

_ = wx.GetTranslation
VIEW_TOOLBAR_ID         = wx.NewId()
VIEW_STATUSBAR_ID       = wx.NewId()
SAVEALL_ID              = wx.NewId()
SIDE_WINDOW_LEFT_ID     = wx.NewId()
SIDE_WINDOW_BOTTOM_ID   = wx.NewId()
SIDE_WINDOW_RIGHT_ID    = wx.NewId()
REGISTER_EXPLORER_ID    = wx.NewId()
UNREGISTER_EXPLORER_ID  = wx.NewId()
CONTACT_ME_ID           = wx.NewId()
VIEW_HEX_ID             = wx.NewId()
SOFT_WRAP_ID            = wx.NewId()
SERVICES_MENU_ID        = wx.NewId()

class AuiDocTabbedParentFrame(wx.Frame):
    """
    This class provide main frame of PIS, it is baseed wx.AUI library and
    implement Doc Parent Frame for pydocview.
    The notepage control in this frame uses wx.lib.flatnotebook library.
    Main frame manages:
    1) menu/toolbar/status bar
    2) left/right/bottom tool windows
    4) dispatch event in top windows level.
    """
    
    def __init__(self, docManager, parent, id, title):
        pos, size = self._GetParentFrameSize()
        wx.Frame.__init__(self, parent, id, title, pos, size, style=wx.DEFAULT_FRAME_STYLE)
        self._logger     = wx.GetApp().GetLogger()
        self._docManager = docManager
        self._art        = wx.GetApp().GetArtProvider()
        self._temp_menu_mapping = {}
        self._inReloading = False

        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        flags = wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE | wx.aui.AUI_MGR_VENETIAN_BLINDS_HINT
        self._mgr.SetFlags(self._mgr.GetFlags() ^ flags)
        self._mgr.GetArtProvider().SetMetric(wx.aui.AUI_DOCKART_GRADIENT_TYPE, wx.aui.AUI_GRADIENT_HORIZONTAL)
        self._mgr.GetArtProvider().SetMetric(wx.aui.AUI_DOCKART_SASH_SIZE, 5)
                    
        # create document notebook
        self._docnb  = self._CreateDocumentNoteBook()
        self._mgr.AddPane(self._docnb, wx.aui.AuiPaneInfo().
                          Name("document").CenterPane())
        self._sidenb = {}
        
        # create left region notebook
        self._sidenb['left'] = self._CreateSideNoteBook('left')
        self._mgr.AddPane(self._sidenb['left'], wx.aui.AuiPaneInfo().
                          Name("left").Left().Layer(0).Position(0).
                          BestSize(wx.Size(200, 100)).MinSize(wx.Size(50,50)).
                          CloseButton(True).MaximizeButton(True))
        #self._mgr.GetPane('left').Show(config.ReadInt('LeftSideShow', True))
        self._mgr.GetPane('left').Show(True)
        self._sidenb['left'].Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnLeftSidePageClosing)
        self._sidenb['left'].SetImageList(wx.ImageList(16, 16))
        
        # create right region notebook
        self._sidenb['right'] = self._CreateSideNoteBook('right')
        self._mgr.AddPane(self._sidenb['right'], wx.aui.AuiPaneInfo().
                          Name("right").Right().Layer(0).Position(0).
                          BestSize(wx.Size(200, 100)).MinSize(wx.Size(50,50)).
                          CloseButton(True).MaximizeButton(True)) 
                          
        #self._mgr.GetPane('right').Show(config.ReadInt('RightSideShow', True))
        self._mgr.GetPane('right').Show(False)
        self._sidenb['right'].Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnRightSidePageClosing)
        self._sidenb['right'].SetImageList(wx.ImageList(16, 16))
        
        # create bottom region notebook
        self._sidenb['bottom'] = self._CreateSideNoteBook('bottom')
        self._mgr.AddPane(self._sidenb['bottom'], wx.aui.AuiPaneInfo().
                          Name("bottom").Bottom().Layer(1).Position(0).
                          BestSize(wx.Size(200, 180)).MinSize(wx.Size(50,145)).PaneBorder(False).PinButton(False).
                          CloseButton(True).MaximizeButton(True).Gripper(False)) 
        #self._mgr.GetPane('bottom').Show(config.ReadInt('BottomSideShow', True))
        self._mgr.GetPane('bottom').Show(True)
        self._sidenb['bottom'].Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnBottomSidePageClosing)
        self._sidenb['bottom'].SetImageList(wx.ImageList(16, 16))
        
        # create default menu bar
        self.SetMenuBar(self.CreateDefaultMenuBar())
        
        self._toolBars  = {}
        # create and add general tool bar
        self.AddToolBar('toolbar0', 'General Tool Bar', self.CreateGeneralToolBar())       
        self.CreateDefaultStatusBar()
        self.SetMinSize(wx.Size(400, 300))

        # commit all components to AUI manager
        self._mgr.Update()
        
        # event mapping =====>
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        wx.EVT_MENU_RANGE(self, wx.ID_FILE1, wx.ID_FILE9, self.OnMRUFile)

        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_CLOSE(self, self.OnCloseFrame)
        wx.EVT_IDLE(self, self.OnIdle)
        wx.EVT_ACTIVATE(self, self.OnActivate)
        # End mapping <=====
        
        # create task bar
        if AppConfig().GetBoolean('ShowTrayIcon', True):
            self._taskbarIcon = FrameTaskBarIcon(self)
        
        if wx.GetApp().GetDefaultIcon():
            self.SetIcon(wx.GetApp().GetDefaultIcon())
                    
        # accept file drag to main frame
        self.SetDropTarget(FrameFileDropTarget(self))
        self.PlayTextToasterBox(_('Welcome to EDES2008!'))
        
    def OnActivate(self, event):
        # work around for focus lost when IDE get activate
        if event.GetActive():
            self._mgr.GetPane('document').Show()
        
    def ShowPane(self, name, bShow=True):
        pane = self._mgr.GetPane(name)
        pane.Show(bShow)
        self._mgr.Update()
        
    def CloseSideWindow(self, win):
        nb = win.GetParent()
        index = nb.GetPageIndex(win)
        #win.Close()
        nb.DeletePage(index)
        
    def OnLeftSidePageClosing(self, event):
        self._logger.info('Closeing left page')
        sel = event.GetSelection()
        page = self._sidenb['left'].GetPage(sel)
        if hasattr(page, 'Close'):
            page.Close()
        count = self._sidenb['left'].GetPageCount()
        if count == 1:
            self.ShowPane('left', False)
        
    def OnRightSidePageClosing(self, event):
        sel = event.GetSelection()
        page = self._sidenb['right'].GetPage(sel)
        if hasattr(page, 'Close'):
            page.Close()
        count = self._sidenb['right'].GetPageCount()
        if count == 1:
            self.ShowPane('right', False)
                    
    def OnBottomSidePageClosing(self, event):
        self._logger.info('Closeing bottom page')
        sel = event.GetSelection()
        page = self._sidenb['bottom'].GetPage(sel)
        if hasattr(page, 'Close'):
            page.Close()
        count = self._sidenb['bottom'].GetPageCount()
        if count == 1:
            self.ShowPane('bottom', False)                   
                        
    def GetAuiManager(self):
        return self._mgr
    
    def GetDocumentManager(self):
        """
        Returns the document manager associated with the DocMDIParentFrame.
        """
        return self._docManager
    
    def _CreateSideNoteBook(self, position):
        """
        Create flatbook for left/right/bottom and document windows.
        
        @param position    left/right/bottom/document
        @return created notebook
        """
        if position == 'left' or position == 'right':
            # right/left
            bookStyle = fnb.FNB_VC71
            bookStyle &= ~(fnb.FNB_NODRAG)
            bookStyle |= fnb.FNB_BOTTOM|fnb.FNB_HIDE_ON_SINGLE_TAB
        else: 
            # bottom
            #bookStyle = fnb.FNB_VC8|fnb.VC8_SHAPE_LEN
            bookStyle = fnb.FNB_FF2
            bookStyle &= ~(fnb.FNB_NODRAG)
            bookStyle |= fnb.FNB_BOTTOM|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_BACKGROUND_GRADIENT
        
        notebook = fnb.FlatNotebook(self, wx.NewId(), style=bookStyle|wx.NO_BORDER|fnb.FNB_NO_X_BUTTON)
        
        notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnSideNoteBookChanged)
        return notebook
    
    def OnSideNoteBookChanged(self, event):
        if event.EventObject == self._sidenb['bottom']:
            nb   = self._sidenb['bottom']
            view =  nb.GetPage(nb.GetSelection())
            if hasattr(view, 'GetService'):
                self.SetPaneTitle('bottom', view.GetService().GetTitle())
        
    def SetPaneTitle(self, position, text):
        pane = self.GetSidePane(position)
        pane.Caption(text)
        self._mgr.Update()
        
    def _CreateDocumentNoteBook(self):
        bookStyle =  wx.aui.AUI_NB_DEFAULT_STYLE
        bookStyle |= wx.aui.AUI_NB_WINDOWLIST_BUTTON|wx.aui.AUI_NB_TAB_FIXED_WIDTH
        nb = DocAuiTabNoteBook(self, wx.ID_ANY, style=bookStyle)
        return nb
    
    def CloseAllDocumentWindows(self):
        self._docnb.CloseAllDocumentWindows()
        
    def _CreateTabRightContextMenu(self):
        self._doctabmenu = wx.Menu()
        item = wx.MenuItem(self._doctabmenu, CLOSE_TAB_ID, 'Close', 'Close')
        self._doctabmenu.AppendItem(item)
        wx.EVT_MENU(self, CLOSE_TAB_ID, self.OnMenuNoteBookCloseTab)
        item = wx.MenuItem(self._doctabmenu, CLOSE_OTHERS_TAB_ID, 'Close Others', 'Close Others')
        self._doctabmenu.AppendItem(item)
        wx.EVT_MENU(self, CLOSE_OTHERS_TAB_ID, self.OnMenuNoteBookCloseOthers)
        item = wx.MenuItem(self._doctabmenu, CLOSE_ALL_TAB_ID, 'Close All', 'Close All')
        self._doctabmenu.AppendItem(item)
        wx.EVT_MENU(self, CLOSE_ALL_TAB_ID, self.OnMenuNoteBookCloseAll)
        return self._doctabmenu
        
    def OnSize(self, event):
        self._mgr.Update()
        
    def OnCloseFrame(self, event):
        """
        Callback for wx.EVT_CLOSE event
        """
        if self._taskbarIcon is not None:
            self._taskbarIcon.Destroy()
                    
        # deinitialize the frame manager
        self._mgr.UnInit()
        
        self._SaveFrameSize()
        
        # save and close services last
        for service in wx.GetApp().GetServices():
            if not service.OnCloseFrame(event):
                return

        # From docview.MDIParentFrame
        if self.GetDocumentManager().Clear(not event.CanVeto()):
            self.Destroy()
        else:
            event.Veto()
        
    def _GetParentFrameSize(self):
        """
        Get main frame's size and position.
        """
        config = wx.ConfigBase_Get()
        pos = config.ReadInt("MainFrameX", -1), config.ReadInt("MainFrameY", -1)
        if wx.Display_GetFromPoint(pos) == -1:  # Check if the frame position is offscreen
            pos = wx.DefaultPosition        
        size = wx.Size(config.ReadInt("MainFrameWidth", 600), config.ReadInt("MainFrameHeight", 400))

        return pos, size
        
    def _SaveFrameSize(self):
        """
        Save main frame's position and size
        """
        config = wx.ConfigBase_Get()
        if not self.IsMaximized():
            config.WriteInt('MainFrameWidth', self.GetSizeTuple()[0])
            config.WriteInt('MainFrameHeight', self.GetSizeTuple()[1])
            config.WriteInt('MainFrameX', self.GetPositionTuple()[0])
            config.WriteInt('MainFrameY', self.GetPositionTuple()[1])
        config.WriteInt("MainFrameMaximized", self.IsMaximized())
        config.WriteInt("LeftSideShow", self._mgr.GetPane('left').IsShown())
        config.WriteInt("RightSideShow", self._mgr.GetPane('right').IsShown())
        config.WriteInt("BottomSideShow", self._mgr.GetPane('bottom').IsShown())
        
    def CreateGeneralToolBar(self):
        toolbar = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                         wx.TB_FLAT | wx.TB_NODIVIDER)
        toolbar.SetToolBitmapSize(wx.Size(16,16))
        toolbar.AddLabelTool(wx.ID_NEW, 'New', self._art.GetBitmap(wx.ART_NEW, size=(16, 16)), shortHelp='New', longHelp='Creates a new document')
        toolbar.AddLabelTool(wx.ID_OPEN, 'Open', self._art.GetBitmap(wx.ART_FILE_OPEN, size=(16, 16)), shortHelp='Open', longHelp='Opens an existing document')
        toolbar.AddLabelTool(wx.ID_SAVE, 'Save', self._art.GetBitmap(wx.ART_FILE_SAVE, size=(16, 16)), shortHelp='Save', longHelp='Saves the active document')
        toolbar.AddLabelTool(SAVEALL_ID,  "Save All", images.getSaveAllBitmap(), shortHelp='Save All', longHelp='Saves all opened document')
        toolbar.AddSeparator()
        toolbar.AddLabelTool(wx.ID_PRINT, "Print", self._art.GetBitmap(wx.ART_PRINT, size=(16, 16)), shortHelp='Print', longHelp='Displays full pages')
        toolbar.AddLabelTool(wx.ID_PREVIEW, "Print Preview", images.getPrintPreviewBitmap(), shortHelp='Print Preview', longHelp='Prints the active document')
        toolbar.AddSeparator()
        toolbar.AddLabelTool(wx.ID_CUT, "Cut", self._art.GetBitmap(wx.ART_CUT, size=(16, 16)), shortHelp="Cut", longHelp='Cuts the selection and puts it on the Clipboard')
        toolbar.AddLabelTool(wx.ID_COPY, "Copy", self._art.GetBitmap(wx.ART_COPY, size=(16, 16)), shortHelp="Copy", longHelp="Copies the selection and puts it on the Clipboard")
        toolbar.AddLabelTool(wx.ID_PASTE, "Paste", self._art.GetBitmap(wx.ART_PASTE, size=(16, 16)), shortHelp="Paste", longHelp='Inserts Clipboard contents')
        toolbar.AddLabelTool(wx.ID_UNDO, 'Undo', self._art.GetBitmap(wx.ART_UNDO, size=(16, 16)), shortHelp="Undo", longHelp="Reverses the last action")
        toolbar.AddLabelTool(wx.ID_REDO, 'Redo', self._art.GetBitmap(wx.ART_REDO, size=(16, 16)), shortHelp='Redo', longHelp="Reverses the last undo")
        toolbar.AddSeparator()
        toolbar.AddLabelTool(SIDE_WINDOW_LEFT_ID, 'Show Left/Hide Pane', core.images.getShowLeftBitmap(), shortHelp='Show/Hide Left Pane', longHelp="Show/Hide Left Pane")
        toolbar.AddLabelTool(SIDE_WINDOW_BOTTOM_ID, 'Show Left/Hide Pane', core.images.getShowBottomBitmap(), shortHelp='Show/Hide Bottom Pane', longHelp="Show/Hide Bottom Pane")
        toolbar.AddLabelTool(SIDE_WINDOW_RIGHT_ID, 'Show/Hide Right Pane', core.images.getShowRightBitmap(), shortHelp='Show/Hide Right Pane', longHelp="Show/Hide Right Pane")
        toolbar.Realize()
        return toolbar
       
    def AddToolBar(self, paneName, caption, toolbar, row=1, size=wx.DefaultSize):
        if self._toolBars.has_key(paneName):
            self._logger.error('tool bar %s has been exists and fail to added' % paneName)
            return
        id = wx.NewId()
        self._toolBars[paneName] = [id, caption, toolbar]
        self._mgr.AddPane(toolbar, wx.aui.AuiPaneInfo().
                          Name(paneName).Caption(caption).
                          ToolbarPane().Top().Row(row).
                          LeftDockable(True).RightDockable(False))        
        self._mgr.Update()
        
        # Add tool bar to view menu
        menuBar = self.GetMenuBar()
        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        toolsSubMenuIndex = viewMenu.FindItem('Tool Bars')
        if toolsSubMenuIndex == -1:
            self._toolbarMenu = wx.Menu()
            viewMenu.AppendSubMenu(self._toolbarMenu, 'Tool Bars', 'Show Tool Bar')
        self._toolbarMenu.AppendCheckItem(id, caption, caption)
        wx.EVT_MENU(self, id, self.OnShowToolBar)
        wx.EVT_UPDATE_UI(self, id, self.OnUpdateToolBar)

    def DetachToolBar(self, paneName):
        if not self._toolBars.has_key(paneName):
            self._logger.error('tool bar %s has been exists and fail to added' % paneName)
            return
        pane = self._toolBars[paneName][2]
        self._mgr.DetachPane(pane)
        self._mgr.Update()
        del self._toolBars[paneName]
        
        menuBar = self.GetMenuBar()
        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        toolsSubMenuIndex = viewMenu.FindItem('Tool Bars')        
        #subMenu = menuBar.GetMenu(toolsSubMenuIndex)
        #print subMenu
                
    def GetToolBar(self, paneName):
        if not self._toolBars.has_key(paneName):
            self._logger.error('tool bar %s does not exist' % paneName)
            return        
        return self._toolBars[paneName][2]
    
    def GetGeneralToolBar(self):
        return self.GetToolBar('toolbar0')
    
    def AddSideWindow(self, page, name, position='left', icon=wx.EmptyIcon):
        if position not in ['left', 'right', 'bottom']:
            raise core.plugin.PluginException('Invalid plugin view position %s' % position)
        #self._mgr.GetPane(position).Show(True)
        #self._mgr.Update()
        if icon != wx.EmptyIcon:
            index = self._sidenb[position].GetImageList().AddIcon(icon)
            self._sidenb[position].AddPage(page, name, imageId=index)
        else:
            self._sidenb[position].AddPage(page, name)
        self._sidenb[position].SetSelection(self._sidenb[position].GetPageCount() - 1)
        self._mgr.Update()
       
    def RemoveSideWindow(self, RemovePage, position='left'):
        count = self._sidenb[position].GetPageCount()
        found = False
        for index in range(count):
            page = self._sidenb[position].GetPage(index)
            if page == RemovePage:
                found = True
                break
        if found:
            self._sidenb[position].RemovePage(index)
            self._mgr.Update()
                
    def GetSideWindow(self, name, position='left'):
        if position not in ['left', 'right', 'bottom']:
            raise core.plugin.PluginException('Invalid plugin view position %s' % position)
        for index in range(self._sidenb[position].GetPageCount()):
            if self._sidenb[position].GetPageText(index) == name:
                return self._sidenb[position].GetPage(index)
        return None
        
    def GetSideParent(self, position):
        if position not in ['left', 'right', 'bottom']:
            raise core.plugin.PluginException('Invalid plugin view position %s' % position)
        return self._sidenb[position]
    
    def ActivatePageInSideWindow(self, page):
        for position in ['left', 'right', 'bottom']:
            count = self._sidenb[position].GetPageCount()
            for index in range(count):
                if page == self._sidenb[position].GetPage(index):
                    self.ShowPane(position)
                    self._sidenb[position].SetSelection(index)
                    break
                    
    def GetSidePane(self, position):
        if position not in ['left', 'right', 'bottom']:
            raise core.plugin.PluginException('Invalid plugin view position %s' % position)
        pane = self._mgr.GetPane(position)
        return pane
        
    def AppendBitmapMenu(self, menu, id, shortHelp, longHelp, bitmap=None):
        item = wx.MenuItem(menu, id, shortHelp, longHelp)
        if bitmap != None:
            item.SetBitmap(bitmap)

        wx.EVT_MENU(self, id, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, id, self.ProcessUpdateUIEvent)
        
        menu.AppendItem(item)
        
    def CreateDefaultMenuBar(self, sdi=False):
        """
        Creates the default MenuBar.  Contains File, Edit, View, Tools, and Help menus.
        """
        menuBar = wx.MenuBar()
        self.ConstructNewMenu()
        # contruct general file menu
        fileMenu = wx.Menu()
        fileMenu.AppendSubMenu(self.ConstructNewMenu(), "&New...", 'New')
        #self.AppendBitmapMenu(fileMenu, wx.ID_NEW, "&New...\tCtrl+N", "Creates a new document", self._art.GetBitmap(wx.ART_NEW))
        self.AppendBitmapMenu(fileMenu, wx.ID_OPEN, "&Open...\tCtrl+O", "Opens an existing document", self._art.GetBitmap(wx.ART_FILE_OPEN))
        self.AppendBitmapMenu(fileMenu, wx.ID_CLOSE, _("&Close"), _("Closes the active document"))
        self.AppendBitmapMenu(fileMenu, wx.ID_CLOSE_ALL, _("Close A&ll"), _("Closes all open documents"))
        fileMenu.AppendSeparator()
        self.AppendBitmapMenu(fileMenu, wx.ID_SAVE, _("&Save\tCtrl+S"), _("Saves the active document"), self._art.GetBitmap(wx.ART_FILE_SAVE))
        self.AppendBitmapMenu(fileMenu, wx.ID_SAVEAS, _("Save &As..."), _("Saves the active document with a new name"), self._art.GetBitmap(wx.ART_FILE_SAVE_AS))
        self.AppendBitmapMenu(fileMenu, SAVEALL_ID, _("Save All\tCtrl+Shift+A"), _("Saves the all active documents"), images.getSaveAllBitmap())
        fileMenu.AppendSeparator()
        self.AppendBitmapMenu(fileMenu, wx.ID_PRINT, _("&Print\tCtrl+P"), _("Prints the active document"), self._art.GetBitmap(wx.ART_PRINT))
        self.AppendBitmapMenu(fileMenu, wx.ID_PREVIEW, _("Print Pre&view"), _("Displays full pages"), images.getPrintPreviewBitmap())

        #self.AppendBitmapMenu(fileMenu, wx.ID_PRINT_SETUP, _("Page Set&up"), _("Changes page layout settings"))
        fileMenu.AppendSeparator()
        self.AppendBitmapMenu(fileMenu, wx.ID_EXIT, _("E&xit"), _("Closes this program"), self._art.GetBitmap(wx.ART_QUIT))
        self._docManager.FileHistoryUseMenu(fileMenu)
        self._docManager.FileHistoryAddFilesToMenu()
        menuBar.Append(fileMenu, _("&File"));

        # construct edit menu
        editMenu = wx.Menu()
        self.AppendBitmapMenu(editMenu, wx.ID_UNDO, _("&Undo\tCtrl+Z"), _("Reverses the last action"), self._art.GetBitmap(wx.ART_UNDO))
        self.AppendBitmapMenu(editMenu, wx.ID_REDO, _("&Redo\tCtrl+Y"), _("Reverses the last undo"), self._art.GetBitmap(wx.ART_REDO))
        editMenu.AppendSeparator()
        self.AppendBitmapMenu(editMenu, wx.ID_CUT, _("Cu&t\tCtrl+X"), _("Cuts the selection and puts it on the Clipboard"), self._art.GetBitmap(wx.ART_CUT))                
        self.AppendBitmapMenu(editMenu, wx.ID_COPY, _("&Copy\tCtrl+C"), _("Copies the selection and puts it on the Clipboard"), self._art.GetBitmap(wx.ART_COPY))                
        self.AppendBitmapMenu(editMenu, wx.ID_PASTE, _("&Paste\tCtrl+V"), _("Inserts Clipboard contents"), self._art.GetBitmap(wx.ART_PASTE))                
        self.AppendBitmapMenu(editMenu, wx.ID_CLEAR, _("&Delete"), _("Erases the selection"))
        editMenu.AppendSeparator()
        self.AppendBitmapMenu(editMenu, wx.ID_SELECTALL, _("Select A&ll\tCtrl+A"), _("Selects all available data"))
        menuBar.Append(editMenu, _("&Edit"))

        # construct view menu
        viewMenu = wx.Menu()
        viewMenu.AppendCheckItem(VIEW_HEX_ID, _("View &Hex"), _("View Hex"))
        wx.EVT_MENU(self, VIEW_HEX_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, VIEW_HEX_ID, self.ProcessUpdateUIEvent)
        viewMenu.AppendSeparator()
        viewMenu.AppendCheckItem(VIEW_STATUSBAR_ID, _("&Status Bar"), _("Shows or hides the status bar"))
        wx.EVT_MENU(self, VIEW_STATUSBAR_ID, self.OnViewStatusBar)
        wx.EVT_UPDATE_UI(self, VIEW_STATUSBAR_ID, self.OnUpdateViewStatusBar)
        sideMenu = wx.Menu()
        sideMenu.AppendCheckItem(SIDE_WINDOW_LEFT_ID, 'Left', 'Show left side window')
        wx.EVT_MENU(self, SIDE_WINDOW_LEFT_ID, self.OnShowSideWindow)
        wx.EVT_UPDATE_UI(self, SIDE_WINDOW_LEFT_ID, self.OnUpdateSideWindow)
        sideMenu.AppendCheckItem(SIDE_WINDOW_RIGHT_ID, 'Right', 'Show right side window')
        wx.EVT_MENU(self, SIDE_WINDOW_RIGHT_ID, self.OnShowSideWindow)
        wx.EVT_UPDATE_UI(self, SIDE_WINDOW_RIGHT_ID, self.OnUpdateSideWindow)
        sideMenu.AppendCheckItem(SIDE_WINDOW_BOTTOM_ID, 'Bottom', 'Show bottom side window')
        wx.EVT_MENU(self, SIDE_WINDOW_BOTTOM_ID, self.OnShowSideWindow)
        wx.EVT_UPDATE_UI(self, SIDE_WINDOW_BOTTOM_ID, self.OnUpdateSideWindow)
        viewMenu.AppendSubMenu(sideMenu, 'Side Windows', 'Show/Hide side windows')
        
        menuBar.Append(viewMenu, _("&View"))
        docMenu  = wx.Menu()
        menuBar.Append(docMenu, _("&Document"))
        
        toolMenu = wx.Menu()
        toolMenu.Append(SERVICES_MENU_ID, 'Services', 'List current installed service')
        wx.EVT_MENU(self, SERVICES_MENU_ID, self.OnListServices)
        if wx.Platform == '__WXMSW__':
            toolMenu.Append(REGISTER_EXPLORER_ID, 'Register to Explorer', 
                            'Regiter Project Insight Studio in right context menu in explorer')
            wx.EVT_MENU(self, REGISTER_EXPLORER_ID, self.OnRegisterTool)
            item = toolMenu.Append(UNREGISTER_EXPLORER_ID, 'UnRegister to Explorer', 
                            'UnRegiter Project Insight Studio in right context menu in explorer')
            wx.EVT_MENU(self, UNREGISTER_EXPLORER_ID, self.OnUnRegisterTool)
        menuBar.Append(toolMenu, 'Tools')
        helpMenu = wx.Menu()
        helpMenu.Append(wx.ID_ABOUT, _("&About" + " " + wx.GetApp().GetAppName()), _("Displays program information, version number, and copyright"))
        self.AppendBitmapMenu(helpMenu, CONTACT_ME_ID, _("&Contact Me"), _("Send email to ken!"), getEmailBitmap())        
        menuBar.Append(helpMenu, _("&Help"))

        wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
        wx.EVT_UPDATE_UI(self, wx.ID_ABOUT, self.ProcessUpdateUIEvent)  # Using ID_ABOUT to update the window menu, the window menu items are not triggering
        wx.EVT_MENU(self, CONTACT_ME_ID, self.OnContact)
        return menuBar        
    
    def ConstructNewMenu(self):
        menu = wx.Menu()
        mgr  = self.GetDocumentManager()
        # find default template
        defaultTemp = None
        for temp in mgr.GetTemplates():
            #if not temp.IsVisible(): continue
            if (temp.GetFlags() == wx.lib.docview.TEMPLATE_NO_CREATE): continue
            if (temp.GetFlags() & wx.lib.docview.TEMPLATE_VISIBLE) == 0: continue 
            if temp.GetFileFilter() == '*.*':
                label = '%s\tCtrl+N' % temp.GetDescription()
                id    = wx.ID_NEW
            else:
                label = temp.GetDescription()
                id    = wx.NewId()
            self._temp_menu_mapping[id] = temp
            item = wx.MenuItem(menu, id, label, temp.GetDescription())
            item.SetBitmap(wx.BitmapFromIcon(temp.GetIcon()))
            menu.AppendItem(item)
            
            wx.EVT_MENU(self, id, self.OnFileNew)
        return menu
                
    def OnFileNew(self, event):
        id = event.GetId()
        if not self._temp_menu_mapping.has_key(id):
            return
        
        temp = self._temp_menu_mapping[id]
        temp.CreateDocument('', wx.lib.docview.DOC_NEW)
        
    def CreateDefaultStatusBar(self):
        """
        Creates the default StatusBar.
        """
        wx.Frame.CreateStatusBar(self)
        self.GetStatusBar().Show(True)
        self.UpdateStatus()
        return self.GetStatusBar()
    
    
    def ProcessEvent(self, event):
        """
        Processes an event, searching event tables and calling zero or more
        suitable event handler function(s).  Note that the ProcessEvent
        method is called from the wxPython docview framework directly since
        wxPython does not have a virtual ProcessEvent function.
        """
        if wx.GetApp().ProcessEventBeforeWindows(event):
            return True
        
        id    = event.GetId()
        if id not in [wx.ID_NEW, wx.ID_OPEN, wx.ID_SAVE, wx.ID_FIND, SAVEALL_ID, \
                      wx.ID_PRINT, wx.ID_PREVIEW]:
            focus = self.FindFocus()
            if hasattr(focus, 'GetId') and \
               self._docnb.FindWindowById(focus.GetId()) == None and \
               focus != self and \
               focus != self._docnb:
                if hasattr(focus, 'ProcessEvent'):
                    if focus.ProcessEvent(event):
                        return True
        if id == VIEW_HEX_ID:
            self.OnViewHex(event.IsChecked())
            return True
            
        if self._docManager and self._docManager.ProcessEvent(event):
            return True
        
        if id == SAVEALL_ID:
            self.OnFileSaveAll(event)
            return True

        return wx.GetApp().ProcessEvent(event)
    
    def ProcessUpdateUIEvent(self, event):
        """
        Processes a UI event, searching event tables and calling zero or more
        suitable event handler function(s).  Note that the ProcessEvent
        method is called from the wxPython docview framework directly since
        wxPython does not have a virtual ProcessEvent function.
        """
    
        if wx.GetApp().ProcessUpdateUIEventBeforeWindows(event):
            return True
        
        # must deal with event in active focus window before sending to 
        # doc manager. Otherwice, some service's view can not receive
        # any event
        id    = event.GetId()
        focus = self.FindFocus()
        if id not in [wx.ID_NEW, wx.ID_OPEN, wx.ID_SAVE, wx.ID_FIND, SAVEALL_ID, \
                      wx.ID_PRINT, wx.ID_PREVIEW]:
            if hasattr(focus, 'GetId') and \
               self._docnb.FindWindowById(focus.GetId()) == None and \
               focus != self and focus != self._docnb and not isinstance(focus, wx.TreeCtrl):
                if hasattr(focus, 'ProcessUpdateUIEvent'):
                    if focus.ProcessUpdateUIEvent(event):
                        return True
                        
        if self._docManager and self._docManager.ProcessUpdateUIEvent(event):
            return True

        id = event.GetId()
        if id == wx.ID_CUT:
            event.Enable(False)
            return True
        elif id == wx.ID_COPY:
            event.Enable(False)
            return True
        elif id == wx.ID_PASTE:
            event.Enable(False)
            return True
        elif id == wx.ID_CLEAR:
            event.Enable(False)
            return True
        elif id == wx.ID_SELECTALL:
            event.Enable(False)
            return True
        elif id == SAVEALL_ID:
            filesModified = False
            docs = wx.GetApp().GetDocumentManager().GetDocuments()
            for doc in docs:
                if doc.IsModified():
                    filesModified = True
                    break

            event.Enable(filesModified)
            return True
        elif id == VIEW_HEX_ID:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            if view == None:
                event.Check(False)
                event.Enable(False)
                return True
            if hasattr(view, 'IsViewHex'):
                event.Enable(True)
                event.Check(view.IsViewHex())
                return True
            else:
                event.Check(False)
                event.Enable(False)
                return True
        else:
            return wx.GetApp().ProcessUpdateUIEvent(event)    
    
    def OnViewHex(self, isHex):
        docmgr   = self.GetDocumentManager()
        doc      = docmgr.GetCurrentDocument()
        if doc == None: return
        view     = doc.GetFirstView()
        if view == None: return
        view.ViewHex(isHex)
        
    def OnFileSaveAll(self, event):
        """
        Saves all of the currently open documents.
        """
        docs = wx.GetApp().GetDocumentManager().GetDocuments()

        # save child documents first
        for doc in docs:
            if isinstance(doc, wx.lib.pydocview.ChildDocument):
                doc.Save()

        # save parent and other documents later
        for doc in docs:
            if not isinstance(doc, wx.lib.pydocview.ChildDocument):
                doc.Save()
                
    def OnAbout(self, event):
        """
        Invokes the about dialog.
        """
        service = wx.GetApp().GetService(pydocview.AboutService)
        if service != None:
            service.ShowAbout()
        
    def OnContact(self, event):
        import webbrowser
        webbrowser.open("mailto:%s?subject=[Project Insight Studio]" % version.CONTACT_EMAIL)
        
    def OnUpdateViewStatusBar(self, event):
        """
        Updates the View StatusBar menu item.
        """
        event.Check(self.GetStatusBar().IsShown())

    def OnListServices(self, event):
        """
        Menu callback to show dialog box to list current installed services.
        """
        dlg = ServicesListDialog()
        dlg.ShowModal()
        
    def OnRegisterTool(self, event):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, '*', _winreg.KEY_ALL_ACCESS)
            filename = os.path.basename(sys.argv[0])
            f, ext = os.path.splitext(filename)
            if ext == '.exe':
                command = '"%s" "%%L"' % os.path.normpath(os.path.join(wx.GetApp().GetAppLocation(), filename))
            else:
                path = os.path.normpath(os.path.join(os.getcwd(), '%s.pyw' % f))
                #path = os.path.normpath(os.path.join(os.getcwd(), filename))
                execute = sys.executable.replace('python.exe', 'pythonw.exe')
                command = '"%s" "%s" "%%L"' % (execute, path)
            _winreg.SetValue(key, 'shell\\Project Insight Studio\\command', _winreg.REG_SZ, command)
        except:
            wx.MessageDialog(self, _('Register to explore context menu failed!'), _("Error"), wx.OK | wx.ICON_INFORMATION).ShowModal()
            return
        wx.MessageDialog(self, _('Success to register PIS into right context menu in explorer!'), _('Success'),wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def OnUnRegisterTool(self, event):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, '*\\shell', _winreg.KEY_ALL_ACCESS)
            _winreg.DeleteKey(key, 'Project Insight Studio\\command')
            _winreg.DeleteKey(key, 'Project Insight Studio')
        except:
            wx.MessageDialog(self, _('Unregister from explore context menu failed!'), _("Error"), wx.OK | wx.ICON_INFORMATION).ShowModal()
            return
        wx.MessageDialog(self, _('Success to remove PIS into right context menu in explorer!'), _('Success'),wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def OnViewStatusBar(self, event):
        """
        Toggles whether the StatusBar is visible.
        """        
        self.GetStatusBar().Show(not self.GetStatusBar().IsShown())
        self._mgr.Update()
    
    def OnShowToolBar(self, event):
        for key in self._toolBars.keys():
            if self._toolBars[key][0] == event.GetId():
                self._mgr.GetPane(key).Show(not self._mgr.GetPane(key).IsShown())
                self._mgr.Update()
                return
    
    def OnUpdateToolBar(self, event):
        for key in self._toolBars.keys():
            if self._toolBars[key][0] == event.GetId():
                event.Check(self._mgr.GetPane(key).IsShown())
                self._mgr.Update()
                return
            
    def OnShowSideWindow(self, event):
        id = event.GetId()
        pane = None
        if id == SIDE_WINDOW_LEFT_ID:
            pane = self._mgr.GetPane('left')
        elif id == SIDE_WINDOW_RIGHT_ID:
            pane = self._mgr.GetPane('right')
        elif id == SIDE_WINDOW_BOTTOM_ID:
            pane = self._mgr.GetPane('bottom')

        pane.Show(not pane.IsShown())
        self._mgr.Update()
            
    def OnUpdateSideWindow(self, event):
        id = event.GetId()
        nb = None
        if id == SIDE_WINDOW_LEFT_ID:
            nb = self._sidenb['left']
        elif id == SIDE_WINDOW_RIGHT_ID:
            nb = self._sidenb['right']
        else:
            nb = self._sidenb['bottom']
        
        event.Check(nb.IsShown())
        
    def UpdateStatus(self, message = _("Ready")):
        """
        Updates the StatusBar.
        """
        if self.GetStatusBar().GetStatusText() != message:
            self.GetStatusBar().PushStatusText(message)
    
    def OnExit(self, event):
        """
        menu function for wx.ID_EXIT
        """
        self.Close()
        
    def OnMRUFile(self, event):
        """
        Opens the appropriate file when it is selected from the file history
        menu.
        """
        n = event.GetId() - wx.ID_FILE1
        filename = self._docManager.GetHistoryFile(n)
        if filename:
            try:
                self._docManager.CreateDocument(filename, wx.lib.docview.DOC_SILENT)
            except:
                self._docManager.RemoveFileFromHistory(n)
                wx.MessageBox("Can not open %s!" % filename,
                              "File Error",
                              wx.OK|wx.ICON_EXCLAMATION,
                              self)
        else:
            self._docManager.RemoveFileFromHistory(n)
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            wx.MessageBox("The file '%s' doesn't exist and couldn't be opened.\nIt has been removed from the most recently used files list" % FileNameFromPath(file),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self)    
    
    def GetNotebook(self):
        """
        Return document note book.
        """
        return self._docnb
    
    def AddNotebookPage(self, panel, title):
        """
        Adds a document page to the notebook.
        """
        self._docnb.AddPage(panel, title)
        index = self._docnb.GetPageCount() - 1
        self._docnb.SetSelection(index)
        
        # set page icon
        doc = panel.GetDocument()
        icon = None
        if doc != None:
            template = doc.GetDocumentTemplate()
            icon = template.GetIcon()
        if icon != None:
            self._docnb.SetPageBitmap(index, wx.BitmapFromIcon(icon))
        else:
            self._docnb.SetPageBitmap(index, self._art.GetBitmap(wx.ART_NORMAL_FILE))
            
    def GetNotebookPageTitle(self, panel):
        """
        Get title of notebook.
        """
        index = self._docnb.GetPageIndex(panel)
        if index != -1:
            return self._docnb.GetPageText(index)
        else:
            return None
        
    def SetNotebookPageTitle(self, panel, title):
        """
        Set title of notebook.
        """
        self._docnb.SetPageText(self._docnb.GetPageIndex(panel), title)
        
    def ActivateNotebookPage(self, panel):
        """
        Sets the notebook to the specified panel.
        """
        index = self._docnb.GetPageIndex(panel)
        if index == -1: return
        self._docnb.SetSelection(index)
        self._mgr.GetPane('document').Show()
        doc = panel.GetDocument()
        if doc == None: return
        
    def ActivateDocumentPane(self):
        self._mgr.GetPane('document').Show()
        
    def RemoveNotebookPage(self, panel):
        """
        Removes a document page from the notebook.
        Do nothing for matching implement of pydocview
        """
        pass
        
    def OnIdle(self, event):
        if wx.GetApp().IsActive() and self._docnb.GetPageCount():
            if self._inReloading: return False
            doc = self._docnb.GetSelectionDoc()
            sel = self._docnb.GetSelection()
            if doc and not doc.IsDocumentModificationDateCorrect():
                wx.CallAfter(self.ReloadModifiedDoc, sel, doc)
                #self.ReloadModifiedDoc(doc)
            
    def ReloadModifiedDoc(self, sel, doc):
        self._inReloading = True
        dlg = wx.MessageDialog(self,
                               _("%s has been modified by another "
                               "application.\n\nWould you like "
                               "to Reload it?") % doc.GetPrintableName(),
                               _("Reload File?"),
                               wx.YES_NO | wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        ret = dlg.ShowModal()
        dlg.Destroy()
        path = doc.GetFilename()
        if ret == wx.ID_YES:
            docManager = wx.GetApp().GetDocumentManager()
            if not docManager.CloseDocument(doc, False):
                wx.MessageBox(_("Couldn't reload '%s'.  Unable to close current '%s'.") % (doc.GetPrintableName(), doc.GetPrintableName()))
            else:
                self._docnb.DeletePage(sel)
                docManager.CreateDocument(path, wx.lib.docview.DOC_SILENT)
        elif ret == wx.ID_NO:
            doc.SetDocumentModificationDate()
        
        self._inReloading = False

    def SetStatusBar(self, bar):
        statusBar = self.GetStatusBar()
        if statusBar != None:
            statusBar.Hide()
        wx.Frame.SetStatusBar(self, bar)
        
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
        tb.SetPopupBitmap(getToasterBoxbackgroundBitmap())        
        if size == None:
            size = (200, 100)
        tb.SetPopupSize(size)
        tb.SetPopupPosition((screenWidth - size[0] - 5, screenHeight - size[1] - 10))
        tb.SetPopupPauseTime(5000)
        tb.Play()
                        
class DocAuiTabNoteBook(wx.aui.AuiNotebook):
    """
    This class provide document container and herite from AuiNoteBook.
    Add a tab menu interface for displaying the tab context menu: close/
    close all/close others
    """
    CLOSE_TAB_ID          = wx.NewId()
    CLOSE_OTHERS_TAB_ID   = wx.NewId()
    CLOSE_ALL_TAB_ID      = wx.NewId()
    COPY_PATH_ID          = wx.NewId()
    
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        if 'EVT_AUINOTEBOOK_TAB_RIGHT_DOWN' in dir(wx.aui):
            # This event was only added as of wx 2.8.7.1, so ignore it on
            # earlier releases        
            self.Bind(wx.aui.EVT_AUINOTEBOOK_TAB_RIGHT_DOWN, self.OnTabContextMenu)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnTabClose)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnNoteBookChanged)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.OnNoteBookChanging)
                
    def OnTabContextMenu(self, evt):
        oldIndex = self.GetSelection()
        newIndex = evt.GetSelection()
        if oldIndex != newIndex:
            self.SetSelection(evt.GetSelection())
            
        self.PopupMenu(self._CreateTabRightContextMenu())
    
    def GetSelectionDoc(self):
        return self.GetPageDoc(self.GetSelection())
        
    def GetPageDoc(self, index):
        """
        Get document object for given index page
        """
        page = self.GetPage(index)
        if page == None: return None
        
        doc = page.GetDocument()
        return doc
            
    def CloseDoc(self, doc):
        if doc != None:
            docmgr = wx.GetApp().GetDocumentManager()
            docmgr.ActivateView(doc.GetFirstView(), False)
            if not docmgr.CloseDocument(doc, False):
                return False
        docNum = len(wx.GetApp().GetDocumentManager().GetDocuments())
        if docNum == 0:
            wx.GetApp().GetTopWindow().SetTitle(wx.GetApp().GetAppName())
        return True
        
    def _CreateTabRightContextMenu(self):
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.CLOSE_TAB_ID, 'Close', 'Close')
        menu.AppendItem(item)
        wx.EVT_MENU(self, self.CLOSE_TAB_ID, self.OnMenuTabClose)
        item = wx.MenuItem(menu, self.CLOSE_OTHERS_TAB_ID, 'Close Others', 'Close Others')
        menu.AppendItem(item)
        wx.EVT_MENU(self, self.CLOSE_OTHERS_TAB_ID, self.OnMenuTabCloseOthers)
        item = wx.MenuItem(menu, self.CLOSE_ALL_TAB_ID, 'Close All', 'Close All')
        menu.AppendItem(item)
        wx.EVT_MENU(self, self.CLOSE_ALL_TAB_ID, self.OnMenuTabCloseAll)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.COPY_PATH_ID, 'Copy Filename', 'Copy Filename')
        wx.EVT_MENU(self, self.COPY_PATH_ID, self.OnMenuTabCopyPath)
        menu.AppendItem(item)
        return menu

    def OnTabClose(self, evt):
        page = self.GetPage(self.GetSelection())
        doc = page.GetDocument()
        if doc != None:
            if not self.CloseDoc(doc):
                evt.Veto()
        else:
            page.Close()
    def OnMenuTabClose(self, evt):
        """
        Callback function for tab's popup menu 'Close'
        """   
        if not self.CloseDoc(self.GetSelectionDoc()):
            return
        self.DeletePage(self.GetSelection())
                
    def OnMenuTabCloseOthers(self, evt):
        """
        Callback function for tab's popup menu 'Close Others'
        """
        pages = []
        # cache current selection page
        selPage = self.GetPage(self.GetSelection())
        # cache all opened pages
        for index in range(self.GetPageCount()):
            pages.append(self.GetPage(index))
        
        for page in pages:
            if page != selPage:
                doc = page.GetDocument()
                if doc != None:
                    if not self.CloseDoc(doc):
                        continue
                self.DeletePage(self.GetPageIndex(page))
        
        
    def OnMenuTabCloseAll(self, evt):
        """
        Callback function for tab's popup menu 'Close All'
        """
        pages = []
        count = self.GetPageCount()
        for index in range(count):
            pages.append(self.GetPage(index))
            
        for page in pages:
            doc = page.GetView().GetDocument()
            if doc != None:
                if not self.CloseDoc(doc):
                    continue
                self.DeletePage(self.GetPageIndex(page))            
    
    def CloseAllDocumentWindows(self):
        pages = []
        count = self.GetPageCount()
        for index in range(count):
            pages.append(self.GetPage(index))
            
        for page in pages:
            doc = page.GetView().GetDocument()
            if doc != None:
                if not self.CloseDoc(doc):
                    continue
            self.DeletePage(self.GetPageIndex(page))            
        
    def OnMenuTabCopyPath(self, evt):
        self.CopyTextToClipboard(self.GetSelectionDoc().GetFilename())
        
    def CopyTextToClipboard(self, text):
        """
        Copy string to clipboard
        """
        textObj = wx.TextDataObject()
        textObj.SetText(text)
        # Copy text object to clipboard
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(textObj)
        wx.TheClipboard.Close()        
        
    def OnNoteBookChanging(self, event):
        #pass
        #import outline
        #serv = wx.GetApp().GetService(outline.OutlineService)
        #serv.UnLoad()
        event.Skip()
        
    def OnNoteBookChanged(self, event):
        page = self.GetPage(self.GetSelection())
        #if hasattr(page, '_view'):
        #    view = page._view
        #    if hasattr(view, 'Activate'):
        #        view.Activate()
        #    if hasattr(view, 'SetFocus'):
        #        wx.CallAfter(view.SetFocus)

        if hasattr(page, 'Activate'):
            page.Activate()
            if hasattr(page, '_childView'):
                if hasattr(page._childView, 'SetFocus'):
                    page._childView.SetFocus()
                
        # Update frame's title
        appname = wx.GetApp().GetAppName()
        doc     = self.GetSelectionDoc()
        if doc != None:
            filename = doc.GetFilename()
            # TODO: Consider more about unicode filename
            #try:
            str = appname + ' - ' + filename
            #except:
            #    wx.GetApp().GetLogger().exception('filename error')
            
            #wx.GetApp().GetTopWindow().SetTitle(u'%s - %s' % (appname, self.GetSelectionDoc().GetFilename()))
            wx.GetApp().GetTopWindow().SetTitle(str)
        
               
class ServicesListDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, wx.GetApp().GetTopWindow(), size=(400, 300), title='Installed Services')
        self._list = wx.ListBox(self, -1)
        button     = wx.Button(self, -1, 'OK')
        button.Bind(wx.EVT_BUTTON, self.OnOk)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._list, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.SetSizer(sizer)
        self.Layout()
        
        #self._list.InsertColumn(0, 'Services Class')
        #self._list.SetColumnWidth(0, 250)
        self.RefreshServices()
        
    def RefreshServices(self):
        services = wx.GetApp().GetServices()
        for service in services:
            #self._list.InsertStringItem(self._list.GetItemCount(), service.__class__.__name__)
            self._list.Insert(service.__class__.__name__, 0)
            
    def OnOk(self, event):
        self.EndModal(0)
        
class FrameTaskBarIcon(wx.TaskBarIcon):
    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE   = wx.NewId()
    TBMENU_CHANGE  = wx.NewId()
    TBMENU_REMOVE  = wx.NewId()    
    
    def __init__(self, parent):
        wx.TaskBarIcon.__init__(self)
        
        self._frame = parent
        self.SetIcon(core.images.getAppIcon())
        
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        #self.Bind(wx.EVT_MENU, self.OnTaskBarChange, id=self.TBMENU_CHANGE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarRemove, id=self.TBMENU_REMOVE)
                
    def OnTaskBarActivate(self, event):
        if self._frame.IsIconized():
            self._frame.Iconize(False)
        if not self._frame.IsShown():
            self._frame.Show(True)
        self._frame.Raise()        
        
    def OnTaskBarClose(self, evt):
        wx.CallAfter(self._frame.Close)
                
    def OnTaskBarRemove(self, evt):
        self.RemoveIcon() 
        
    def OnTaskBarActivate(self, evt):
        if self._frame.IsIconized():
            self._frame.Iconize(False)
        if not self._frame.IsShown():
            self._frame.Show(True)
        self._frame.Raise()               
        
    def CreatePopupMenu(self):
        """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_RESTORE, "Restore Project Insight Studio")
        menu.Append(self.TBMENU_CLOSE,   "Close Project Insight Studio")
        menu.AppendSeparator()
        #menu.Append(self.TBMENU_CHANGE, "Change the Tray Icon")
        menu.Append(self.TBMENU_REMOVE, "Remove the Tray Icon")
        return menu  
    
class FrameFileDropTarget(wx.FileDropTarget):
    def __init__(self, frame):
        wx.FileDropTarget.__init__(self)
        self._frame = frame
        
    def OnDropFiles(self, x, y, filenames):
        for file in filenames:
            self._frame.GetDocumentManager().CreateDocument(file, wx.lib.docview.DOC_SILENT)
            
#----------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib

def getEmailData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2_y\xba8\x86D\
\xb4\xbe\x9d\xee-\xd4d \xe0r\x9fe\xfd\xda\xbe*C\x9b\x19\xdb\xb8;]]\'\xfa+\
\x15\x1e\xcca\xebR\xf9\xfb\xe2\x80\xc1\x8c\xd6\xb6Y\x82\xabV\xe53\xfcg\xd8\
\xd0\xcd~\xfcp\\v\xe7\xbcs\xe2\xd5\xcc\x0c\x05\xe5*\x0c\x8ca6\xb3K\xa5\xbe\
\xcf\xd61a;)\xe6\x91\xc0\x96\x10\xb3>\xf7b\x8e[y\xb1gD\xc6\x86\x0b\x0f\xdeU\
\xb11\xa9,\xdc\x96\xdb\xfd\xe4_\xd5;=\x87@s\xc6\x1f6+\xa7\xec8"\xd1\xd0\xe5T\
3\xcb\xfefcL\xc7\xc2\xca\xcd2\x11\\\x1fs\xff\xe4\xb0?s\xea\xe9\x8d~r\xe0\xca\
\xd1\xe5\x0ei\xd6\x06*Fe{_\x18\x1b|\xff\xa3\x9e\x7f0\xc4}\x93\xcc\x89\xbb\
\x9f\xd7X\x05l\x15\n\xfb+6E\xcc_q\x1f\xd3\x1f\xaf=\xfc\x1bw\xf0M9\xa5\xd9p\
\xf4\x7f\x93i\xb4Q\xb9z\x99\x8b~\x83\xc4\xae\xfba\x8c\x92,\x11\xd6\xab\xb6?\
\x95>\xc0\xf6\x81!\xa8M\xd7\xceq\x9a\x8e\x15\xd0\xd7\x0c\x9e\xae~.\xeb\x9c\
\x12\x9a\x00\xd9\xf5w\x9f' )

def getEmailBitmap():
    return BitmapFromImage(getEmailImage().Scale(16, 16))

def getEmailImage():
    stream = cStringIO.StringIO(getEmailData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
# This file was generated by N:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

ToasterBoxbackground = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAA3NCSVQICAjb4U/gAAADEklE"
    "QVR4nO2b25aDIAxFYRb//8udh96wJSUnEBIx+20cQNylFDyaUsAmp5Rut5t1N05AzvnPug9n"
    "ImQBhCyAkAUQsgBCFkDIAghZACELIGQBhCyAkAUQsgBCFkDIAghZACELIGQBhCyAkAUQsgBC"
    "FkDIAghZACELIGQBhCyAkAUQsgBCFkDIAiiJ/XxWzlm5M94p/KIjz7ztIbqklD4caFyWWLQr"
    "y42RNfLM5PQrczWcS0pSPa2e7C268TVktSWr9q7cYHZ7QzRFAxP8oa2BfuTZw2/ZcL4vHch6"
    "Kh+atOLQcE4TRFcjq1WP29YS0aOihkXf56wbfmHHGtcQXaRtvWu4Eq06b9BLB/ZpF4r+Kv51"
    "btXhTC8dvo4CF6Yl2ng4I3vDgaLca/M4nN81Vu0NpeUcDOd3jcac1WiL3Q/LXzF90byvIbvL"
    "e4t+rLPQrgKl9UUvmzfKz/8y2zIW3S6lILraG/Lb+jy6SDT2mYhF06fpzFnMJViT6aLNh/Nj"
    "6bBuuSAWbTSc69KPpYNgJy08M4+GCaPhXJcunwdQsrNbycDRT7qigdvK7bbGVPm6ldw7qrM3"
    "/GK6aJN5o5FIa0R180eQhehWbugpqlOZEKWNCtMdir1FD+SGs3EV8dN7w9+dvF7yTNEZWddM"
    "nilEe0Me502eKZbvDXn4FP3cGw70w5Vo1Yi/HP/s1b5G8kzRXTpcMXmmUN0bKoo2Gc6N28qu"
    "ojpXw3nsmdJNk2fq3LP3hgPl/Is+fg3tAtF0hoi/9Isw29ooeaZg7A2l/QAKOkueKTqLUvOo"
    "rl9qoejHnOUqecZKKyTPVMGfz5Q6iOrMLdcFJywd9kueKYZzwzF8Js/UGdgvOl0peabaYj9T"
    "eqXkmWLJ+4ZnS54pjPaGLfyLBl4oP7S1d8RPzBvS9w23Tp6pFuftDdn4T54pqqWDy6iuxnw4"
    "V7mhm+SZblLOFNHi9w2rthSs+FqXPUWr7Q15+EyeKYiXBq6dPFO8bv5F8tzntXSI5LnPlL3h"
    "bskzBe8WjcdM1GDe4N3800+eWd0gilvOGwHFP1gtOyUKg9+8AAAAAElFTkSuQmCC")
getToasterBoxbackgroundData = ToasterBoxbackground.GetData
getToasterBoxbackgroundImage = ToasterBoxbackground.GetImage
getToasterBoxbackgroundBitmap = ToasterBoxbackground.GetBitmap
