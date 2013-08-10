import os, sys, locale
import wx
import interfaces.core
import interfaces.docview
import codecs
from interfaces.docview import *
from interfaces.event import *
import editor
 
_=wx.GetTranslation

BOMTable = {"utf-8": codecs.BOM_UTF8, "utf-16": codecs.BOM}

class TextDocument(IDocument):
    def __init__(self, provider, path):
        IDocument.__init__(self, provider, path)
        self._cache = None
        self._encoding = "utf-8"        # default encoding is utf-8
        self._bom = None
        
    def CheckBom(self, fd):
        try:
            teststr = fd.read(4)
        except Exception, e:
            self.GetLogger().error("Fail to read file %s for checking BOM" % self.GetFilename())
            fd.close()
            return False
        
        for encoding, bomstr in BOMTable.iteritems():
            if teststr.startswith(bomstr):
                self._encoding = encoding
                self._bom = encoding
                return True

        return False
    
    def GetEncoding(self):
        return self._encoding
    
    def GetText(self):
        return self._cache
    
    def GetViewClasses(self):
        return [TextView]

    def LoadObject(self):
        try:
            fd = open(self.GetFilename(), "rb")
        except Exception, e:
            self.GetLogger().error("Fail to open file %s" % self.GetFilename())
            return False

        if self.CheckBom(fd):
           self.GetLogger().info("File %s contains %s BOM." % (self.GetFilename(), self._encoding))
           fd.seek(0) 
           reader = codecs.getreader(self._encoding)(fd)
           self._cache =  reader.read()
        else:
            self._cache = self.DetectEncodingAndRead(fd)
        
        fd.close()
        
        if self._bom:
            self._cache.replace(unicode(BOMTable[self._bom], self._bom), u'', 1)
        
        
        return True
     
    def SaveObject(self, path):
        try:
            fd = open(path, "wb")
        except:
            logger.error("Fail to open the file %s" % path)
            return False
        
        try:
            writer = codecs.getwriter(self._encoding)(fd)
        except Exception, e:
            logger.error("Fail to get encoding writer for file %s." % path)
            fd.close()
            return False
        
        text = self.GetFirstView().GetText()
        if self._bom != None:
            text = unicode(BOMTable[self._bom], self._bom) + text
        writer.write(text)
            
        fd.close()
        return True   
            
    def DetectEncodingAndRead(self, fd):
        encodings = ["utf-8", "utf-16"]
        if locale.getpreferredencoding() not in encodings:
            encodings.append(locale.getpreferredencoding())
        if sys.getdefaultencoding() not in encodings:
            encodings.append(sys.getdefaultencoding())
        if locale.getdefaultlocale()[1] not in encodings:
            encodings.append(locale.getdefaultlocale()[1])
        if sys.getfilesystemencoding() not in encodings:
            encodings.append(sys.getfilesystemencoding())
        if 'latin-1' not in encodings:
            encodings.append('latin-1')
            
        for enc in encodings:
            fd.seek(0)
            try:
                reader = codecs.getreader(enc)(fd)
                content = reader.read()
            except:
                continue
            else:
                self._encoding = enc
                logger.info("Detect file %s 's encoding is %s" % (self.GetFilename(), self._encoding))
                return content
            
        logger.error("Fail to detect the encoding for file %s" % self.GetFilename())
        return None
            
