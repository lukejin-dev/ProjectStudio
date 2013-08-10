"""
Need redesign 
"""
import wx
import ui.MessageWindow
import core.service
import threading
import os, shutil
import re
import array
from plugins.EdkPlugins.basemodel.message import *

class BuildManager(wx.EvtHandler):
    ID_PLATFORM_SELECTOR  = wx.NewId()
    ID_TOOLTAG_SELECTOR   = wx.NewId()
    ID_TARGET_SELECTOR    = wx.NewId()
    ID_BUILD_PROCESS_END  = wx.NewId()
    ID_BUILD_START        = wx.NewId()
    ID_BUILD_CANCEL       = wx.NewId()
    
    def __init__(self, extension):
        wx.EvtHandler.__init__(self)
        self._projext = extension
        self._frame   = wx.GetApp().GetTopWindow()
        self._toolbar = self.CreateBuildToolBar()
        self._service = self.InstallBuildService()
        self._envs    = {}
        self._process = None
        self._inputThread = None
        self._errorThread = None
 
    def GetFrame(self):
        return self._frame
        
    def CreateBuildToolBar(self):
        toolbar = wx.ToolBar(self.GetFrame(), -1, wx.DefaultPosition, (400, -1),
                             style=wx.TB_FLAT|wx.TB_NODIVIDER|wx.TB_DOCKABLE|wx.TB_TEXT)
        self._platformselector = wx.ComboBox(toolbar, self.ID_PLATFORM_SELECTOR, "",
                                             size=(150, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        toolbar.AddControl(self._platformselector)

        self._archselector = ArchSelector(toolbar, -1)
        toolbar.AddControl(self._archselector)
        self._tagselector = wx.ComboBox(toolbar, self.ID_TOOLTAG_SELECTOR,
                                        choices=['MYTOOLS', 'ICC', 'ELFGCC', 'CYGWINGCC', 'UNIXGCC'], 
                                        size=(100, -1),
                                        style=wx.CB_DROPDOWN)
        self._tagselector.SetValue('MYTOOLS')
        toolbar.AddControl(self._tagselector)
        self._targetselector = wx.ComboBox(toolbar, self.ID_TARGET_SELECTOR,
                                           choices=['DEBUG', 'RELEASE'], 
                                           size=(100, -1),
                                           style=wx.CB_DROPDOWN)
        self._targetselector.SetValue('DEBUG')
        toolbar.AddControl(self._targetselector)
        toolbar.AddSeparator()
        self._buildbt = wx.BitmapButton(toolbar, self.ID_BUILD_START, getBuildStartBitmap())
        toolbar.AddControl(self._buildbt)
        self._cancelbt = wx.BitmapButton(toolbar, self.ID_BUILD_CANCEL, getBuildCancelBitmap())
        toolbar.AddControl(self._cancelbt)
        toolbar.Realize()
        self.GetFrame().AddToolBar('edk2builder', 'Build', toolbar, 2, (570, -1))
        self.ShowToolbar(False)
        self.EnableToolbar(False)
        
        self._platformselector.Bind(wx.EVT_COMBOBOX, self.OnChangePlatform)
        self._buildbt.Bind(wx.EVT_BUTTON, self.OnClickBuild)
        self._cancelbt.Bind(wx.EVT_BUTTON, self.OnClickCancel)
        wx.EVT_UPDATE_UI(self.GetFrame(), self.ID_BUILD_START, self.OnUpdateUI)
        wx.EVT_UPDATE_UI(self.GetFrame(), self.ID_BUILD_CANCEL, self.OnUpdateUI)

        return toolbar
        
    def ShowToolbar(self, bShow=True):
        self.GetFrame().ShowPane('edk2builder', bShow)
        
    def RefreshToolbar(self):
        cur = self._platformselector.GetValue()
        self._platformselector.Clear()
        
        pObjs  = self._projext.GetPlatforms()
        if len(pObjs) == 0:
            self.EnableToolbar(False)
            return
            
        self.EnableToolbar(True)
        curpObj = None
        for obj in pObjs:
            name = obj.GetName()
            self._platformselector.Append(name)
            if cur == name:
                curpObj = obj
                 
        if curpObj == None:
            curpObj = pObjs[0]
            
        self._platformselector.SetValue(curpObj.GetName())
        self._archselector.EnableArchs(curpObj.GetSupportArchs())
        
    def OnChangePlatform(self, event):
        pName = event.GetString()
        pObjs = self._projext.GetPlatforms()
        curObj = None
        for pObj in pObjs:
            if pObj.GetName() == pName:
                curObj = pObj
                break
        assert curObj != None, "Fail to get platform object"
        self._archselector.EnableArchs(curObj.GetSupportArchs())
        
    def EnableToolbar(self, isEnable=True):
        if isEnable:
            self._platformselector.Enable()
            self._tagselector.Enable()
            self._targetselector.Enable()
            self._buildbt.Enable()
            self._archselector.Enable()
        else:
            self._platformselector.Disable()
            self._tagselector.Disable()
            self._targetselector.Disable()
            self._buildbt.Disable()
            self._archselector.Disable()
    
    def InstallBuildService(self):
        service = BuildService(self)
        wx.GetApp().InstallService(service)
        frame = wx.GetApp().GetTopWindow()
        service.SetFrame(frame)
        service.Activate()
        return service
        
    def OnClickBuild(self, event):
        name = self._platformselector.GetValue()
        if len(name) == 0: 
            wx.MessageBox("Please select platform want to be built!")
            return
        archs = self._archselector.GetArchs()
        if len(archs) == 0:
            wx.MessageBox("No arch is selected for build %s" % platform)
        pObj = self._projext.GetPlatformObjByName(name)
        assert pObj != None, 'Fail to get platform object from project extension'
        
        tag = self._tagselector.GetValue()
        target = self._targetselector.GetValue()
        self.Build(self._projext.GetWorkspace(), pObj.GetRelativeFilename(), archs, tag, target)
        
    def OnClickCancel(self, event):
        if self._process == None:
            return
        if self._pid == None:
            return
        wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)
                
    def CheckBuildConfigFile(self, workspace):
        targetfile = os.path.join(workspace, "Conf", "target.txt")
        if not os.path.exists(targetfile):
            sourcefile = os.path.join(workspace, "BaseTools", "Conf", "target.template")
            if os.path.exists(sourcefile):
                shutil.copy(sourcefile, targetfile)
                
        rulefile = os.path.join(workspace, "Conf", "build_rule.txt")
        if not os.path.exists(rulefile):
            sourcefile = os.path.join(workspace, "BaseTools", "Conf", "build_rule.template")
            if os.path.exists(sourcefile):
                shutil.copy(sourcefile, rulefile)
        
        deffile = os.path.join(workspace, "Conf", "tools_def.txt")
        if not os.path.exists(deffile):
            sourcefile = os.path.join(workspace, "BaseTools", "Conf", "tools_def.template")
            if os.path.exists(sourcefile):
                shutil.copy(sourcefile, deffile)
                
    def Build(self, workspace, platform, archs, tag=None, target=None, module=None, reason=None):
        if self._process != None:
            wx.MessageBox("Build is running, please terminate current building firstly then do others building!")
            return
            
        self._service.GetView().Activate()
        self._service.GetView().Clear()
        self._workspace = self._projext.GetWorkspace()
        
        self.CheckBuildConfigFile(self._workspace)
        self.ConfigEnviron()
        
        if wx.Platform == '__WXMSW__':
            cmd = os.path.join(workspace, 'BaseTools\\Bin\\Win32\\Build.exe ')
        else:
            cmd = os.path.join(workspace, 'Conf/BaseToolsSource/BinWrappers/Linux-i686/build ')
        cmd += ' -p %s ' % platform
        
        if tag != None:
            cmd += ' -t %s ' % tag
        else:
            cmd += ' -t %s ' % self._tagselector.GetValue()
            
        if target != None:
            cmd += ' -b %s ' % target
        else:
            cmd += ' -b %s ' % self._targetselector.GetValue()
            
        for arch in archs:
            cmd += ' -a %s ' % arch.upper()
        if module != None:
            cmd += ' -m %s ' % module
        if reason != None:
            cmd += ' %s' % reason
        
        oldpath = os.getcwd()
        os.chdir(self._workspace)
        self._service.GetView().SetCurrentDir(self._workspace)
        self._service.GetView().AddMessage('%s\n' % cmd)
        self._service.GetView().SetTitle('Building ... %s' % cmd)
        wx.GetApp().GetTopWindow().PlayTextToasterBox('Starting building: ' + cmd)
        try:
            self._process = BuildProcess(self, self.ID_BUILD_PROCESS_END)
            self._process.SetParent(self)
            self._process.Redirect()
            self._pid    = wx.Execute(cmd, wx.EXEC_ASYNC|wx.EXEC_MAKE_GROUP_LEADER, self._process)
            self._input  = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self._service.GetView().AddMessage('Fail to launch build cmd!')
            self._process = None  
            os.chdir(oldpath)
        os.chdir(oldpath)    
        self._inputThread = MonitorThread(self._input, self.MonitorThreadCallback)
        self._errorThread = MonitorThread(self._error, self.MonitorThreadCallback)
        self._inputThread.start()  
        self._errorThread.start()
        
    def MonitorThreadCallback(self, message):
        view = self._service.GetView()
        if view != None:
            view.AddMessage(message)
        
    def ConfigEnviron(self):
        self._envs = os.environ
        self.ConfigVcEnviron()
        
        self.ConfigEdk2Environ() 

        for env in self._envs.keys():
            os.putenv(env, self._envs[env])
            
    def ConfigEdk2Environ(self):
        if wx.Platform == '__WXMSW__':
            self._envs['EDK_TOOLS_PATH'] = os.path.join(self._workspace, "BaseTools")
        else:
            self._envs['EDK_TOOLS_PATH'] = os.path.join(self._workspace, "Conf/BaseToolsSource")

        for environ in self._envs.keys():
            if environ.lower() == 'path':
                if wx.Platform == '__WXMSW__':
                    self._envs[environ] = '%s;%s\\BaseTools\\Bin\\Win32' % (self._envs[environ], self._workspace)
        if wx.Platform != '__WXMSW__':
            self._envs['PATH'] = '%s:%s/Conf/BaseToolsSource/BinWrappers/Linux-i686:/home/work/edk2/Conf/BaseToolsSource/Bin/Linux2' % (os.getenv('PATH'), self._workspace)
        
        if wx.Platform == '__WXMSW__':
            self._envs['WORKSPACE_TOOLS_PATH'] = os.path.join(self._workspace, "BaseTools")
        self._envs['WORKSPACE'] = self._workspace
        
    def ConfigVcEnviron(self):
        if 'VS80COMNTOOLS' not in os.environ.keys():
            #print "Fail to config Visual Studio .NET environment for not finding VS71COMNTOOLS environment variable."
            if 'VS71COMNTOOLS' not in os.environ.keys():
                print "Fail to config Visual Studio .NET environment for not finding VS71COMNTOOLS or VS80COMNTOOLS environment variable."
                return
            else:
                vcCommonToolDir = os.environ['VS71COMNTOOLS']
        else:
            vcCommonToolDir = os.environ['VS80COMNTOOLS']
   
        
        #vcCommonToolDir = os.environ['VS71COMNTOOLS']
        
        vsVarPath = os.path.join(vcCommonToolDir, 'vsvars32.bat')
        
        f = open(vsVarPath, 'r')
        lines = f.readlines()
        f.close()
        
        for line in lines:
            if line[0:4].lower() == '@set':
                type  = line[line.index(' ') + 1:].split('=')[0].strip()
                value = line[line.index(' ') + 1:].split('=')[1].strip()
                expandValue = ''
                
                if value.find('%') != -1:
                    segments = value.split('%')
                    
                    for segment in segments:
                        segment = segment.strip()
                        if segment in self._envs.keys():
                            expandValue = '%s%s' % (expandValue, self._envs[segment])
                        elif segment in os.environ.keys():
                            expandValue = '%s%s' % (expandValue, os.environ[segment])
                        else:
                            expandValue = '%s%s' % (expandValue, segment)
                else:
                    expandValue = value
                    
                self._envs[type] = expandValue
                            
    def OnBuildProcessEnd(self, id, status):
        if self._inputThread:
            self._inputThread.Terminate()
            self._inputThread = None
        if self._errorThread:
            self._errorThread.Terminate()
            self._errorThread = None
            
        view = self._service.GetView()
        if view != None:
            view.Activate()
        if self._error:
            while self._error.CanRead():
                text = self._error.read()
                if view != None:
                    view.AddMessage(text)
        if self._input:
            while self._input.CanRead():
                text = self._input.read()
                if view != None:
                    view.AddMessage(text)        
        self._process.Detach()

        self._process.CloseOutput()             
        self._process = None
        self._pid     = None
        wx.GetApp().GetTopWindow().PlayTextToasterBox('Building Finished!')
        if view != None:
            wx.Yield()
            view.SetTitle('Build Finished! Return status = %s... ' % status)
            view.AddMessage("\nBuild process is finished! process id = %d, status = %s" % (id, status))
        self._input   = None
        self._error   = None
        self._output  = None
        
    def OnUpdateUI(self, event):
        id = event.GetId()
        if id == self.ID_BUILD_START:
            if self._process == None:
                self._buildbt.Enable()
            else:
                self._buildbt.Disable()
        if id == self.ID_BUILD_CANCEL:
            if self._process == None:
                self._cancelbt.Disable()
            else:
                self._cancelbt.Enable()

    def OnQuit(self):
        if self._process == None:
            return
        if self._pid == None:
            return
        if self._inputThread:
            self._inputThread.Terminate()  
        if self._errorThread:
            self._errorThread.Terminate()   
                              
        wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)  
                  
