"""Dos plugin is provide dos prompt service, It is sample service plugin
"""

import core.plugin
import wx, re, array
import wx.lib.pydocview as pydocview
import core.service
import ui.MessageWindow
import os
import locale
        
# currently, shell plug-in is only suit for window platform        
if wx.Platform == '__WXMSW__':
    #
    # plug-in meta information, it describe plug-in interface and will be recognized by EDES2008's core
    #
    _plugin_module_info_ = [{"name":"DosPlugin",
                             "author":"ken",
                             "version":"1.0",
                             "description":"Provide dos command line windows",
                             "class":"DosPlugin"}]

class DosPlugin(core.plugin.IServicePlugin):
    """
    Service plugin interface implementation.
    """
    def IGetClass(self):
        return DosService
        
class DosService(core.service.PISService):
    """
    Dos service class provide shell service information, such service view class, view's position.
    """
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Dos'
    
    def GetViewClass(self):
        return DosView
    
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        pass
    
    def GetIcon(self):
        return getDosIcon()
    
class DosView(core.service.PISServiceView):
    """
    Shell view which is a tab window in EDES2008's bottom.
    """
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._dos = DosWindow(self, -1)
        sizer.Add(self._dos, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Bind(wx.EVT_CLOSE, self.OnViewClose)
        
    def OnViewClose(self, event):
        self._dos.Close()
        
class DosWindow(ui.MessageWindow.MessageWindow):
    ID_CLEAR             = wx.NewId()
    ID_BROWSER_DIR       = wx.NewId()
    ID_TERMINATE_CHILD   = wx.NewId()
        
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, name='Dos'): 
        ui.MessageWindow.MessageWindow.__init__(self, parent, id, pos, size, style, name)
        self.SetCaretLineBack('#FF8000') 
        self.SetCaretLineVisible(True)
        
        self._process =None
        self._commandLen          = 0
        self._writePosition       = 0
        self._editPoint           = 0
        self._commandArray        = []
        self._commandArrayPos     = -1
        self._cachedirs           = []
        self._tabcount            = 0
        self._repstart            = 0
        self._searchdir           = None
        self._pid                 = None
        self._curdir              = None
        self._curchildproc        = None
        self._interm              = False
        self._isquit              = False
        self._inputThread         = None
        self._errorThread         = None
        self.MAX_PROMPT_COMMANDS  = 25    
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)  
        wx.EVT_KEY_UP(self, self.OnKeyUp) 
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        wx.stc.EVT_STC_DOUBLECLICK(self, self.GetId(), self.OnDoubleClick)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        config = wx.ConfigBase_Get()
        self.RunDocCommand('cmd.exe', config.Read('LastDirectory', ''))
        
    def GetLogger(self):
        return self.GetParent()._logger
    
    def ProcessEvent(self, event):      
        id = event.GetId()
        if id == 165:
            return True
        return ui.MessageWindow.MessageWindow.ProcessEvent(self, event)
    
    def GetBackgroundColor(self):
        return '#000000'
    
    def GetForegroundColor(self):
        return '#FFFFFF'
    
    def GetConfig(self):
        plugin = core.plugin.PluginManager().GetPlugin('DosPlugin')
        return plugin.GetConfig()
     
    def RunDocCommand(self, command, dir):
        oldPath = None
        if dir != None and len(dir) != 0 and os.path.exists(dir):
            oldPath = os.getcwd()
            os.chdir(dir)
        
        try:
            self._process = ShellProcess(self)
            self._process.SetParent(self)
            self._process.Redirect()
            self._pid = wx.Execute(command, wx.EXEC_ASYNC, self._process)
            self._input = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self._process = None
            dlg = wx.MessageDialog(self, "There are some problems when running the program!\nPlease run it in shell." ,
                    "Stop running", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal() 
        if oldPath != None:
            os.chdir(oldPath)
        self._inputThread = PipeMonitorThread(self._input, self.InputMonitorCallback)
        self._errorThread = PipeMonitorThread(self._error, self.ErrorMonitorCallback)
        self._inputThread.start()
        self._errorThread.start()
        
    def OnIdle(self, event):
        if self._process != None and not self._interm:
            if self._error:
                if self._error.CanRead():
                    text = self._error.read()
                    self.AppendText(text)
                    self._writePosition = self.GetLength()
                    self._editPoint     = self.GetLength()
            if self._input:
                if self._input.CanRead():
                    text = self._input.read()
                    if self._commandLen > 0:
                        if len(text) >= self._commandLen:
                            text = text[self._commandLen:]
                            self._commandLen = 0
                        else:
                            text = ''
                            self._commandLen -= len(text)

                    self.AppendText(text)
                    self._writePosition = self.GetLength()
                    self._editPoint     = self.GetLength()
                    
                    (t, p) = self.GetCurLine()
                    mo = re.match(r'([A-Z,a-z]?:[\\\w-]+)>', t)
                    if mo != None:
                        if os.path.exists(mo.groups()[0]) and os.path.isdir(mo.groups()[0]):
                            self.OnChangeDir(mo.groups()[0])
                            self._tabcount = 0
                            self._curchildproc = None
                   
    def InputMonitorCallback(self, message):
        text = message
        if self._commandLen > 0:
            if len(text) >= self._commandLen:
                text = text[self._commandLen:]
                self._commandLen = 0
            else:
                text = ''
                self._commandLen -= len(text)

        self.AppendText(text)
        self._writePosition = self.GetLength()
        self._editPoint     = self.GetLength()
                    
        (t, p) = self.GetCurLine()
        mo = re.match(r'([A-Z,a-z]?:[\\\w-]+)>', t)
        if mo != None:
            if os.path.exists(mo.groups()[0]) and os.path.isdir(mo.groups()[0]):
                self.OnChangeDir(mo.groups()[0])
                self._tabcount = 0
                self._curchildproc = None
                 
    def ErrorMonitorCallback(self, message):
        self.AppendText(message)
        self._writePosition = self.GetLength()
        self._editPoint     = self.GetLength()
        
    def AppendText(self, text):
        self.GotoPos(self.GetLength())
        if not isinstance(text, unicode):
            try:
                text = unicode(text, locale.getdefaultlocale()[1])
            except:
                pass
        self.AddMessage(text)
        self.DocumentEnd()
        self.EmptyUndoBuffer()   
        
    def OnDisplayDirInBrower(self, event):
        self.DisplayDirInBrowser(self._curdir)
            
    def DisplayDirInBrowser(self, dir):
        if not os.path.exists(dir):
            return
        pluginmgr = wx.GetApp().GetPluginMgr()
        plugin    = pluginmgr.GetPlugin('FolderBrowserPlugin')
        if plugin != None:
            folderService = plugin.GetServiceInstance()
            folderService.SetPath(dir)
            self.GetParent().Activate()
        
    def OnChangeDir(self, dir):
        if not os.path.exists(dir):
            return
         
        if self._curdir != dir:
            self._curdir = dir

        config = wx.ConfigBase_Get()
        config.Write('LastDirectory', dir)
                
    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        pos = self.GetCurrentPos()

        # if user input ANSIC key, caret should goto last pos firstly
        if keycode < 127 and (self.GetLineCount() - 1) != self.GetCurrentLine():
            self.GotoPos(self.GetLength())

        if self._pid > -1:
            if (pos >= self._editPoint) and (keycode == wx.WXK_RETURN):
                text = self.GetTextRange(self._writePosition, self.GetLength())
                l = len(self._commandArray)
                if (l < self.MAX_PROMPT_COMMANDS):
                    self._commandArray.insert(0, text)
                    self._commandArrayPos = -1
                else:
                    self._commandArray.pop()
                    self._commandArray.insert(0, text)
                    self._commandArrayPos = -1
    
                if isinstance(text, unicode):
                    text = text.encode(locale.getdefaultlocale()[1])
                self._commandLen = len(text) + 1
                self.firstread = True
                self._curchildproc = text
                self.GetParent().SetTitle('Last command line : ' + text)
                if text == '.':
                    self.DisplayDirInBrowser(self._curdir)
                    self._output.write(' \n')
                elif text.lower().startswith('pis'):
                    fname = text[text.find(' ') + 1:]
                    if os.path.exists(os.path.join(self._curdir, fname)):
                        fname = os.path.join(self._curdir, fname)
                    if os.path.exists(fname):
                        wx.GetApp().GetDocumentManager().CreateDocument(fname, 
                                                                        wx.lib.docview.DOC_SILENT)
                    temptxt = ''
                    for count in range(len(text)):
                        temptxt += ' '
                    self._output.write(temptxt + '\n')
                else:
                    self._output.write(text + '\n')
                
                self.GotoPos(self.GetLength())
    
            if keycode == wx.WXK_UP:
                l = len(self._commandArray)
                if (len(self._commandArray) > 0):
                    if (self._commandArrayPos + 1) < l:
                        self.GotoPos(self._editPoint)
                        self.SetTargetStart(self._editPoint)
                        self.SetTargetEnd(self.GetLength())
                        self._commandArrayPos = self._commandArrayPos + 1
                        self.ReplaceTarget(self._commandArray[self._commandArrayPos])
                self.GotoPos(self.GetLength())
            elif keycode == wx.WXK_DOWN:
                if len(self._commandArray) > 0:
                    self.GotoPos(self._editPoint)
                    self.SetTargetStart(self._editPoint)
                    self.SetTargetEnd(self.GetLength())
                    if (self._commandArrayPos - 1) > -1:
                        self._commandArrayPos = self._commandArrayPos - 1
                        self.ReplaceTarget(self._commandArray[self._commandArrayPos])
                    else:
                        if (self._commandArrayPos - 1) > -2:
                            self._commandArrayPos = self._commandArrayPos - 1
                            self.ReplaceTarget("")
                self.GotoPos(self.GetLength())
            elif keycode == wx.WXK_TAB:
                # ignore tab key, keydown event will handle it.
                return
        self._tabcount = 0
        if ((pos > self._editPoint) and (not keycode == wx.WXK_UP)) or ((not keycode == wx.WXK_BACK) and (not keycode == wx.WXK_LEFT) and (not keycode == wx.WXK_UP) and (not keycode == wx.WXK_DOWN)):
            if (pos < self._editPoint):
                if (not keycode == wx.WXK_RIGHT):
                    event.Skip()
            else:
                event.Skip()
                    
    def OnKeyUp(self, event):    
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_HOME:
            if (self.GetCurrentPos() < self._editPoint):
                self.GotoPos(self._editPoint)
            return
        elif keycode == wx.WXK_PRIOR:
            if (self.GetCurrentPos() < self._editPoint):
                self.GotoPos(self._editPoint)
            return
        elif keycode == wx.WXK_TAB:
            if self._curdir == None: return
            if self._tabcount == 0:
                start     = self.GetCurrentPos()
                end       = start
                visit     = start
                while (self.GetCharAt(start - 1) not in [ord(' '), ord('>')]):
                    start -= 1
                searchstring = self.GetTextRange(start, end).strip()
                key          = None
                if re.match('^\.\\\\', searchstring) or re.match('^\.\.\\\\', searchstring):
                    path = searchstring[:searchstring.rfind('\\')]
                    key  = searchstring[searchstring.rfind('\\') + 1:]
                    self._searchdir = os.path.join(self._curdir, path)
                elif re.match('^\w:\\\\', searchstring):
                    path = searchstring[:searchstring.rfind('\\') + 1]
                    key  = searchstring[searchstring.rfind('\\') + 1:]                    
                    self._searchdir = path
                elif re.match('^\w:', searchstring):
                    self._searchdir = searchstring + '\\'
                elif re.match('^\w:\\\\', searchstring):
                    path = searchstring[:searchstring.rfind('\\')]
                    key  = searchstring[searchstring.rfind('\\') + 1:]
                    self._searchdir = path
                elif re.match('^\\\\', searchstring):
                    path = searchstring[:searchstring.rfind('\\')]
                    key  = searchstring[searchstring.rfind('\\') + 1:]                      
                    self._searchdir = os.path.join(self._curdir[:self._curdir.find(':') + 1], path)
                elif re.match('^[\w\\\\]+\\\\', searchstring):
                    path = searchstring[:searchstring.rfind('\\')]
                    key  = searchstring[searchstring.rfind('\\') + 1:]                       
                    self._searchdir = os.path.join(self._curdir, path)
                elif re.match('^[\w]+', searchstring):
                    key  = searchstring
                    self._searchdir = self._curdir
                else:
                    self._searchdir = self._curdir
                    key  = searchstring

                if not (os.path.exists(self._searchdir) and os.path.isdir(self._searchdir)): 
                    return
                self._repstart  = start
                del self._cachedirs[:]
                for dir in os.listdir(self._searchdir):
                    if key != None and not dir.lower().startswith(key.lower()):
                        continue
                    if self._searchdir == self._curdir:
                        self._cachedirs.append(dir)
                    elif re.match('^[\w\\\\]+\\\\', searchstring):
                        path = searchstring[:searchstring.rfind('\\')]
                        self._cachedirs.append(os.path.join(path, dir))
                    else:
                        if not self._searchdir.endswith('\\'):
                            self._searchdir += '\\'
                        self._cachedirs.append(os.path.join(self._searchdir, dir))
                
                self._cachedirs.sort()
            if len(self._cachedirs) == 0: return
            if self._tabcount >= len(self._cachedirs):
                self._tabcount = 0
            self.GotoPos(self._repstart)
            self.DelLineRight()
            self.InsertText(self._repstart, self._cachedirs[self._tabcount])
            self.GotoPos(self.GetLength())
            self._tabcount += 1
            event.StopPropagation()
        
    def RunCheck(self, event):
        if (self.GetCurrentPos() < self._editPoint) or (self._pid == -1):
            self.SetReadOnly(1)
        else:
            self.SetReadOnly(0)    
            
    def OnDoubleClick(self, event):
        text, pos =  self.GetCurLine()
        if isinstance(text, unicode):
            text = text.encode(locale.getdefaultlocale()[1])
            
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.ID_CLEAR, 'Clear', 'Clear DOS window')
        menu.Append(self.ID_BROWSER_DIR, 'Open dir in browser', 'Open dir in browser')
        wx.EVT_MENU(self, self.ID_CLEAR, self.OnClearDos)
        wx.EVT_MENU(self, self.ID_BROWSER_DIR, self.OnDisplayDirInBrower)
        if self._curchildproc != None:
            menu.Append(self.ID_TERMINATE_CHILD, 'Terminate %s' % self._curchildproc.split(' ')[0], 'Terminate process')
            wx.EVT_MENU(self, self.ID_TERMINATE_CHILD, self.OnTerminateChildProcess)
        return menu
    
    def OnTerminateChildProcess(self, event):
        self._interm = True
        self._inputThread.Terminate()
        self._errorThread.Terminate()
        self.AddText('\nTry to terminate process %s' % self._curchildproc)
        status = wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)
        self._curchildproc = None
        self._interm = False
        
    def ShellProcessNotifyTerminate(self, id, status):
        self._inputThread.Terminate()
        self._errorThread.Terminate()            
        
        if not self._isquit:
            self.AppendText("\nShell process %s has been terminated with status %d\n" % (id, status))
            self.RunDocCommand('cmd.exe /k \"cd %s\"' % self._curdir, self._curdir)
        
    def OnClearDos(self, event):
        self.ClearAll()
        self._output.write('\n')
        
    def OnRightUp(self, event):
        self.PopupMenu(self.CreatePopupMenu(), event.GetPosition())

    def OnClose(self, event):
        self._isquit = True
        self._inputThread.Terminate()
        self._errorThread.Terminate()        
        wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)
        
