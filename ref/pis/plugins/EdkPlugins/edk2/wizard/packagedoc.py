import plugins.EdkPlugins.util.wizard
import plugins.EdkPlugins.basemodel.doxygen as doxygen
import plugins.EdkPlugins.edk2.model.inf as inf
import plugins.EdkPlugins.edk2.model.dec as dec
import plugins.EdkPlugins.edk2.model.doxygengen as doxygengen
import wx
import os, sys, re
import shutil
import ui.MessageWindow

from plugins.EdkPlugins.basemodel.message import *

_inf_key_description_mapping_table = {
  'INF_VERSION':'Version of INF file specification',
  #'BASE_NAME':'Module Name',
  'FILE_GUID':'Module Guid',
  'MODULE_TYPE': 'Module Type',
  'VERSION_STRING': 'Module Version',
  'LIBRARY_CLASS': 'Produced Library Class',
  'EFI_SPECIFICATION_VERSION': 'UEFI Specification Version',
  'PI_SPECIFICATION_VERSION': 'PI Specification Version',
  'ENTRY_POINT': 'Module Entry Point Function',
  'CONSTRUCTOR': 'Library Constructor Function'
}

_dec_key_description_mapping_table = {
  'DEC_SPECIFICATION': 'Version of DEC file specification',
  'PACKAGE_GUID': 'Package Guid'
}

class EDK2PackageDocumentWizard(plugins.EdkPlugins.util.wizard.EDKWizard):
    def __init__(self, parent, packageObject, id=-1, title="Generate Package Reference Document", pos=(-1,-1)):
        plugins.EdkPlugins.util.wizard.EDKWizard.__init__(self, parent, id, title, pos)
        self.SetPageSize((475, 330))
        self._pObj         = packageObject
        self._generatePage = None
        
        if self._pObj != None:
            self._locationPage = EDK2PackageDocumentLocationPage(self, self._pObj.GetFilename(), self._pObj.GetWorkspace())
        else:
            self._locationPage = EDK2PackageDocumentLocationPage(self)
        
        self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnFinished)
        
    def RunWizard(self):
        return wx.wizard.Wizard.RunWizard(self, self._locationPage)
        
    def GetPackageFilePath(self):
        return self._locationPage.GetPackagePath()
        
    def GetWorkspacePath(self):
        return self._locationPage.GetWorkspacePath()
        
    def GetDoxygenPath(self):
        return self._locationPage.GetDoxygenPath()
        
    def GetCHMPath(self):
        return self._locationPage.GetCHMPath()
    
    def GetOutputPath(self):
        return self._locationPage.GetOutputPath()
        
    def GetDocumentMode(self):
        return self._locationPage.GetDocumentMode()
        
    def GetIsOnlyDocumentInclude(self):
        return self._locationPage.GetIsOnlyDocumentInclude()
    
    def GetArchitecture(self):
        value = self._locationPage._archCtrl.GetValue()
        return value.split('/')[0]
        
    def GetCustomizeMacros(self):
        return self._locationPage.GetMacros()
    
    def GetToolTag(self):
        value = self._locationPage._archCtrl.GetValue()
        if value == 'ALL':
            return 'ALL'
        return value.split('/')[1]
        
    def GetPackageObject(self):
        return self._pObj
        
    def OnPageChanging(self, event):
        page = event.GetPage()
        
        if hasattr(page, "VerifyPage"):
            if not page.VerifyPage():
                event.Veto()
                return
            
         
    def OnFinished(self, event):
        if not self._locationPage.VerifyPage():
            event.Veto()
            return
        service = wx.GetApp().GetService(DoxygenGenerateService)
        if service == None:
            service = DoxygenGenerateService()
            wx.GetApp().InstallService(service)
            service.Activate()
        service.GetView().Activate()

        service.Start(self.GetDoxygenPath(),
                      self.GetCHMPath(), 
                      self.GetOutputPath(), 
                      self._pObj, 
                      self.GetDocumentMode(), 
                      self.GetArchitecture(), 
                      self.GetToolTag(), 
                      self.GetCustomizeMacros(), 
                      self.GetIsOnlyDocumentInclude(),
                      True)
        