import threading
class MonitorThread(threading.Thread):
    def __init__(self, pipe, callback):
        threading.Thread.__init__(self)
        self._pipe = pipe
        self._callback = callback
        self._isCancel = False
        
    def run(self):
        while (not self._isCancel):
            self._pipe.Peek()
            if self._pipe.LastRead() == 0:
                break
            text = self._pipe.read()
            wx.GetApp().ForegroundProcess(self._callback, (text,))
        
    def Terminate(self):
        self._pipe.flush()
        self._isCancel = True
                                 
class ArchSelector(wx.Control):
    def __init__(self, parent, id):
        wx.Control.__init__(self, parent, id, size=(160, -1), style=wx.NO_BORDER)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._ia32 = wx.CheckBox(self, -1, 'IA32') 
        sizer.Add(self._ia32, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 1)
        self._x64 = wx.CheckBox(self, -1, 'X64')
        sizer.Add(self._x64, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 1)
        self._ipf = wx.CheckBox(self, -1, 'IPF')
        sizer.Add(self._ipf, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 1)
        self._ebc = wx.CheckBox(self, -1, 'EBC')
        sizer.Add(self._ebc, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 1)
        self.SetSize((160, -1))
        self.SetSizer(sizer)
        self.Layout()
                
        self._mapping = {'ia32':self._ia32, 'x64':self._x64, 'ipf':self._ipf, 'ebc':self._ebc}
        
    def EnableArchs(self, archs):
        for ctl in self._mapping.values():
            ctl.SetValue(False)
            ctl.Disable()
        if len(archs) == 0: return
        for arch in archs:
            if arch.lower() not in self._mapping.keys():
                ErrorMsg('Invalid arch string %s which is not in IA32, X64, IPF, EBC' % arch)
                continue
            ctl = self._mapping[arch.lower()]
            ctl.Enable()
            ctl.SetValue(True)
            
    def GetArchs(self):
        ret = []
        for arch in self._mapping.keys():
            if self._mapping[arch].IsEnabled() and \
               self._mapping[arch].IsChecked():
                ret.append(arch)
        return ret
        
class BuildService(core.service.PISService):
    def __init__(self, parent):
        self._parent = parent
        core.service.PISService.__init__(self)
        
    def GetViewClass(self):
        return BuildView
    
    def GetPosition(self):
        return 'bottom'
        
    def GetName(self):
        return 'Build'
        
    def GetIcon(self):
        return getBuildStartIcon()
    
    def OnCloseFrame(self, event):
        self._parent.OnQuit()
        return core.service.PISService.OnCloseFrame(self, event)
    
class BuildView(core.service.PISServiceView):    
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._output = BuildOutputWindow(self, -1)
        self._output.SetReadOnly(True)
        #self._output.SetWrapMode(True)
        sizer.Add(self._output, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
    
    def AddMessage(self, text):
        self._output.DocumentEnd()
        self._output.AddMessage(text)
        self._output.DocumentEnd()
        
    def Clear(self):
        self._output.SetReadOnly(False)
        self._output.ClearAll()
        self._output.SetReadOnly(True)
        
    def SetCurrentDir(self, path):
        self._output.SetCurrentDir(path)
        
class BuildOutputWindow(ui.MessageWindow.MessageWindow):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, name='Dos'): 
        ui.MessageWindow.MessageWindow.__init__(self, parent, id, pos, size, style, name)
        self.SetWrapMode(True)
        self.SetCaretLineVisible(False)
        #self.SetCaretLineBack('#000000') 
        self.SetCaretForeground('#FFFFFF')

    def GetBackgroundColor(self):
        return '#000000'
    
    def GetForegroundColor(self):
        return '#FFFFFF'  
          
