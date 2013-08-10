"""@file
Provide default editor for PIS, it's syntax is expandable.
default editor provide framework of source file's editor, including:
    - Find interface
    - Outline interface
    - Highlight
    ...
"""
__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__svnid__    = "$Id$"
__revision__ = "$Revision$"

import os, sys, re, string
import wx, wx.stc, wx.gizmos
import wx.lib.docview   as docview
import wx.lib.pydocview as pydocview
import wx.lib.multisash
import service
import outline
import textfile
from core.search import FindService
import search
_ = wx.GetTranslation
import array

    
TEXT_ID = wx.NewId()
VIEW_WHITESPACE_ID = wx.NewId()
VIEW_EOL_ID = wx.NewId()
VIEW_INDENTATION_GUIDES_ID = wx.NewId()
VIEW_RIGHT_EDGE_ID = wx.NewId()
VIEW_LINE_NUMBERS_ID = wx.NewId()
ZOOM_ID = wx.NewId()
ZOOM_NORMAL_ID = wx.NewId()
ZOOM_IN_ID = wx.NewId()
ZOOM_OUT_ID = wx.NewId()
CHOOSE_FONT_ID = wx.NewId()
WORD_WRAP_ID = wx.NewId()
TEXT_STATUS_BAR_ID = wx.NewId()

EXPAND_TEXT_ID = wx.NewId()
COLLAPSE_TEXT_ID = wx.NewId()
EXPAND_TOP_ID = wx.NewId()
COLLAPSE_TOP_ID = wx.NewId()
EXPAND_ALL_ID = wx.NewId()
COLLAPSE_ALL_ID = wx.NewId()
CHECK_CODE_ID = wx.NewId()
AUTO_COMPLETE_ID = wx.NewId()
CLEAN_WHITESPACE = wx.NewId()
COMMENT_LINES_ID = wx.NewId()
UNCOMMENT_LINES_ID = wx.NewId()
INDENT_LINES_ID = wx.NewId()
DEDENT_LINES_ID = wx.NewId()
USE_TABS_ID = wx.NewId()
SET_INDENT_WIDTH_ID = wx.NewId()
FOLDING_ID = wx.NewId()
CHANGE_EOL_MODE = wx.NewId()
CHANGE_EOL_MODE_WINDOWS = wx.NewId()
CHANGE_EOL_MODE_UNIX    = wx.NewId()
CHANGE_EOL_MODE_MAC     = wx.NewId()

class EditorDocument(docview.Document):
    """Default editor document class inherited from docview.Document class
    """

    def __init__(self):
        docview.Document .__init__(self)
        self._inModify = False
        
    def SaveObject(self, fileObject):
        view = self.GetFirstView()
        #fileObject.write(view.GetValue())
        file = textfile.TextFile(self.GetFilename())
        file.DoOpen('rw')
        file.Write(view.GetValue())
        file.Close()
        
        view.SetModifyFalse()
        return True

    def LoadObject(self, fileObject):
        #data = fileObject.read()
        file = textfile.TextFile(self.GetFilename())
        file.DoOpen('rb')
        data = file.Read()
        file.Close()
        view = self.GetFirstView()
        view.SetValue(data)
        view.SetModifyFalse()
        
        return True

    def IsModified(self):
        view = self.GetFirstView()
        if view:
            return view.IsModified()
        return False
    
    def Modify(self, modify):
        if self._inModify:
            return
        self._inModify = True
        
        view = self.GetFirstView()
        if not modify and view:
            view.SetModifyFalse()
        docview.Document.Modify(self, modify)  # this must called be after the SetModifyFalse call above.
        self._inModify = False
    
    def OnCreateCommandProcessor(self):
        # Don't create a command processor, it has its own
        pass

# Use this to override MultiClient.Select to prevent yellow background.     
def MultiClientSelectBGNotYellow(a):     
    a.GetParent().multiView.UnSelect()     
    a.selected = True     
    #a.SetBackgroundColour(wx.Colour(255,255,0)) # Yellow     
    a.Refresh()

