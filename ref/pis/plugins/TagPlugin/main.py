
"""
 _plugin_info_ must be defined in plugin code, it is provide base information
 for plugin.
"""
import core.plugin
import wx
import os
import threading
import wx.lib.docview
    
_plugin_module_info_ = [{"name":"TagPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide tag function for source codes",
                         "class":"TagPlugin"}]
                         
class TagPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return TagService
        
    def Install(self):
        path = wx.GetApp().GetAppLocation()
        path = os.path.join(path, 'ctags.exe')
        
        if not os.path.exists(path):
            wx.MessageBox("Fail to find ctag.exe under folder %s" % wx.GetApp().GetAppLocation())
            return core.plugin.Plugin.PLUGIN_INSTALL_FAILURE        
        return core.plugin.IServicePlugin.Install(self)
        
class TagService(core.service.PISService, wx.EvtHandler):
    def __init__(self):
        core.service.PISService.__init__(self)
        wx.EvtHandler.__init__(self)
        self._creationProcess = None
        self._pid           = None
        self._progress      = None
        self._timer         = None
        self._tagPath       = None
        
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Symbols'
    
    def GetIcon(self):
        return getsymbolIcon()
        
    def GetTagPath(self):
        return self._tagPath
        
    def GetViewClass(self):
        return TagView
    
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        pass
    
    def GetCTagsPath(self):
        path = wx.GetApp().GetAppLocation()
        path = os.path.join(path, 'ctags.exe')
        return path
        
    def OpenTag(self, filename):
        self._tagPath = filename
        if not os.path.exists(filename):
            self.GetView().Enable(False)
        else:
            self.GetView().Enable()
            
    def CloseTag(self):
        view = self.GetView()
        if view != None:
            view.Enable(False)
            
    def BuildTags(self, tagPath, files):
        if self._creationProcess != None:
            wx.MessageBox("Another creation process is running! Please wait for it finished!")
            return
        path = self.GetCTagsPath()
        
        cmd = path
        cmd += ' -o ' + tagPath + ' '
        cmd += ' --languages=Asm,C++,C '
        cmd += ' --c-kinds=+lpx '
        cmd += ' --recurse '
        cmd += ' --excmd=number '
        #cmd += ' -a '
        cmd += ' -R '
        cmd += ' -V '
        cmd += ' --exclude=.svn '
        cmd += ' --exclude=PackageDocument '
        cmd += ' --exclude=Build '
        cmd += ' '.join(files)

        try:
            self._creationProcess = TagCreationProcess(self)
            self._creationProcess.SetParent(self)            
            self._creationProcess.Redirect()
            self._pid    = wx.Execute(cmd, wx.EXEC_ASYNC, self._creationProcess)
            self._input  = self._creationProcess.GetInputStream()
            self._output = self._creationProcess.GetOutputStream()
            self._error  = self._creationProcess.GetErrorStream()
            self._progress = wx.ProgressDialog("Building Tags ....",
                                                   "Building Tags ....",
                                                   style=wx.PD_ELAPSED_TIME|wx.PD_APP_MODAL)
            self._progress.SetSize((500, 130))
            self._progress.CenterOnParent()
            
            wx.EVT_IDLE(wx.GetApp(), self.OnIdle)                         
        except:
            wx.MessageBox("Fail to launch the ctags.exe process to create tags!")
            return
        
    def OnNotifyCreationProcessEnd(self, id, status):
        self._progress.Destroy()
        self._progress = None
        del self._creationProcess
        self._creationProcess = None
        self.GetView().Enable()
        
    def OnIdle(self, event):
        if self._progress == None: return
        if self._input.CanRead():
            text = self._input.read().split('\n')
            for item in text:
                self._progress.Pulse(item)
            
    def OnTimer(self, event):
        if self._progress != None:
            wx.Yield()
            self._progress.Pulse()
            
        
    #def GetIcon(self):
    #    return getDosIcon()