import wx.stc
class TextView(IDocView):
    _viewmenu = None
    
    def __init__(self, doc=None):
        IDocView.__init__(self, doc)
        self._editor = None
        EVT_VIEW_UPDATE(self, self.OnUpdate)
        EVT_VIEW_CREATING(self, self.OnCreate)
        EVT_VIEW_ACTIVE(self, self.OnTextViewActive)
        EVT_VIEW_CLOSE(self, self.OnTextViewClose)
        EVT_QUERY_VIEW_SEARCH_EVENT(self, -1, self.OnQueryCanSearch)
        
    def CanUndo(self):
        return self._editor.CanUndo()
    
    def CanRedo(self):
        return self._editor.CanRedo()
    
    def GetConfig(self):
        return config
    
    def GetText(self):
        return self._editor.GetText()
    
    def OnTextViewActive(self, event):
        if event.active:
            self._ViewConfigChange()
        self._ActiveViewMenu(event.active)
        
    def OnTextViewClose(self, event):
        event.Skip()
        self._ActiveViewMenu(False)
        
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
        frame.Bind(EVT_QUERY_FOCUS_EDIT_EVENT, self.OnQueryFocusEdit)
        frame.Bind(EVT_FOCUS_EDIT_EVENT, self.OnFocusEdit)
        
        self._ViewConfigChange()
        
    def IsModified(self):
        if self._editor == None:
            return False
        return self._editor.GetModify()
    
    def OnFocusEdit(self, event):
        id = event.GetId()
        if id == interfaces.event.ID_FOCUS_UNDO:
            self._editor.Undo()
            return
        if id == interfaces.event.ID_FOCUS_REDO:
            self._editor.Redo()
            return
        if id == interfaces.event.ID_FOCUS_COPY:
            self._editor.Copy()
            return
        if id == interfaces.event.ID_FOCUS_CUT:
            self._editor.Cut()
            return
        if id == interfaces.event.ID_FOCUS_PASTE:
            self._editor.Paste()
            return
        
    def OnModify(self, event):
        self.ProcessEvent(ViewModifiedEvent(modified=self._editor.GetModify()))
        
    def OnQueryCanSearch(self, event):
        event.can = True
        
    def OnQueryFocusEdit(self, event):
        id = event.GetId()
        if id == ID_FOCUS_UNDO:
            event.can = self._editor.CanUndo()
            return
        if id == ID_FOCUS_REDO:
            event.can = self._editor.CanRedo()
            return
        if id == ID_FOCUS_COPY or \
           id == ID_FOCUS_CUT:
            start, end = self._editor.GetSelection()
            event.can = start != end
            return
        if id == ID_FOCUS_PASTE:
            event.can = self._editor.CanPaste()
            return
        
    def OnShowLineNumbers(self, event):
        self.GetConfig().Set("ShowLineNumbers", event.IsChecked())
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view != None and isinstance(view, TextView):
            view._ViewConfigChange()
        
    def OnShowSpaceCharacter(self, event):
        self.GetConfig().Set("ShowSpaceCharacter", event.IsChecked())
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view != None and isinstance(view, TextView):
            view._ViewConfigChange()
        
    def OnShowEOLCharacter(self, event):
        self.GetConfig().Set("ShowEOLCharacter", event.IsChecked())
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view != None and isinstance(view, TextView):
            view._ViewConfigChange()
        
    def OnShowIndentationGuide(self, event):
        self.GetConfig().Set("ShowIndentationGuide", event.IsChecked())
        view = wx.GetApp().GetMainFrame().GetChildFrame().GetActiveView()
        if view != None and isinstance(view, TextView):
            view._ViewConfigChange()
        
    def OnUpdate(self, event):
        logger.info("View is update for reason:%s" % event.hint)
        text = self.GetDoc().GetText()
        if text != None:
            self._editor.SetText(self.GetDoc().GetText())
            self._editor.EmptyUndoBuffer()
        
    def SetModifyFalse(self):
        IDocView.SetModifyFalse(self)
        self._editor.SetSavePoint()
           
    def _ActiveViewMenu(self, active):
        frame = wx.GetApp().GetMainFrame()
        menubar = frame.GetMenuBar()
        if active:
            index = menubar.FindMenu(_("&View"))
            if index != -1:
                return
            index = menubar.FindMenu(_("&Edit"))
            if index == -1:
                self.GetLogger().error("Fail to find edit menu to compute view menu position!")
                return
            menubar.Insert(index + 1, self._GetViewMenu(), _("&View"))
        else:
            index = menubar.FindMenu(_("&View"))
            if index == -1:
                return
            menubar.Remove(index)
        
    def _GetViewMenu(self):
        if TextView._viewmenu == None:
             path = os.path.join(plugin.GetPath(), "icons")
             TextView._viewmenu = wx.GetApp().GetMainFrame().CreateMenu()
             frame = wx.GetApp().GetMainFrame()
             viewmenu = TextView._viewmenu
             item = viewmenu.AppendCheckItem(-1, _("Line Numbers"), "Show/Display line numbers")
             item.Check(self.GetConfig().Get("ShowLineNumbers", False))
             wx.EVT_MENU(frame, item.GetId(), self.OnShowLineNumbers)
             
             item = viewmenu.Append(-1, _("Space Character"), "Show/Display white space character", wx.ITEM_CHECK)
             item.Check(self.GetConfig().Get("ShowSpaceCharacter", False))
             wx.EVT_MENU(frame, item.GetId(), self.OnShowSpaceCharacter)
             
             item = viewmenu.Append(-1, _("EOL Character"), "Show/Display TAB character", wx.ITEM_CHECK)
             item.Check(self.GetConfig().Get("ShowEOLCharacter", False))
             wx.EVT_MENU(frame, item.GetId(), self.OnShowEOLCharacter)
             
             item = viewmenu.Append(-1, _("Indentation Guide"), "Show/Display indentation character", wx.ITEM_CHECK)
             item.Check(self.GetConfig().Get("ShowIndentationGuide", False))
             wx.EVT_MENU(frame, item.GetId(), self.OnShowIndentationGuide)
             
        return TextView._viewmenu
    
    def _ViewConfigChange(self):
        if self._editor == None:
            return
        self._editor.SetViewEOL(self.GetConfig().Get("ShowEOLCharacter", False))
        self._editor.SetViewWhiteSpace(self.GetConfig().Get("ShowSpaceCharacter", False))
        self._editor.SetIndentationGuides(self.GetConfig().Get("ShowIndentationGuide", False))
        self._editor.SetViewLineNumbers(self.GetConfig().Get("ShowLineNumbers", False))
        
def __extension_main__(pluginInfo):
    global logger
    logger = wx.GetApp().GetLogger("TextEditor")
    
    global config
    config = wx.GetApp().GetConfig("TextEditor")
    
    global plugin
    plugin = pluginInfo
    
    bitmap = wx.Bitmap(os.path.join(pluginInfo.GetPath(), "icons", "textfile.ico"))
    docmgr = wx.GetApp().GetDocManager()
    docmgr.RegisterDocumentProvider("TextFile", _("Text File"), ["txt", "log", "*"], TextDocument, bitmap, False)
    
    