class EditorView(docview.View):
    """Default editor's view inherited from docview.View"""
    MARKER_NUM = 0
    MARKER_MASK = 0x1
    PRINTABLE_CHAR = ['/', '\\', '#', '~', '!', '@', '$', '%', '^', '&', '*', '(', \
                      ')', '{', '}', '[', ']', '<', '>', ':', ';', '\"', '\'', '?',\
                      '-', '+', '=', '_']
    PRINTABLE_CHAR_INT = [ord(item) for item in PRINTABLE_CHAR]
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self._textEditor       = None
        self._markerCount      = 0
        self._commandProcessor = None
        self._dynSash          = None
        self._isHex            = False

    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        import editorstc
        return editorstc.EditorTextCtrl

    def IsViewHex(self):
        return self._isHex
        
    def ViewHex(self, isHex=False):
         
        if isHex:
            if self.IsModified():
                dlg = wx.MessageDialog(wx.GetApp().GetTopWindow(),
                                       "You must save document before viewing Hex!\nDo you want to save current document?",
                                       "Save document before viewing Hex",
                                       style = wx.OK|wx.CANCEL)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    self.GetDocument().Save()
                else:
                    return
                    
            self._value = self.GetValue()
            arr = array.array('B')
            try: 
                f = open(self.GetDocument().GetFilename(), 'rb')
                fstat = os.stat(self.GetDocument().GetFilename())
                arr.fromfile(f, fstat.st_size)
                f.close()
            except:
                wx.MessageBox("Fail to view hex!")
                return
                 
            list = self._listToText(0, arr.tolist())
            #elf.SetValue('\n'.join(list))
            self._isHex = True
            self.GetCtrl().SetText('\n'.join(list))   
            self.GetCtrl().SetReadOnly(True)
            self.SetModifyFalse()
        else:
            #self._textEditor = self.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
            #self.SetCtrl(self._textEditor)
            self.GetCtrl().SetReadOnly(False)
            #self.GetCtrl().SetWordWrap(True)
            #self.SetModifyFalse()
            self.SetValue(self._value)            
            self._isHex = False
            self.SetModifyFalse()
            
    def _listToText(self, base, listdata):
        newlist    = []
        line       = ''
        linestr    = ''
        newstr     = ''
        linecount  = 0
        count      = 0
        for item in listdata:
            if count < 15:
                if count == 7:
                    line += '%02X-' % item
                else:
                    line += '%02X ' % item
                    
                if (item <= ord('z') and item >= ord('a')) or \
                   (item <= ord('Z') and item >= ord('A')) or \
                   (item <= ord('9') and item >= ord('0')) or \
                   item in self.PRINTABLE_CHAR_INT:
                    linestr += chr(item)
                else:
                    linestr += '.'
                
                count += 1
            else:
                line += '%02X ' % item
                if (item < ord('z') and item > ord('a')) or \
                    (item < ord('Z') and item > ord('A')):
                    linestr += chr(item)
                else:
                    linestr += '.'
                newstr = '0x%08X: ' % (base + linecount * 16)
                newstr += line
                #self.AddText('0x%08X: ' % (base + linecount * 16))
                newstr += '  %s' % linestr
                newlist.append(newstr)
                line = ''
                linestr = ''
                count = 0
                linecount += 1
        
        if len(line) != 0 and count != 15:
            newstr = '0x%08X: ' % (base + (linecount) * 16)
            #self.AddText('0x%08X: ' % (base + (linecount) * 16))
            newstr += line
            while count <= 15:
                newstr += '   '
                count += 1
            newstr += '  %s' % linestr
            newlist.append(newstr)
            #self.AddText(line)
            #self.AddText('  %s' % linestr)
            #self.AddText('\n')   
        return newlist
                
    def GetCtrl(self):
        if wx.Platform == "__WXMAC__":
            # look for active one first     
            self._textEditor = self._GetActiveCtrl(self._dynSash)     
            if self._textEditor == None:  # it is possible none are active     
                # look for any existing one     
                self._textEditor = self._FindCtrl(self._dynSash)
        return self._textEditor

    def SetCtrl(self, ctrl):
        self._textEditor = ctrl


    def OnCreatePrintout(self):
        """ for Print Preview and Print """
        return TextPrintout(self, self.GetDocument().GetPrintableName())
            
    def OnCreate(self, doc, flags):
    	""" Create document' frame window.
    	
    	document window is dynamic sash window and stc text ctrl embedded in it.
    	"""
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        frame.Freeze()
        # wxBug: DynamicSashWindow doesn't work on Mac, so revert to
        # multisash implementation
        if wx.Platform == "__WXMAC__":
            wx.lib.multisash.MultiClient.Select = MultiClientSelectBGNotYellow
            self._dynSash = wx.lib.multisash.MultiSash(frame, -1)
            self._dynSash.SetDefaultChildClass(self.GetCtrlClass()) # wxBug:  MultiSash instantiates the first TextCtrl with this call
            
            self._textEditor = self.GetCtrl()  # wxBug: grab the TextCtrl from the MultiSash datastructure
        else:
            self._dynSash = wx.gizmos.DynamicSashWindow(frame, -1, style=wx.CLIP_CHILDREN)
            self._dynSash._view = self
            self._textEditor = self.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
            
        #wx.EVT_LEFT_DOWN(self._textEditor, self.OnLeftClick)
        self._textEditor.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModify)
        
        # create sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._dynSash, 1, wx.EXPAND)
        frame.SetSizer(sizer)        
        frame.Show(True)
        frame.Layout()
        frame.Thaw()
        # focus the text editor after sash window created.
        wx.CallAfter(self.GetCtrl().SetFocus)
        
        # add _view reference for a child frame.
        frame._view = self
        return True

    def OnModify(self, event):
        if not self.IsViewHex():
            self.GetDocument().Modify(self._textEditor.GetModify())
        
    #def OnLeftClick(self, event):
    #    print '1'
    #    self.Activate()
    #    event.Skip()

    def OnUpdate(self, sender = None, hint = None):
        if docview.View.OnUpdate(self, sender, hint):
            return

        if hint == "ViewStuff":
            self.GetCtrl().ConfigureView()
        
    def LoadOutline(self):
        if self.GetDocument() == None:
            return

        serv = wx.GetApp().GetService(outline.OutlineService)
        if serv == None: return
        callbacks = self.GetCtrl().GetOutlineCallback()
        if callbacks != None:
            serv.UnLoad()
            serv.ResigterCallbacks(callbacks.get('InitTree', None),
                                   callbacks.get('SelectAction', None))
            serv.Load(self)
        else:
            serv.UnLoad()
                        
    def UnLoadOutline(self):
        serv = wx.GetApp().GetService(outline.OutlineService)
        serv.UnLoad()
        
    def OnActivateView(self, activate, activeView, deactiveView):
        wx.GetApp().GetTopWindow().ActivateDocumentPane()
        if activate:
            if not self.GetCtrl(): return

            if activeView == deactiveView:  return
            self.LoadOutline()
            
            # change frame window's title for document's full path.
            frame = wx.GetApp().GetTopWindow()
            title = '%s - %s' % (wx.GetApp().GetAppName(), self.GetDocument().GetFilename())
            frame.SetTitle(title)
        else:
            self.UnLoadOutline()

    def SetFocus(self):
    	"""Always set control focus"""
        if self.GetCtrl():
            self.GetCtrl().SetFocus()
                                
    def OnClose(self, deleteWindow = True):
        if not docview.View.OnClose(self, deleteWindow):
            return False
        self.Activate(False)
        
        outlineService = wx.GetApp().GetService(outline.OutlineService)
        if outline:
            outlineService.Clear()        
        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True

    def ProcessEvent(self, event):  
        id = event.GetId()
        if id == wx.ID_UNDO:
            self.GetCtrl().Undo()
            return True
        elif id == wx.ID_REDO:
            self.GetCtrl().Redo()
            return True
        elif id == wx.ID_CUT:
            self.GetCtrl().Cut()
            return True
        elif id == wx.ID_COPY:
            self.GetCtrl().Copy()
            return True
        elif id == wx.ID_PASTE:
            self.GetCtrl().OnPaste()
            return True
        elif id == wx.ID_CLEAR:
            self.GetCtrl().OnClear()
            return True
        elif id == wx.ID_SELECTALL:
            self.GetCtrl().SetSelection(0, -1)
            return True
        elif id == VIEW_WHITESPACE_ID:
            self.GetCtrl().SetViewWhiteSpace(not self.GetCtrl().GetViewWhiteSpace())
            return True
        elif id == VIEW_EOL_ID:
            self.GetCtrl().SetViewEOL(not self.GetCtrl().GetViewEOL())
            return True
        elif id == VIEW_INDENTATION_GUIDES_ID:
            self.GetCtrl().SetIndentationGuides(not self.GetCtrl().GetIndentationGuides())
            return True
        elif id == VIEW_RIGHT_EDGE_ID:
            self.GetCtrl().SetViewRightEdge(not self.GetCtrl().GetViewRightEdge())
            return True
        elif id == VIEW_LINE_NUMBERS_ID:
            self.GetCtrl().SetViewLineNumbers(not self.GetCtrl().GetViewLineNumbers())
            return True
        elif id == ZOOM_NORMAL_ID:
            self.GetCtrl().SetZoom(0)
            return True
        elif id == ZOOM_IN_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_ZOOMIN)
            return True
        elif id == ZOOM_OUT_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_ZOOMOUT)
            return True
        elif id == WORD_WRAP_ID:
            self.GetCtrl().SetWordWrap(not self.GetCtrl().GetWordWrap())
            return True
        elif id == EXPAND_TEXT_ID:
            self.GetCtrl().ToggleFold(self.GetCtrl().GetCurrentLine())
            return True
        elif id == COLLAPSE_TEXT_ID:
            self.GetCtrl().ToggleFold(self.GetCtrl().GetCurrentLine())
            return True
        elif id == EXPAND_TOP_ID:
            self.GetCtrl().ToggleFoldAll(expand = True, topLevelOnly = True)
            return True
        elif id == COLLAPSE_TOP_ID:
            self.GetCtrl().ToggleFoldAll(expand = False, topLevelOnly = True)
            return True
        elif id == EXPAND_ALL_ID:
            self.GetCtrl().ToggleFoldAll(expand = True)
            return True
        elif id == COLLAPSE_ALL_ID:
            self.GetCtrl().ToggleFoldAll(expand = False)
            return True
        elif id == CHECK_CODE_ID:
            self.OnCheckCode()
            return True
        elif id == CLEAN_WHITESPACE:
            self.OnCleanWhiteSpace()
            return True
        elif id == SET_INDENT_WIDTH_ID:
            self.OnSetIndentWidth()
            return True
        elif id == USE_TABS_ID:
            self.GetCtrl().SetUseTabs(not self.GetCtrl().GetUseTabs())
            return True
        elif id == INDENT_LINES_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_TAB)
            return True
        elif id == DEDENT_LINES_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_BACKTAB)
            return True
        elif id == COMMENT_LINES_ID:
            self.OnCommentLines()
            return True
        elif id == UNCOMMENT_LINES_ID:
            self.OnUncommentLines()
            return True
        elif id == FindService.FIND_ID:
            self.OnFind()
            return True
        elif id == FindService.FIND_IN_FILES_ID:
            self.OnFindInFiles()
            return True
        elif id == FindService.FIND_PREVIOUS_ID:
            self.DoFind(forceFindPrevious = True)
            return True
        elif id == FindService.FIND_NEXT_ID:
            self.DoFind(forceFindNext = True)
            return True
        elif id == FindService.REPLACE_ID:
            self.OnFind(replace = True)
            return True
        elif id == FindService.FINDONE_ID:
            self.DoFind()
            return True
        elif id == FindService.REPLACEONE_ID:
            self.DoFind(replace = True)
            return True
        elif id == FindService.REPLACEALL_ID:
            self.DoFind(replaceAll = True)
            return True
        elif id == FindService.GOTO_LINE_ID:
            self.OnGotoLine(event)
            return True
        elif id == CHANGE_EOL_MODE_WINDOWS:
            self.GetCtrl().ConvertEOLs(wx.stc.STC_EOL_CRLF)
            return True
        elif id == CHANGE_EOL_MODE_UNIX:
            self.GetCtrl().ConvertEOLs(wx.stc.STC_EOL_LF)
            return True
        elif id == CHANGE_EOL_MODE_MAC:
            self.GetCtrl().ConvertEOLs(wx.stc.STC_EOL_CR)
            return True
        else:
            return docview.View.ProcessEvent(self, event)

    def ProcessUpdateUIEvent(self, event):
        if not self.GetCtrl():
            return False

        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(self.GetCtrl().CanUndo())
            event.SetText(_("&Undo\tCtrl+Z"))  # replace menu string
            return True
        elif id == wx.ID_REDO:
            event.Enable(self.GetCtrl().CanRedo())
            event.SetText(_("&Redo\tCtrl+Y"))  # replace menu string
            return True
        elif (id == wx.ID_CUT
              or id == wx.ID_COPY
              or id == wx.ID_CLEAR):
            hasSelection = self.GetCtrl().GetSelectionStart() != self.GetCtrl().GetSelectionEnd()
            event.Enable(hasSelection)
            return True
        elif id == wx.ID_PASTE:
            event.Enable(self.GetCtrl().CanPaste())
            return True
        elif id == wx.ID_SELECTALL:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id in [TEXT_ID, CHANGE_EOL_MODE_WINDOWS, CHANGE_EOL_MODE_UNIX, CHANGE_EOL_MODE_MAC]:
            event.Enable(True)
            return True
        elif id == VIEW_WHITESPACE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewWhiteSpace())
            return True
        elif id == VIEW_EOL_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewEOL())
            return True
        elif id == VIEW_INDENTATION_GUIDES_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetIndentationGuides())
            return True
        elif id == VIEW_RIGHT_EDGE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewRightEdge())
            return True
        elif id == VIEW_LINE_NUMBERS_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewLineNumbers())
            return True
        elif id == ZOOM_ID:
            event.Enable(True)
            return True
        elif id == ZOOM_NORMAL_ID:
            event.Enable(self.GetCtrl().GetZoom() != 0)
            return True
        elif id == ZOOM_IN_ID:
            event.Enable(self.GetCtrl().GetZoom() < 20)
            return True
        elif id == ZOOM_OUT_ID:
            event.Enable(self.GetCtrl().GetZoom() > -10)
            return True
        elif id == WORD_WRAP_ID:
            event.Enable(self.GetCtrl().CanWordWrap())
            event.Check(self.GetCtrl().CanWordWrap() and self.GetCtrl().GetWordWrap())
            return True
        elif id == EXPAND_TEXT_ID:
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().CanLineExpand(self.GetCtrl().GetCurrentLine()))
            else:
                event.Enable(False)
            return True
        elif id == COLLAPSE_TEXT_ID:
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().CanLineCollapse(self.GetCtrl().GetCurrentLine()))
            else:
                event.Enable(False)
            return True
        elif (id == EXPAND_TOP_ID
              or id == COLLAPSE_TOP_ID
              or id == EXPAND_ALL_ID
              or id == COLLAPSE_ALL_ID):
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().GetTextLength() > 0)
            else:
                event.Enable(False)
            return True            
        elif (id == AUTO_COMPLETE_ID
              or id == CLEAN_WHITESPACE
              or id == INDENT_LINES_ID
              or id == DEDENT_LINES_ID
              or id == COMMENT_LINES_ID
              or id == UNCOMMENT_LINES_ID):
            event.Enable(self.GetCtrl().GetTextLength() > 0)
            return True
        elif id == CHECK_CODE_ID:
            event.Enable(False)
            return True
        elif id == SET_INDENT_WIDTH_ID:
            event.Enable(True)
            return True
        elif id == FOLDING_ID:
            event.Enable(self.GetCtrl().GetViewFolding())
            return True
        elif id == USE_TABS_ID:
            event.Enable(True)
            event.Check(self.GetCtrl().GetUseTabs())
            return True
        elif id == FindService.FIND_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == FindService.FIND_PREVIOUS_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText and
                         self._FindServiceHasString() and
                         self.GetCtrl().GetSelection()[0] > 0)
            return True
        elif id == FindService.FIND_NEXT_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText and
                         self._FindServiceHasString() and
                         self.GetCtrl().GetSelection()[0] < self.GetCtrl().GetLength())
            return True
        elif id == FindService.REPLACE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == FindService.GOTO_LINE_ID:
            event.Enable(True)
            return True
        elif id == TEXT_STATUS_BAR_ID:
            self.OnUpdateStatusBar(event)
            return True
        else:
            return docview.View.ProcessUpdateUIEvent(self, event)

    def _GetParentFrame(self):
        return wx.GetTopLevelParent(self.GetFrame())

    def _GetActiveCtrl(self, parent):     
        """ Walk through the MultiSash windows and find the active Control """     
        if isinstance(parent, wx.lib.multisash.MultiClient) and parent.selected:     
            return parent.child     
        if hasattr(parent, "GetChildren"):     
            for child in parent.GetChildren():     
                found = self._GetActiveCtrl(child)     
                if found:     
                    return found     
        return None     

    def _FindCtrl(self, parent):     
        """ Walk through the MultiSash windows and find the first TextCtrl """     
        if isinstance(parent, self.GetCtrlClass()):     
            return parent     
        if hasattr(parent, "GetChildren"):     
            for child in parent.GetChildren():     
                found = self._FindCtrl(child)     
                if found:     
                    return found     
        return None     
 
    #----------------------------------------------------------------------------
    # Methods for TextDocument to call
    #----------------------------------------------------------------------------

    def IsModified(self):
        if not self.GetCtrl():
            return False
        return self.GetCtrl().GetModify()

    def SetModifyFalse(self):
        if self.GetCtrl() != None:
            self.GetCtrl().SetSavePoint()

    def GetValue(self):
        if self.GetCtrl():            try:                value = self.GetCtrl().GetText()            except:                try:                    value = self.GetCtrl().GetTextUtf8()                except:                    value = self.GetCtrl().GetTextRaw()            return value
        else:
            return None

    def SetValue(self, value):        try:            self.GetCtrl().SetText(value)        except:            try:                self.GetCtrl().SetTextUtf8(value)            except:                self.GetCtrl().SetTextRaw(value)            
        self.GetCtrl().UpdateLineNumberMarginWidth()
        self.GetCtrl().EmptyUndoBuffer()

    #----------------------------------------------------------------------------
    # STC events
    #----------------------------------------------------------------------------

    def OnUpdateStatusBar(self, event):
        statusBar = self._GetParentFrame().GetStatusBar()
        statusBar.SetInsertMode(self.GetCtrl().GetOvertype() == 0)
        statusBar.SetLineNumber(self.GetCtrl().GetCurrentLine() + 1)
        statusBar.SetColumnNumber(self.GetCtrl().GetColumn(self.GetCtrl().GetCurrentPos()) + 1)

    #----------------------------------------------------------------------------
    # Find methods
    #----------------------------------------------------------------------------

    def OnFind(self, replace = False):
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.ShowFindReplaceDialog(findString = self.GetCtrl().GetSelectedText(), replace = replace)

    def OnFindInFiles(self, replace=False):
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.ShowFindReplaceDialog(self.GetCtrl().GetSelectedText(), replace, True)
        
    def DoFind(self, forceFindNext = False, forceFindPrevious = False, replace = False, replaceAll = False):
        findService = wx.GetApp().GetService(FindService)
        if not findService:
            return
        findString = findService.GetFindString()
        if len(findString) == 0:
            return -1
        replaceString = findService.GetReplaceString()
        flags = findService.GetFlags()
        startLoc, endLoc = self.GetCtrl().GetSelection()

        listAll   = flags & FindService.FR_LISTALL > 0
        wholeWord = flags & wx.FR_WHOLEWORD > 0
        matchCase = flags & wx.FR_MATCHCASE > 0
        regExp = flags & FindService.FR_REGEXP > 0
        down = flags & wx.FR_DOWN > 0
        wrap = flags & FindService.FR_WRAP > 0

        if forceFindPrevious:   # this is from function keys, not dialog box
            down = False
            wrap = False        # user would want to know they're at the end of file
        elif forceFindNext:
            down = True
            wrap = False        # user would want to know they're at the end of file

        badSyntax = False
        
        # On replace dialog operations, user is allowed to replace the currently highlighted text to determine if it should be replaced or not.
        # Typically, it is the text from a previous find operation, but we must check to see if it isn't, user may have moved the cursor or selected some other text accidentally.
        # If the text is a match, then replace it.
        if replace:
            result, start, end, replText = findService.DoFind(findString, replaceString, self.GetCtrl().GetSelectedText(), 0, 0, True, matchCase, wholeWord, regExp, replace)
            if result > 0:
                self.GetCtrl().ReplaceSelection(replText)
                self.GetDocument().Modify(True)
                wx.GetApp().GetTopWindow().PushStatusText(_("1 occurrence of \"%s\" replaced") % findString)
                if down:
                    startLoc += len(replText)  # advance start location past replacement string to new text
                endLoc = startLoc
            elif result == FindService.FIND_SYNTAXERROR:
                badSyntax = True
                wx.GetApp().GetTopWindow().PushStatusText(_("Invalid regular expression \"%s\"") % findString)

        if listAll:
            results = findService.DoFind(findString, None, self.GetCtrl().GetText(), 0, 0, True, matchCase, wholeWord, regExp, listAll=True)
            arr = []
            existing = []
            for start, end in results:
                line = self.GetCtrl().LineFromPosition(start) + 1
                if line not in existing:
                    arr.append((line, self.GetCtrl().GetLine(line - 1)))
                    existing.append(line)
            findService.ListResults([(self.GetDocument().GetFilename(), arr)],
                                    True)
            return
            
        if not badSyntax:
            text = self.GetCtrl().GetText()
    
            # Find the next matching text occurance or if it is a ReplaceAll, replace all occurances
            # Even if the user is Replacing, we should replace here, but only select the text and let the user replace it with the next Replace operation
            result, start, end, text = findService.DoFind(findString, replaceString, text, startLoc, endLoc, down, matchCase, wholeWord, regExp, False, replaceAll, wrap)
            if result > 0:
                self.GetCtrl().SetTargetStart(0)
                self.GetCtrl().SetTargetEnd(self.GetCtrl().GetLength())
                self.GetCtrl().ReplaceTarget(text)  # Doing a SetText causes a clear document to be shown when undoing, so using replacetarget instead
                self.GetDocument().Modify(True)
                if result == 1:
                    wx.GetApp().GetTopWindow().PushStatusText(_("1 occurrence of \"%s\" replaced") % findString)
                else:
                    wx.GetApp().GetTopWindow().PushStatusText(_("%i occurrences of \"%s\" replaced") % (result, findString))
            elif result == 0:
                self.GetCtrl().SetSelection(start, end)
                self.GetCtrl().EnsureVisible(self.GetCtrl().LineFromPosition(end))  # show bottom then scroll up to top
                self.GetCtrl().EnsureVisible(self.GetCtrl().LineFromPosition(start)) # do this after ensuring bottom is visible
                wx.GetApp().GetTopWindow().PushStatusText(_("Found \"%s\".") % findString)
            elif result == search.FIND_SYNTAXERROR:
                # Dialog for this case gets popped up by the FindService.
                wx.GetApp().GetTopWindow().PushStatusText(_("Invalid regular expression \"%s\"") % findString)
            else:
                wx.MessageBox(_("Can't find \"%s\".") % findString, "Find",
                          wx.OK | wx.ICON_INFORMATION)


    def _FindServiceHasString(self):
        findService = wx.GetApp().GetService(FindService)
        if not findService or not findService.GetFindString():
            return False
        return True

    def OnGotoLine(self, event):
        findService = wx.GetApp().GetService(FindService)
        if findService:
            line = findService.GetLineNumber(self.GetDocumentManager().FindSuitableParent())
            if line > -1:
                line = line - 1
                self.GetCtrl().EnsureVisible(line)
                self.GetCtrl().GotoLine(line)

    def GotoLine(self, lineNum):
        if lineNum > -1:
            lineNum = lineNum - 1  # line numbering for editor is 0 based, we are 1 based.
            if self.GetCtrl():
                self.GetCtrl().EnsureVisibleEnforcePolicy(lineNum)
                self.GetCtrl().GotoLine(lineNum)
                
    def GetSelectedText(self):
        return self.GetCtrl().GetSelectedText()
    
    def InsertLine(self, line, text):
        pos = self.PositionFromLine(line)
        t = text.rstrip() + self.GetCtrl().GetEOLChar()
        self.GetCtrl().InsertText(pos, t)

    def LineDelete(self, lineNum):
        self.GetCtrl().EnsureVisibleEnforcePolicy(lineNum - 1)
        self.GetCtrl().GotoLine(lineNum - 1)
        self.GetCtrl().LineDelete()
        
    def SetSelection(self, start, end):
        self.GetCtrl().SetSelection(start, end)

    def EnsureVisible(self, line):
        self.GetCtrl().EnsureVisible(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def EnsureVisibleEnforcePolicy(self, line):
        self.GetCtrl().EnsureVisibleEnforcePolicy(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def LineFromPosition(self, pos):
        return self.GetCtrl().LineFromPosition(pos)+1  # line numbering for editor is 0 based, we are 1 based.

    def PositionFromLine(self, line):
        return self.GetCtrl().PositionFromLine(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLineEndPosition(self, line):
        return self.GetCtrl().GetLineEndPosition(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLine(self, lineNum):
        return self.GetCtrl().GetLine(lineNum-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLineCount(self):
        return self.GetCtrl().GetLineCount()
        
    def OnCleanWhiteSpace(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = string.rstrip(self.GetCtrl().GetLine(lineNo))
            indent = 0
            lstrip = 0
            for char in lineText:
                if char == '\t':
                    indent = indent + self.GetCtrl().GetIndent()
                    lstrip = lstrip + 1
                elif char in string.whitespace:
                    indent = indent + 1
                    lstrip = lstrip + 1
                else:
                    break
            if self.GetCtrl().GetUseTabs():
                indentText = (indent / self.GetCtrl().GetIndent()) * '\t' + (indent % self.GetCtrl().GetIndent()) * ' '
            else:
                indentText = indent * ' '
            lineText = indentText + lineText[lstrip:] + '\n'
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)

    def OnChangeFilename(self):
        wx.lib.docview.View.OnChangeFilename(self)
        self.GetCtrl().ChangeFilename(self.GetDocument().GetFilename())
        self.LoadOutline()
        self.GetCtrl().SetFocus()
        
    def OnSetIndentWidth(self):
        dialog = wx.TextEntryDialog(self._GetParentFrame(), _("Enter new indent width (2-10):"), _("Set Indent Width"), "%i" % self.GetCtrl().GetIndent())
        dialog.CenterOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            try:
                indent = int(dialog.GetValue())
                if indent >= 2 and indent <= 10:
                    self.GetCtrl().SetIndent(indent)
                    self.GetCtrl().SetTabWidth(indent)
            except:
                pass
        dialog.Destroy()

    def GetIndentWidth(self):
        return self.GetCtrl().GetIndent()

    def OnCommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if (len(lineText) > 1 and lineText[0] == '/') or (len(lineText) > 2 and lineText[:2] == '##'):
                newText = newText + lineText
            else:
                newText = newText + "//" + lineText
        self._ReplaceSelectedLines(newText)

    def OnUncommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if len(lineText) >= 2 and lineText[:2] == "//":
                lineText = lineText[2:]
            elif len(lineText) >= 1 and lineText[:1] == "/":
                lineText = lineText[1:]
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)

    def _GetSelectedLineNumbers(self):
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        return range(self.GetCtrl().LineFromPosition(selStart), self.GetCtrl().LineFromPosition(selEnd))

    def _GetPositionsBoundingSelectedLines(self):
        startPos = self.GetCtrl().GetCurrentPos()
        endPos = self.GetCtrl().GetAnchor()
        if startPos > endPos:
            temp = endPos
            endPos = startPos
            startPos = temp
        if endPos == self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(endPos)):
            endPos = endPos - 1  # If it's at the very beginning of a line, use the line above it as the ending line
        selStart = self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(startPos))
        selEnd = self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(endPos) + 1)
        return selStart, selEnd

    def _ReplaceSelectedLines(self, text):
        if len(text) == 0:
            return
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        self.GetCtrl().SetSelection(selStart, selEnd)
        self.GetCtrl().ReplaceSelection(text)
        self.GetCtrl().SetSelection(selStart + len(text), selStart)
        
class EditorService(service.PISService):
    """Editor service provide tool bar and status bar for default editor"""

    def __init__(self):
        service.PISService.__init__(self)

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != TextDocument:
            return

        statusBar = TextStatusBar(frame, TEXT_STATUS_BAR_ID)
        frame.SetStatusBar(statusBar)
        wx.EVT_UPDATE_UI(frame, TEXT_STATUS_BAR_ID, frame.ProcessUpdateUIEvent)

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))

        viewMenu.AppendSeparator()
        
        viewMenu.AppendCheckItem(WORD_WRAP_ID, _("Soft Wrap"), _("Wraps text horizontally when checked"))
        wx.EVT_MENU(frame, WORD_WRAP_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, WORD_WRAP_ID, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendCheckItem(VIEW_WHITESPACE_ID, _("&Whitespace"), _("Shows or hides whitespace"))
        wx.EVT_MENU(frame, VIEW_WHITESPACE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_WHITESPACE_ID, frame.ProcessUpdateUIEvent)
        viewMenu.AppendCheckItem(VIEW_EOL_ID, _("&End of Line Markers"), _("Shows or hides indicators at the end of each line"))
        wx.EVT_MENU(frame, VIEW_EOL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_EOL_ID, frame.ProcessUpdateUIEvent)
        viewMenu.AppendCheckItem(VIEW_INDENTATION_GUIDES_ID, _("&Indentation Guides"), _("Shows or hides indentations"))
        wx.EVT_MENU(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessUpdateUIEvent)
        viewMenu.AppendCheckItem(VIEW_RIGHT_EDGE_ID, _("&Right Edge"), _("Shows or hides the right edge marker"))
        wx.EVT_MENU(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessUpdateUIEvent)
        viewMenu.AppendCheckItem(VIEW_LINE_NUMBERS_ID, _("&Line Numbers"), _("Shows or hides the line numbers"))
        wx.EVT_MENU(frame, VIEW_LINE_NUMBERS_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_LINE_NUMBERS_ID, frame.ProcessUpdateUIEvent)
        
        isWindows = (wx.Platform == '__WXMSW__')

        viewMenu.AppendSeparator()
        #zoomMenu = wx.Menu()
        viewMenu.Append(ZOOM_NORMAL_ID, _("Normal Size"), _("Sets the document to its normal size"))
        wx.EVT_MENU(frame, ZOOM_NORMAL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_NORMAL_ID, frame.ProcessUpdateUIEvent)
        if isWindows:
            item = wx.MenuItem(viewMenu, ZOOM_IN_ID, _("Zoom In\tCtrl+Page Up"), _("Zooms the document to a larger size"))
            item.SetBitmap(getZoomInBitmap())
            viewMenu.AppendItem(item)
        else:
            item = wx.MenuItem(viewMenu, ZOOM_IN_ID, _("Zoom In"), _("Zooms the document to a larger size"))
            item.SetBitmap(getZoomInBitmap())
            viewMenu.AppendItem(item)

        wx.EVT_MENU(frame, ZOOM_IN_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_IN_ID, frame.ProcessUpdateUIEvent)
        if isWindows:
            #viewMenu.Append(ZOOM_OUT_ID, _("Zoom Out\tCtrl+Page Down"), _("Zooms the document to a smaller size"))
            item = wx.MenuItem(viewMenu, ZOOM_OUT_ID, _("Zoom Out\tCtrl+Page Down"), _("Zooms the document to a smaller size"))
            item.SetBitmap(getZoomOutBitmap())
            viewMenu.AppendItem(item)            
        else:
            #viewMenu.Append(ZOOM_OUT_ID, _("Zoom Out"), _("Zooms the document to a smaller size"))
            item = wx.MenuItem(viewMenu, ZOOM_OUT_ID, _("Zoom Out"), _("Zooms the document to a smaller size"))
            item.SetBitmap(getZoomOutBitmap())
            viewMenu.AppendItem(item)            
        wx.EVT_MENU(frame, ZOOM_OUT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_OUT_ID, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendSeparator()
        viewMenu.Append(EXPAND_TEXT_ID, _("&Expand"), _("Expands a collapsed block of text"))
        wx.EVT_MENU(frame, EXPAND_TEXT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, EXPAND_TEXT_ID, frame.ProcessUpdateUIEvent)        
        viewMenu.Append(COLLAPSE_TEXT_ID, _("&Collapse"), _("Collapse a block of text"))
        wx.EVT_MENU(frame, COLLAPSE_TEXT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, COLLAPSE_TEXT_ID, frame.ProcessUpdateUIEvent)
        viewMenu.Append(EXPAND_TOP_ID, _("Expand &Top Level"), _("Expands the top fold levels in the document"))
        wx.EVT_MENU(frame, EXPAND_TOP_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, EXPAND_TOP_ID, frame.ProcessUpdateUIEvent)
        viewMenu.Append(COLLAPSE_TOP_ID, _("Collapse Top &Level"), _("Collapses the top fold levels in the document"))
        wx.EVT_MENU(frame, COLLAPSE_TOP_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, COLLAPSE_TOP_ID, frame.ProcessUpdateUIEvent)
        viewMenu.Append(EXPAND_ALL_ID, _("Expand &All"), _("Expands all of the fold levels in the document"))
        wx.EVT_MENU(frame, EXPAND_ALL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, EXPAND_ALL_ID, frame.ProcessUpdateUIEvent)
        viewMenu.Append(COLLAPSE_ALL_ID, _("Colla&pse All"), _("Collapses all of the fold levels in the document"))
        wx.EVT_MENU(frame, COLLAPSE_ALL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, COLLAPSE_ALL_ID, frame.ProcessUpdateUIEvent)        
        formatMenuIndex = menuBar.FindMenu(_("&Document"))
        formatMenu = menuBar.GetMenu(formatMenuIndex)
        
        formatMenu.Append(CLEAN_WHITESPACE, _("Clean &Whitespace"), _("Converts leading spaces to tabs or vice versa per 'use tabs' and clears trailing spaces"))
        wx.EVT_MENU(frame, CLEAN_WHITESPACE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CLEAN_WHITESPACE, frame.ProcessUpdateUIEvent)
        
        #formatMenu.Append(COMMENT_LINES_ID, _("Comment Lines"), _("Comment current lines"))
        item = wx.MenuItem(formatMenu, COMMENT_LINES_ID, _("Comment Lines"), _("Comment current lines"))
        item.SetBitmap(getCommentBitmap())
        formatMenu.AppendItem(item)
        wx.EVT_MENU(frame, COMMENT_LINES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, COMMENT_LINES_ID, frame.ProcessUpdateUIEvent)
        
        #formatMenu.Append(UNCOMMENT_LINES_ID, _("UnComment Lines"), _("UnComment current lines"))
        item = wx.MenuItem(formatMenu, UNCOMMENT_LINES_ID, _("UnComment Lines"), _("UnComment current lines"))
        item.SetBitmap(getUncommentBitmap())
        formatMenu.AppendItem(item)
        wx.EVT_MENU(frame, UNCOMMENT_LINES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, UNCOMMENT_LINES_ID, frame.ProcessUpdateUIEvent)   
        
        #formatMenu.Append(INDENT_LINES_ID, _("Indent Lines"), _("Indent current lines"))
        item = wx.MenuItem(formatMenu, INDENT_LINES_ID, _("Indent Lines"), _("Indent current lines"))
        item.SetBitmap(getIndentBitmap())
        formatMenu.AppendItem(item)
        wx.EVT_MENU(frame, INDENT_LINES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, INDENT_LINES_ID, frame.ProcessUpdateUIEvent)   
             
        #formatMenu.Append(DEDENT_LINES_ID, _("Dedent Lines"), _("Dedent current lines"))
        item = wx.MenuItem(formatMenu, DEDENT_LINES_ID, _("Dedent Lines"), _("Dedent current lines"))
        item.SetBitmap(getDedentBitmap())
        formatMenu.AppendItem(item)
        wx.EVT_MENU(frame, DEDENT_LINES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, DEDENT_LINES_ID, frame.ProcessUpdateUIEvent)  

        #item = formatMenu.Append(CHANGE_EOL_MODE, _("End of Line Character"), _("End of Line Character"))
        #wx.EVT_MENU(frame, CHANGE_EOL_MODE, frame.ProcessEvent)
        #wx.EVT_UPDATE_UI(frame, CHANGE_EOL_MODE, frame.ProcessUpdateUIEvent)  

        eolMenu = wx.Menu()
        eolMenu.Append(CHANGE_EOL_MODE_WINDOWS, _('Windows (\\r\\n)'), _('Windows'))
        wx.EVT_MENU(frame, CHANGE_EOL_MODE_WINDOWS, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CHANGE_EOL_MODE_WINDOWS, frame.ProcessUpdateUIEvent)  
        eolMenu.Append(CHANGE_EOL_MODE_UNIX, _('Unix (\\n)'), _('Unix'))
        wx.EVT_MENU(frame, CHANGE_EOL_MODE_UNIX, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CHANGE_EOL_MODE_UNIX, frame.ProcessUpdateUIEvent)  
        eolMenu.Append(CHANGE_EOL_MODE_MAC, _('Macintosh (\\r)'), _('Macintosh'))
        wx.EVT_MENU(frame, CHANGE_EOL_MODE_MAC, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CHANGE_EOL_MODE_MAC, frame.ProcessUpdateUIEvent)
        formatMenu.AppendMenu(CHANGE_EOL_MODE, _("Change EOL Character to"), eolMenu) 
        #formatMenu.AppendSubMenu(eolMenu, _("End of Line Character"), _("End of Line Character"))
        
        if formatMenuIndex == -1:
            viewMenuIndex = menuBar.FindMenu(_("&View"))
            menuBar.Insert(viewMenuIndex + 1, formatMenu, _("&Document"))
            
    def GetCustomizeToolBars(self):
        ret = []
        toolbar = wx.ToolBar(wx.GetApp().GetTopWindow(),
                              -1, wx.DefaultPosition, wx.DefaultSize,
                             wx.TB_FLAT | wx.TB_NODIVIDER)
        toolbar.AddLabelTool(ZOOM_IN_ID,
                             'Zoom In',
                             getZoomInBitmap(),
                             shortHelp = _("Zoom In"), 
                             longHelp = _("Zooms the document to a larger size"))
        toolbar.AddLabelTool(ZOOM_OUT_ID,
                             'Zoom In',
                             getZoomOutBitmap(),
                             shortHelp = _("Zoom Out"), 
                             longHelp = _("Zooms the document to a smaller size"))
        toolbar.AddLabelTool(INDENT_LINES_ID,
                             "Indent Lines",
                             getIndentBitmap(),
                             shortHelp = _("Indent Lines"),
                             longHelp  = _("Indent Lines"))
        toolbar.AddLabelTool(DEDENT_LINES_ID,
                             "Dedent Lines",
                             getDedentBitmap(),
                             shortHelp = _("Dedent Lines"),
                             longHelp  = _("Dedent Lines"))
        toolbar.AddLabelTool(COMMENT_LINES_ID,
                             "Comment Lines",
                             getCommentBitmap(),
                             shortHelp = _('Comment Lines'),
                             longHelp  = _('Comment Lines'))
        toolbar.AddLabelTool(UNCOMMENT_LINES_ID,
                             "Uncomment Lines",
                             getUncommentBitmap(),
                             shortHelp = _("Uncomment Lines"),
                             longHelp  = _("Uncomment Lines"))
        toolbar.Realize()
        ret.append(toolbar)
        return ret
        
    
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if (id == TEXT_ID
        or id == VIEW_WHITESPACE_ID
        or id == VIEW_EOL_ID
        or id == VIEW_INDENTATION_GUIDES_ID
        or id == VIEW_RIGHT_EDGE_ID
        or id == VIEW_LINE_NUMBERS_ID
        or id == ZOOM_ID
        or id == ZOOM_NORMAL_ID
        or id == ZOOM_IN_ID
        or id == ZOOM_OUT_ID
        or id == WORD_WRAP_ID
        or id == EXPAND_TEXT_ID
        or id == COLLAPSE_TEXT_ID
        or id == EXPAND_TOP_ID
        or id == COLLAPSE_TOP_ID
        or id == EXPAND_ALL_ID
        or id == COLLAPSE_ALL_ID
        or id == CLEAN_WHITESPACE
        or id == COMMENT_LINES_ID
        or id == UNCOMMENT_LINES_ID
        or id == INDENT_LINES_ID
        or id == DEDENT_LINES_ID
        or id == CHANGE_EOL_MODE_WINDOWS
        or id == CHANGE_EOL_MODE_UNIX
        or id == CHANGE_EOL_MODE_MAC):
            event.Enable(False)
            return True
        else:
            return False
    
class EditorStatusBar(wx.StatusBar):

    # wxBug: Would be nice to show num key status in statusbar, but can't figure out how to detect if it is enabled or disabled

    def __init__(self, parent, id, style = wx.ST_SIZEGRIP, name = "statusBar"):
        wx.StatusBar.__init__(self, parent, id, style, name)
        self.SetFieldsCount(4)
        self.SetStatusWidths([-1, 50, 50, 55])

    def SetInsertMode(self, insert = True):
        if insert:
            newText = _("Ins")
        else:
            newText = _("")
        if self.GetStatusText(1) != newText:     # wxBug: Need to check if the text has changed, otherwise it flickers under win32
            self.SetStatusText(newText, 1)

    def SetLineNumber(self, lineNumber):
        newText = _("Ln %i") % lineNumber
        if self.GetStatusText(2) != newText:
            self.SetStatusText(newText, 2)

    def SetColumnNumber(self, colNumber):
        newText = _("Col %i") % colNumber
        if self.GetStatusText(3) != newText:
            self.SetStatusText(newText, 3)

class EditorPrintout(wx.lib.docview.DocPrintout):
    """ for Print Preview and Print """
    

    def OnPreparePrinting(self):
        """ initialization """
        dc = self.GetDC()

        ppiScreenX, ppiScreenY = self.GetPPIScreen()
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        scaleX = float(ppiPrinterX)/ppiScreenX
        scaleY = float(ppiPrinterY)/ppiScreenY

        pageWidth, pageHeight = self.GetPageSizePixels()
        self._scaleFactorX = scaleX/pageWidth
        self._scaleFactorY = scaleY/pageHeight

        w, h = dc.GetSize()
        overallScaleX = self._scaleFactorX * w
        overallScaleY = self._scaleFactorY * h
        
        txtCtrl = self._printoutView.GetCtrl()
        font, color = txtCtrl.GetFontAndColorFromConfig()

        self._margin = 40
        self._fontHeight = font.GetPointSize() + 1
        self._pageLines = int((h/overallScaleY - (2 * self._margin))/self._fontHeight)
        self._maxLines = txtCtrl.GetLineCount()
        self._numPages, remainder = divmod(self._maxLines, self._pageLines)
        if remainder != 0:
            self._numPages += 1

        spaces = 1
        lineNum = self._maxLines
        while lineNum >= 10:
            lineNum = lineNum/10
            spaces += 1
        self._printFormat = "%%0%sd: %%s" % spaces


    def OnPrintPage(self, page):
        """ Prints the given page of the view """
        dc = self.GetDC()
        
        txtCtrl = self._printoutView.GetCtrl()
        font, color = txtCtrl.GetFontAndColorFromConfig()
        dc.SetFont(font)
        
        w, h = dc.GetSize()
        dc.SetUserScale(self._scaleFactorX * w, self._scaleFactorY * h)
        
        dc.BeginDrawing()
        
        dc.DrawText("%s - page %s" % (self.GetTitle(), page), self._margin, self._margin/2)

        startY = self._margin
        startLine = (page - 1) * self._pageLines
        endLine = min((startLine + self._pageLines), self._maxLines)
        for i in range(startLine, endLine):
            text = txtCtrl.GetLine(i).rstrip()
            startY += self._fontHeight
            if txtCtrl.GetViewLineNumbers():
                dc.DrawText(self._printFormat % (i+1, text), self._margin, startY)
            else:
                dc.DrawText(text, self._margin, startY)
                
        dc.EndDrawing()

        return True

    def HasPage(self, pageNum):
        return pageNum <= self._numPages

    def GetPageInfo(self):
        minPage = 1
        maxPage = self._numPages
        selPageFrom = 1
        selPageTo = self._numPages
        return (minPage, maxPage, selPageFrom, selPageTo)

class TextStatusBar(wx.StatusBar):

    # wxBug: Would be nice to show num key status in statusbar, but can't figure out how to detect if it is enabled or disabled

    def __init__(self, parent, id, style = wx.ST_SIZEGRIP, name = "statusBar"):
        wx.StatusBar.__init__(self, parent, id, style, name)
        self.SetFieldsCount(4)
        self.SetStatusWidths([-1, 50, 50, 55])

    def SetInsertMode(self, insert = True):
        if insert:
            newText = _("Ins")
        else:
            newText = _("")
        if self.GetStatusText(1) != newText:     # wxBug: Need to check if the text has changed, otherwise it flickers under win32
            self.SetStatusText(newText, 1)

    def SetLineNumber(self, lineNumber):
        newText = _("Ln %i") % lineNumber
        if self.GetStatusText(2) != newText:
            self.SetStatusText(newText, 2)

    def SetColumnNumber(self, colNumber):
        newText = _("Col %i") % colNumber
        if self.GetStatusText(3) != newText:
            self.SetStatusText(newText, 3)

class TextPrintout(wx.lib.docview.DocPrintout):
    """ for Print Preview and Print """

    def OnPreparePrinting(self):
        """ initialization """
        dc = self.GetDC()

        ppiScreenX, ppiScreenY = self.GetPPIScreen()
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        scaleX = float(ppiPrinterX)/ppiScreenX
        scaleY = float(ppiPrinterY)/ppiScreenY

        pageWidth, pageHeight = self.GetPageSizePixels()
        self._scaleFactorX = scaleX/pageWidth
        self._scaleFactorY = scaleY/pageHeight

        w, h = dc.GetSize()
        overallScaleX = self._scaleFactorX * w
        overallScaleY = self._scaleFactorY * h
        
        txtCtrl = self._printoutView.GetCtrl()
        font  = txtCtrl.GetFont()
        color = txtCtrl.GetFontColor()
         
        self._margin = 40
        self._fontHeight = font.GetPointSize() + 1
        self._pageLines = int((h/overallScaleY - (2 * self._margin))/self._fontHeight)
        self._maxLines = txtCtrl.GetLineCount()
        self._numPages, remainder = divmod(self._maxLines, self._pageLines)
        if remainder != 0:
            self._numPages += 1

        spaces = 1
        lineNum = self._maxLines
        while lineNum >= 10:
            lineNum = lineNum/10
            spaces += 1
        self._printFormat = "%%0%sd: %%s" % spaces

    def OnPrintPage(self, page):
        """ Prints the given page of the view """
        dc = self.GetDC()
        
        txtCtrl = self._printoutView.GetCtrl()
        font    = txtCtrl.GetFont()
        color   = txtCtrl.GetFontColor()
        dc.SetFont(font)
        
        w, h = dc.GetSize()
        dc.SetUserScale(self._scaleFactorX * w, self._scaleFactorY * h)
        
        dc.BeginDrawing()
        
        dc.DrawText("%s - page %s" % (self.GetTitle(), page), self._margin, self._margin/2)

        startY = self._margin
        startLine = (page - 1) * self._pageLines
        endLine = min((startLine + self._pageLines), self._maxLines)
        for i in range(startLine, endLine):
            text = txtCtrl.GetLine(i).rstrip()
            startY += self._fontHeight
            if txtCtrl.GetViewLineNumbers():
                dc.DrawText(self._printFormat % (i+1, text), self._margin, startY)
            else:
                dc.DrawText(text, self._margin, startY)
                
        dc.EndDrawing()

        return True


    def HasPage(self, pageNum):
        return pageNum <= self._numPages


    def GetPageInfo(self):
        minPage = 1
        maxPage = self._numPages
        selPageFrom = 1
        selPageTo = self._numPages
        return (minPage, maxPage, selPageFrom, selPageTo)

#----------------------------------------------------------------------------
# Menu Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO, zlib

#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO

def getTextData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x015IDAT8\x8d\xad\x90\xb1N\xc2P\x14\x86\xbf\x02/\xe0\xec#\x18g\xc3\xe6T\
\x13':1\x18H\x98\x14\x12\x17G\x177\x17\x9c4a\xc5\xc0d0\xc2\xccdLx\x02^@+\t\
\xc1\x90\xf6r\xdb\xc6\x94\xe5:\\\xdbP)\xc5DOr\x92\x9b{\xff\xfb\xfd\xff9\xc6h\
l+\xbek.\x02\x00\xec\x99\x03\x80\xeb\xf8\\\x9d\x1d\x1bd\xd5hl\xab\xd7O\x15\
\xf7x\xa1\xfb\xeeq\xa4^>\x94\xba\xb8yRF.\xcf\xa6.D\xa0Nw\x18C\xad\xb2\x19\
\x9f\x0f\xca\x165\xd1V\xed\xebZj\x92\xc2\\\x04\xec\x02\xd5\x8a\x89\xb7\xd4\
\x97n\xa8\xe3?\x0f\x86\x08\x19dNP\x00\xf0\x96\xd0\x7f\xd0\t\x84\x0c(U-\x0eK&\
\xd3P\x8bz\xcdV6 \x8a\xed\x86\x99f\xe9\x00{\xe6\xb0\x13\xc2\xa0\xd3\xd7\t\
\x84\x9f\x10\xec\x9dTp\x1d\xb1=A\xa9j\x01\xc4\xb1\x01&\xfe\x9a~\x1d\xe0:Zu\
\x7f\xdb\x05@J/!(\xd6\x1bL\xde\xec\xcd\x00!\x03\xa6!\x1c\x9dVR\x9d\xdf\xe5\
\x96\x04\xd1au\xd3\xab3\xef\x9f_f\x03\xa2\xa5\x15\xeb\x8d\xc4\xc36\xe7\x18 \
\xa5G\xaf\xd9J\xb8f\xcd\xfc\xb3\x0c#\x97\xff\xb58\xadr\x7f\xfa\xfd\x1f\x80/\
\x04\x1f\x8fW\x0e^\xc3\x12\x00\x00\x00\x00IEND\xaeB`\x82" 


def getTextBitmap():
    return BitmapFromImage(getTextImage())

def getTextImage():
    stream = cStringIO.StringIO(getTextData())
    return ImageFromStream(stream)

def getTextIcon():
    return wx.IconFromBitmap(getTextBitmap())


#----------------------------------------------------------------------------
# Menu Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
#----------------------------------------------------------------------
def getZoomInData():
    return zlib.decompress(
'x\xda\x01\xd5\x02*\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\
\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x02\x8cIDAT8\x8d\xa5\x92_h\x8dq\x18\xc7\xbf\
\xcf\xef}\xdfm\xc6\x8c\xb9p\x96\x9a\x0b\xe7$v\xb5\xabc9\xe5\xcf\x98\x1b1rAM\
\x88\x91"nh\xb9\xe3B\x92\xd2BD\xa2\xa9\xe5\xcf\x9cs\xb8P.\xa4\xb4b6\xe6\xcf\
\x965\xb6L\xecla\x9c\x1c\xe7}\xdf\xdf\xbf\xc7\x8d?\xcd\x96]\xf8^=W\x9f>\xcf\
\xf3|\x81\xff\x0c\xfd\x1a:[\xea\xe3D\xa2\x91 \x12 \xa7\x8c\xad\x05K=\xaa\x94\
lC\xa8\x8fU\xef\xb9\xd9>\x11@\x00@W\xcb\xe6\x06\x87\xbc4,\xe6\x9aP6Y?_\x19|\
\xcbV*\xe97\xc1\xf2\\v\xdc\xf4\x83\x93u\r\x13\x1at\xb6\xd4\xc7\x1d\xf2\xd2V\
\xcbKH\x9c\xbdB\x84J\x10\xcd!\x82!\xb6\x83\x02\xdc\xf35\xb5e\x07\xc1\xd9\xa6\
TP\xb7\xfc\xc0\x9d1&\x82 \x1a\xad1\x19N\x9cm&\x81\xa5 \xc4\x88\xb8\x90AE\x0c\
\x115\xe4T\x97\xac\xbd|\xdeZ\x93aC\x8d\xe3V P\xc2j\x99t],\x04PJ\x04\xc3 C\
\xcc\x06\x04\xc5\xe0R\x16nT\xfb*\t\x88\xc4\xdf\x00\x17$\xca(\xa4Vf\xaa\x01\
\x91\x06\xb3\x01`A0\xe7\xbaw\x9f\x92RA\x05\n\xf5R/(\x98\xea\x1e\x1eg`-#D\x08\
0k0+f\x18"h\xcb\xac\x03_be\xac\x16~>\x04\x00\xb06\xe3\x8e\xe8j\xa9F\x85\x11\
\x1b,\x89N\x01\x9e\xc7\xc4|\xfa\xd9\xae3*T\x88L+G\xa0\x03D\xa6GpbZ\xdf+\x19d\
\xc7\xbf\xd1J\xd9\xc6L\xeb\x85Q\xbd`|$\x82\n\xf3!\x96\xcd\xafA4\x12\xc3pn\
\x18\xb1\x8a\x18V-\xfec2\x06\xa0\xf3\xe11\x0b\x94gS[wZ\xe3\xb4\x03\xf4\xc6\
\xcf\x87H\xb6%\xd1\xd1\xdb\tO\x14\xe1\xf1\xf3\x0e\\M\xdf@\x98\x0f\x91\xdc\
\x97\xd84\xa6\x07\x00p\xff\xf8\x9a\x06\xc7\xa3#J\x9a\x8c\x95*i4\xb7\x02\xc0Q\
7\xfbj\xc5\x92Z\xa4o\xa7pk\xe3^\xa8 \x87\x81\xfb\x0f\xf0\xfd\xedpd\xed\xc5\
\xf6\x11\xe0g\x13\x97\x1d\xbc}A\xfb\xaa\xce*;\x08\xe1\xee\xf3\n\xbd\x1e\xd7s\
{\xfc|\x88d*\x89\xc0\x97\xf0\xa6\x14c\xea\xac\x08*\x16UA\xa2`\xa8e{|\xf6o\
\x83\x7f%\xb5\x7f\xc9\xe6\xb2\x8a\xf2\xe6\x8ax\x1cE\xd3g"\xcc}\xc3H\xf7S\xdc\
k}\xd8\x7f\xe8no\xd4\x99\x0cp\xed\xd1\xe0\x8b\xd5\xf3f\x0c\xf8\x9f?\xad+(\
\xf6\xa0|\x1f\xb9\x91!\x14\xaa {\xe3\xc9\x87\xa6I\x01\x00p\xbd\xe3\xdd\x8b\
\xd5\xd1\x92\xd7\xef\xbb\xfa\xaau\xf0\xa5\xe4\xf3\xebL\x7f\x90GU\xea\xe5\x87\
\xf0\x07\xa6\xa3K\xe6\xf6\n\x1c\xbc\x00\x00\x00\x00IEND\xaeB`\x82]\xb9N~' )

def getZoomInBitmap():
    return BitmapFromImage(getZoomInImage())

def getZoomInImage():
    stream = cStringIO.StringIO(getZoomInData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getZoomOutData():
    return zlib.decompress(
'x\xda\x01\xc2\x02=\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\
\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x02yIDAT8\x8d\xa5\x92MHTa\x14\x86\xdf\xf3\xdd\
\x99\xb4`\x9c\x9a\xca\xb4B-\'\x90\x84\xda5HCE\xcb\x884qc)\x154\xad\x82\xda\
\x04\x83\xbb\\\x84H\x10.J\n\xa4\xb0\xd0~\xa6\xd1U\xd0\xc2\x04\x11J\xd0\xa2(\
\x08"I\xfa\x99\x06\xcc\xbczg\xee\xdc\xfb\xfd\x9c\x16\xa1\x90#\xb8\xe8]\x9d\
\xcdyx\xde\xc3\x01\xfe3\xb44L\x0e\xb4\xc5\x88D\x92 \xe2 +\xc2\xc6\x80}5\'\
\xa5?\x0eOu5\\|:\xb1\x1a@\x00\xc0\x9b\x81\xf6\x84E\xc1a\x18Tk\xcf\xef1n\xbe\
\xbe\xb0h\xd7K\xdf\xed\x81\xe1j\xb6\x02\xc3c7\x9a\x12\xab\x1aL\x0e\xb4\xc5,\
\n\x0e\x1b\xe5\xdfE\xbc\xf7>\x11\xeaA\xb4\x83\x08\x9a\xd8\xcc\x08\xf0\x87\
\xf9\xa13\xe7\t\xd69)\x0bMG\xaf<\xfb\xc7D\x10D\xd2h\x9d\xe1xo?\t\x1c\x01a\
\x0f\x11\x970\xa8\x94!\xa2\x9a\xac\x86P\xe3\xbd;\xc6\xe8\x0ckJ\x16U P\xdc(?\
\x1d\x08`/\x800\x114\x8341k\x10$\x83\xc3,\x02Q\xe5\xca4 \xe2\xc57 \x11!\x8fR\
\xccT\t\x12\nL\x12\x0c\x05\x82dfM\x0cM\x84m\xd2W)\x12\x14)\x02\x18\xc3\xf0\
\xe0\x01\xcc\n\xcc\x92\xff.(\xc3\xac\x080L\xd0\xc4P\x00\xc0J\x17\x1d1\xa0|9\
\'\xb4h1$&\x05\xb8\x96\x89y\xff\xad\xce\x9b\xc6\xf5`\x9c\x1c\xb4\xed@\xdb\
\x0b\xd85\xef@\xdbN1\xc0\xf8\xfe8\x98\x9a\x85\x96\x0f \x02e$\x106\xae\x07\
\xd5\xda\x0c.\x14\xc0y\x17\xc8\xe5!r.dG\xd7*\x06y\xafK\xac+\x19\xb6\x87\xce^\
\x085\r\xde\x16B\xef6N\x0e|\xbd\x17\xda^\x80\x9e_\x80\xb6\x1d\x18\'\x07\xe3z\
H_\x8a\xb76\xf7\x8c\x0f.\xff\x01\x00\x8cv\x9fHXA\xea\x94\xbe\xce\x18_\xa6\
\xb5\xe2\x14\x00\xb0\xaf[\xd6o.\xbbZ^W\'B\x155\x90\x05\x07\xd3\xa3c\xc8}\xf9\
Y\xd1\xd87\x91]\x06\x00\xc0\x8bk\xc7b\xda \t\xa2\xb8 D\xd80|_/\x06\xad`\xb8\
\xe6\xd0A\x84\xcaw\x82\x84\x80\xfd\xed\x13\xde>\x1c1\x12\xfe\xf6S}\x13YZ\xd9\
ie\x86.\x1fn\x8fTU\xf6W\xc5b(-\xdb\x04\xcfYD\xf6\xfdk\x8c\xa4^~\xeex\xfe1j\
\xad\x05x\xf4j\xe6\xdd\xf1\xda\x8d\xd3\xee\xaf\xd9\x93\xeb6\x04!]\x17N\xf6\
\x07J\xa4\x8b\'S\xdf\xbb\xd74X\xca\xe3\xc4\x81v\xe9\xea\xfe-\xd1\xad\xb0\xbf\
\xfe\xce\xc8\xbc\xdawzpj\xf6\x0fjkL\xd7\xbe\xc3\x82\xb0\x00\x00\x00\x00IEND\
\xaeB`\x82\x83\xd32\xe4' )
 

def getZoomOutBitmap():
    return BitmapFromImage(getZoomOutImage())

def getZoomOutImage():
    stream = cStringIO.StringIO(getZoomOutData())
    return ImageFromStream(stream)

def getDedentData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\x02 \xcc\xc1\
\x06$\xe5?\xffO\x04R,\xc5N\x9e!\x1c@P\xc3\x91\xd2\xc1\xc0\xc0\xc8\xe8\xe9\
\xe2\x18b\xd1\x9b\x9c \xf1\xa9A\xf0\x98\x86\xb6\xf6\xef\xff\xef\xef\xdb\xb7\
\xd9\xd7\xff;\xf0\xf1\xfd\xfd\xfd\x0f\x7f\\_\x1f_\xf0\x0bH\xf0\xfc\xfe\xf66\
\xf9H\xba\xc1K\xbd\x04 \xc8\x88\xfc\xff\xcc\xcbwA\x07\xdf\xa6\x08\x07\x87\
\x03\xa53\xd6\x1a\xfc\xf9\xfd=\xbfms\xfa\xf9,#\x03\x03\x83\r@l\xc0\xf2\xe5\
\xfe\xf5)\xe2\xc9\xb1\x9f\xdf~\xbf\xff\xff\x85\xd9\x9f__\xbd?>??_cV\xfd\xdf_\
\xad\x05\x8d\xe1\xc7k}3\x0b\x9f\xb9FMz\xa3\xe6\xd3s\x86\x87\xff~M\xbb\xf77\
\xd7\xd3B_\xd4\x95\x99\x99\x99\x9bco\xa6\xfaf\xb2\xae\xdb\x1a\xf3F\xe6\xff35\
\xef\xc5\x15\x07\x8f\x1d{v\xaa_\xde\xfe\x81\xde\x8f\xcf\xcf\xf9\x0f\xaf\x8f\
\xdf/!g[\xb5\x84\xf9\xfb\xa1\x85zw_\xf3\xf0\xf0D\x05^\x9e\x1f\xe3\xb8\xfd\
\xe1\xf1~y\xad\x1b\x87\x1a\xb2\x18\xde\xb9\xeb\xeb\xaf\x07Z\xbd\xf0vW\xcf\
\xfe\x9a\x9fNOK\x12\x92\x93?\xcbG\x97(\xde\xfe\xf5\xf1\xb1\xfb\xab\x1b^\xa1\
\x0c\x0c\xa7\x98N\x87m\xb6\xe0~\x0c\x0c\x1c\x06OW?\x97uN\tM\x00\xed2\x98\x05\
' )

def getDedentBitmap():
    return BitmapFromImage(getDedentImage())

def getDedentImage():
    stream = cStringIO.StringIO(getDedentData())
    return ImageFromStream(stream)

def getDedentIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getDedentBitmap())
    return icon

#----------------------------------------------------------------------
def getIndentData():
    return zlib.decompress(
'x\xda\x01A\x01\xbe\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\
\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x00\xf8IDAT8\x8dc`\x18\xf2\x80\x11\xc6(++\xfb\
\xff\xef\xdf?\x86?\x7f\xfe\xc0\xf1\xef\xdf\xbf\xe1\xf8\xd7\xaf_p\xfa\xd7\xaf\
_\x0c\xfb\xf6\xedc\xc4g0\xe9.\x80\x81\xf6\xcdo\xaeT\xfa\x8a\xe8\xc0\xf8\x01\
\x01\x01\xd7a\xb6\xc2\xf0\xef\xdf\xbf\x19\xce\x9e=\xab\xc9\xc0\xc0\xc0\xc0\
\x82n\xc0\x8f\xdf\xff\x182\x16<\xbez\xe7\xce\xb7\x90=-\xea\xd7\x7f\xfd\xfa\
\xa5\xf8\xf3\xe7O\x14\xcd\xbf~\xfdBuA\xf3\xa6\xe7\xffa\x02"\xdcl\x0c\x9f\xbe\
\xfff8}\xe7\xeb\x99\xc77\xbf\xc5\x9d\x9c\xae{\x9d$/d/zv\xe5\xe5\xfb\xefLw/}\
\x08>?\xd7\xf8\xba\x8d\x8d\xcd\x95\x1f?~\xc0]\xf0\xe7\xcf\x1f\x86_\xbf~1<z\
\xf4H\x07\xab\x17\xbe\xfd\xfc\xc7\xb0&_Y\x0b\xee\xa5\x1f?T\xb0\x85\x01\xd5\
\x00\xdc\x0b^^^\xff\xd1mB\xb7\x15\x19\x7f\xf9\xf2\x85\xca\xe9\xc0\xc6\xc6\
\xe6?\xb6\xe8B\xb6\xf5\xe3\xc7\x8f\xd4\xb1\x95\xaa\x00\x00\xda\xd5\xdc\xbf\
\xc7\x1a\x11N\x00\x00\x00\x00IEND\xaeB`\x82\xe7\x97\x9eK' )

def getIndentBitmap():
    return BitmapFromImage(getIndentImage())

def getIndentImage():
    stream = cStringIO.StringIO(getIndentData())
    return ImageFromStream(stream)

def getIndentIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getIndentBitmap())
    return icon

def getUncommentData():
    return zlib.decompress(
"x\xda\x018\x01\xc7\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x00\xefIDATX\x85\xed\x96A\n\xc20\x10E\xff\x88+M\xb7n\xbcE\
\x8f\xe0\x11\xdc\x17q'(=\x8cx\x03\xaf\xe2\xba\xc7\x10]\x9b\xd2]\xe3\xa2\x16\
\xe9\xd84\x89URJ\xfe2d\x86\xc9\xe3\xff!$\xa5\x82\x8b\x8a\xfc\n\x00(\xcb\xaa\
\x8e\xa8:\x9f\x89\xa5S\x9fZ\x93\xaf\xaa~\xa8\xa9k\xc1bw\xd3 \xbb\x03\x00N\
\xab\x0b\x00`\xb3M\xc9\xa6\xdf\xf0\x08DI\xa6\x00\xe0q\x8e\xa9\xed\xdc\xf4\
\xc2(\xc1\x8b\xd0Qu\xdd\xab\xe5\x9d\x00\xf1\x14\xd4/\xe5\xe2DL\xd2\x91\xe4\
\xf2N\xc0\xfb\x00\xd61\xb4E\xca\xcd\n\xc4\x9d}\xbd\x13\xf80!\x97\x98\xc3jW\
\xd3:\x03\xf0~\xf9\xfe\x90\xb6\xde\x939\x1a\x04\x87O\xe0\xdf\xf2N \x0c`\xdc\
\x03\xb6)\xb0\xd5\xe0R`$\xc0'\x1e\xdd\x97,\x0c\xe0\xbc\t\x85\xa0^\xa9\x90R5<\
\xe5<@0\xe1\xe8\x06\xd0.\xa2\xbef\xd3\x89\x9b\xd0;\x81\x90\x82'\xa7\x97c\xc4\
Cl\x92\x7f\x00\x00\x00\x00IEND\xaeB`\x82\xaa\x8a\x88\xcf" )

def getUncommentBitmap():
    return BitmapFromImage(getUncommentImage().Scale(16,16))

def getUncommentImage():
    stream = cStringIO.StringIO(getUncommentData())
    return ImageFromStream(stream)

def getUncommentIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getUncommentBitmap())
    return icon
    
def getCommentData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2\xcb=]\x1cC"Z\
\xdfN?\xc8u@\x81\xc7\xf9\xf2\xc3\xdc\xbf\xff\xf5\xdf\x9e{\x17r\x83\xcd\x88\
\x7f*\xcf\xb4r!\x91Z\x16\xe6,AY\x1f\xb3W/\x19\xa2\xf8\xee\xbc\x15su\xd9~1\
\x86u\xa7\xbd-\xe3\xef\xbf\xb2\x13\x18b\x17\xec\xd5g\xacq\xaf\xe5\xe5\xafY\
\xdc\x16\xcc\xb9\xe4-\xd7\x0bN\x0f\x07\xdd\x00n\x15\x83R\xf6y!6\x17\xbf\xa8x\
\x03E\x1a\xf4\x0c\xd6<\xec\xba\x7fA\xf4\xaa\xc1B\xf5\x02\xa67.\xaa\xbb_\x7f\
\xb5\x049\x81\xc1\xd3\xd5\xcfe\x9dSB\x13\x00\xa4AA\x8b' )

def getCommentBitmap():
    return BitmapFromImage(getCommentImage().Scale(16, 16))

def getCommentImage():
    stream = cStringIO.StringIO(getCommentData())
    return ImageFromStream(stream)

def getCommentIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getCommentBitmap())
    return icon
        
if 'wxMSW' in wx.PlatformInfo:
    FACES = { 'CourierNew': 'Courier New',
              'times'     : 'Times New Roman',
              'mono'      : 'Lucida Console',   #     'Courier New',
              'helv'      : 'Arial',
              'lucida'    : 'Lucida Console',
              'other'     : 'Comic Sans MS',
              'size'      : 10,       #10,
              'lnsize'    : 10,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }      