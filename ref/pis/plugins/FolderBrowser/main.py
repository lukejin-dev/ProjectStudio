"""Folder browser plugin is provide dos prompt service, It is sample service plugin
"""
import wx
import wx.lib.pydocview as pydocview
import wx.lib.docview
import ui.MessageWindow
import os, sys
import locale
import threading
import core.plugin
import core.service
if wx.Platform == '__WXMSW__':
    import  wx.lib.iewin  as  iewin
        
import stat
import time

"""
 _plugin_info_ must be defined in plugin code, it is provide base information
 for plugin.
"""
_plugin_module_info_ = [{"name":"FolderBrowserPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"Folder browser service",
                         "class":"FolderBrowserPlugin"}]

class FolderBrowserPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return FolderBrowserService
    
class FolderBrowserService(core.service.PISService):
    def GetPosition(self):
        return 'left'
    
    def GetName(self):
        return 'Folders'
    
    def GetViewClass(self):
        return FolderBrowserView
    
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        pass

    def GetIcon(self):
        return wx.GetApp().GetArtProvider().GetIcon(wx.ART_HARDDISK)
    
    def SetPath(self, dir):
        self.GetView().SetPath(dir)
        
FB_NEW_FILE_ID = wx.NewId()   
FB_NEW_DIR_ID  = wx.NewId()
FB_DELETE_ID   = wx.NewId()
FB_RENAME_ID   = wx.NewId()
FB_OPEN_IN_OS_ID = wx.NewId() 
MENU_CHECKOUT_ID = wx.NewId()
MENU_COMMIT_ID = wx.NewId()
MENU_UPDATE_ID = wx.NewId()
MENU_CLEAN_UP_ID = wx.NewId()


