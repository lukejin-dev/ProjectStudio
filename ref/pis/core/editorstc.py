import wx, wx.stc
import config
import os
import syntax
import string
import outline
import search

if wx.Platform == '__WXMSW__':
    _WINDOWS = True
else:
    _WINDOWS = False

# Margin Positions
MARK_MARGIN = 0
NUM_MARGIN  = 1
FOLD_MARGIN = 2
    
class EditorTextCtrl(wx.stc.StyledTextCtrl):
    CURRENT_LINE_MARKER_NUM = 2
    BREAKPOINT_MARKER_NUM = 1
    CURRENT_LINE_MARKER_MASK = 0x4
    BREAKPOINT_MARKER_MASK = 0x2
        
    def __init__(self, parent, id=-1, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.stc.StyledTextCtrl.__init__(self, parent, id, style=style)

        if isinstance(parent, wx.gizmos.DynamicSashWindow):
            self._dynSash = parent
            self.SetupDSScrollBars()
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_SPLIT, self.OnDSSplit)
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_UNIFY, self.OnDSUnify)
        self._config    = config.EditorConfig()

        self._doc = self.GetParent()._view.GetDocument()
        ext = None
        if self._doc != None:
            fname = self._doc.GetFilename()
            if fname != None and len(fname) != 0:
                ext = fname.split(os.extsep)[-1].lower()
        self._style = syntax.Style(ext)
        
        # KEN: not sure how to use Visible Policy
        #self.SetVisiblePolicy(wx.stc.STC_VISIBLE_STRICT,1)
        self.SetVisiblePolicy(wx.stc.STC_VISIBLE_SLOP, 7)
        
        # Setting zoom key.
        self.CmdKeyClear(wx.stc.STC_KEY_ADD, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.stc.STC_KEY_SUBTRACT, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyAssign(wx.stc.STC_KEY_PRIOR, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(wx.stc.STC_KEY_NEXT, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMOUT)
        
        # Drop target
        # accept file drag to main frame
        # TODO: it not better to use frame's file drop class, stc should deal with
        # file/data/text drop case.
        import auitabbedframe
        self.SetDropTarget(auitabbedframe.FrameFileDropTarget(wx.GetApp().GetTopWindow()))

        # Set up left margins
        ## Outer Left Margin Bookmarks
        self.SetMarginType(MARK_MARGIN, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginSensitive(MARK_MARGIN, True)
        self.SetMarginWidth(MARK_MARGIN, 12)
        
        ## Middle Left Margin Line Number Indication
        self.SetMarginType(NUM_MARGIN, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(NUM_MARGIN, self.EstimatedLineNumberMarginWidth())
        
        ## Inner Left Margin Setup Folders
        self.SetMarginType(FOLD_MARGIN, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(FOLD_MARGIN, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(FOLD_MARGIN, True)
        
        self.ConfigureView()
        self.RefreshStyle()
        
        if self.GetMatchingBraces(): 
            wx.stc.EVT_STC_UPDATEUI(self, self.GetId(), self.OnUpdateUI)
        
        # Event Mapping
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.stc.EVT_STC_ZOOM, self.OnUpdateLineNumberMarginWidth)  # auto update line num width on zoom
        wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)
        wx.EVT_SET_FOCUS(self, self.OnFocus)
        wx.stc.EVT_STC_MARGINCLICK(self, self.GetId(), self.OnMarginClick)
        self.SetSelectionMode(wx.stc.STC_SEL_RECTANGLE)

    def ConfigureView(self):
        """Editor view configuration
        These configurations does not matter with language. And setting will be applied
        for all language document.
        """
        self.SetViewWhiteSpace(self._config.GetBoolean("EditorViewWhitespace", False))
        self.SetViewEOL(self._config.GetBoolean("EditorViewEOL", False))
        self.SetIndentationGuides(self._config.GetBoolean("EditorViewIndentationGuides", False))
        self.SetViewLineNumbers(self._config.GetBoolean("EditorViewLineNumbers", True))
        self.SetViewFolding(self._config.GetBoolean("EditorViewFolding", True))
        self.SetWordWrap(self._config.GetBoolean("EditorWordWrap", False))
        self.SetUseTabs(self._config.GetBoolean("EditorUseTabs", False))
        self.SetIndent(self._config.GetInt("EditorIndentWidth", 4))
        self.SetTabWidth(self._config.GetInt("EditorTabWidth", 4))
        self.SetEOLMode(self.GetEOLModeFromString(self._config.Get("EditorEOLMode", 'Unix')))
        bShowEdge = self._config.GetBoolean("EditorShowEdge", True)
        if bShowEdge:
            self.SetEdgeColumn(self._config.GetInt("EdtitorEdgeColumn", 80))
            self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        else:
            self.SetEdgeMode(wx.stc.STC_EDGE_NONE)
        self.SetCaretLineVisible(self._config.GetBoolean("EditorCaretVisible", True))
        self.SetWrapMode(self._config.GetBoolean("EditorWrapMode", False))
        
    def RefreshStyle(self):
        self.ClearDocumentStyle()
        self.SetLexer(self._style.GetLex())
        self.UpdateBaseStyles()
        self.ConfigureLexer()
        properties = self._style.GetProperties()
        for key in properties.keys():
            self.SetProperty(key, properties[key])
        
    def GetEOLModeFromString(self, modStr):
        mode_map = {'Macintosh': wx.stc.STC_EOL_CR,  # \r
                    'Unix': wx.stc.STC_EOL_LF,       # \n
                    'Windows': wx.stc.STC_EOL_CRLF}  # \r\n
        mode = mode_map.get(modStr, wx.stc.STC_EOL_LF)
        #return mode
        #
        # TODO: work around for EDES2008 can not handle window
        # EOL correctly.
        #
        return wx.stc.STC_EOL_CRLF
        
    def GetEOLChar(self):
        """Gets the eol character used in document
        @return: the character used for eol in this document

        """
        mode = self.GetEOLModeFromString(self._config.Get("EditorEOLMode", 'Windows'))
        if mode == wx.stc.STC_EOL_CR:
            return u'\r'
        elif mode == wx.stc.STC_EOL_CRLF:
            return u'\r\n'
        else:
            return u'\n'
                    
    def StyleDefault(self):
        """Clears the editor styles to default
        @postcondition: style is reset to default

        """
        self.StyleClearAll()
        self.SetCaretForeground(wx.NamedColor("black"))
        self.Colourise(0, -1)
                
    def UpdateBaseStyles(self):
        self.StyleDefault()
        self.SetMargins(2, 0)
        
        # Global default styles for all languages
        globalStyle = syntax.Style()
        self.StyleSetSpec(0, globalStyle.GetStyle('STC_STYLE_DEFAULT'))
        for styname in globalStyle.GetStyleNames():
            if not hasattr(wx.stc, styname):
                continue
            stc_id = getattr(wx.stc, styname)
            self.StyleSetSpec(stc_id, globalStyle.GetStyle(styname))

        self.SetCaretForeground('#555555')
        self.SetCaretLineBack('#D8F8FF')
        self.DefineMarkers()
        self.Colourise(0, -1)
    
    def DefineMarkers(self):
        fore = self._config.Get('EditorMarkerForeColor', '#D1D1D1')
        back = self._config.Get('EditorMarkerBackColor', 'black')

        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     
                          wx.stc.STC_MARK_BOXPLUSCONNECTED,  
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, 
                          wx.stc.STC_MARK_BOXMINUSCONNECTED, 
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, 
                          wx.stc.STC_MARK_TCORNER,  
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    
                          wx.stc.STC_MARK_LCORNER,  
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     
                          wx.stc.STC_MARK_VLINE,    
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        
                          wx.stc.STC_MARK_BOXPLUS,  
                          fore, back)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    
                          wx.stc.STC_MARK_BOXMINUS, 
                          fore, back)

        # Define the current line marker
        self.MarkerDefine(self.CURRENT_LINE_MARKER_NUM, 
                          wx.stc.STC_MARK_SHORTARROW, 
                          wx.BLACK, 
                          (255,255,128))
                          
        #self.MarkerDefine(0, wx.stc.STC_MARK_SHORTARROW, fore, back)
        self.MarkerDefine(0, wx.stc.STC_MARK_ROUNDRECT, wx.BLACK, wx.BLUE)
        self.SetFoldMarginHiColour(True, fore)
        self.SetFoldMarginColour(True, fore)
             
    def ConfigureLexer(self):
        if self._style.IsDefault():
            return
        
        # Set keywords
        self.SetKeyWords(0, self._style.GetKeywords())
        
        # Set language related style
        for styname in self._style.GetStyleNames():
            if not hasattr(wx.stc, styname):
                continue
            stc_id = getattr(wx.stc, styname)
            self.StyleSetSpec(stc_id, self._style.GetStyle(styname))

    def ChangeFilename(self, file):
        """When file name is changed, the syntax should be also
        changed.
        """
        ext = file.split(os.extsep)[-1].lower()
        self._style = syntax.Style(ext)
        self.RefreshStyle()
        
    def GetOutlineCallback(self):
        return self._style.GetOutlineCallback()
        
    def OnFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return

        self.SetSelBackground(1, "BLUE")
        self.SetSelForeground(1, "WHITE")
        if hasattr(self, "_dynSash"):
            self._dynSash._view.SetCtrl(self)
        event.Skip()

    def OnKillFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return
        self.SetSelBackground(0, "BLUE")
        self.SetSelForeground(0, "WHITE")
        self.SetSelBackground(1, "#C0C0C0")
        # Don't set foreground color, use syntax highlighted default colors.
        event.Skip()

    def GetFont(self):
        sty = syntax.Style()
        face = sty.GetDefaultFont('STC_STYLE_DEFAULT')
        size = sty.GetDefaultSize('STC_STYLE_DEFAULT')
        font = wx.Font(size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = face)
        return font
        
    def GetFontColor(self):
        sty = syntax.Style()
        colorstr = sty.GetDefaultForeColor('STC_STYLE_DEFAULT')
        red = int("0x" + colorstr[1:3], 16)
        green = int("0x" + colorstr[3:5], 16)
        blue = int("0x" + colorstr[5:7], 16)
        color = wx.Color(red, green, blue)
        return color

    def SetFontColor(self, fontColor = wx.BLACK):
        self._fontColor = fontColor
        self.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, "#%02x%02x%02x" % (self._fontColor.Red(), self._fontColor.Green(), self._fontColor.Blue()))
        
    def EstimatedLineNumberMarginWidth(self):
        MARGIN = 4
        baseNumbers = "000"
        lineNum = self.GetLineCount()
        lineNum = lineNum/100
        while lineNum >= 10:
            lineNum = lineNum/10
            baseNumbers = baseNumbers + "0"

        return self.TextWidth(wx.stc.STC_STYLE_LINENUMBER, baseNumbers) + MARGIN

    def OnUpdateLineNumberMarginWidth(self, event):
        self.UpdateLineNumberMarginWidth()
            
    def UpdateLineNumberMarginWidth(self):
        if self.GetViewLineNumbers():
            self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())
        
    def OnClear(self):
        # Used when Delete key is hit.
        sel = self.GetSelection()
                
        # Delete the selection or if no selection, the character after the caret.
        if sel[0] == sel[1]:
            self.SetSelection(sel[0], sel[0] + 1)
        else:
            # remove any folded lines also.
            startLine = self.LineFromPosition(sel[0])
            endLine = self.LineFromPosition(sel[1])
            endLineStart = self.PositionFromLine(endLine)
            if startLine != endLine and sel[1] - endLineStart == 0:
                while not self.GetLineVisible(endLine):
                    endLine += 1
                self.SetSelectionEnd(self.PositionFromLine(endLine))
            
        self.Clear()

    def OnPaste(self):
        # replace any folded lines also.
        sel = self.GetSelection()
        startLine = self.LineFromPosition(sel[0])
        endLine = self.LineFromPosition(sel[1])
        endLineStart = self.PositionFromLine(endLine)
        if startLine != endLine and sel[1] - endLineStart == 0:
            while not self.GetLineVisible(endLine):
                endLine += 1
            self.SetSelectionEnd(self.PositionFromLine(endLine))
                
        self.Paste()

    #----------------------------------------------------------------------------
    # View Text methods
    #----------------------------------------------------------------------------
    def SetViewRightEdge(self, viewRightEdge):
        if viewRightEdge:
            self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        else:
            self.SetEdgeMode(wx.stc.STC_EDGE_NONE)
    def GetViewRightEdge(self):
        return self.GetEdgeMode() != wx.stc.STC_EDGE_NONE

    def GetViewLineNumbers(self):
        return self.GetMarginWidth(1) > 0

    def SetViewLineNumbers(self, viewLineNumbers = True):
        if viewLineNumbers:
            self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())
        else:
            self.SetMarginWidth(1, 0)

    def GetViewFolding(self):
        return self.GetMarginWidth(2) > 0

    def SetViewFolding(self, viewFolding = True):
        if viewFolding:
            self.SetMarginWidth(FOLD_MARGIN, 12)
        else:
            self.SetMarginWidth(FOLD_MARGIN, 0)

    def GetWordWrap(self):
        return self.GetWrapMode() == wx.stc.STC_WRAP_WORD

    def SetWordWrap(self, wordWrap):
        if wordWrap:
            self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        else:
            self.SetWrapMode(wx.stc.STC_WRAP_NONE)

    #----------------------------------------------------------------------------
    # DynamicSashWindow methods
    #----------------------------------------------------------------------------

    def SetupDSScrollBars(self):
        # hook the scrollbars provided by the wxDynamicSashWindow
        # to this view
        v_bar = self._dynSash.GetVScrollBar(self)
        h_bar = self._dynSash.GetHScrollBar(self)
        v_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        h_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        v_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)
        h_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)

        # And set the wxStyledText to use these scrollbars instead
        # of its built-in ones.
        self.SetVScrollBar(v_bar)
        self.SetHScrollBar(h_bar)


    def OnDSSplit(self, evt):
        newCtrl = self._dynSash._view.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
        newCtrl.SetDocPointer(self.GetDocPointer())     # use the same document
        self.SetupDSScrollBars()
        if self == self._dynSash._view.GetCtrl():  # originally had focus
            wx.CallAfter(self.SetFocus)  # do this to set colors correctly.  wxBug:  for some reason, if we don't do a CallAfter, it immediately calls OnKillFocus right after our SetFocus.


    def OnDSUnify(self, evt):
        self.SetupDSScrollBars()
        self.SetFocus()  # do this to set colors correctly
    
    def OnDSSBScroll(self, evt):
        # redirect the scroll events from the _dynSash's scrollbars to the STC
        self.GetEventHandler().ProcessEvent(evt)


    def OnDSSBFocus(self, evt):
        # when the scrollbar gets the focus move it back to the STC
        self.SetFocus()


    def DSProcessEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            if event.GetId() == wx.ID_SELECTALL:
                # force focus so that select all occurs in the window user right clicked on.
                self.SetFocus()

            return self._dynSash._view.ProcessEvent(event)
        return False


    def DSProcessUpdateUIEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            id = event.GetId()
            if (id == wx.ID_SELECTALL  # allow select all even in non-active window, then force focus to it, see above ProcessEvent
            or id == wx.ID_UNDO
            or id == wx.ID_REDO):
                pass  # allow these actions even in non-active window
            else:  # disallow events in non-active windows.  Cut/Copy/Paste/Delete is too confusing user experience.
                if self._dynSash._view.GetCtrl() != self:
                     event.Enable(False)
                     return True

            return self._dynSash._view.ProcessUpdateUIEvent(event)
        return False

    def OnRightUp(self, event):
        #Hold onto the current line number, no way to get it later.
        self._rightClickPosition = self.PositionFromPoint(event.GetPosition())
        self._rightClickLine = self.LineFromPosition(self._rightClickPosition)
        self.PopupMenu(self.CreatePopupMenu(), event.GetPosition())
        self._rightClickLine = -1
        self._rightClickPosition = -1
        

    def CreatePopupMenu(self):
        TOGGLEBREAKPOINT_ID = wx.NewId()
        TOGGLEMARKER_ID = wx.NewId()
        SYNCTREE_ID = wx.NewId()
        SEARCH_IN_WORKSPACE_ID = wx.NewId()
        
        menu = wx.Menu()
        
        itemIDs = [wx.ID_UNDO, wx.ID_REDO, None, search.FindService.FIND_ID, search.FindService.REPLACE_ID,
                   search.FindService.FIND_IN_FILES_ID, None,
                   wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR, None, wx.ID_SELECTALL]

        menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
        for itemID in itemIDs:
            if not itemID:
                menu.AppendSeparator()
            else:
                item = menuBar.FindItemById(itemID)
                if item:
                    menu.Append(itemID, item.GetLabel())
                    wx.EVT_MENU(self, itemID, self.DSProcessEvent)  # wxHack: for customized right mouse menu doesn't work with new DynamicSashWindow
                    wx.EVT_UPDATE_UI(self, itemID, self.DSProcessUpdateUIEvent)  # wxHack: for customized right mouse menu doesn't work with new DynamicSashWindow
        return menu
                

    def HasSelection(self):
        return self.GetSelectionStart() - self.GetSelectionEnd() != 0  

    def ClearCurrentLineMarkers(self):
        self.MarkerDeleteAll(self.CURRENT_LINE_MARKER_NUM)

    def GetMatchingBraces(self):
        """ Overwrite this method for language specific braces """
        return "[]{}()"

    def CanWordWrap(self):
        return True
        
    def OnKeyPressed(self, event):
        parent = self
        while not (hasattr(parent, '_view')):
            parent = parent.GetParent()
        
        doc = parent._view.GetDocument()
        filename = doc.GetFilename()
        line = self.GetCurrentLine()
        
        if self.CallTipActive():
            self.CallTipCancel()
        
        key = event.GetKeyCode()
        
        if False:  # key == wx.WXK_SPACE and event.ControlDown():
            pos = self.GetCurrentPos()
            # Tips
            if event.ShiftDown():
                self.CallTipSetBackground("yellow")
                self.CallTipShow(pos, 'param1, param2')
            # Code completion
            else:
                #lst = []
                #for x in range(50000):
                #    lst.append('%05d' % x)
                #st = string.join(lst)
                #print len(st)
                #self.AutoCompShow(0, st)

                kw = keyword.kwlist[:]
                kw.append("zzzzzz")
                kw.append("aaaaa")
                kw.append("__init__")
                kw.append("zzaaaaa")
                kw.append("zzbaaaa")
                kw.append("this_is_a_longer_value")
                kw.append("this_is_a_much_much_much_much_much_much_much_longer_value")

                kw.sort()  # Python sorts are case sensitive
                self.AutoCompSetIgnoreCase(False)  # so this needs to match

                self.AutoCompShow(0, string.join(kw))
        elif key == wx.WXK_RETURN:
            self.DoIndent()
        elif key == wx.WXK_NUMPAD_ADD:  #wxBug: For whatever reason, the key accelerators for numpad add and subtract with modifiers are not working so have to trap them here
            if event.ControlDown():
                self.ToggleFoldAll(expand = True, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = True)
            else:
                self.ToggleFold(self.GetCurrentLine())
        elif key == wx.WXK_NUMPAD_SUBTRACT:
            if event.ControlDown():
                self.ToggleFoldAll(expand = False, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = False)
            else:
                self.ToggleFold(self.GetCurrentLine())
        else:
            event.Skip()

    def GetIndentChar(self):
        """Gets the indentation char used in document
        @return: indentation char used either space or tab

        """
        if self.GetUseTabs():
            return u'\t'
        else:
            return u' ' * self.GetTabWidth()
            
    def DoIndent(self):
        line = self.GetCurrentLine()
        text = self.GetTextRange(self.PositionFromLine(line), \
                                 self.GetCurrentPos())
        if text.strip() == u'':
            self.AddText(self.GetEOLChar() + text)
            self.EnsureCaretVisible()
            return
        indent = self.GetLineIndentation(line)
        i_space = indent / self.GetTabWidth()
        ndent = self.GetEOLChar() + self.GetIndentChar() * i_space
        self.AddText(ndent + \
                     ((indent - (self.GetTabWidth() * i_space)) * u' '))
        self.EnsureCaretVisible()        

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                lineCount = self.GetLineCount()
                expanding = True

                # find out if we are folding or unfolding
                for lineNum in range(lineCount):
                    if self.GetFoldLevel(lineNum) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                        expanding = not self.GetFoldExpanded(lineNum)
                        break;

                self.ToggleFoldAll(expanding)
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())
                if self.GetFoldLevel(lineClicked) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

        elif evt.GetMargin() == 0:
            """
            Currently, need not support debug service
            """
            #This is used to toggle breakpoints via the debugger service.
            #import DebuggerService
            #db_service = wx.GetApp().GetService(DebuggerService.DebuggerService)
            #if db_service:
            #    db_service.OnToggleBreakpoint(evt, line=self.LineFromPosition(evt.GetPosition()))
            

    def OnUpdateUI(self, evt):
        braces = self.GetMatchingBraces()
        
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in braces:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in braces:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

        evt.Skip()

    def ToggleFoldAll(self, expand = True, topLevelOnly = False):
        i = 0
        lineCount = self.GetLineCount()
        while i < lineCount:
            if not topLevelOnly or (topLevelOnly and self.GetFoldLevel(i) & wx.stc.STC_FOLDLEVELNUMBERMASK  == wx.stc.STC_FOLDLEVELBASE):
                if (expand and self.CanLineExpand(i)) or (not expand and self.CanLineCollapse(i)):
                    self.ToggleFold(i)
            i = i + 1

    def CanLineExpand(self, line):
        return not self.GetFoldExpanded(line)

    def CanLineCollapse(self, line):
        return self.GetFoldExpanded(line) and self.GetFoldLevel(line) & wx.stc.STC_FOLDLEVELHEADERFLAG

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1
        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & wx.stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)
                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1;

        return line

