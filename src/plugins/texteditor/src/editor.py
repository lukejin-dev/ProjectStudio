import sys
import wx
import wx.stc

MARKGIN_INDEX_LINENUMBERS = 0

class TextEditor(wx.stc.StyledTextCtrl):
    def __init__(self, parent, viewowner):
        wx.stc.StyledTextCtrl.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER, "TextEditor")
        self._owner = viewowner
        
        fontface = wx.SystemSettings_GetFont(wx.SYS_ANSI_FIXED_FONT).GetFaceName()
        self.StyleSetFontAttr(wx.stc.STC_STYLE_DEFAULT, 
                              self.GetConfig().Get("TextFontSize", 10), 
                              self.GetConfig().Get("TextFontFace", fontface),
                              False, False, False)
        self.SetMarginType(MARKGIN_INDEX_LINENUMBERS, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(MARKGIN_INDEX_LINENUMBERS, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)
        self.SetMarginWidth(3, 0)
        
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        
    def EstimatedLineNumberMarginWidth(self):
        base = "000"
        lineNum = self.GetLineCount() / 100
        while lineNum >= 10:
            lineNum = lineNum / 10
            base = base + "0"

        return self.TextWidth(wx.stc.STC_STYLE_LINENUMBER, base) + 4

        
    def GetConfig(self):
        return self._owner.GetConfig()
    
    def OnKeyDown(self, event):
        event.Skip()

    def SetViewLineNumbers(self, show):
        if show:
            self.SetMarginWidth(MARKGIN_INDEX_LINENUMBERS, self.EstimatedLineNumberMarginWidth())
        else:
            self.SetMarginWidth(MARKGIN_INDEX_LINENUMBERS, 0)        