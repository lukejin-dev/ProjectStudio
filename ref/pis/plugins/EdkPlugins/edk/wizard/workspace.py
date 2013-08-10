import os
import wx
import plugins.EdkPlugins.util.wizard
import wx.wizard

class EDKNewProject(plugins.EdkPlugins.util.wizard.EDKWizard):
    def __init__(self, parent, id, title="Create New EDK Project", pos=(-1,-1)):
        plugins.EdkPlugins.util.wizard.EDKWizard.__init__(self, parent, id, title, pos)
        self.SetPageSize((450, 200))
        self._locationPage = EDKLocationPage(self)
        
        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnWizardFinished)
        self.CenterOnParent()        
        
    def RunWizard(self):
        return wx.wizard.Wizard.RunWizard(self, self._locationPage)
        
    def OnPageChanging(self, event):
        page = event.GetPage()
        
        if hasattr(page, "VerifyPage"):
            if not page.VerifyPage():
                event.Veto()
                return
                
        dir  = event.GetDirection()
        if isinstance(page, EDKLocationPage) and dir:
            next = page.GetNext()
            next.RefreshPlatforms(page.GetProjectLocation())
            
    def OnPageChanged(self, event):
        pass
        
    def OnWizardFinished(self, event):
        pass
        
    def GetPlatforms(self):
        if not hasattr(self, '_platformPage'):
            return None
        return self._platformPage.GetPlatforms()
        
    def GetProjectLocation(self):
        return self._locationPage.GetProjectLocation()
        
    def GetEdkSourcePath(self):
        return self._locationPage.GetEdkSourcePath()
        
    def GetProjectName(self):
        return self._locationPage.GetProjectName()
        
    def GetEdkToolsPath(self):
        return self._locationPage.GetToolLocation()
        