class BuildProcess(wx.Process):
    def OnTerminate(self, id, status):                   
        self._parent.OnBuildProcessEnd(id, status)
        
    def SetParent(self, parent):
        self._parent = parent
#----------------------------------------------------------------------
# This file was generated by util\img2py.exe
#
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getBuildStartData():
    return zlib.decompress(
'x\xda\x01X\x06\xa7\xf9\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x06\x0fIDATX\x85\xc5\x97ML\x1b\xe9\x19\xc7\x7f\xf6\xd83\
\xc6\xe3\x0f\x1cdb\xc0\xe6\xc3\nI\x81\x1aV\x01\x05C\x02A\xb0]%=$R\x8e=\xefJ\
\xbb\xa7\xb6\xdaC\xb6\x87\xad\xaa\x1e\xb6j\x15\xa9\xad\xf6\xd2CO=T\xea}9\xb1\
\xda\xa0n\x0bnJR\x9c -\x08\x16\x1coH\xea\x0f\x16b\xec\x01\xcfx\xfc\xf6\x90\
\xc6\x84x\x1c\xa2\xaa\xab\xfc\xa5\x91f\x9e\xff\xfb\xcc\xf3\x7f\x9e\xf7y\xdfw\
\xc6f\xb3K\xbcI\xd8\xdfht+\x013\xd3\x9f\x8aH\xf8\xb2\xb0\x1a\xfc\xd6\xd0\x07\
b|\xeccK\x0e`|\xecc\xf1\xd6\xd0\x07\x96|$|Y\xccL\x7fZ\xc79^6\xa4\xd3_P(|c\
\x19 \x9bM"\xcbj\xa3\xf8<~\x9c@\xd7K\x96\\\xa1\xf0\r\xe9\xf4\x17\xf5\x84\xcd\
.\xbd\xf2\x9a\x98\xf8D4\xe2FF>\x14##\x1f6\xe4_\xe5\xfb\xfc\xaa\xab\xc0\xcb\
\xc8d\xee6\xe4\xf2\xf9\x95\xff\xd9\xb7a\x05\xa6\xa6n\x89px\xd2R\xf9\xe0\xe0{\
bt\xf4\xa3\x86Y\x8d\x8e~$\x06\x07\xdf\xb3\xe4\xc3\xe1I15u\xab\x8e\xab\xab@.w\
\x1fM\xcb[\x8a\xd5\xf5"\x07\x07\xd6\x1c\xc0\xb7\xdf\xae!I.KN\xd3\xf2\xe4r\
\xf7\xeb\x0b\xf0:\xfb@\xdf\xf7~$|\xbe.\xfeq\xe7W\xb6\x17\xedC\x83\xef\x0b\
\x80\xe4\xfd?\x1c\xb3\x8f^\xf8\x99(\x14\x1e\xf2\xd5\xea\x9f\x8f\xd9\xadpb\
\x0f\x00(\x8a\x0fE\xf1\xd7\xd9\x8b\xc5G\r\xc6\xfbQ\x14\xdf\xeb\xbc\xfah\x1f\
\xb8tq\\t\xb4\xb75\\\xe3V\xf8z\xf33\xdb\xd7\x9b\x9f\x9d\x98\xe5\x8b\xe8ho\
\x13\x97.\x8e\xd7\xe2\xd4\x04x<\x1edY\xb6tr\xb9N5\x9c[+H\x92\x0b\x97\xeb\x94\
%\'\xcb2\x1e\x8f\xa7\xf6\xdcp\n.\x8e\xffR\x00\xd8\xed\x0e\x14\xa5\x19I\x92\
\x99\xba|K\x18\x86\x06@\xa1\x90\xe6\xc1\xca\x1fm\x00\xb1\xef\xbf+|\xbeN\x00\
\x9cN7\xb2\xecA\x92d&.}"\xaa\xd5\n\x00\x7f_\xf8\xb9e\xa5\x1a\n0\x8c"\xaa\xda\
FSSK\xcd\xe6v\xb7b\x18\x1a\xa5\xd2\xbf1\x8c\xfd\x17\xc6\xee#D\x15U\r\xe1t\
\xba\xff[\x05\x19Y\xf6pp\xb0C\xa9\xf4\xa4Q\x98\xc6\x02\xee\xfc\xf376\x80\x1f\
^\xfd\xd3\xb1\xbe\xd0\xf5\xa7,,\xfe\xe2X6\xabk\x7f\xb1\x01\\\x9e\xfc\xb5x.\
\xe09n\xcf\xff\xf4\x95=r\xe2ix\xf6\xec)\xfc~\x05Y\x96\x88D\xbc\xc4b\xad\r\
\xc7\xc6b\xadD"^dY\xc2\xefW8{\xd6\xba\x0f^D\xc3\n|>\xf7\xb9\x90\xe5\x16J%\
\x99\xf9\xf94O\x9e\x14\x89\xc7;8w\xee\x1c7n|)\x1e<X\xe2\xc7?y\x96\xdd\xef\
\x7f\xf7[\x11\x8b\x8d\xe0r\xb5\xb0\xb6V\xe4\xf6\xed\x87\xb4\xb5y\x98\x9a\xea\
\xe4\xc6\x8d\x7f\t]\xdf\xe1\xed\x1f\xbc\xfd\xea\x1e\xb0\xd9ltuu\xb1\x95z\x08\
\xc0\xe4\xe4%L\xd3dg\xe7\x80LF\xc3\xe7S\x18\x18\x08\x12\x8b\xb5b\xb7\xf7\x10\
\x08\x1c\x95zrr\x92\xfe\xfe~\xaa\xd5*\x0eG\x96\xc7\x8f\x8bttx\x89\xc5N\xd3\
\xd2\xd2\x84$\x1dmv]]]\xd8l\xb6z\x01\x0e\x87\x83\x99\x99\x19n\xde\xbc)\xa2\
\xd1(\xa6ib\xb7\xdb\xf1\xfb]\\\xb8\xd0N\xa9\xa4\x13\x89\xf8\xb1\xdb\xedT\xab\
UB\xa1\x10\x7f\xfb\xf2\xaf\x02 \x14\nQ\xadV\xb1\xdb\xedtv\xfay\xe7\x9d\x1eTU\
\xc6\xefwa\xb7\xdb1M\x93\xb5\xd5\xaf\xc4\xe6\xe6&KKK\xdc\xb9s\xa7^\x80$I\xf4\
\xf5\xf51==M.\x97#\x95J\xd1\xda\xda\x8a\xdb\xedFUu\x1c\x8e2\x8a"0\x0c\x83\\.\
\x87i\x9a\x0c\x0e\x0e\x02\x90\xcdf9<<$\x18\x0c\xa2(\x02\xbf\xbf\x8c\xa2\x80\
\xc3a\xa3X,\x92\xcdf\xf1z\xbdLOOS*\x95\xb8{\xf7\xe8\x94\xackB\xc30X^^fvv\x96\
T*\x85\xa6i,--177\xc7\xf6\xf66{{{,,,0??O.\x97#\x97\xcb1??\xcf\xc2\xc2\x02{{{\
loo377\xc7\xd2\xd2\x12\x9a\xa6\x91J\xa5\x98\x9d\x9deyy\x19\xc30\x1a\xf7\xc0s\
T\xabU\x9e>}J&\x93A\xd34*\x95\n\xbb\xbb\xbb\xb5,\r\xc3`gg\x07M\xd3(\x97\xcb\
\x00\xe4\xf3y\xdcn7\x86apxxH6\x9bEQ\x14*\x95\n\x9a\xa6\x91\xc9dhkk\xa3Z\xad\
\x9e,@\x96e\x86\x87\x87\xe9\xec\xec\xa4\xa7\xa7\x07UU\x89\xc7\xe3\x0c\x0c\
\x0c\x10\x0e\x87q\xb9\\LLLP\xa9Thm}\xb6$gffp8\x1c\x04\x02\x01\x9a\x9a\x9a\
\xb8r\xe5\n^\xaf\x17UU\xe9\xe9\xe9\xe1\xda\xb5k\x04\x83A\xcb\xad\xbeN\x80$I\
\x9c>}\x9a\xe6\xe6\xe6\xda\xf9\xd0\xde\xde\x8ea\x18x<\x1e$I"\x12\x89 \x84@U\
\x9f}\x1fvwwc\xb3\xd9p\xb9\\8\x9dN\xa2\xd1(N\xa7\x13Y\x96inn\xa6\xb7\xb7\x17\
EQ\x8e\xad\x86\x86\x02t]\xe7\xde\xbd{lll066F8\x1c&\x91H\x90\xcb\xe5\x88\xc7\
\xe3\xf8|>\x12\x89\x04\x87\x87\x87\x8c\x8d\x8d\x01\xb0\xb8\xb8\x88\xcb\xe5"\
\x1e\x8fS(\x14H$\x12\x04\x83A\xe2\xf18\x8f\x1e=bqq\x913g\xce\x10\x8f\xc7\xeb\
\x04\xd45\xa1i\x9a\xa4\xd3i\x92\xc9$\xf9|\x1e]\xd7\xd9\xda\xdabee\x85\xdd\
\xdd]4Mc}}\x9d\xd5\xd5U\xf6\xf7\xf7\xd9\xdf\xdfguu\x95\xf5\xf5u4Mcww\x97\x95\
\x95\x15\xb6\xb6\xb6\xd0u\x9d|>O2\x99$\x9dNc\x9a\xe6\xc9\x15p:\x9d\x9c?\x7f\
\x9e\xf6\xf6v\xa2\xd1(\xaa\xaa2::J__\x1f\xe1p\x18\xb7\xdb\xcd\xc4\xc4\x04\
\x86a\x1c\xeb\x01\xa7\xd3I \x10@Q\x14\xae^\xbd\x8a\xcf\xe7CUU\xa2\xd1(\xd7\
\xaf_\'\x14\n\xe1t:\x1b\x0b\x10BP.\x97\xd1u\x9d\xee\xeen\xba\xbb\xbb\x81g\
\xab\xa2\xb7\xb7\xf7\x98S\x7f\x7f\xff\xb1\xe7\xa1\xa1\xa1\xda\xbd\xd7\xebexx\
\xb8\xe6\x1b\x08\x04j\xa5\xd7u\x9dr\xb9\x8c\x10G\xe7[M\x80i\x9a$\x93IJ%\xeb\
\x1f\x8b\xff\x17666\x8eMEM\x80a\x18$\x93I\x92\xc9\xe4w*\xe0e\xbc\xd6W\xf1w\
\x897\xfew\xfc\x1f\x89\xaa`D\x81@\xf8\xa0\x00\x00\x00\x00IEND\xaeB`\x82\x97V\
\x13W' )