class FolderBrowserView(core.service.PISServiceView):
    
    def __init__(self, parent, service,id=-1, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Folder'):
        core.service.PISServiceView.__init__(self, parent, service, id, pos, size, style, name)
            
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        style = wx.DIRCTRL_EDIT_LABELS|wx.DIRCTRL_SHOW_FILTERS
        filter = "All files (*.*)|*.*|Python files (*.py)|*.py|C files(*.cpp;*.c;*.h;*.hpp)|*.cpp;*.c;*.h;*.hpp"
        self._dirctrl = wx.GenericDirCtrl(self, -1, style=style)

        self._dirframe      = None
        self._sizer.Add(self._dirctrl, 1, wx.EXPAND)
        self.SetSizer(self._sizer)
        self.Layout()
        self.SetAutoLayout(True)
        self._browserpage   = None
        self._svnservice    = None
        self._imagecount    = 0
        self._icon_dict     = {}
        self._isClosing     = False
        # event binding...
        wx.EVT_LEFT_DCLICK(self.GetTreeCtrl(), self.OnDoubleClick)
        #self.GetTreeCtrl().Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.GetTreeCtrl().Bind(wx.EVT_TREE_ITEM_MENU, self.OnItemMenu)
        self.GetTreeCtrl().Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.GetTreeCtrl().Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnExpanded)
        wx.EVT_MENU(wx.GetApp().GetTopWindow(), self.GetTreeCtrl().GetId(), self.OnOpen)
        wx.EVT_CLOSE(self, self.OnClose)
        
        config = wx.ConfigBase_Get()
        dir = config.Read('LastDirectory', '')
        self.SetPath(dir)
                
    def OnOpen(self, event):
        return False
    
    def SetPath(self, dir):
        if self._dirctrl == None or not os.path.exists(dir):
            return
        self._dirctrl.SetPath(dir)
        
    def GetLogger(self):
        return self._logger
    
    def GetConfig(self):
        return self._config
    
    def GetTreeCtrl(self):
        return self._dirctrl.GetTreeCtrl()
    
    def GetSvnService(self):
        if not hasattr(self, "_svnservice") or self._svnservice == None:
            pm = wx.GetApp().GetPluginMgr()
            p  = pm.GetPlugin('SvnPlugin')
            if p != None:
                self._svnservice = pm.GetPlugin('SvnPlugin').GetServiceInstance()
            else:
                self._svnservice = None
        
        return self._svnservice
        
    def OnExpanded(self, event):
        self.GetSvnService()
        if self._svnservice == None: return
        
        item = event.GetItem()
        self.GetTreeCtrl().SelectItem(item)
        rootPath = self._dirctrl.GetPath()
        #self._svnservice.GetSvnStatus(rootPath, self.CallbackPathSvnStatus, item)
        (child, cookie) = self.GetTreeCtrl().GetFirstChild(item)
        while child.IsOk():
            path = os.path.join(rootPath, self.GetTreeCtrl().GetItemText(child))
            self._svnservice.GetSvnInfo(path, self.CallbackPathSvnInfo, child)
            self._svnservice.GetSvnStatus(path, False, False, self.CallbackPathSvnStatus, (child, ))
            (child, cookie) = self.GetTreeCtrl().GetNextChild(item, cookie)
               
    def CallbackPathSvnInfo(self, info, item):
        if item == None or not item.IsOk(): return
        timestr = time.strftime( '%d/%m/%y %H:%M', time.localtime(info.data['commit_time']))
        text = self.GetTreeCtrl().GetItemText(item)
        self.GetTreeCtrl().SetItemText(item, '%-15s (r%s, %s, %s)' %  
                                       (text, 
                                       info.data['commit_revision'].number, 
                                       timestr, 
                                       info.data['commit_author'])) 
        
    def CallbackPathSvnStatus(self, status, item):
        imageindex = self.GetTreeCtrl().GetItemImage(item)
        self.GetTreeCtrl().SetItemImage(item, self.GetSvnImage(item, imageindex, status))

    def OnDoubleClick(self, event):
        path =  self._dirctrl.GetPath()
        if  os.path.isdir(path):
            event.Skip()
            return
        
        root, ext = os.path.splitext(path)

        if ext in ['.exe', '.ppt', '.xls', '.doc', '.chm']:
            try:
                os.startfile(path)
            except WindowsError, (winerror, strerror):
                wx.MessageBox('[Window error %d]: %s' % (winerror, strerror),
                              'Fail to open %s in platform shell' % path,
                              style=wx.ICON_ERROR) 
        else:               
            doc = wx.GetApp().GetDocumentManager().CreateDocument(path, 
                                                                  wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
            if doc == None:
                return
            view = doc.GetFirstView()
            if view != None:
                view.Activate()
                if hasattr(view, 'SetFocus'):
                    view.SetFocus()
                    
    def OnItemMenu(self, event):
        item = event.GetItem()
        self.GetTreeCtrl().SelectItem(item)
        self.GetTreeCtrl().PopupMenu(self.CreateRightContextMenu())
        
    def CreateRightContextMenu(self):
        menu = wx.Menu()
        item = wx.MenuItem(menu, FB_NEW_FILE_ID, 'New File', 'Create New File')
        item.SetBitmap(wx.GetApp().GetArtProvider().GetBitmap(wx.ART_NEW))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, FB_NEW_DIR_ID, 'New Dir', 'Create New Directory')
        item.SetBitmap(wx.GetApp().GetArtProvider().GetBitmap(wx.ART_NEW_DIR))
        menu.AppendItem(item)
        item = wx.MenuItem(menu, FB_DELETE_ID, 'Delete', 'Delete file/directory')
        item.SetBitmap(wx.GetApp().GetArtProvider().GetBitmap(wx.ART_DELETE))
        menu.AppendItem(item) 
        item = wx.MenuItem(menu, FB_RENAME_ID, 'Rename', 'Rename file/directory')
        menu.AppendItem(item)   
        item = wx.MenuItem(menu, FB_OPEN_IN_OS_ID, 'Open in OS shell', 'Open in OS shell')
        menu.AppendItem(item)
        self.GetSvnService()
        
        if self._svnservice != None:
            menu.AppendSeparator()        
            menu.AppendSubMenu(self._svnservice.GetSvnMenu(), 'SVN')
            wx.EVT_MENU(self, self._svnservice.ID_UPDATE, self.OnUpdate)
            wx.EVT_MENU(self, self._svnservice.ID_COMMIT, self.OnCommit)
            wx.EVT_MENU(self, self._svnservice.ID_CHECKOUT, self.OnCheckoutModule)
            wx.EVT_MENU(self, self._svnservice.ID_CLEANUP, self.OnCleanup)
            wx.EVT_MENU(self, self._svnservice.ID_REVERT, self.OnRevert)
            wx.EVT_MENU(self, self._svnservice.ID_ADD, self.OnAdd)
            wx.EVT_MENU(self, self._svnservice.ID_REMOVE, self.OnRemove)
            wx.EVT_MENU(self, self._svnservice.ID_CONFIG, self.OnConfig)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_UPDATE, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_COMMIT, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_CHECKOUT, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_CLEANUP, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_REVERT, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_ADD, self.ProcessUpdateUIEvent)
            wx.EVT_UPDATE_UI(self, self._svnservice.ID_REMOVE, self.ProcessUpdateUIEvent)

        wx.EVT_MENU(self, FB_NEW_FILE_ID, self.OnNewFile)
        wx.EVT_MENU(self, FB_NEW_DIR_ID, self.OnNewDir)
        wx.EVT_MENU(self, FB_DELETE_ID, self.OnDelete)
        wx.EVT_MENU(self, FB_RENAME_ID, self.OnRename)
        wx.EVT_MENU(self, FB_OPEN_IN_OS_ID, self.OnOpenInOs)
        wx.EVT_UPDATE_UI(self, FB_NEW_FILE_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, FB_NEW_DIR_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, FB_DELETE_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, FB_RENAME_ID, self.ProcessUpdateUIEvent)
        return menu
    
    def GetSvnImage(self, item, old_index, status):
        icon_status = 'ok'
        
        #
        # BugBug: pysvn can not report status correctly.
        #
        if len(status) == 1 and os.path.isfile(status[0].data['path']):
            snew = self._svnservice.TranslateTextStatus(status[0].data['text_status'])
            if snew == 'unversioned':
                icon_status = 'none'
            if snew in ['added', 'modified', 'missing', 'incomplete']:
                icon_status = 'modified'
        else:
            for s in status:
                snew = self._svnservice.TranslateTextStatus(s.data['text_status'])
                if snew in ['added', 'modified', 'missing', 'incomplete']:
                    icon_status = 'modified'
        """
        for s in status:
            snew = self._svnservice.TranslateTextStatus(s.data['text_status'])
            if snew in ['normal', 'external']:
                icon_status = 'ok'
                continue
            if snew in ['added', 'modified', 'missing', 'incomplete']:
                icon_status = 'modified'
                break
        """
        # mean first time, initialize icon dict.
        imgList = self.GetTreeCtrl().GetImageList()
        if self._imagecount == 0:
            count = imgList.GetImageCount()
            self._imagecount = count
        
            for index in range(count - 1):
                self._icon_dict[index] = {}
                
            newimg  = self._svnservice.GetSvnNoChangeImage()
            for index in range(count - 1):
                img      = imgList.GetBitmap(index).ConvertToImage()
                combined = self._svnservice.CombineImage(img, newimg)
                new_index    = imgList.Add(combined.ConvertToBitmap())
                self._icon_dict[index]['ok'] = new_index
                
            newimg  = self._svnservice.GetSvnModifiedImage()
            for index in range(count - 1):
                img      = imgList.GetBitmap(index).ConvertToImage()
                combined = self._svnservice.CombineImage(img, newimg)
                new_index = imgList.Add(combined.ConvertToBitmap())
                self._icon_dict[index]['modify'] = new_index
            self._imagecount = self.GetTreeCtrl().GetImageList().GetImageCount()
            
        if old_index > self._imagecount or (old_index not in self._icon_dict.keys()):
            self._icon_dict[old_index] = {}
            img = imgList.GetBitmap(old_index).ConvertToImage()
            
            newimg = self._svnservice.GetSvnNoChangeImage()
            combined = self._svnservice.CombineImage(img, newimg)
            new_index    = imgList.Add(combined.ConvertToBitmap())
            self._icon_dict[old_index]['ok'] = new_index

            newimg = self._svnservice.GetSvnModifiedImage()
            combined = self._svnservice.CombineImage(img, newimg)
            new_index    = imgList.Add(combined.ConvertToBitmap())
            self._icon_dict[old_index]['modify'] = new_index
            self._imagecount = imgList.GetImageCount()
        
        if icon_status == 'none':
            return old_index
        elif icon_status == 'modified':
            return self._icon_dict[old_index]['modify']
        else:
            return self._icon_dict[old_index]['ok']
    
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == FB_NEW_FILE_ID or id == FB_NEW_DIR_ID:
            file = self._dirctrl.GetPath()
            event.Enable(os.path.isdir(file))
            return True
        if id == FB_DELETE_ID or id == FB_RENAME_ID:
            path = self._dirctrl.GetPath()
            event.Enable(path[-2:] != ':\\')
            return True
        if id in [wx.ID_CLOSE, wx.ID_CLOSE_ALL, wx.ID_PAGE_SETUP]:
            event.Enable(False)
            return True
        
        # Update svn menu
        if self._svnservice != None:
            if id in [self._svnservice.ID_UPDATE, self._svnservice.ID_COMMIT, \
                      self._svnservice.ID_CHECKOUT, self._svnservice.ID_CLEANUP, \
                      self._svnservice.ID_ADD, self._svnservice.ID_REMOVE]:
                event.Enable(not self._svnservice.IsBusy())
                return True
        return False
    
    def OnConfig(self, event):
        self._svnservice.Config(event)
        
    def OnCheckoutModule(self, event):
        """Check out remote module to selected folder
        """
        item = self.GetTreeCtrl().GetSelection()
        self._svnservice.SvnCheckout(self._dirctrl.GetPath(), self.SvnCallback, (item,))
        
    def OnOpenInOs(self, event):
        path =  self._dirctrl.GetPath()
        root, ext = os.path.splitext(path)

        try:
            os.startfile(path)
        except WindowsError, (winerror, strerror):
            wx.MessageBox('[Window error %d]: %s' % (winerror, strerror),
                          'Fail to open %s in platform shell' % path,
                          style=wx.ICON_ERROR) 
                                      
    def SvnCallback(self, item):
        if not item.IsOk(): return
        text       = self.GetTreeCtrl().GetItemText(item).split('(')[0].strip()
        isExpanded = self.GetTreeCtrl().IsExpanded(item)
        parentItem = self.GetTreeCtrl().GetItemParent(item)
        
        self.GetTreeCtrl().CollapseAndReset(parentItem)
        self.GetTreeCtrl().Expand(parentItem)
        
        (child, cookie) = self.GetTreeCtrl().GetFirstChild(parentItem)
        while (child != None and child.IsOk()):
            if self.GetTreeCtrl().GetItemText(child).find(text) != -1:
                break
            (child, cookie) = self.GetTreeCtrl().GetNextChild(parentItem, cookie)
        if child != None:
            if isExpanded:
                self.GetTreeCtrl().Expand(child)        
            
    def OnCommit(self, event):
        self._svnservice.SvnCommit(self._dirctrl.GetPath(),
                                   self.SvnCallback,
                                   (self.GetTreeCtrl().GetSelection(),))
        
    def OnUpdate(self, event):
        self._svnservice.SvnUpdate(self._dirctrl.GetPath(), 
                                   self.SvnCallback, 
                                   (self.GetTreeCtrl().GetSelection(),))
        
    def OnCleanup(self, event):
        self._svnservice.SvnCleanUp(self._dirctrl.GetPath(), 
                                    self.SvnCallback, 
                                    (self.GetTreeCtrl().GetSelection(),))
        
    def OnRevert(self, event):
        self._svnservice.SvnRevert(self._dirctrl.GetPath(), 
                                   self.SvnCallback, 
                                   (self.GetTreeCtrl().GetSelection(),))
        
    def OnAdd(self, event):
        self._svnservice.SvnAdd(self._dirctrl.GetPath(), 
                                self.SvnCallback, 
                                (self.GetTreeCtrl().GetSelection(),))
        
    def OnRemove(self, event):
        self._svnservice.SvnRemove(self._dirctrl.GetPath(), 
                                   self.SvnCallback, 
                                   (self.GetTreeCtrl().GetSelection(),))
        
    def OnNewFile(self, event):
        base = 'NewFile'
        dir  = self._dirctrl.GetPath()
        for i in range(100):
            name = '%s%d' % (base, i)
            path = os.path.join(dir, name)
            if not os.path.exists(path):
                break
        try:
            file = open(path, 'w')
            file.close()
        except:
            self.GetLogger().exception('Fail to create file %s under %s' %(name, dir))
            wx.MessageBox('Fail to create file %s under %s' %(name, dir), 'Error', wx.OK)
            return
            
        item = self.GetTreeCtrl().GetSelection()
        if self.GetTreeCtrl().IsExpanded(item):
            self.Freeze()
            self.GetTreeCtrl().CollapseAndReset(item)
            self.GetTreeCtrl().Expand(item)
            self.Thaw()
        else:
            self.GetTreeCtrl().SetItemHasChildren(item)
            self.GetTreeCtrl().Expand(item)
            
        (child, cookie) = self.GetTreeCtrl().GetFirstChild(item)
        while child.IsOk():
            t = self.GetTreeCtrl().GetItemText(child)
            if t == name:
                newChild = child
                break
            (child, cookie) = self.GetTreeCtrl().GetNextChild(item, cookie)
        self.GetTreeCtrl().EditLabel(newChild)
    
    def OnNewDir(self, event):
        base = 'NewDir'
        dir  = self._dirctrl.GetPath()
        for i in range(100):
            name = '%s%d' % (base, i)
            path = os.path.join(dir, name)
            if not os.path.exists(path):
                break
            
        try:
            os.mkdir(path)
        except:
            self.GetLogger().exception('Fail to create dir %s under %s' % (name, dir))
            wx.MessageBox('Fail to create dir %s under %s' %(name, dir), 'Error', wx.OK)
            return


        item = self.GetTreeCtrl().GetSelection()
        if self.GetTreeCtrl().IsExpanded(item):
            self.Freeze()
            self.GetTreeCtrl().CollapseAndReset(item)
            self.GetTreeCtrl().Expand(item)
            self.Thaw()
        else:
            self._dirctrl.ExpandPath(path)
            self.GetTreeCtrl().CollapseAndReset(item)
            self.GetTreeCtrl().Expand(item)
            
            
        (child, cookie) = self.GetTreeCtrl().GetFirstChild(item)
        while child.IsOk():
            t = self.GetTreeCtrl().GetItemText(child)
            if t == name:
                newChild = child
                break
            (child, cookie) = self.GetTreeCtrl().GetNextChild(item, cookie)
        self.GetTreeCtrl().EditLabel(newChild)

    def OnDelete(self, event):
        item = self.GetTreeCtrl().GetSelection()
        path = self._dirctrl.GetPath()
        
        if os.path.isdir(path):
            if len(os.listdir(path)) != 0:
                dlg = wx.MessageDialog(self, 'Do you really want remove non-blank dir %s' % path,
                                       'Warning', wx.YES_NO|wx.ICON_WARNING)
                dlg.CenterOnParent()
                result = dlg.ShowModal()
                if result == wx.ID_NO or not result:
                    return
            try:
                import shutil
                shutil.rmtree(path, False, self.CallBackOnDelError)
            except WindowsError, e:
                wx.MessageBox('Fail to delete dir %s: %s' % (path, e))
                return
        else:
            try:
                os.remove(path)
            except WindowsError, e:
                wx.MessageBox('Fail to delete file %s: %s' % (path, e))
                return
                
        self.GetTreeCtrl().Delete(item)
    
    def CallBackOnDelError(self, func, path, excinfo):
        # change file attribute to writable
        os.chmod (path, stat.S_IWRITE)
        # try again
        func(path)
        
    def OnRename(self, event):
        item = self.GetTreeCtrl().GetSelection()
        self.GetTreeCtrl().EditLabel(item)
        
    def OnSelChanged(self, event):
        if self._isClosing:
            return 
        
        if not os.path.isdir(self._dirctrl.GetPath()): 
            return
        
        name = wx.GetApp().GetAppName()
        wx.GetApp().GetTopWindow().SetTitle('%s - [Folder] %s' % (name, self._dirctrl.GetPath()))

        if wx.Platform != '__WXMSW__':
            return

        # Open the folder browser to get customer's feedback.
        #if not self._config.GetBoolean('EnableBrowser', False):
        #    return 

        # search the opened folder browser frame first.
        frame = wx.GetApp().GetTopWindow()
        nb    = frame.GetNotebook()
        count = nb.GetPageCount()
        index = -1
        for i in range(count):
            text = nb.GetPageText(i)
            if text == "Folder Browser":
                index = i
                
        if index == -1:
            self._browserpage = DirBrowerFrame(nb, self._dirctrl, self._dirctrl.GetPath())
            frame.AddNotebookPage(self._browserpage, 'Folder Browser')            
        else:
            nb.SetSelection(index)
            page = nb.GetPage(index)
            page.OpenDir(self._dirctrl.GetPath())
        
        event.Skip()
            
    def OnClose(self, event):
        # Disable general dir control to skip all windows event
        self._isClosing = True
        
        # DeActivate svn service.
        if self._svnservice != None:
            self._svnservice.DeActivate()

        # destroy browser page
        #if self._browserpage != None:
        #    self._browserpage.Close()

        # destroy dir control
        if self._dirctrl != None:
            self._dirctrl.Destroy()
            self._dirctrl = None
            
        return True
    