class EDKLocationPage(wx.wizard.WizardPageSimple):
    
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)      
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        namesizer = wx.BoxSizer(wx.HORIZONTAL)
        namesizer.Add(wx.StaticText(self, -1, "Project Name :    "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._namectrl = wx.TextCtrl(self, -1)
        namesizer.Add(self._namectrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(namesizer, 0, wx.EXPAND|wx.TOP, 20)
        
        pathsizer = wx.BoxSizer(wx.HORIZONTAL)
        pathsizer.Add(wx.StaticText(self, -1, "Location :            "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._pathctrl = wx.ComboBox(self, -1)
        pathsizer.Add(self._pathctrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self._pathbt = wx.Button(self, -1, "...", size=(20,20), style=wx.NO_BORDER)
        pathsizer.Add(self._pathbt, 0, wx.LEFT, 4)
        sizer.Add(pathsizer, 0, wx.EXPAND|wx.TOP, 20)
        
        efisourcesizer = wx.BoxSizer(wx.HORIZONTAL)
        efisourcesizer.Add(wx.StaticText(self, -1, "EFI_SOURCE :    "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._efisourcectrl = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        efisourcesizer.Add(self._efisourcectrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(efisourcesizer, 0, wx.EXPAND|wx.TOP, 20)
        
        edksourcesizer = wx.BoxSizer(wx.HORIZONTAL)
        edksourcesizer.Add(wx.StaticText(self, -1, "EDK_SOURCE :   "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._edksourcectrl = wx.ComboBox(self, -1)
        edksourcesizer.Add(self._edksourcectrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self._edksourcebt = wx.Button(self, -1, "...", size=(20,20), style=wx.NO_BORDER)
        edksourcesizer.Add(self._edksourcebt, 0, wx.LEFT, 4)
        sizer.Add(edksourcesizer, 0, wx.EXPAND|wx.TOP, 20)
                                
        toolsizer = wx.BoxSizer(wx.HORIZONTAL)
        toolsizer.Add(wx.StaticText(self, -1, "EDK Tool Path :   "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._toolctrl = wx.ComboBox(self, -1)
        toolsizer.Add(self._toolctrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self._toolbt = wx.Button(self, -1, "...", size=(20,20), style=wx.NO_BORDER)
        toolsizer.Add(self._toolbt, 0, wx.LEFT, 4)
        sizer.Add(toolsizer, 0, wx.EXPAND|wx.TOP, 20)
        
        self.SetSizer(sizer)
        self.Layout()
        self.SetAutoLayout(True)
        
        parent._platformPage = EDKPlatformPage(parent)
        self.SetNext(parent._platformPage)
        self.GetNext().SetPrev(self)
        config = wx.ConfigBase_Get()
        histories = config.Read("EdkProjectLocationHistory", "")
        if len(histories) != 0:
            arr = histories.split(";")
            for item in arr:
                self._pathctrl.Append(item)
                
        histories = config.Read("EdkToolsLocationHistory", "")
        if len(histories) != 0:
            arr = histories.split(";")
            for item in arr:
                self._toolctrl.Append(item)                
                        
        wx.EVT_BUTTON(self._pathbt, self._pathbt.GetId(), self.OnBrowserProjectLocation)
        wx.EVT_BUTTON(self._toolbt, self._toolbt.GetId(), self.OnBrowserEdkToolsLocation)
        wx.EVT_TEXT(self._pathctrl, self._pathctrl.GetId(), self.OnLocationChanged)
        
        # Add sample input for testing
        self._namectrl.SetValue('Test')
        self._pathctrl.SetValue('M:\\tree\\Framework_20080530')
        self._toolctrl.SetValue('C:\\TianoTools')
        
    def OnBrowserProjectLocation(self, event):
        dlg = wx.DirDialog(self, "Choose Project Location")
        if dlg.ShowModal() == wx.ID_OK:
            self._pathctrl.SetValue(dlg.GetPath())
            
        dlg.Destroy()
        
    def OnBrowserEdkToolsLocation(self, event):
        dlg = wx.DirDialog(self, "Choose EDK Tools Location")
        if dlg.ShowModal() == wx.ID_OK:
            self._toolctrl.SetValue(dlg.GetPath())
            
        dlg.Destroy()
        
    def OnLocationChanged(self, event):
        self._efisourcectrl.SetValue(self._pathctrl.GetValue())
        self._edksourcectrl.SetValue(self._pathctrl.GetValue() + os.sep + 'edk')
        
    def GetProjectLocation(self):
        return self._pathctrl.GetValue()
        
    def GetProjectName(self):
        return self._namectrl.GetValue()
        
    def GetToolLocation(self):
        return self._toolctrl.GetValue()
        
    def GetEdkSourcePath(self):
        return self._edksourcectrl.GetValue()
        
    def VerifyPage(self):
        pPath = self.GetProjectLocation()
        tPath = self.GetToolLocation()
        name  = self.GetProjectName()
        if len(pPath) == 0:
            wx.MessageBox("Please input project location!")
            return False
        if len(tPath) == 0:
            wx.MessageBox("Please input EDK tool location!")
            return False
        if len(name) == 0:
            wx.MessageBox("Please input project name!")
            return False
        if not os.path.exists(pPath):
            wx.MessageBox("Project location does not exist!")
            return False
        if not os.path.exists(tPath):
            wx.MessageBox("EDK tool location does not exist!")
            return False            
            
        config = wx.ConfigBase_Get()
        histories = config.Read("EdkProjectLocationHistory", "")

        if len(histories) == 0:
            histories = pPath
            arr = [pPath]
        else:
            arr = histories.split(';')
            if pPath not in arr:
                arr.append(pPath)
            
        config.Write("EdkProjectLocationHistory", ";".join(arr))
        
        histories = config.Read("EdkToolsLocationHistory", "")

        if len(histories) == 0:
            histories = tPath
            arr = [tPath]
        else:
            arr = histories.split(';')
            if tPath not in arr:
                arr.append(tPath)
            
        config.Write("EdkToolsLocationHistory", ";".join(arr))        
        return True
        
class EDKPlatformPage(wx.wizard.WizardPageSimple):
    
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(wx.StaticText(self, -1, "Please select platforms:"), 0, wx.TOP, 5)
        
        self._platformctrl = wx.CheckListBox(self, -1, style=wx.HSCROLL)
        sizer.Add(self._platformctrl, 1, wx.EXPAND|wx.TOP, 10)
        
        self.SetSizer(sizer)
        self.Layout()
        self.SetAutoLayout(True)
        
    def GetPlatforms(self):
        p = []
        count = self._platformctrl.GetCount()
        for index in range(count):
            if self._platformctrl.IsChecked(index):
                str = self._platformctrl.GetString(index)
                name, path = str.split("(")
                path = path.split(")")[0]
                fullPath = os.path.join(path, name.rstrip())
                p.append(fullPath[len(self.GetParent().GetProjectLocation()) + 1:])
        return p
        
    def RefreshPlatforms(self, path):
        self._platformctrl.Clear()
        if not os.path.exists(path): return
        
        pd = wx.ProgressDialog("Search platform file under %s ..." % path, 
                               "Search platform under %s ..." % path, 
                               1, 
                               wx.GetApp().GetTopWindow(),
                               wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if dir.lower() in ['cvs', '.svn', '_svn']:
                    dirs.remove(dir)
                if dir.lower() == 'build':
                    dirs.remove(dir)
                    buildpath = os.path.join(root, dir)
                    tfiles    = os.listdir(buildpath)
                    for t in tfiles:
                        tfile = os.path.join(buildpath, t)
                        if not os.path.isfile(tfile): continue
                        (name, ext) = os.path.splitext(tfile)
                        if ext == '.dsc':
                            index = self._platformctrl.Append("%s (%s)" % (t, buildpath))

            pd.Pulse("Searching %s ..." % os.path.join(root, dir))
            for file in files:
                tfile = os.path.join(root, file)
                (name, ext) = os.path.splitext(tfile)
                if ext == '.dsc':
                    index = self._platformctrl.Append("%s (%s)" % (file, root))

        pd.Destroy()