import wx.stc
import os
import wx
from core.editor import ZOOM_ID, ZOOM_NORMAL_ID, ZOOM_IN_ID, ZOOM_OUT_ID

class HexCtrl(wx.stc.StyledTextCtrl):
    PRINTABLE_CHAR = ['/', '\\', '#', '~', '!', '@', '$', '%', '^', '&', '*', '(', \
                      ')', '{', '}', '[', ']', '<', '>', ':', ';', '\"', '\'', '?',\
                      '-', '+', '=', '_']
    PRINTABLE_CHAR_INT = [ord(item) for item in PRINTABLE_CHAR]
        
    def __init__(self, parent, id=-1, size=wx.DefaultSize, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.stc.StyledTextCtrl.__init__(self, parent, id, size=size, style=style)
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = 'Courier New')
        self.SetFont(font)
        self.SetMarginWidth(1, 0)
        #self.SetCaretLineBack('#FF8000') 
        self.SetCaretLineVisible(True)
        
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "face:Courier New,fore:#000000,face:Courier New,size:10")
        self._base = 0
        self.SetReadOnly(True)

        wx.EVT_MENU(self, wx.ID_COPY, self.ProcessEvent)
        wx.EVT_MENU(self, wx.ID_SELECTALL, self.ProcessEvent)
        wx.EVT_MENU(self, ZOOM_NORMAL_ID, self.ProcessEvent)
        wx.EVT_MENU(self, ZOOM_IN_ID, self.ProcessEvent)
        wx.EVT_MENU(self, ZOOM_OUT_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, wx.ID_COPY, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, wx.ID_SELECTALL, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, ZOOM_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, ZOOM_NORMAL_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, ZOOM_IN_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, ZOOM_OUT_ID, self.ProcessUpdateUIEvent)
    
    def ProcessEvent(self, event):
        id = event.GetId()

        if id == wx.ID_SELECTALL:
            self.SetSelection(0, -1)
            return True        
        elif id == wx.ID_COPY:
            self.Copy()
            return True
        elif id == ZOOM_NORMAL_ID:
            self.SetZoom(0)
            return True
        elif id == ZOOM_IN_ID:
            self.CmdKeyExecute(wx.stc.STC_CMD_ZOOMIN)
            return True
        elif id == ZOOM_OUT_ID:
            self.CmdKeyExecute(wx.stc.STC_CMD_ZOOMOUT)
            return True        
                
        return False
    
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        
        if id == wx.ID_SELECTALL:
            hasText = self.GetTextLength() > 0
            event.Enable(hasText)
            return True        
        elif id == wx.ID_COPY:
            hasSelection = self.GetSelectionStart() != self.GetSelectionEnd()
            event.Enable(hasSelection)
            return True
        elif id == ZOOM_ID:
            event.Enable(True)
            return True
        elif id == ZOOM_NORMAL_ID:
            event.Enable(self.GetZoom() != 0)
            return True
        elif id == ZOOM_IN_ID:
            event.Enable(self.GetZoom() < 20)
            return True
        elif id == ZOOM_OUT_ID:
            event.Enable(self.GetZoom() > -10)
            return True        
        return False
    
    def GetHeight(self):
        return self.GetLineCount() * 16 + 20
   
    def ClearAll(self):
        self.SetReadOnly(False)
        wx.stc.StyledTextCtrl.ClearAll(self)
        self.SetReadOnly(True)
        
    def SetRawData(self, base, data):
        lines = self._listToText(base, data)
        self.Freeze()
        self.SetReadOnly(False)
        self.AddText('\n'.join(lines))
        self.SetReadOnly(True)
        self.Thaw()
                
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
                   (item in self.PRINTABLE_CHAR_INT):
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