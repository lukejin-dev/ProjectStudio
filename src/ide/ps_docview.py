import os
import wx
import interfaces.core
import interfaces.docview
import ps_error
import ps_mainframe
import ps_menu

class PSDocProvider:
    def __init__(self, typeName, typeDesc, exts, docClass, bitmap, readonly, activeSceneName):
        self._typeName = typeName
        self._typeDesc = typeDesc
        if exts == None:
            self._exts = []
        else:
            self._exts    = exts
        self._docClass    = docClass
        self._bitmap      = bitmap
        self._isReadOnly  = readonly
        self._sceneName   = activeSceneName
        
    def CreateDocument(self, path=None):
        doc = self._docClass(self, path)
        doc.CreateViews()
        
        # Post event to load document object to memory.
        if path != None:
            doc.Load()
        
        wx.GetApp().GetDocManager().ManageDoc(doc)
        return doc
    
    def OpenDocument(self, path):
        doc = self._docClass(self, path)
        if doc.Load():
            doc.CreateViews()
            for view in doc.GetViews():
                view.Update(hint="DocumentLoad")
                view.SetModifyFalse()

            wx.GetApp().GetDocManager().ManageDoc(doc)
            return doc
        else:
            return None
    
    def GetDescription(self):
        return self._typeDesc
    
    def GetExts(self):
        return self._exts
    
    def GetBitmap(self):
        return self._bitmap
    
    def GetName(self):
        return self._typeName
    
    def IsActive(self, sceneName):
        if self._sceneName == None:
            return True
        elif sceneName.lower() == self._sceneName.lower():
            return True
        return False
    
    def IsReadOnly(self):
        return self._isReadOnly
    