def getBuildStartBitmap():
    return BitmapFromImage(getBuildStartImage().Scale(16, 16))

def getBuildStartImage():
    stream = cStringIO.StringIO(getBuildStartData())
    return ImageFromStream(stream)

def getBuildStartIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getBuildStartBitmap())
    return icon



def getBuildCancelData():
    return zlib.decompress(
'x\xda\x01\xd1\x05.\xfa\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x05\x88IDATX\x85\xed\x96Ko\x1b\xd7\x19\x86\x9f\xb9\xf0\xcc\
\x85\x97\xe1e\x86TIy(\xeab\xba\x8a$\xbbrd4u\x0b\xc3F\x0b\xb8\x12\x0cX\xfb\
\xae\x93\xfc\x83.\x8b.\x9a\x02\xfd\t]w\xef\xd4\xae\rk%8\xf0\xa2\xb6j\xa1\xb6\
\x03\xd5V\xcc*\xd4%\x92#\x86\xb2L\x8a\xa2\x86\xb7,h1P\xa9X\n*w\xd5oG\xf2\xe5\
9\xcf\xf7\x9d\xf7\xbc3\x92$+\x9ct\xfd\xe9\x17?o%\x03\x81\xf6\x87\x81\x01\x18\
\x1b\xe37\x1f~$\x1d\xa6UO|w (\x04\x84\xc3\xd0\xd3\x03\x89\x04\xa8\xdf\xbf\
\xcd\x89\x02\xfc\xe1\xe2\xcfZ\xe9P\x08d\x19"\x118}\x9a\x86a\xd0l6\xff7\x00aM\
\x03\xcb\x82d\x12\xe2q\x10\x82\xa5\xa5%\x9e<y\xf2\xbd\xff\x91\x8e\xf2\xc0\
\x9f\x7f\xf5\xcb\x96\x10\x02U\x96\xa1\xd1ho\xf0\xde{\xe4*\x15~\xf7\xc9\x1f%\
\x80\xdf\x7f\xf0\xd3\xd6@$\x02\x8a\x02\xbd\xbd02B\xdd4\xf1<\x8f\x0f?\xfa\xf8\
\xd0\xb3\xdf\xaf#\'pgu\x95\xf1\xf1q\xfa\x93IX]\x85\xdd]XZ"V\xafw41]\x87P\xa8\
\xddy"\x01\xba\xce\xf2\xf22\xf3\xf3\xf3G-\x7f4\xc0\xa7\xffz&Y\x13\x13-;\x16C\
\xdf\xdeFT*\xb0\xb1A\xb8\xd9\xe4/\xbf\xbe\xda\xea\x08\xfd~H\xa7\xf1\x02\x01\
\xaa\xd5*\xb9\\\x8eO\xffz\xf3\xad\xdd\x1f\x0b\x00\xe0\xc1\x83\x07l}\xfd5\x13\
\xfd\xfddN\x9f\x86\x95\x15\xd8\xde>T\xbb\xb6\xb6\xc6\xdc\xdc\x1c\x8b\x8b\x8b\
\xc7Y\x1a\xf98\xa2g\xcf\x17\xa5\x9bwg\xa4\x82\xaa\xb6\xcf\xd8\xef\xef\x16\
\xd5\xebP\xa9PX]\xe5\xe6\xad\xbfI\xcf\x9e/\x1e\xd9=\x9c\xe4-(\x95\xe0\x8b/\
\xda>\xf9\x01\xf5\xc3\x00*\x15(\x97\xa1Vk;^\xd3\xbe\x0b\x99z\x1d^\xbeD/\x16\
\xdf!\xc0\x97_\xb67*\x95\xc04\xa1\xaf\xaf}-\x01\xb6\xb6 \x9f\'\x15\x0c\xf2\
\xdb\xf7\xcf\xb7\xfe\xb9\xb9\xc9L~\xf9dL\xb8_\xe6\xf66\xe8:\x18\x06\xd86$\
\x93\xa8\x89\x04\xba\xae\xa3\x14\x8b\xa0\xaa\x98\xa6\x89\xbd\xb5E\x13\x98\
\xc9/\x1f\xb9\xe6\x91A\x040\xd9\x97n\xfd$\x1e\xe7G\x81\x00\xe1X\x0c2\x99v\
\xce\x87B\x84\x1c\x07\xd7u\t\xf8|\xf0\xfa5\xc5\xcf?g\xe5\xb3\xcf\xf8jm\x8d\
\xf5r\x99O\xe6\xfe\xf1\xdf\x05\x11\xc0\x90m\xf3\xe3X\xac\xfdA\x08\x88\xc5\
\xa8\x85\xc3\xec\xec\xecP\xfb\xe6\x1b\x82\xc1 \x8dP\x08\x84`K\xd7)H\x12\x8a\
\xae\x93\xd5\xf5\xe3O\xe0\xc2\xc4\xfb\xad\xc3\x04!Y\xe6\x03\xbf\x9f\xac\xa6\
\xb5\xbf\x88Fal\x8cm\xbf\x9f\\.G\xb9\\\xc6\xef\xf7\xa3\xbe1\xa3\xf7\xfa5;/_b\
{\x1e\x03\xc0\xbf\xabU\xfe^\xa9\xb0\xf3\x1f\x0f\xa4\x87o&\xd3\x99\x80\xe38\
\xf4\xf4\xf4\xe08\xce\x01\xa1\xf0<\xe2\x1b\x1bm\xe3\x05\x02\xa8\xf18\x81x\
\x1c=\x10\xa0\\.#\x848\xa07"\x11\x8cH\x84\x04\x90\x00\x04\xe0\x03\xbc7\xbfon\
n\xb2\xb1\xb1\xd1\xd1w\x00\x14Ea||\x9cK\x97.\x1dX\xd0+\x16Y\x9f\x99a\xeb\xf9\
s\xe8\xeb\xc3\xc8f\xe9\x1b\x1b#\x1c\x8f3::J\xadV;t\xb4\x1a\xe0\x07j\xc0\x04\
\xb0\xdf\xff\xbd{\xf7\x98\x99\x99\xe9\xe8:I(\xcb2\x89D\x82\xa1\xa1!L\xd3doo\
\x0f\xdb\xb6\x19\xccf\xb1\xd2iT\xd7%\x92\xcd\x12J\xa7\xd9\xde\xdd\xe5\xd5\
\xabW\xc4\xe3qR\xa9T\xbb\x13U\xc5u]zzzh4\x1a\xa0i\x84\xfb\xfb\xd1l\x9b\xdd\
\xbd=L\xd3dhh\x88D"\x81,\x7f\x17\xc0]&\xf4<\x8f\xb9\xb99\x1e?~\xcc\xd4\xd4\
\x14\xa3\xc3\xc3\xe0\xba\xe8\x9aFzt\x94\xa6\xaa2;;K\xadVcjj\n\x80\xbbw\xefb\
\x9a&\x93\x93\x93\x14\x8bE\xee\xdc\xb9Coo/\x93\x93\x93\xe4r9n\xdf\xbe\xcd\
\xd9\xb3g\xbb\x8e\xf7P\x00I\x92\x08\x06\x838\x8e\x83a\x18(B\x10u]D4\x8a\x93J\
Q\xaf\xd7q\x1c\x87j\xb5\xda9\xffh4\x8a\xae\xeb\xf8|>4M#\x16\x8baY\x16\x8a\
\xa2`\x18\x06\x8e\xe3\x10\x0c\x06\x91\xa4\xee\x1b\xd9\x05\xa0i\x1a\x17.\\`dd\
\x04\xcb\xb2\x10Bp\xea\xd4)\x9a\xcd&\x9a\xa6\xd1j\xb5\xb8r\xe5\n\xcdf\x13\
\xebM\n^\xbdz\x15Y\x96\xb1,\x8bP(\xc4\xb5k\xd7\x10B\x10\x08\x04\x18\x18\x18\
\xc0\xb6mL\xd3D\xdb\xbfIo\x03h4\x1a\x14\n\x05677\xc9d2(\x8aB>\x9f\xa7T*\x91\
\xc9d\xd0u\x9d\xf5\xf5u\xea\xf5zg\x02kkk\xa8\xaa\x8a\xae\xebT\xabUVVV\x08\
\x06\x83\x98\xa6I\xa9T"\x9f\xcf\xe38\x0e\x81\xfd7\xe5\xb7\x01x\x9e\xc7\xc3\
\x87\x0fy\xf4\xe8\x11\xd3\xd3\xd3\x9c9s\x86\xfb\xf7\xef\xb3\xbc\xbc\xcc\xf5\
\xeb\xd7\xb1m\x9b\xd9\xd9Yvvv\x98\x9e\x9e\xeex\xc0\xef\xf7cY\x16\x85B\x81[\
\xb7n\xe1\xba.\xb6m\xf3\xe2\xc5\x0bn\xdc\xb8\xc1\xf9\xf3\xe7I&\x93G\x03(\x8a\
B*\x95bww\x97h4\x8a\x10\x02\xd7u1\x0c\x03\xcb\xb20\x0c\x83L&C\xb5Z\xedt488\
\x88\xae\xeb\x1dM6\x9b\xc5q\x1c\x84\x10D\xa3Q\x86\x87\x87I\xa5R(Jw\xecw\x01\
\x08!\x98\x98\x98\xe0\xdc\xb9s\x18\x86\x81\xaa\xaa\\\xbcx\x91F\xa3\x81a\x18\
\xc8\xb2\xcc\xe5\xcb\x97i\xb5Z\x18\x86\xd1\xf1\x80$I\x18\x86A8\x1c\xc6q\x9c\
\x8e\x01\x07\x07\x07I\xa5R\xf8|\xbe\xae\xd0:\x00\xd0h4XXX\xc0\xe7\xf3u\x89N\
\xb2\x16\x16\x16\xda9q\x18\xc0\xfc\xfc<O\x9f>}\xa7\x00\xb5Z\xed\x00\xc0\xb1\
\x1e\xc7\xef\xb2\x8e\xf5R\xfa\x7f\x80wY\xdf\x02O\x85\xb7\x85{\xe5\x19\xfd\
\x00\x00\x00\x00IEND\xaeB`\x82\x96\xe2\xccF' )

def getBuildCancelBitmap():
    return BitmapFromImage(getBuildCancelImage().Scale(16, 16))

def getBuildCancelImage():
    stream = cStringIO.StringIO(getBuildCancelData())
    return ImageFromStream(stream)

def getBuildCancelIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getBuildCancelBitmap())
    return icon
                