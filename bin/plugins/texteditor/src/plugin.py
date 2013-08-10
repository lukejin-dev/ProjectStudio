import os
import wx
import interfaces.core
import interfaces.docview
from interfaces.docview import *
import editor
 
_=wx.GetTranslation

class TextDocument(IDocument):
    def __init__(self, provider, path):
        IDocument.__init__(self, provider, path)
        self._cache = None

    def GetText(self):
        return self._cache
    
    def GetViewClasses(self):
        return [TextView]

    def LoadObject(self):
        try:
            fd = open(self.GetFilename(), "r")
        except Exception, e:
            logger.error("Fail to open the file %s!\n%s" % (self.GetFilename(), e))
            return False
        
        try:
            self._cache = fd.read()
        except:
            logger.error("Fail to read file %s" % self.GetFilename())
            return False
        
        fd.close()
        return True
     
    def SaveObject(self, path):
        try:
            fd = open(path, "w")
        except:
            logger.error("Fail to open the file %s" % path)
            return False
        
        try:
            fd.write(self.GetFirstView().GetText())
        except Exception, e:
            logger.error("Fail to write content to disk for %s" % path)
            print e
            fd.close()
            return False
        
        fd.close()
        return True   
            
import wx.stc
class TextView(IDocView):
    def __init__(self, doc=None):
        IDocView.__init__(self, doc)
        self._editor = None
        EVT_VIEW_UPDATE(self, self.OnUpdate)
        EVT_VIEW_CREATING(self, self.OnCreate)
        
    def GetText(self):
        return self._editor.GetText()
    
    def OnCreate(self, event):
        """Event handler for EVT_VIEW_CREATING."""
        frame = self.GetFrame()
        frame.Freeze()
        size = wx.BoxSizer(wx.VERTICAL)
        self._editor = editor.TextEditor(frame, self)
        size.Add(self._editor, 1, wx.EXPAND|wx.ALL, 0)
        frame.SetSizer(size)
        frame.Layout()
        frame.Thaw()
        self._editor.SetFocus()
        
        frame.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModify)
        
    def IsModified(self):
        if self._editor == None:
            return False
        return self._editor.GetModify()
    
    def OnModify(self, event):
        self.ProcessEvent(ViewModifiedEvent(modified=self._editor.GetModify()))
        
    def OnUpdate(self, event):
        logger.info("View is update for reason:%s" % event.hint)
        text = self.GetDoc().GetText()
        if text != None:
            self._editor.SetText(self.GetDoc().GetText())
        
    def SetModifyFalse(self):
        IDocView.SetModifyFalse(self)
        self._editor.SetSavePoint()
        
def __extension_main__(pluginInfo):
    global logger
    logger = wx.GetApp().GetLogger("TextEditor")
        
    bitmap = wx.Bitmap(os.path.join(pluginInfo.GetPath(), "icons", "textfile.ico"))
    docmgr = wx.GetApp().GetDocManager()
    docmgr.RegisterDocumentProvider("TextFile", _("Text File"), ["txt", "log", "*"], TextDocument, bitmap, False)
    
    