class TagView(core.service.PISServiceView):
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._keyword = wx.ComboBox(self, -1)
        sizer.Add(self._keyword, 0 , wx.EXPAND)
        self._result  = wx.ListBox(self, -1)
        sizer.Add(self._result, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.Layout()
        
        #self._keyword.Bind(wx.EVT_TEXT, self.OnEnter)
        self._lines = None
        self._tagLoadingThread = None
        self._last_symbol = ''
        self._inSearching = False
        self.Enable(False)
        wx.EVT_IDLE(self, self.OnIdle)
        wx.EVT_LISTBOX_DCLICK(self, self._result.GetId(), self.OnDoubleClick)
        
    def Enable(self, isEnable=True):
        if isEnable:
            self.LoadTag()
            #    self._keyword.Enable()
            #    self._result.Enable()
            #    return
            return
        
        self._keyword.SetValue('')
        self._result.Clear()
        if self._lines != None and len(self._lines) != 0:
            del self._lines[:]
        self._keyword.Disable()
        self._result.Disable()
        return
            
    def LoadTag(self):
        path = self.GetService().GetTagPath()
        if not os.path.exists(path):
            wx.MessageBox('Tag file does not exists!')
            return False
        
        self._tagLoadingThread = TagLoadingThread(path, self.OnFinishLoadTag)
        self._tagLoadingThread.start()
        self.SetTitle("Loading Tag file %s ..." % path)
        return True
          
    def OnFinishLoadTag(self, lines):
        self.SetTitle('')
        if self._lines != None:
            del self._lines[:]
        self._lines = lines
        self._tagLoadingThread = None
        self._keyword.Enable()
        self._result.Enable()
          
    def OnIdle(self, event):
        if self._inSearching: return
        if not self._keyword.IsEnabled():
            return
            
        curKey = self._keyword.GetValue()
        curKeyLen = len(curKey)
        if curKeyLen == 0:
            self._result.Clear()
            return
        if curKey == self._last_symbol:
            return
        self._last_symbol = curKey
        length = len(self._lines)
        if length == 0:
            return
        
        self._inSearching = True
        self._result.Clear()
        start = 0
        end   = length - 1
        
        mid   = 0
        while (start < end):
            mid = (end - start)/2 + start
            line = self._lines[mid]
            key =  line.split('\t')[0]
            match = True
            for x in range(min(curKeyLen, len(key))):
                if curKey[x] < key[x]:
                    end   = mid - 1
                    match = False
                    break
                elif curKey[x] > key[x]:
                    start = mid + 1
                    match = False
                    break
            if match:
                if curKeyLen > len(key):
                    start = mid + 1
                else:
                    break
        start = mid
        end   = mid
        while start > 0  and self._lines[start].startswith(curKey):
            start -= 1
        index = start + 1
        while end < len(self._lines) and self._lines[end].startswith(curKey):
            end += 1
        while (index < end):
            text = self._lines[index].replace('\t', '    ') 
            self._result.Append(text)
            index += 1
        
        self._inSearching = False
        
    def OnDoubleClick(self, event):
        text = self._result.GetStringSelection()
        arr = text.split('    ')
        file = arr[1]
        no   = arr[2][:-2]
        if not os.path.exists(file):
            wx.MessageBox('File %s does not exist!' % file)
            return
        doc = wx.GetApp().GetDocumentManager().CreateDocument(file, wx.lib.docview.DOC_SILENT)
        if doc == None: return
        view = doc.GetFirstView()
        if view == None: return
        view.GotoLine(int(no))
        
class TagLoadingThread(threading.Thread):
    def __init__(self, path, callback):
        threading.Thread.__init__(self)
        self._tagPath   = path
        self._callback  = callback
        
    def run(self):
        try:
            f = open(self._tagPath, 'r')
            lines = f.readlines()
            f.close()
        except:
            return
        
        lines = lines[6:]

        wx.GetApp().ForegroundProcess(self._callback, (lines,))
           
class TagCreationProcess(wx.Process):
    def OnTerminate(self, id, status):                   
        self._parent.OnNotifyCreationProcessEnd(id, status)
        
    def SetParent(self, parent):
        self._parent = parent            
        
        
#----------------------------------------------------------------------
# This file was generated by N:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

symbol = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAQVJ"
    "REFUOI1jZGRiZqAEMFGkmxoGsBBSMHnPm/8/GH4wMPxgYLj/4jvDtBRVRpIMOH/jPgMHBwMD"
    "AwMHw9KuEkwFjEzMOHH2vGv/YeyWdc//Cyh4/UdXgzMMPMtX/b9++Tyc/52BgYED4hQUgNMA"
    "SVlNhv0T4xD+/cHAIKjpRJwBkVNO/z93eB+GuKKCEYYYRiB6lu/6ryggyXCdgYFBXC/hPwMD"
    "A4OkoiUDJwd2L2AYYGiqxdAWIoMSVS8vLWBwCr39n0NUAL8XipY8+X/+9DUsnmJg+PGBgYET"
    "izgTA9SpkT2X/3/48J3hxw9MRQbhq/4/f/yD4fnrHwziahn/keUYh35mAgBO30tRPNokAgAA"
    "AABJRU5ErkJggg==")
getsymbolData = symbol.GetData
getsymbolImage = symbol.GetImage
getsymbolBitmap = symbol.GetBitmap
getsymbolIcon = symbol.GetIcon


        