import wx
import os
import re
import array
import wx.stc

class MessageWindow(wx.stc.StyledTextCtrl):
    STYLE_UNDERLINE = 20
    __FileName = r"((?:[A-Z,a-z]:)?[\\/\w.-]+)"
    __LineNumber = r"(\d+)"
    __OutputPatternList = [
        __FileName + r":" + __LineNumber + r":",
        __FileName + r"\(" + __LineNumber,
        __FileName + r"," + __LineNumber,
        __FileName + r"\s*VfrCompile\(" + __LineNumber + r"\)",
        __FileName    
        ]    
    __ReOutputPattern = re.compile("|".join(__OutputPatternList))
         
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, name='NoName'): 
        wx.stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style, name)
        
        # clear all margin
        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)
        
        # set font, inherit class can overide GetBackgroundColor() and GetForegroundColor()
        self._faces = {
            'name':self.GetFontName(),
            'size':self.GetFontSize(),
            'backcol':self.GetBackgroundColor(),
            'forecol':self.GetForegroundColor(),
        }        
        
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "face:%(name)s,size:%(size)d,back:%(backcol)s,fore:%(forecol)s" % self._faces)
        self.StyleClearAll()
        self.SetScrollWidth(1)
        
        #disable popup
        self.UsePopUp(0)
        
        self.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.SetScrollWidth(5000)
        
        self.StyleSetSpec(self.STYLE_UNDERLINE,  "face:%(name)s,size:%(size)d,underline" % self._faces)
        self.StyleSetHotSpot(self.STYLE_UNDERLINE, True)
        self.SetHotspotActiveUnderline(True)
        self.SetHotspotSingleLine(True)   
        self.Bind(wx.stc.EVT_STC_HOTSPOT_CLICK, self.OnHotSpotClick)
        self._curdir = None
        
    def GetFontName(self):
        """This interface could be overided by child class"""
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        
        return font    
    
    def GetBackgroundColor(self):
        """This interface could be overided by child class"""
        return '#FFFFFF'
    
    def GetForegroundColor(self):
        """This interface could be overided by child class"""
        return '#000000'
    
    def GetFontSize(self):
        """This interface could be overided by child class"""
        return 10
    
    def SetCurrentDirectory(self, dir):
        self._curdir = dir
        
    def OnHotSpotClick(self, event):  
        event.Skip()
        pos = event.GetPosition()

        start = pos
        end   = pos
        while (self.GetStyleAt(start) == self.STYLE_UNDERLINE):
            start -= 1
        while (self.GetStyleAt(end) == self.STYLE_UNDERLINE):
            end += 1        
        text = self.GetTextRange(start, end)
        (hasError, list) = self.ParseText(text)
        if not hasError:
            return
        
        record = None
        for item in list:
            if len(item[2]) != 0:
                record = item
                
        if record == None:
            return
        
        fName = record[2]
        line  = record[3]
        if not os.path.exists(fName):
            if self._curdir == None:
                return
            fName = os.path.join(self._curdir, fName)
            if not os.path.exists(fName):
                return
            
        doc = wx.GetApp().GetDocumentManager().CreateDocument(fName, 
                                                              wx.lib.docview.DOC_SILENT)
        if doc == None: return
        view = doc.GetFirstView()
        if view != None:
            if line > -1:
                line = line - 1
                view.Activate()
                view.GetCtrl().EnsureVisible(line)
                view.GetCtrl().GotoLine(line)
                view.GetCtrl().SetFocus()
                start = view.GetCtrl().GetLineIndentPosition(line)
                end = view.GetCtrl().GetLineEndPosition(line)
                view.GetCtrl().SetSelection(start, end)
                
    def __YieldFileName(self, Text):
        for Match in self.__ReOutputPattern.finditer(Text):
            Groups = Match.groups()
            for Index in range(0, len(Groups), 2):
                if Groups[Index]:
                    FileName = Groups[Index]
                    if Index < (len(Groups) - 1) and Groups[Index + 1].isalnum():
                        LineNum = Groups[Index + 1]
                    else:
                        LineNum = -1

                    if os.path.exists(FileName) and not os.path.isdir(FileName):
                        #if LineNum != None:
                        yield FileName, int(LineNum), Match.start(), Match.end()
                    elif self._curdir != None: 
                        fFileName = os.path.join(self._curdir, FileName)
                        if os.path.exists(fFileName) and not os.path.isdir(fFileName):
                            yield FileName, int(LineNum), Match.start(), Match.end()
                        #else:
                        #    yield FileName, -1, Match.start(), Match.end()
    
    def SetCurrentDir(self, path):
        self._curdir = path
        
    def ParseText(self, Text):
        ReturnTuple = []
        CurrentPos = 0
        TextLen = len(Text)
        isContained = False
        for FileName, LineNum, Start, End in self.__YieldFileName(Text):
            if CurrentPos < Start:
                ReturnTuple.append((CurrentPos, Start, "", 0))
            ReturnTuple.append((Start, End, FileName, LineNum))
            isContained = True
            CurrentPos = End
    
        if CurrentPos < TextLen:
            ReturnTuple.append((CurrentPos, TextLen, "", 0))
            
        return isContained, ReturnTuple
    
    def AddText(self, text):
        ro = self.GetReadOnly()
        self.SetReadOnly(False)
        (hasError, list) = self.ParseText(text)
        if not hasError:
            wx.stc.StyledTextCtrl.AddText(self, text)
        else:
            for r in list:
                if len(r[2]) == 0:
                    wx.stc.StyledTextCtrl.AddText(self, text[r[0]:r[1]])
                elif len(r[2]) > 4 and (r[2][-4:].lower() == '.exe' or r[2][-4:].lower() == '.efi'):
                    wx.stc.StyledTextCtrl.AddText(self, text[r[0]:r[1]])
                else:
                    self.AddUnderLine(text[r[0]:r[1]])
        self.SetReadOnly(ro)
              
    def AddUnderLine(self, text):
        style_str = chr(self.STYLE_UNDERLINE)
        styledText = array.array('c')
        for c in text:
            styledText.append(chr(ord(c)))
            styledText.append(style_str)
        self.AddStyledText(styledText.tostring())  
            
    def AddMessage(self, text):
        if not isinstance(text, unicode):
            try:
                text = unicode(text, locale.getdefaultlocale()[1])
            except:
                pass        
        self.AddText(text)
        self.DocumentEnd()
        
    def SetSelectedText(self, text):
        ro = self.GetReadOnly()
        self.SetReadOnly(False)
        self.SetTargetStart(self.GetSelectionStart())
        self.SetTargetEnd(self.GetSelectionEnd())
        self.ReplaceTarget(text)
        self.SetReadOnly(ro)            
               
    def ProcessEvent(self, event):
        id = event.GetId()
        if id == wx.ID_COPY:
            self.Copy()
            return True
        if id == wx.ID_PASTE:
            self.Paste()
            return True
        if id == wx.ID_CUT:
            self.Cut()
            return True
        if id == wx.ID_CLEAR:
            self.SetText('')
            return True
        if id == wx.ID_REDO:
            self.Redo()
            return True
        if id == wx.ID_UNDO:
            self.Undo()
            return True
        if id == wx.ID_SELECTALL:
            self.SetSelection(0, -1)
            return True
        return False   
    
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(self.CanUndo())
            return True
        elif id == wx.ID_REDO:
            event.Enable(self.CanRedo())
            return True
        elif (id == wx.ID_CUT
        or id == wx.ID_COPY
        or id == wx.ID_CLEAR):
            hasSelection = self.GetSelectionStart() != self.GetSelectionEnd()
            event.Enable(hasSelection)
            return True  
        elif id == wx.ID_PASTE:
            event.Enable(self.CanPaste())
            return True
        elif id == wx.ID_SELECTALL:
            hasText = self.GetTextLength() > 0
            event.Enable(hasText)
            return True                      
        return False                  