import threading
class PipeMonitorThread(threading.Thread):
    def __init__(self, pipe, callback):
        threading.Thread.__init__(self)
        self._pipe     = pipe        
        self._isCancel = False
        self._callback = callback
        
    def run(self):
        while not self._isCancel:
            self._pipe.Peek()
            if self._pipe.LastRead() == 0:
                break
            message = self._pipe.read()
            #print message
            wx.GetApp().ForegroundProcess(self._callback, (message,))
            
    def Terminate(self):
        self._pipe.flush()
        self._isCancel = True
        
class ShellProcess(wx.Process):
    def OnTerminate(self, id, status):
        # maybe parent is destroy, but do not care about that.
        try:
            self._parent.ShellProcessNotifyTerminate(id, status)
        except:
            pass
        
    def SetParent(self, parent):
        self._parent = parent
            
#----------------------------------------------------------------------
# This file was generated by N:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

dos = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAf5J"
    "REFUWIXNlr9LHUEQxz/r3WljIYZE0ZfaQhHyF6QMIf9FxE7FwsDTJp080EqsFAUhkHRpYmGV"
    "P+FBEEQkRBEttDD65D3fj7u12N376UGKyO40ezs7ezPzne/Mnei0H7ApfVa9A34URQB8rB1I"
    "gPrfl8/q8M3QNQC71XcC3EAgBKB+8wKAyebPZ3VYl28BMH5dQEBxgKgHgOd5AFRXP/1XR7WV"
    "tYwf49c6AtYDSEogdQn8YkwTg/pBqkVktyBETmEejCX4viqtcK0EcRuKsAtAMOAXjBZXfwDQ"
    "arYAaNzeqfWuofVNAA6+LQMgdeZCxpDECMi28uNOG0pdCxlpBIIiArWlD5l9scJKumHWIgVA"
    "/F7R6ml/7nFARRb0BwWj6vp+Zt95aAPQ1LW/b9wDCRfa+vz7XjW+EyMbddTiDAeSUawiCwKv"
    "YPR5/j2QanMteQ7kudGLkhsxB0LTBe5wwCCgIjP9mpauzkRInZvI5Vo2AVMQJRxwDwHTBYoD"
    "vq8i/br1JTYSpq/NhEsOlD6PQOHbAJ5BNnRtEppajI8MA7B/eFUwKpt8ZYk/dcGoKqOvAIc4"
    "YD0AcX528s/GMxu/JMDFxSWQ/iFRS2VsDICdhel8tUrFPgJnf44zitnNQ53leaKU+fZ6eiiX"
    "kRVgvPIagO25qcyxfQROfx9ZDcA6Ao8bZtvxC9J5QAAAAABJRU5ErkJggg==")
getDosData = dos.GetData
getDosImage = dos.GetImage
getDosBitmap = dos.GetBitmap
getDosIcon = dos.GetIcon