class PSDocManager(interfaces.docview.IDocumentManager):
    def __init__(self):
        self._logger = wx.GetApp().GetLogger("DocManager")
        self._config = wx.GetApp().GetConfig("DocManager")
        self._providers  = {}
        self._extMapping = {}
        self._docs       = []
        self._latestOpened = self._GetLatestOpenedFileList()
        
        frame = wx.GetApp().GetMainFrame()
        wx.EVT_UPDATE_UI(frame, ps_mainframe.ID_MENU_FILE_SAVE, self.OnUpdateMenuSave)
        wx.EVT_UPDATE_UI(frame, ps_mainframe.ID_MENU_FILE_SAVE_AS, self.OnUpdateMenuSaveAs)
        wx.EVT_UPDATE_UI(frame, ps_mainframe.ID_MENU_FILE_SAVEALL, self.OnUpdateMenuSaveAll)
        wx.EVT_UPDATE_UI(frame, ps_mainframe.ID_MENU_LASTEST_OPEN, self.OnUpdateMenuLatestOpened)
        wx.EVT_MENU(frame, ps_mainframe.ID_MENU_FILE_SAVE, self.OnFileSave)
        wx.EVT_MENU(frame, ps_mainframe.ID_MENU_FILE_SAVEALL, self.OnFileSaveAll)
        wx.EVT_MENU(frame, ps_mainframe.ID_MENU_FILE_OPEN, self.OnFileOpen)
        wx.EVT_MENU(frame, ps_mainframe.ID_MENU_FILE_SAVE_AS, self.OnFileSaveAs)
        
    def AddFileToHistory(self, path):
        if path in self._latestOpened:
            return
        if len(self._latestOpened) == 10:
            del self._latestOpened[9]
            
        self._latestOpened.insert(0, path)
        self._config.Set("LatestOpenedFileList", ";".join(self._latestOpened))
        
        item = self._latestSubMenu.Insert(0, -1, path, "Open file %s" % path)
        wx.EVT_MENU(wx.GetApp().GetMainFrame(), item.GetId(), self.OnMenuOpenHistory)
        
    def CloseDocument(self, doc):
        if not doc.Close():
            return False
        self._docs.remove(doc)
        del doc
        return True
    
    def CreateDocument(self, path=None, name=None):
        """Create document according to document type name and file extension string.
        
        @param name    document type name.
        @param ext     file extensionn string.
        """
        if path != None:
            file, ext = os.path.splitext(path)
        else:
            ext = None
            
        provider = self._FindProvider(name, ext)
        if provider == None:
            self._logger.error("Fail to find the document provider!")
            return None
        return provider.CreateDocument(path)

    def GetCenterFrame(self):
        return self.GetMainFrame().GetChildFrame()
    
    def GetDocs(self):
        return self._docs
    
    def GetMainFrame(self):
        return wx.GetApp().GetMainFrame()
    
    def GetProviders(self):
        return self._providers
    
    def ManageDoc(self, doc):
        if doc in self._docs:
            self._logger.error("doc %s has been managed!" % doc.GetFilename())
            return
        self._docs.append(doc)
        if doc.GetFilename() != None:
            self.AddFileToHistory(doc.GetFilename())
            
    def OnFileOpen(self, event):
        wildcards = []
        for provider in self.GetProviders().values():
            exts = ["*.%s" % ext for ext in provider.GetExts()]
            extstr = ";".join(exts)
            wildcards.append("%s (%s)|%s" % (provider.GetDescription(), extstr, extstr))
        
        dlg = wx.FileDialog(wx.GetApp().GetMainFrame(), "Open ...", "",
                            "", "|".join(wildcards), wx.FD_OPEN)
        dlg.CenterOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            self.OpenDocument(dlg.GetPath())
        
    def OnFileSave(self, event):
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        doc  = view.GetDoc()
        doc.Save()
    
    def OnFileSaveAs(self, event):
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        doc  = view.GetDoc()
        doc.SaveAs()
        
    def OnFileSaveAll(self, event):
        for doc in self.GetDocs():
            doc.Save()
    
    def OnMenuOpenHistory(self, event):
        id = event.GetId()
        item = self._latestSubMenu.FindItem(id)
        self.OpenDocument(item.GetLabel())
        
    def OpenDocument(self, path):
        if path == None or not os.path.exists(path):
            self._logger.error("Fail to open file for invalid path %s" % path)
            return
        path = os.path.normpath(path)
        for doc in self.GetDocs():
            if doc.GetFilename() == None:
                continue
            
            if doc.GetFilename().lower() == path.lower():
                view = doc.GetFirstView()
                view.Active()
                return
            
        base, ext = os.path.splitext(path)
        provider = self._FindProvider(None, ext)
        if provider == None:
            self._logger.error("Fail to find the document provider!")
            return None
        
        return provider.OpenDocument(path)
        
    def OnUpdateMenuLatestOpened(self, event):
        event.Enable(len(self._latestOpened) != 0)
    
    def OnUpdateMenuSave(self, event):
        childframe = wx.GetApp().GetMainFrame().GetChildFrame()
        view = childframe.GetActiveView()
        if view == None:
            event.Enable(False)
            return
        
        if view.IsModified():
            event.Enable(True)
        else:
            event.Enable(False)
        
    def OnUpdateMenuSaveAs(self, event):
        view = self.GetCenterFrame().GetActiveView()
        if view == None:
            event.Enable(False)
            return
        else:
            doc = view.GetDoc()
            if doc == None:
                event.Enable(False)
                return
            
            if doc.GetProvider().IsReadOnly():
                event.Enable(False)
                return
            
        event.Enable(True)
                
    
    def OnUpdateMenuSaveAll(self, event):
        for doc in self.GetDocs():
            if doc.IsModified():
                event.Enable(True)
                return
        event.Enable(False)
        
    def RegisterDocumentProvider(self, typeName, typeDesc, exts, docClass, bitmap=wx.NullBitmap, 
                                 readonly=False, activeSceneName=None):
        """Register a new document type.
        
        @param typeName     the type name of document
        @param typeDesc     the type description of document
        @param exts         the list of file extensions
        @param docClass     the class of document
        """
        if typeName.lower() in self._providers.keys():
            self._logger.error("The document provider %s is registered failed due to already exist!" % typeName)
            return

        if not issubclass(docClass, interfaces.docview.IDocument):
            self._logger.error("The document class %s is not an implement class for IDocument." % docClass.__name__)
            return
        
        if exts != None:
            if type(exts) != type([]):
                self._logger.error("The ext parameter for RegisterDocumentProvider() should be a list!")
                return
            for ext in exts:
                if ext.lower() in self._extMapping.keys():
                    self._logger.error("The file ext %s has been provided by %s document type!" % (ext, self._extMapping[ext.lower()].GetName()))
                    return
                
        provider = PSDocProvider(typeName, typeDesc, exts, docClass, bitmap, readonly, activeSceneName)
        self._providers[typeName.lower()] = provider
        for ext in provider.GetExts():
            self._extMapping[ext.lower()] = provider 
            
    def _FindProvider(self, name, ext):
        if ext == None or ext == "":
            if name == None:
                return self._extMapping["*"]
            elif name.lower() not in self._providers.keys():
                self._logger.error("Fail to determine the document provider by name %s and ext %s" % (name, ext))
                return None
            return self._providers[name.lower()]
        else:
            if ext.startswith("."):
                ext = ext[1:]
            if name == None and not self._extMapping.has_key(ext.lower()):
                return self._extMapping["*"]
            if name != None and self._extMapping[ext.lower()] != self._providers[name.lower()]:
                self._logger.error("The document providers computed by name and ext are different!")
                return None
            return self._extMapping[ext.lower()]
            
        
    def _GetLatestOpenedFileList(self):
        frame = wx.GetApp().GetMainFrame()
        latestMenuItem = frame.GetMenuBar().FindMenuItem(ps_mainframe.ID_MENU_LASTEST_OPEN)
        self._latestSubMenu  = ps_menu.PSMenu()
        latestMenuItem.SetSubMenu(self._latestSubMenu)

        latest = self._config.Get("LatestOpenedFileList", "")
        if latest == "":
            return []
        
        filelist = latest.split(";")
        for file in filelist:
            if os.path.exists(file):
                item = self._latestSubMenu.Append(-1, file, "Open latest file %s" % file, wx.ITEM_NORMAL)
                wx.EVT_MENU(frame, item.GetId(), self.OnMenuOpenHistory)
            else:
                filelist.remove(file)
        if len(filelist) != 0:
            self._config.Set("LatestOpenedFileList", ";".join(filelist))
        return latest.split(";")
    
    
        
        
        