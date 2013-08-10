import os
import stat
import wx
import wx.lib.agw.genericmessagedialog as gmd

from event import *
from core import *

DocumentCloseEvent, EVT_DOCUMENT_CLOSE = NewNotifyEvent()

_=wx.GetTranslation

class IDocument(Interface, wx.EvtHandler):
    def __init__(self, provider, path=None):
        wx.EvtHandler.__init__(self)

        self._filename = None
        self._lastFileDate = None
        if path != None:
            self._filename = os.path.normpath(path)
            if os.path.exists(self._filename):
                self._lastFileDate = os.stat(self._filename)[stat.ST_MTIME]
        
        self._logger   = wx.GetApp().GetLogger("DocView")
        self._views    = []
        self._provider = provider
        
    def Close(self, destoryView=True):
        ret = True
        if self.IsModified():
            name = self.GetFilename()
            if name == None:
                name = self.GetFirstView().GetDescription()
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("File %s is modified, Do you want to save?" % name, 
                                                                 "Close Document", 
                                                                 wx.ICON_ASTERISK|wx.OK|wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                ret = self.Save()
            dlg.Destroy()
        return ret
    
    def CreateViews(self):
        """Create document's views."""
        classes = self.GetViewClasses()
        if classes == None:
            return
        for cls in classes:
            view = cls(self)
            view.Create()
            self._views.append(view)

        for view in self._views:
            view.Update(hint="ViewCreate")
            
    def DestroyAllViews(self):
        """Destroy document's views."""
        
    def GetBitmap(self):
        return self._provider.GetBitmap()
    
    def GetFilename(self):
        return self._filename
    
    def GetFirstView(self):
        if len(self._views) == 0:
            return None
        return self._views[0]
    
    def GetLogger(self):
        return self._logger
    
    def GetProvider(self):
        return self._provider
    
    @interface
    def GetViewClasses(self):
        """Get list of all document views."""
    
    def GetViews(self):
        return self._views
    
    def IsDirty(self):
        """Is document dirty. The reason of document dirty is document
        updated by third part tools out of project studio.
        """
        if self.GetFilename() == None:
            return False
        lastModDate = os.stat(self.GetFilename())[stat.ST_MTIME]
        return lastModDate != self._lastFileDate
    
    def IsModified(self):
        for view in self.GetViews():
            if view.IsModified():
                return True
        return False
    
    def Load(self):
        """Load file content to memory."""
        ret = False
        try:
            ret = self.LoadObject()
        except Exception, e:
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("Fail to load file %s, because %s!" % (self.GetFilename(), str(e)), 
                                                                 "Failure of loading file", 
                                                                 style=wx.ICON_ERROR|wx.OK)
            if dlg != None:
                dlg.ShowModal()
                dlg.Destroy()
            return False   
        
        if not ret:
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("Fail to load file %s!" % self.GetFilename(), 
                                                                 "Failure of loading file", 
                                                                 wx.ICON_ERROR|wx.OK)
            if dlg != None:
                dlg.ShowModal()
                dlg.Destroy()
            return False   
            
        self.UpdateFileDate()
        return True
    
    def Reload(self):
        """Load file content to memory."""
        if not self.LoadObject():
            return False
        
        for view in self.GetViews():
            view.Update(hint="DocumentLoad")
            view.SetModifyFalse()
        self._lastFileDate = os.stat(self.GetFilename())[stat.ST_MTIME]
        return True
        
    def LoadObject(self):
        """Load file object to memory. This interface need to be implemented by child."""
        return True
        
    def Save(self):
        """Save file content to disk."""
        filename = self.GetFilename()
        if filename == None:
            filename = os.path.join(wx.StandardPaths.Get().GetDocumentsDir(), self.GetFirstView().GetDescription() + ".txt")
            dlg = wx.FileDialog(wx.GetApp().GetMainFrame(), "Save file %s as ..." % self.GetFirstView().GetDescription(), os.path.dirname(filename),
                                os.path.basename(filename), "*.txt", wx.FD_SAVE)
            dlg.CenterOnScreen()
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            filename = dlg.GetPath()
            dlg.Destroy()
            
            if os.path.exists(filename):
                dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("File %s already exists, Do you want to overwrite?" % filename, 
                                                                     "File Overwritten", 
                                                                     wx.ICON_ASTERISK|wx.OK|wx.CANCEL,
                                                                     "FileOverwritten")
                if dlg != None and dlg.ShowModal() != wx.ID_OK:
                    return False
                
        elif not self.IsModified():
            return True
        
        if not self.SaveObject(filename):
            return False

        self._lastFileDate = os.stat(filename)[stat.ST_MTIME]
        
        for view in self.GetViews():
            view.SetModifyFalse()
        
        if self.GetFilename() == None:
            self.SetFilename(filename)
        
        return True
        
    def SaveAs(self):
        filename = self.GetFilename()
        if filename == None:
            filename = os.path.join(wx.StandardPaths.Get().GetDocumentsDir(), self.GetFirstView().GetDescription() + ".txt")
        
        provider = self.GetProvider()
        exts = ["*.%s" % ext for ext in provider.GetExts()]
        extstr = ";".join(exts)
        wildcard = "%s (%s)|%s" % (provider.GetDescription(), extstr, extstr)
        
        dlg = wx.FileDialog(wx.GetApp().GetMainFrame(), "Save file %s as ..." % self.GetFirstView().GetDescription(), os.path.dirname(filename),
                            os.path.basename(filename), wildcard, wx.FD_SAVE)
        dlg.CenterOnScreen()
        dlg.ShowModal()
        filename = dlg.GetPath()
        dlg.Destroy()
        
        if os.path.exists(filename):
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("File %s already exists, Do you want to overwrite?" % filename,
                                                                 "File Overwritten",
                                                                 wx.ICON_ASTERISK|wx.OK|wx.CANCEL,
                                                                 "FileOverwritten")
            if dlg != None and dlg.ShowModal() != wx.ID_OK:
                return False
            
        if not self.SaveObject(filename):
            return False
                    
        self._lastFileDate = os.stat(filename)[stat.ST_MTIME]
        self.SetFilename(filename)
        for view in self.GetViews():
            view.SetModifyFalse()        
        return True
        
    def SaveObject(self, path):
        """Save object to disk, need to be inherited from child class."""
        return True
    
    def SetDirty(self, isDirty=True):
        self._isDirty = isDirty
        
    def SetFilename(self, path):
        if path == None:
            self._filename = None
        elif self._filename == None or self._filename != os.path.normpath(path):
            self._filename = path
            for view in self.GetViews():
                view.ProcessEvent(ViewTitleChangeEvent(name=os.path.normpath(path)))
        
    def UpdateFileDate(self):
        filename = self.GetFilename()
        if filename == None or not os.path.exists(filename):
            return
        self._lastFileDate = os.stat(filename)[stat.ST_MTIME]
        
ViewUpdateEvent, EVT_VIEW_UPDATE = NewEvent()        
ViewCreatingEvent, EVT_VIEW_CREATING = NewEvent()
"""ViewCloseEvent is triggered when want to close a view, this event can be Veto()."""
ViewCloseEvent, EVT_VIEW_CLOSE = NewNotifyEvent()
ViewModifiedEvent, EVT_VIEW_MODIFIED = NewEvent()
ViewTitleChangeEvent, EVT_VIEW_TITLE_CHANGE = NewEvent()
ViewActiveEvent, EVT_VIEW_ACTIVE = NewEvent()

class IDocView(Interface, wx.EvtHandler):
    """Doc view class manage the view page in IDE center notebook."""
    _untitlecount = 0
    
    def __init__(self, doc=None):
        wx.EvtHandler.__init__(self)
        self._doc   = doc
        self._frame = None
        self._ucount = -1
        self._lastModifyState = False
        self._monitorTimer = wx.Timer(self)
        self._logger = wx.GetApp().GetLogger("DocView")
        
        wx.EVT_TIMER(self, self._monitorTimer.GetId(), self.OnMonitorTimer)
        EVT_VIEW_CLOSE(self, self.OnViewClose)
        EVT_VIEW_MODIFIED(self, self.OnViewModified)
        EVT_VIEW_TITLE_CHANGE(self, self.OnViewTitleChange)
        EVT_VIEW_ACTIVE(self, self.OnViewActive)
        
    def Active(self):
        self.GetFrame().Active()
    
    def Close(self):
        wx.GetApp().GetMainFrame().GetChildFrame().CloseView(self)
        
    def Create(self):
        self._frame = wx.GetApp().GetMainFrame().GetChildFrame().CreateViewFrame(self)
        self.ProcessEvent(ViewCreatingEvent())
        
    def GetBitmap(self):
        if self._doc != None:
            return self._doc.GetBitmap()
        return wx.NullBitmap
    
    def GetDescription(self):
        if self._doc != None:
            if self._doc.GetFilename() != None:
                return self._doc.GetFilename()
        
        if self.GetUntitledCount() == 0:
            title = _("Untitled")
        else:
            title = _("Untitled") + "%d" % self.GetUntitledCount()
        return title
        
    def GetDoc(self):
        return self._doc
    
    def GetFrame(self):
        return self._frame
    
    def GetId(self):
        return self._id
    
    def GetLogger(self):
        return self._logger
    
    def GetName(self):
        if self._doc != None:
            if self._doc.GetFilename() != None:
                return os.path.basename(self._doc.GetFilename())
        
        if self.GetUntitledCount() == 0:
            title = _("Untitled")
        else:
            title = _("Untitled") + "%d" % self.GetUntitledCount()
        return title

    def GetUntitledCount(self):
        if self._ucount == -1:
            self._ucount = IDocView._untitlecount
            IDocView._untitlecount += 1
        return self._ucount
    
    def IsActive(self):
        return wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView() == self
    
    def IsModified(self):
        """This interface need to be inherited by child class."""
        return False
    
    def OnMonitorTimer(self, event):
        
        doc = self.GetDoc()
        filename = doc.GetFilename()

        if filename == None:
            return

        if not os.path.exists(filename):
            self._monitorTimer.Stop()
            self.GetLogger().info("%s does not exist!" % filename)
            self.GetDoc().SetFilename(None)
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("File %s has been deleted! Do you want to close?" % self.GetDescription(),
                                                                 "File Manager",
                                                                 wx.ICON_ASTERISK|wx.OK|wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                self.Close()
            return
        
        if doc.IsDirty():
            self._monitorTimer.Stop()
            self.GetLogger().info("File %s is dirty and reloading..." % self.GetDescription())
            dlg = wx.GetApp().GetMainFrame().CreateConfirmDialog("File %s is modified out of ProjectStudio, Do you want to reload?" % self.GetDescription(),
                                                                 "File Manager",
                                                                 wx.ICON_ASTERISK|wx.OK|wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                doc.Reload()
            else:
                self.GetDoc().UpdateFileDate()
            dlg.Destroy()
            self._monitorTimer.Start(2000, wx.TIMER_CONTINUOUS)
            
    def OnViewActive(self, event):
        if self.GetDoc() == None:
            return

        if event.active:
            self._monitorTimer.Start(2000, wx.TIMER_CONTINUOUS)
        else:
            self._monitorTimer.Stop()
        
    def OnViewClose(self, event):
        self._monitorTimer.Stop()
        doc = self.GetDoc()
        if doc != None:
            if not wx.GetApp().GetDocManager().CloseDocument(doc):
                event.Veto()
        
    def OnViewModified(self, event):
        if event.modified:
            if self._lastModifyState:
                return
            else:
                self._lastModifyState = True
                self.GetFrame().SetTitle(self.GetFrame().GetTitle() + "*")
        else:
            if not self._lastModifyState:
                return
            else:
                self._lastModifyState = False
                self.GetFrame().SetTitle(self.GetFrame().GetTitle()[:-1])
            
    def OnViewTitleChange(self, event):
        self.GetFrame().SetTitle(self.GetName())
        if self.IsActive():
            wx.GetApp().GetMainFrame().SetTitle(self.GetDescription() + " - " + wx.GetApp().GetAppName())
        
        if not self._monitorTimer.IsRunning():
            self._monitorTimer.Start(2000, wx.TIMER_CONTINUOUS)
            
    def SetModifyFalse(self):
        """Set view modify state. """
        self.ProcessEvent(ViewModifiedEvent(modified=False))
        
    def Update(self, hint=None):
        self.ProcessEvent(ViewUpdateEvent(hint=hint))
    
            
class IDocumentManager(Interface):
    pass
        