class EDK2PackageDocumentLocationPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent, packagePath=None, workspacePath=None):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        subsizer = wx.GridBagSizer(5, 10)
        
        subsizer.Add(wx.StaticText(self, -1, "Package Location : "), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._packagePathCtrl = wx.ComboBox(self, -1, size=(290, -1))
        if packagePath != None:
            self._packagePathCtrl.SetValue(packagePath)
            self._packagePathCtrl.Disable()
        else:
            list = self.GetConfigure("PackagePath")
            if len(list) != 0:
                for item in list:
                    self._packagePathCtrl.Append(item)
                self._packagePathCtrl.SetValue(list[len(list) - 1])
                    
        subsizer.Add(self._packagePathCtrl, (0, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self._packagePathBt = wx.BitmapButton(self, -1, bitmap=wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN))
        if packagePath != None:
            self._packagePathBt.Disable()
        subsizer.Add(self._packagePathBt, (0, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        wx.EVT_BUTTON(self._packagePathBt, self._packagePathBt.GetId(), self.OnBrowsePath)
        
        subsizer.Add(wx.StaticText(self, -1, "Workspace Location : "), (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        
        self._workspacePathCtrl = wx.ComboBox(self, -1)
        if workspacePath != None:
            self._workspacePathCtrl.SetValue(workspacePath)
            self._workspacePathCtrl.Disable()
        else:
            list = self.GetConfigure("WorkspacePath")
            if len(list) != 0:
                for item in list:
                    self._workspacePathCtrl.Append(item)
                self._workspacePathCtrl.SetValue(list[len(list) - 1])
                            
        subsizer.Add(self._workspacePathCtrl, (1, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self._workspacePathBt = wx.BitmapButton(self, -1, bitmap=wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN))
        if workspacePath != None:
            self._workspacePathBt.Disable()
        subsizer.Add(self._workspacePathBt, (1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        wx.EVT_BUTTON(self._workspacePathBt, self._workspacePathBt.GetId(), self.OnBrowsePath)
        
        subsizer.Add(wx.StaticText(self, -1, "Doxygen Tool Location : "), (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._doxygenPathCtrl = wx.ComboBox(self, -1, self.GetDoxygenToolPath())
        self._doxygenPathBt = wx.BitmapButton(self, -1, bitmap=wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN))
        subsizer.Add(self._doxygenPathCtrl, (2, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(self._doxygenPathBt, (2, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        wx.EVT_BUTTON(self._doxygenPathBt, self._doxygenPathBt.GetId(), self.OnBrowsePath)
        
        subsizer.Add(wx.StaticText(self, -1, "CHM Tool Location : "), (3, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._chmPathCtrl = wx.TextCtrl(self, -1, self.GetCHMToolPath())
        self._chmPathBt = wx.BitmapButton(self, -1, bitmap=wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN))
        subsizer.Add(self._chmPathCtrl, (3, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(self._chmPathBt, (3, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        wx.EVT_BUTTON(self._chmPathBt, self._chmPathBt.GetId(), self.OnBrowsePath)
        
        subsizer.Add(wx.StaticText(self, -1, "Output Location : "), (4, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._outputPathCtrl = wx.ComboBox(self, -1)
        if packagePath != None:
            path = os.path.dirname(packagePath) + os.sep + "PackageDocument"
            self._outputPathCtrl.SetValue(path)
            self._outputPathCtrl.Disable()
        else:
            list = self.GetConfigure("OutputPath")
            if len(list) != 0:
                for item in list:
                    self._outputPathCtrl.Append(item)
                self._outputPathCtrl.SetValue(list[len(list) - 1])            
        
        subsizer.Add(self._outputPathCtrl, (4, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self._outputPathBt = wx.BitmapButton(self, -1, bitmap=wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN))
        subsizer.Add(self._outputPathBt, (4, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        if packagePath != None:
            self._outputPathBt.Disable()
        wx.EVT_BUTTON(self._outputPathBt, self._outputPathBt.GetId(), self.OnBrowsePath)
        
        subsizer.Add(wx.StaticText(self, -1, "Architecture Specified : "), (5, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._archCtrl = wx.ComboBox(self, -1, value='ALL', choices=['ALL', 'IA32/Microsoft', 'IA32/GCC', 'X64/Microsoft', 'X64/GCC', 'IPF/Microsoft', 'IPF/GCC', 'EBC/Intel'], 
                                     style=wx.CB_READONLY)
        self._archCtrl.Bind(wx.EVT_COMBOBOX, self.OnArchtectureSelectChanged)
        subsizer.Add(self._archCtrl, (5, 1), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sizer.Add(subsizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        sizer.Add(wx.StaticText(self, -1, 'Preprocess Macros: (seperate with blank such as "DEBUG RELEASE")'), 0, wx.EXPAND)
        
        self._macroCtrl = wx.TextCtrl(self, -1, '')
        sizer.Add(self._macroCtrl, 0, wx.EXPAND|wx.TOP, 5)
        self._macroCtrl.Bind(wx.EVT_TEXT, self.OnMacroText)
        self._allMacroCtrl = wx.TextCtrl(self, -1, 'MDE_CPU_IA32 MDE_CPU_X64 MDE_CPU_EBC MDE_CPU_IPF _MSC_EXTENSIONS __GNUC__ __INTEL_COMPILER ASM_PFX= OPTIONAL= ', 
                                           size=(-1, 50), style=wx.BORDER_STATIC|wx.TE_READONLY|wx.TE_MULTILINE)
        sizer.Add(self._allMacroCtrl, 0, wx.EXPAND|wx.TOP, 5)
        
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        self._modesel = wx.RadioBox(self, -1, 'Generated Document Mode', majorDimension=2, choices=['CHM', 'HTML'], style=wx.RA_SPECIFY_COLS)
        self._modesel.SetStringSelection('HTML')
        
        self._includeonlysel = wx.CheckBox(self, -1, 'Only document public include')
        
        sizer6.Add(self._modesel, 0 , wx.EXPAND)
        sizer6.Add(self._includeonlysel, 0, wx.EXPAND|wx.LEFT, 5)
        
        sizer.Add(sizer6, 0, wx.EXPAND|wx.TOP, 5)
        
        self.SetSizer(sizer)
        self.Layout()
        self.SetAutoLayout(True)
               
    def OnArchtectureSelectChanged(self, event):
        str = ''
        selarch = self._archCtrl.GetValue()
        if selarch == 'ALL':
            str += 'MDE_CPU_IA32 MDE_CPU_X64 MDE_CPU_EBC MDE_CPU_IPF _MSC_EXTENSIONS __GNUC__ __INTEL_COMPILER'
        elif selarch == 'IA32/Microsoft':
            str += 'MDE_CPU_IA32 _MSC_EXTENSIONS'
        elif selarch == 'IA32/GCC':
            str += 'MDE_CPU_IA32 __GNUC__'
        elif selarch == 'X64/Microsoft':
            str += 'MDE_CPU_X64 _MSC_EXTENSIONS'
        elif selarch == 'X64/GCC':
            str += 'MDE_CPU_X64 __GNUC__'
        elif selarch == 'IPF/Microsoft':
            str += 'MDE_CPU_IPF _MSC_EXTENSIONS'
        elif selarch == 'IPF/GCC':
            str += 'MDE_CPU_IPF __GNUC__'
        elif selarch == 'EBC/Intel':
            str += 'MDE_CPU_EBC __INTEL_COMPILER'
        
        str += ' ' + self._macroCtrl.GetValue()
        
        str += ' ASM_PFX= OPTIONAL= '
        self._allMacroCtrl.SetValue(str)
        
    def OnMacroText(self, event):
        str = ''
        selarch = self._archCtrl.GetValue()
        if selarch == 'ALL':
            str += 'MDE_CPU_IA32 MDE_CPU_X64 MDE_CPU_EBC MDE_CPU_IPF _MSC_EXTENSIONS __GNUC__ __INTEL_COMPILER'
        elif selarch == 'IA32/Microsoft':
            str += 'MDE_CPU_IA32 _MSC_EXTENSIONS'
        elif selarch == 'IA32/GCC':
            str += 'MDE_CPU_IA32 __GNUC__'
        elif selarch == 'X64/Microsoft':
            str += 'MDE_CPU_X64 _MSC_EXTENSIONS'
        elif selarch == 'X64/GCC':
            str += 'MDE_CPU_X64 __GNUC__'
        elif selarch == 'IPF/Microsoft':
            str += 'MDE_CPU_IPF _MSC_EXTENSIONS'
        elif selarch == 'IPF/GCC':
            str += 'MDE_CPU_IPF __GNUC__'
        elif selarch == 'EBC/Intel':
            str += 'MDE_CPU_EBC __INTEL_COMPILER'

        str += ' ' + self._macroCtrl.GetValue()
        str += ' ASM_PFX= OPTIONAL= '
        self._allMacroCtrl.SetValue(str)
        
    def OnBrowsePath(self, event):
        id       = event.GetId()
        editctrl = None
        
        if id == self._packagePathBt.GetId():
            dlgTitle = "Choose package path:"
            editctrl = self._packagePathCtrl
        elif id == self._workspacePathBt.GetId():
            dlgTitle = "Choose workspace path:"
            editctrl = self._workspacePathCtrl
        elif id == self._doxygenPathBt.GetId():
            dlgTitle = "Choose doxygen installation path:"
            editctrl = self._doxygenPathCtrl
        elif id == self._outputPathBt.GetId():
            dlgTitle = "Choose document output path:"
            editctrl = self._outputPathCtrl
        elif id == self._chmPathBt.GetId():
            dlgTitle = "Choose installation path for Microsoft HTML workshop software"
            editctrl = self._chmPathCtrl
        else:
            return
        
        dlg = wx.DirDialog(self, dlgTitle)
        if dlg.ShowModal() == wx.ID_OK:
            editctrl.SetValue(dlg.GetPath())
        dlg.Destroy()
        
    def GetDoxygenToolPath(self):
        config = wx.ConfigBase_Get()
        path = config.Read("DoxygenToolPath", "")
        if len(path) == 0:
            return "C:\\Program Files\\doxygen"
        return path
    
    def GetCHMToolPath(self):
        config = wx.ConfigBase_Get()
        path = config.Read("CHMToolPath", "")
        if len(path) == 0:
            path = "C:\\Program Files\\HTML Help Workshop"
        return path
        
    def SetDoxygenToolPath(self, path):
        config = wx.ConfigBase_Get()
        config.Write("DoxygenToolPath", path)
        
    def SetCHMToolPath(self, path):
        config = wx.ConfigBase_Get()
        config.Write("CHMToolPath", path)
                
    def GetPackagePath(self):
        return self._packagePathCtrl.GetValue()
        
    def GetDocumentMode(self):
        return self._modesel.GetStringSelection()
        
    def GetIsOnlyDocumentInclude(self):
        return self._includeonlysel.IsChecked()
    
    def GetWorkspacePath(self):
        return self._workspacePathCtrl.GetValue()
        
    def GetDoxygenPath(self):
        return self._doxygenPathCtrl.GetValue()
        
    def GetCHMPath(self):
        return self._chmPathCtrl.GetValue()
    
    def GetOutputPath(self):
        return self._outputPathCtrl.GetValue()
    
    def GetMacros(self):
        return self._macroCtrl.GetValue().split(' ')
    
    def VerifyPage(self):
        pPath = self.GetPackagePath()
        wPath = self.GetWorkspacePath()
        dPath = self.GetDoxygenPath()
        cPath = self.GetCHMPath()
        dbinPath = os.path.join(dPath, 'bin', 'doxygen.exe')
        oPath = self.GetOutputPath()
        
        if len(pPath) == 0 or not os.path.exists(pPath):
            wx.MessageBox("Please input existing package file location!")
            return False
        if len(wPath) == 0 or not os.path.exists(wPath):
            wx.MessageBox("Please input existing workspace path!")
            return False
        if len(dPath) == 0 or not os.path.exists(dPath) or not os.path.exists(dbinPath):
            wx.MessageBox("Can not find doxygen tool under %s! Please download it from www.stack.nl/~dimitri/doxygen/download.html" % dPath)
            return False
        
        if self.GetDocumentMode() == 'CHM' and (len(cPath) == 0 or not os.path.exists(cPath)):
            wx.MessageBox("You select CHM mode to generate document, but can not find software of Microsoft HTML Help Workshop.\nPlease\
 download it from http://www.microsoft.com/downloads/details.aspx?FamilyID=00535334-c8a6-452f-9aa0-d597d16580cc&displaylang=en\n\
and install!")
            return False
        #if len(cPath) == 0 or not os.path.exists(cPath)
        if len(oPath) == 0:
            wx.MessageBox("You must specific document output path")
            return False
            
        self.SetDoxygenToolPath(dPath)
        self.SetCHMToolPath(self.GetCHMPath())
        
        if os.path.exists(oPath):
            return True
        
        self.SaveConfigure('PackagePath', pPath)
        self.SaveConfigure('WorkspacePath', wPath)
        self.SaveConfigure('OutputPath', oPath)
        
        try:
            os.makedirs(oPath)
        except:
            wx.MessageBox("Fail to create output directory, please select another output directory!")
            return False
        return True

    def SaveConfigure(self, name, value):
        config = wx.ConfigBase_Get()
        oldvalues = config.Read(name, '').split(';')
        if len(oldvalues) >= 20:
            oldvalues.remove(oldvalues[0])
        if value not in oldvalues:
            oldvalues.append(value)
        else:
            oldvalues.remove(value)
            oldvalues.append(value)
            
        config.Write(name, ';'.join(oldvalues))
                     
    def GetConfigure(self, name):
        config = wx.ConfigBase_Get()
        return config.Read(name, '').split(';')
    
import core.service as service
class DoxygenGenerateService(service.PISService):
    def __init__(self):
        service.PISService.__init__(self)
        self._isBusy = False
        self._chmPath = None
        self._mode    = None
        self._docOutputPath  = None
        self._arch    = None
        
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Doxygen Generation'
    
    def GetViewClass(self):
        return DoxygenGenerateView

    def Start(self, doxPath, chmPath, outputPath, pObj, mode, arch, tooltag, macros, isOnlyInclude, verbose):
        if self._isBusy:
            wx.MessageBox('Another doxygen process is running! Please try later')
            return
        self.GetView().Clear()
        self._chmPath = chmPath
        self._mode    = mode
        self._docOutputPath  = outputPath
        self._arch    = arch
        
        wx.GetApp().GetTopWindow().PlayTextToasterBox('Start generate package reference document!')
        self.SetTitle("Generating Package document for " + pObj.GetFilename() + "...")
        action = doxygengen.PackageDocumentAction(doxPath, chmPath, outputPath, pObj, mode,
                                                  self.GetView().AddMessage, arch, tooltag, 
                                                  macros, isOnlyInclude, verbose)
        action.RegisterCallbackDoxygenProcess(self.CreateDoxygeProcess)
        wx.GetApp().GetTopWindow().PlayTextToasterBox('[Doxygen Generation] Preprocess and generate doxygen config file...')
        if not action.Generate():
            self._isBusy = False
            self.SetTitle("Error when Generating Package document for " + pObj.GetFilename())
             
    def IsBusy(self):
        return self._isBusy
    
    def CreateDoxygeProcess(self, doxPath, configFile):
        exeFilePath = os.path.join(doxPath, 'bin', 'doxygen.exe')
        if not os.path.exists(exeFilePath):
            wx.MessageBox("Fail to find doxygen.exe file under " + doxPath)
            return False
        
        wx.GetApp().GetTopWindow().PlayTextToasterBox('[Doxygen Generation] Launch doxygen.exe to generate html!')
        cmd = '"%s" %s' % (exeFilePath, configFile)
        try:
            self._process = DoxygenProcess()
            self._process.SetParent(self)
            self._process.Redirect()
            self._pid    = wx.Execute(cmd, wx.EXEC_ASYNC, self._process)
            self._input  = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self.GetView().AddMessage('Fail to launch doxygen cmd %s!' % cmd)
            return False          
        self._inputThread = MonitorThread(self._input, self.MonitorThreadCallback)
        self._errorThread = MonitorThread(self._error, self.MonitorThreadCallback)
        self._inputThread.start()  
        self._errorThread.start()
        return True
    
    def MonitorThreadCallback(self, message):
        view = self.GetView()
        if view != None:
            view.AddMessage(message)
      
    def OnTerminateDoxygenProcess(self):
        if self._inputThread:
            self._inputThread.Terminate()
            self._inputThread = None
        if self._errorThread:
            self._errorThread.Terminate()
            self._errorThread = None

        view = self.GetView()
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
        
        self.DocumentFixup()
        
        if self._mode.lower() == 'chm':
            hhpfile = os.path.join(self._docOutputPath, 'html', 'index.hhp')
            #if os.path.exists(hhpfile):
            #    wx.MessageBox("Fail to create CHM file for %s does not exist!" % hhpfile)
            #    self.SetTitle("Error when Generating Package document!")
            #    self._isBusy = False
            #    return
            if not self.CreateCHMProcess(self._chmPath, hhpfile):
                wx.MessageBox("Fail to Create %s process for %s" % (self._chmPath, hhpfile))
                self.SetTitle("Error when Generating Package document!")
                self._isBusy = False
        else:
            self._isBusy = False
            indexpath = os.path.realpath(os.path.join(self._docOutputPath, 'html', 'index.html'))
            self.GetView().AddMessage('\nSuccess create HTML doxgen document %s\n' % indexpath)
            wx.GetApp().GetTopWindow().PlayTextToasterBox('[Doxygen Generation] Finished!')
            self.SetTitle('Success create HTML doxgen document %s' % indexpath)
            wx.MessageBox('Success create HTML doxgen document %s' % indexpath)
            if os.path.exists(indexpath):
                docMgr = wx.GetApp().GetDocumentManager()
                docMgr.CreateDocument(indexpath, wx.lib.docview.DOC_SILENT)
            
            
    def CreateCHMProcess(self, chmPath, hhpfile):
        exeFilePath = os.path.join(chmPath, 'hhc.exe')
        if not os.path.exists(exeFilePath):
            wx.MessageBox("Fail to find hhp.exe file under " + chmPath)
            return False
        
        wx.GetApp().GetTopWindow().PlayTextToasterBox('[Doxygen Generation] Launch hhc.exe to generate CHM!')
        self.GetView().AddMessage("    >>>>>> Start Microsoft HTML workshop process...Zzz...\n")
        cmd = '"%s" %s' % (exeFilePath, hhpfile)
        try:
            self._process = CHMProcess()
            self._process.SetParent(self)
            self._process.Redirect()
            self._pid    = wx.Execute(cmd, wx.EXEC_ASYNC, self._process)
            self._input  = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self.GetView().AddMessage('\nFail to launch hhp cmd %s!\n' % cmd)
            return False          
        self._inputThread = MonitorThread(self._input, self.MonitorThreadCallback)
        self._errorThread = MonitorThread(self._error, self.MonitorThreadCallback)
        self._inputThread.start()  
        self._errorThread.start()    
        return True
        
    def OnTerminateCHMProcess(self):
        if self._inputThread:
            self._inputThread.Terminate()
            self._inputThread = None
        if self._errorThread:
            self._errorThread.Terminate()
            self._errorThread = None

        view = self.GetView()
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
        self._isBusy  = False
        indexpath = os.path.realpath(os.path.join(self._docOutputPath, 'html', 'index.chm'))
        self.GetView().AddMessage('\nSuccess create CHM doxgen document %s\n' % indexpath)
        wx.GetApp().GetTopWindow().PlayTextToasterBox('[Doxygen Generation] Finished!')
        self.SetTitle('Success create CHM doxgen document %s' % indexpath)
        wx.MessageBox('Success create CHM doxgen document %s' % indexpath)
        if os.path.exists(indexpath):
            os.startfile(indexpath)
        
    def OnCloseFrame(self, event):
        if self._process == None:
            return
        if self._pid == None:
            return
        if self._inputThread:
            self._inputThread.Terminate()  
        if self._errorThread:
            self._errorThread.Terminate()   
                                  
        wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)  
        return core.service.PISService.OnCloseFrame(self, event)
        
    def DocumentFixup(self):
        # find BASE_LIBRARY_JUMP_BUFFER structure reference page
        self.GetView().AddMessage('\n    >>> Start fixup document \n')
        
        for root, dirs, files in os.walk(self._docOutputPath):
            for dir in dirs:
                if dir.lower() in ['.svn', '_svn', 'cvs']:
                    dirs.remove(dir)
            for file in files:
                wx.YieldIfNeeded()
                if not file.lower().endswith('.html'): continue
                fullpath = os.path.join(self._docOutputPath, root, file)
                try:
                    f = open(fullpath, 'r')
                    text = f.read()
                    f.close()
                except:
                    self.GetView().AddMessage('\nFail to open file %s\n' % fullpath)
                    continue
                if text.find('BASE_LIBRARY_JUMP_BUFFER Struct Reference') != -1 and self._arch == 'ALL':
                    self.FixPageBASE_LIBRARY_JUMP_BUFFER(fullpath, text)
                if text.find('MdePkg/Include/Library/BaseLib.h File Reference') != -1  and self._arch == 'ALL':
                    self.FixPageBaseLib(fullpath, text)
                if text.find('IA32_IDT_GATE_DESCRIPTOR Union Reference') != -1  and self._arch == 'ALL':
                    self.FixPageIA32_IDT_GATE_DESCRIPTOR(fullpath, text)
                if text.find('MdePkg/Include/Library/UefiDriverEntryPoint.h File Reference') != -1:
                    self.FixPageUefiDriverEntryPoint(fullpath, text)
                if text.find('MdePkg/Include/Library/UefiApplicationEntryPoint.h File Reference') != -1:
                    self.FixPageUefiApplicationEntryPoint(fullpath, text)
                    
        self.GetView().AddMessage('    >>> Finish all document fixing up! \n')\
        
    def FixPageBaseLib(self, path, text):
        self.GetView().AddMessage('    >>> Fixup BaseLib file page at file %s \n' % path)
        lines = text.split('\n')
        lastBaseJumpIndex = -1
        lastIdtGateDescriptor = -1
        for index in range(len(lines) - 1, -1, -1):
            line = lines[index]
            if line.strip() == '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;4          </td>':
                lines[index] = '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;4&nbsp;[IA32]    </td>'
            if line.strip() == '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;0x10          </td>':
                lines[index] = '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;0x10&nbsp;[IPF]   </td>'
            if line.strip() == '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;8          </td>':
                lines[index] = '<td class="memname">#define BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT&nbsp;&nbsp;&nbsp;9&nbsp;[EBC, x64]   </td>'
            if line.find('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;4') != -1:
                lines[index] = lines[index].replace('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;4',
                                     'BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;4&nbsp;[IA32]')
            if line.find('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;0x10') != -1:
                lines[index] = lines[index].replace('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;0x10',
                                     'BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;0x10&nbsp;[IPF]')
            if line.find('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;8') != -1:
                lines[index] = lines[index].replace('BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;8',
                                     'BASE_LIBRARY_JUMP_BUFFER_ALIGNMENT</a>&nbsp;&nbsp;&nbsp;8&nbsp;[x64, EBC]')
            if line.find('>BASE_LIBRARY_JUMP_BUFFER</a>') != -1:
                if lastBaseJumpIndex != -1:
                    del lines[lastBaseJumpIndex]
                lastBaseJumpIndex = index
            if line.find('>IA32_IDT_GATE_DESCRIPTOR</a></td>') != -1:
                if lastIdtGateDescriptor != -1:
                    del lines[lastIdtGateDescriptor]
                lastIdtGateDescriptor = index
        try:
            f = open(path, 'w')
            f.write('\n'.join(lines))
            f.close()
        except:
            self.GetView().AddMessage("     <<< Fail to fixup file %s\n" % path)
        self.GetView().AddMessage("    <<< Finish to fixup file %s\n" % path)
               
    def FixPageIA32_IDT_GATE_DESCRIPTOR(self, path, text):
        self.GetView().AddMessage('    >>> Fixup structure reference IA32_IDT_GATE_DESCRIPTOR at file %s \n' % path)
        lines = text.split('\n')
        for index in range(len(lines) - 1, -1, -1):
            line = lines[index].strip()
            if line.find('struct {</td>') != -1 and lines[index - 2].find('>Uint64</a></td>') != -1:
                lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For X64</h2></td></tr>')
            if line.find('struct {</td>') != -1 and lines[index - 1].find('Data Fields') != -1:
                lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For IA32</h2></td></tr>')
        try:
            f = open(path, 'w')
            f.write('\n'.join(lines))
            f.close()
        except:
            self.GetView().AddMessage("     <<< Fail to fixup file %s\n" % path)                
        self.GetView().AddMessage("    <<< Finish to fixup file %s\n" % path)
        
    def FixPageBASE_LIBRARY_JUMP_BUFFER(self, path, text):
        self.GetView().AddMessage('    >>> Fixup structure reference BASE_LIBRARY_JUMP_BUFFER at file %s \n' % path)
        lines = text.split('\n')
        bInDetail = True
        bNeedRemove = False
        for index in range(len(lines) - 1, -1, -1):
            line = lines[index]
            if line.find('Detailed Description') != -1:
                bInDetail = False
            if line.startswith('EBC context buffer used by') and lines[index - 1].startswith('x64 context buffer'):
                lines[index] = "IA32/IPF/X64/" + line
                bNeedRemove  = True
            if line.startswith("x64 context buffer") or line.startswith('IPF context buffer used by') or \
               line.startswith('IA32 context buffer used by'):
                if bNeedRemove:
                    lines.remove(line)        
            if line.find('>R0</a>') != -1 and not bInDetail:
                if lines[index - 1] != '<tr><td colspan="2"><br><h2>Data Fields For EBC</h2></td></tr>':
                    lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For EBC</h2></td></tr>')
            if line.find('>Rbx</a>') != -1 and not bInDetail:
                if lines[index - 1] != '<tr><td colspan="2"><br><h2>Data Fields For X64</h2></td></tr>':
                    lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For X64</h2></td></tr>')
            if line.find('>F2</a>') != -1 and not bInDetail:
                if lines[index - 1] != '<tr><td colspan="2"><br><h2>Data Fields For IPF</h2></td></tr>':
                    lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For IPF</h2></td></tr>')
            if line.find('>Ebx</a>') != -1 and not bInDetail:
                if lines[index - 1] != '<tr><td colspan="2"><br><h2>Data Fields For IA32</h2></td></tr>':
                    lines.insert(index, '<tr><td colspan="2"><br><h2>Data Fields For IA32</h2></td></tr>')
        try:
            f = open(path, 'w')
            f.write('\n'.join(lines))
            f.close()
        except:
            self.GetView().AddMessage("     <<< Fail to fixup file %s" % path)
        self.GetView().AddMessage("    <<< Finish to fixup file %s\n" % path)
        
    def FixPageUefiDriverEntryPoint(self, path, text):
        self.GetView().AddMessage('    >>> Fixup file reference MdePkg/Include/Library/UefiDriverEntryPoint.h at file %s \n' % path)
        lines = text.split('\n')
        bInModuleEntry = False
        bInEfiMain     = False
        ModuleEntryDlCount  = 0  
        ModuleEntryDelStart = 0 
        ModuleEntryDelEnd   = 0  
        EfiMainDlCount      = 0
        EfiMainDelStart     = 0
        EfiMainDelEnd       = 0
           
        for index in range(len(lines)):
            line = lines[index].strip()
            if line.find('EFI_STATUS</a> EFIAPI _ModuleEntryPoint           </td>') != -1:
                bInModuleEntry = True
            if line.find('EFI_STATUS</a> EFIAPI EfiMain           </td>') != -1:
                bInEfiMain = True
            if line.startswith('<p>References <a'):
                if bInModuleEntry:
                    ModuleEntryDelEnd = index - 1
                    bInModuleEntry = False
                elif bInEfiMain:
                    EfiMainDelEnd = index - 1
                    bInEfiMain = False
            if bInModuleEntry:
                if line.startswith('</dl>'):
                    ModuleEntryDlCount = ModuleEntryDlCount + 1
                if ModuleEntryDlCount == 1:
                    ModuleEntryDelStart = index + 1
            if bInEfiMain:
                if line.startswith('</dl>'):
                    EfiMainDlCount = EfiMainDlCount + 1
                if EfiMainDlCount == 1:
                    EfiMainDelStart = index + 1
        
        if EfiMainDelEnd > EfiMainDelStart:
            for index in range(EfiMainDelEnd, EfiMainDelStart, -1):
                del lines[index]
        if ModuleEntryDelEnd > ModuleEntryDelStart:
            for index in range(ModuleEntryDelEnd, ModuleEntryDelStart, -1):
                del lines[index]
                
        try:
            f = open(path, 'w')
            f.write('\n'.join(lines))
            f.close()
        except:
            self.GetView().AddMessage("     <<< Fail to fixup file %s" % path)
        self.GetView().AddMessage("    <<< Finish to fixup file %s\n" % path)                

    def FixPageUefiApplicationEntryPoint(self, path, text):
        self.GetView().AddMessage('    >>> Fixup file reference MdePkg/Include/Library/UefiApplicationEntryPoint.h at file %s \n' % path)
        lines = text.split('\n')
        bInModuleEntry = False
        bInEfiMain     = False
        ModuleEntryDlCount  = 0  
        ModuleEntryDelStart = 0 
        ModuleEntryDelEnd   = 0  
        EfiMainDlCount      = 0
        EfiMainDelStart     = 0
        EfiMainDelEnd       = 0
           
        for index in range(len(lines)):
            line = lines[index].strip()
            if line.find('EFI_STATUS</a> EFIAPI _ModuleEntryPoint           </td>') != -1:
                bInModuleEntry = True
            if line.find('EFI_STATUS</a> EFIAPI EfiMain           </td>') != -1:
                bInEfiMain = True
            if line.startswith('<p>References <a'):
                if bInModuleEntry:
                    ModuleEntryDelEnd = index - 1
                    bInModuleEntry = False
                elif bInEfiMain:
                    EfiMainDelEnd = index - 1
                    bInEfiMain = False
            if bInModuleEntry:
                if line.startswith('</dl>'):
                    ModuleEntryDlCount = ModuleEntryDlCount + 1
                if ModuleEntryDlCount == 1:
                    ModuleEntryDelStart = index + 1
            if bInEfiMain:
                if line.startswith('</dl>'):
                    EfiMainDlCount = EfiMainDlCount + 1
                if EfiMainDlCount == 1:
                    EfiMainDelStart = index + 1
        
        if EfiMainDelEnd > EfiMainDelStart:
            for index in range(EfiMainDelEnd, EfiMainDelStart, -1):
                del lines[index]
        if ModuleEntryDelEnd > ModuleEntryDelStart:
            for index in range(ModuleEntryDelEnd, ModuleEntryDelStart, -1):
                del lines[index]
                
        try:
            f = open(path, 'w')
            f.write('\n'.join(lines))
            f.close()
        except:
            self.GetView().AddMessage("     <<< Fail to fixup file %s" % path)
        self.GetView().AddMessage("    <<< Finish to fixup file %s\n" % path)                
    
import ui.MessageWindow    
class DoxygenGenerateView(service.PISServiceView):
    def __init__(self, parent, serv):
        service.PISServiceView.__init__(self, parent, serv)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._output = ui.MessageWindow.MessageWindow(self, -1)
        self._output.SetReadOnly(True)
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
            if len(text.strip()) != 0:
                wx.GetApp().ForegroundProcess(self._callback, (text,))
        
    def Terminate(self):
        self._pipe.flush()
        self._isCancel = True
        
class DoxygenProcess(wx.Process):
    def OnTerminate(self, id, status):                   
        self._parent.OnTerminateDoxygenProcess()
        
    def SetParent(self, parent):
        self._parent = parent
            
class CHMProcess(wx.Process):
    def OnTerminate(self, id, status):
        self._parent.OnTerminateCHMProcess()
        
    def SetParent(self, parent):
        self._parent = parent
                        
def IsCHeaderFile(path):
    return CheckPathPostfix(path, 'h')   
    
def CheckPathPostfix(path, str):
    index = path.rfind('.')
    if index == -1:
        return False
    if path[index + 1:].lower() == str.lower():
        return True
    return False         