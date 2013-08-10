import os
import logging.handlers
import wx
import wx.stc
import wx.lib.newevent
import wx.lib.platebtn as platebtn

import ps_art
from interfaces.core import IService
from interfaces.core import ISingleView
import interfaces.event

LogWriteEvent, EVT_LOG_WRITE = wx.lib.newevent.NewEvent()

_=wx.GetTranslation

class PSOutputService(IService):
    def __init__(self):
        self._logger = wx.GetApp().GetLogger("OutputServ")
        
    def GetName(self):
        return "OutputService"
    
    def Start(self):
        frame = wx.GetApp().GetMainFrame()
        self._view = frame.CreateSingleView(PSOutputView)
        self._handle = logging.StreamHandler(OutputStream(self._view))
        wx.GetApp().AddLogHandler(self._handle)
        self._handle.setFormatter(logging.Formatter("%(name)-8s %(levelname)-8s %(message)s"))
        
    def Stop(self):
        wx.GetApp().RemoveLoggerHandler(self._handle)
    
class OutputStream:
    def __init__(self, view):
        self._view = view
        
    def write(self, text):
        wx.PostEvent(self._view.GetCtrl(), LogWriteEvent(message=text))
    
    def flush(self):
        pass
    
class PSOutputView(ISingleView):
    def __init__(self):
        self._errorLines = []
        
    def GetName(self):
        return "Output"
    
    def GetIconName(self):
        return ps_art.PS_ART_LOG
    
    def Create(self, parentWnd):
        style = platebtn.PB_STYLE_SQUARE|platebtn.PB_STYLE_GRADIENT
        
        self._preErrBt = platebtn.PlateButton(parentWnd, -1, bmp=wx.ArtProvider_GetBitmap(ps_art.PS_ART_UP, size=(16, 16)), style=style)
        self._preErrBt.SetToolTipString(_("Previous Error"))
        self._preErrBt.Bind(wx.EVT_UPDATE_UI, self.OnUpdatePreErrBt)
        parentWnd.Bind(wx.EVT_BUTTON, self.OnPrevError, self._preErrBt)

        self._nextErrBt = platebtn.PlateButton(parentWnd, -1, bmp=wx.ArtProvider_GetBitmap(ps_art.PS_ART_DOWN, size=(16, 16)), style=style)
        self._nextErrBt.SetToolTipString(_("Next Error"))
        self._nextErrBt.Bind(wx.EVT_UPDATE_UI, self.OnUpdateNextErrBt)
        parentWnd.Bind(wx.EVT_BUTTON, self.OnNextError, self._nextErrBt)
        
        self._copybt = platebtn.PlateButton(parentWnd, -1, bmp=wx.ArtProvider_GetBitmap(ps_art.PS_ART_COPY, size=(16, 16)), style=style)
        self._copybt.SetToolTipString(_("Copy to clipboard"))
        self._copybt.Bind(wx.EVT_UPDATE_UI, self.OnUpdateCopyButton)
        parentWnd.Bind(wx.EVT_BUTTON, self.OnCopyLog, self._copybt)
        
        self._clearbt = platebtn.PlateButton(parentWnd, -1, bmp=wx.ArtProvider_GetBitmap(ps_art.PS_ART_CLEAR, size=(16, 16)), style=style)
        self._clearbt.SetToolTipString(_("Clear log"))
        self._clearbt.Bind(wx.EVT_BUTTON, self.OnClearLog)
        parentWnd.Bind(wx.EVT_BUTTON, self.OnClearLog, self._clearbt)
        
        choices = ["All"]
        choices += wx.GetApp().GetLoggerAreas()[1:]
        self._sel  = wx.ComboBox(parentWnd, -1, choices=choices, size=(-1, 20), style=wx.CB_READONLY)
        self._sel.Bind(wx.EVT_COMBOBOX, self.OnAreaSelect)
        self._sel.SetSelection(0)
        
        self._text = wx.stc.StyledTextCtrl(parentWnd, -1, style=wx.SIMPLE_BORDER)
        self._text.SetReadOnly(True)
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
        #self._text.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, 
        #                        "face:%s, size:9" %  font.GetFaceName())
        self._text.Bind(EVT_LOG_WRITE, self.OnLogWrite)
        self._text.SetCaretLineVisible(True)
        self._text.SetCaretLineBack('#6777A2') 
        self._text.SetCaretForeground('#555555')
        
        # clear all margin
        self._text.SetMarginWidth(0, 0)
        self._text.SetMarginWidth(1, 0)
        self._text.SetMarginWidth(2, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        topsizer.Add(self._preErrBt, 0, wx.RIGHT|wx.ALIGN_CENTER, 0)
        topsizer.Add(self._nextErrBt, 0, wx.RIGHT|wx.ALIGN_CENTER, 0)
        topsizer.Add(self._copybt, 0, wx.RIGHT|wx.ALIGN_CENTER, 0)
        topsizer.Add(self._clearbt, 0, wx.RIGHT|wx.ALIGN_CENTER, 5)
        topsizer.Add(self._sel, 0, wx.RIGHT|wx.ALIGN_CENTER, 2)
        sizer.Add(topsizer, 0, wx.ALL|wx.ALIGN_RIGHT, 2)        
        sizer.Add(self._text, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 2)
        parentWnd.SetSizer(sizer)
        
        parentWnd.Bind(interfaces.event.EVT_QUERY_FOCUS_EDIT_EVENT, self.OnQueryFocusEdit)
        parentWnd.Bind(interfaces.event.EVT_FOCUS_EDIT_EVENT, self.OnFocusEdit)
        
    def OnFocusEdit(self, event):
        id = event.GetId()
        if id == interfaces.event.ID_FOCUS_UNDO:
            self._text.Undo()
            return
        if id == interfaces.event.ID_FOCUS_REDO:
            self._text.Redo()
            return
        if id == interfaces.event.ID_FOCUS_COPY:
            self._text.Copy()
            return
        if id == interfaces.event.ID_FOCUS_CUT:
            self._text.Cut()
            return
        if id == interfaces.event.ID_FOCUS_PASTE:
            self._text.Paste()
            return
                
    def OnQueryFocusEdit(self, event):
        id = event.GetId()
        if id == interfaces.event.ID_FOCUS_UNDO:
            event.can = self._text.CanUndo()
            return
        if id == interfaces.event.ID_FOCUS_REDO:
            event.can = self._text.CanRedo()
            return
        if id == interfaces.event.ID_FOCUS_COPY:
            start, end = self._text.GetSelection()
            event.can = start != end
            return
        if id == interfaces.event.ID_FOCUS_CUT or \
           id == interfaces.event.ID_FOCUS_PASTE:
            event.can = False
            return

        
        
    def OnUpdatePreErrBt(self, event):
        if len(self._errorLines) == 0 or self._text.GetCurrentLine() <= self._errorLines[0]:
            self._preErrBt.Disable()
        else:
            self._preErrBt.Enable()
        
    def OnUpdateNextErrBt(self, event):
        if len(self._errorLines) == 0 or self._text.GetCurrentLine() >= self._errorLines[len(self._errorLines) - 1]:
            self._nextErrBt.Disable()
        else:
            self._nextErrBt.Enable()
            
    def OnUpdateCopyButton(self, event):
        if len(self._text.GetText()) == 0:
            self._copybt.Disable()
        else:
            self._copybt.Enable()
            
    def GetCtrl(self):
        return self._text
    
    def GetDockPosition(self):
        return ISingleView.DOCK_BOTTOM
    
    def OnAreaSelect(self, event):
        if self._sel.GetValue() == "All":
            wx.GetApp().SetLoggerArea("")
        else:
            wx.GetApp().SetLoggerArea(self._sel.GetValue())
        
    def OnLogWrite(self, event):
        type = event.message.split()[1]
        if type == "ERROR":
            self._errorLines.append(self._text.GetLineCount() - 1)
        self._text.DocumentEnd()
        self._text.SetReadOnly(False)
        self._text.AppendText(event.message)
        self._text.SetReadOnly(True)
        self._text.GotoLine(self._text.GetLineCount())
        
    def OnCopyLog(self, event):
        textobj = wx.TextDataObject()
        textobj.SetText(self._text.GetText())        
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(textobj)
        wx.TheClipboard.Close()
        
    def OnClearLog(self, event):
        self._text.SetReadOnly(False)
        self._text.ClearAll()
        self._text.SetReadOnly(True)
        del self._errorLines[:]
        
    def OnPrevError(self, event):
        if len(self._errorLines) == 0:
            wx.MessageBox("No error found!")
            return
        
        lineno = self._text.GetCurrentLine()
        prevno = None
        for l in self._errorLines:
            if l < lineno and l > prevno:
                prevno = l
                
        if prevno != None:
            self._text.GotoLine(prevno)
        else:
             wx.MessageBox("No error found!")
        self._text.SetFocus()
        
    def OnNextError(self, event):
        if len(self._errorLines) == 0:
            wx.MessageBox("No error found!")
            return
        
        lineno = self._text.GetCurrentLine()
        nextno = None
        for l in self._errorLines:
            if l > lineno:
                nextno = l
                break
                
        if nextno != None:
            self._text.GotoLine(nextno)
        else:
            wx.MessageBox("No error found!")
        self._text.SetFocus()            