class DirBrowerFrame(wx.Panel):
    def __init__(self, parent, dirctrl, defaultPath):
        wx.Panel.__init__(self, parent)         
        self._lastdir = None
        self._dirctrl = dirctrl
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.Freeze()
        #self._ie = iewin.IEHtmlWindow(self, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self._ie = iewin.IEHtmlWindow(self, -1)
        sizer.Add(self._ie, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.Thaw()
        self.Layout()
        self.OpenDir(defaultPath)
        self._ie.AddEventSink(self)
        
        wx.EVT_CLOSE(self, self.OnClose)
        
    def GetView(self):
        return self
    
    def GetDocument(self):
        return None
    
    def OpenDir(self, path):
        if not os.path.exists(path):
            return
        self.Freeze()
        try:
            self._ie.LoadUrl(path)
        except:
            wx.GetApp().GetLogger().warning('Folder Browser fail to load url %s' % path)
            self.Thaw()
            return
        
        self.Thaw()
        self._lastdir = path
        
    def Activate(self):
        if self._lastdir == None:
            return
        frame = wx.GetApp().GetTopWindow()
        frame.SetTitle('%s - [Folder] %s' % (wx.GetApp().GetAppName(), self._lastdir))
        
    def OnTitleChange(self, event):
        dir = self._dirctrl.GetPath()
        if not os.path.isdir(dir):
            return
        
        tree = self._dirctrl.GetTreeCtrl()
        item = tree.GetSelection()
        if tree.GetItemText(item) == unicode(event.Text):
            return
        if unicode(event.Text) not in os.listdir(self._dirctrl.GetPath()):
            return

        tree.Expand(item)
        
        (child, cookie) = tree.GetFirstChild(item)
        foundItem = None
        while child.IsOk():
            p = tree.GetItemText(child)
            u = unicode(event.Text)
            if unicode(event.Text) == p:
                foundItem = child
                break
            (child, cookie) = tree.GetNextChild(item, cookie)
        if foundItem != None:
            tree.SelectItem(foundItem)
            tree.Expand(foundItem)

    def OnKeyDown(self, event):
        print 'key'
        
    def OnTreeKeyDown(self, event):
        print '22'
        
    def OnError(self, event):
        print 'error'
        
    def OnClose(self, event):
        # Disable IE COM to shield all COM event
        self._ie.Disable()
        
        # Destroy IE COM control
        self._ie.Destroy()
        
        return True
    
    def DocumentComplete(self, this, pDisp, URL):
    # COM interface implementation:
        path = self._dirctrl.GetPath()
        if path != URL[0]:
            self._dirctrl.SetPath(URL[0])
        
    def NewWindow2(self):
        pass
    
    def NewWindow3(self):
        pass
