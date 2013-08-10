import wx
import wx.stc

class TextEditor(wx.stc.StyledTextCtrl):
    def __init__(self, parent, viewowner):
        wx.stc.StyledTextCtrl.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER, "TextEditor")
        self._owner = viewowner
        
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        
    def OnKeyDown(self, event):
        event.Skip()
