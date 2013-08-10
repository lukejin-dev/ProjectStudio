import plugins.EdkPlugins.util.wizard
import wx
import os, sys

class EDK2NewProject(plugins.EdkPlugins.util.wizard.EDKWizard):
    def __init__(self, parent, id, title="Create New EDKII Project", pos=(-1,-1)):
        plugins.EdkPlugins.util.wizard.EDKWizard.__init__(self, parent, id, title, pos)
        self.SetPageSize((450, 200))
        self._locationPage = EDKIILocationPage(self)
        
        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.OnWizardFinished)
        
    def RunWizard(self):
        return wx.wizard.Wizard.RunWizard(self, self._locationPage)
    
    def OnPageChanging(self, event):
        page = event.GetPage()
        
        if hasattr(page, "VerifyPage"):
            if not page.VerifyPage():
                event.Veto()
                return
                
        dir  = event.GetDirection()

        if isinstance(page, EDKIIGetPackagesPage) and dir:
            page.DownloadPackages(self.CallbackFinishDownload)

    def CallbackFinishDownload(self):
        self._selectPlatformPage.RefreshPlatforms(self.GetProjectLocation())
        
    def GetProjectLocation(self):
        return self._locationPage.GetProjectLocation()
        
    def GetProjectName(self):
        return self._locationPage.GetProjectName()
        
    def GetToolConfigFilePath(self):
        return self._locationPage.GetToolLocation()
        
    def GetPlatforms(self):
        return self._selectPlatformPage.GetPlatforms()
        
    def OnWizardFinished(self, event):
        self._packageGetPage._timer.Stop()
        del self._packageGetPage._timer
        
class EDKIILocationPage(wx.wizard.WizardPageSimple):
    
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)      
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        namesizer = wx.BoxSizer(wx.HORIZONTAL)
        namesizer.Add(wx.StaticText(self, -1, "Project Name :    "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._namectrl = wx.TextCtrl(self, -1)
        namesizer.Add(self._namectrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(namesizer, 0, wx.EXPAND|wx.TOP, 40)
        
        pathsizer = wx.BoxSizer(wx.HORIZONTAL)
        pathsizer.Add(wx.StaticText(self, -1, "Location :            "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._pathctrl = wx.ComboBox(self, -1)
        pathsizer.Add(self._pathctrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self._pathbt = wx.Button(self, -1, "...", size=(20,20), style=wx.NO_BORDER)
        pathsizer.Add(self._pathbt, 0, wx.LEFT, 4)
        sizer.Add(pathsizer, 0, wx.EXPAND|wx.TOP, 30)
        
        toolsizer = wx.BoxSizer(wx.HORIZONTAL)
        toolsizer.Add(wx.StaticText(self, -1, "Tool Config File :  "), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self._toolctrl = wx.ComboBox(self, -1)
        toolsizer.Add(self._toolctrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self._toolbt = wx.Button(self, -1, "...", size=(20,20), style=wx.NO_BORDER)
        toolsizer.Add(self._toolbt, 0, wx.LEFT, 4)
        sizer.Add(toolsizer, 0, wx.EXPAND|wx.TOP, 30)
        
        self.SetSizer(sizer)
        self.Layout()
        self.SetAutoLayout(True)

        
        parent._packageGetPage = EDKIIGetPackagesPage(parent)
        self.SetNext(parent._packageGetPage)
        self.GetNext().SetPrev(self)
        
        config = wx.ConfigBase_Get()
        histories = config.Read("EdkIIProjectLocationHistory", "")
        if len(histories) != 0:
            arr = histories.split(";")
            for item in arr:
                self._pathctrl.Append(item)
            self._pathctrl.SetValue(arr[len(arr) - 1])
                
        histories = config.Read("EdkIIToolsLocationHistory", "")
        if len(histories) != 0:
            arr = histories.split(";")
            for item in arr:
                self._toolctrl.Append(item)  
        path = self._pathctrl.GetValue()     
        if len(path) != 0:
            self._toolctrl.SetValue(os.path.join(path, "Conf", "tools_def.txt"))         
                        
        wx.EVT_BUTTON(self._pathbt, self._pathbt.GetId(), self.OnBrowserProjectLocation)
        wx.EVT_BUTTON(self._toolbt, self._toolbt.GetId(), self.OnBrowserToolsLocation)
        wx.EVT_TEXT(self._pathctrl, self._pathctrl.GetId(), self.OnLocationChanged)
        
    def OnBrowserProjectLocation(self, event):
        dlg = wx.DirDialog(self, "Choose Project Location")
        if dlg.ShowModal() == wx.ID_OK:
            self._pathctrl.SetValue(dlg.GetPath())
            self._toolctrl.SetValue(dlg.GetPath() + os.sep + 'Conf' + os.sep + 'tools_def.txt')
        dlg.Destroy()
        
    def OnBrowserToolsLocation(self, event):
        dlg = wx.FileDialog(self, "Choose EDK Tools Location", wildcard="Tool DEF File (tools_def.txt)|tools_def.txt")
        if dlg.ShowModal() == wx.ID_OK:
            self._toolctrl.SetValue(dlg.GetPath())
            
        dlg.Destroy()
        
    def OnLocationChanged(self, event):
        self._toolctrl.SetValue(self._pathctrl.GetValue())
        self._toolctrl.SetValue(self._pathctrl.GetValue() + os.sep + 'Conf' + os.sep + 'tools_def.txt')
        
    def GetProjectLocation(self):
        return self._pathctrl.GetValue()
        
    def GetProjectName(self):
        return self._namectrl.GetValue()
        
    def GetToolLocation(self):
        path = self._toolctrl.GetValue()
        path = path[len(self._pathctrl.GetValue()) + 1:]
        return path
        
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
            
        
        config = wx.ConfigBase_Get()
        histories = config.Read("EdkIIProjectLocationHistory", "")

        if len(histories) == 0:
            histories = pPath
            arr = [pPath]
        else:
            arr = histories.split(';')
            if pPath not in arr:
                arr.append(pPath)
            
        config.Write("EdkIIProjectLocationHistory", ";".join(arr))
        
        histories = config.Read("EdkIIToolsLocationHistory", "")

        if len(histories) == 0:
            histories = tPath
            arr = [tPath]
        else:
            arr = histories.split(';')
            if tPath not in arr:
                arr.append(tPath)
            
        config.Write("EdkIIToolsLocationHistory", ";".join(arr))
        
        return True    

class EDKIIGetPackagesPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        self._svnservice = None
        self._pd         = None
        self.Freeze()
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(wx.StaticText(self, -1, "Import packages from SVN repository to workspace:"), 0, wx.EXPAND|wx.TOP, 20)
        
        addrsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._addr = wx.ComboBox(self, -1)
        addrsizer.Add(self._addr, 1, wx.EXPAND|wx.LEFT, 2)
        self._addbt = wx.Button(self, -1, "+", size=(20, 20))
        self._delbt = wx.Button(self, -1, "-", size=(20, 20))
        addrsizer.Add(self._addbt, 0, wx.LEFT, 2)
        addrsizer.Add(self._delbt, 0, wx.LEFT, 2)
        sizer.Add(addrsizer, 0, wx.EXPAND|wx.TOP, 10)
        
        self._list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.LC_SORT_ASCENDING)
        sizer.Add(self._list, 1, wx.EXPAND|wx.TOP, 20)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Thaw()

        wx.EVT_BUTTON(self._addbt, self._addbt.GetId(), self.OnAddPath)
        wx.EVT_BUTTON(self._delbt, self._delbt.GetId(), self.OnDelPath)
        
        self._list.InsertColumn(0, "URL")
        self._list.InsertColumn(1, "Local Directory")
        self._list.SetColumnWidth(0, 300)
        self._list.SetColumnWidth(1, 100)
        
        # Get history to fill the combox
        config = wx.ConfigBase_Get()
        histories = config.Read("EDKIIPackageSVNPaths", "")
        if len(histories) != 0:
            arr = histories.split(";")
            for item in arr:
                if len(item) == 0: continue
                self._addr.Append(item)
        
        parent._selectPlatformPage = EdkIISelectExsitingPlatformPage(parent)
        self.SetNext(parent._selectPlatformPage)
        self.GetNext().SetPrev(self)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self._timer.Start(1000)
        self._curr = 0
        self._curr_str = None
         
    def OnAddPath(self, event):
        value = self._addr.GetValue()
        if len(value) == 0: return

        for visit in range(self._list.GetItemCount()):
            if self._list.GetItemText(visit) == value:
                wx.MessageBox("%s value has been exist in path list!" % value)
                return
        
        index = self._list.InsertStringItem(sys.maxint, value)
        self._list.SetStringItem(index, 1, value[value.rfind("/") + 1:])
        config = wx.ConfigBase_Get()
        histories = config.Read("EDKIIPackageSVNPaths", "")
        if len(histories) != 0:
            arr = histories.split(";")
            if value not in arr:
                arr.append(value)
        else:
            arr = [value]
        config.Write("EDKIIPackageSVNPaths", ";".join(arr))
                
    def OnDelPath(self, event):
        del_indexes = []
        if self._list.GetItemCount() == 0: return
        sel = self._list.GetFirstSelected()
        while (sel != -1):
            del_indexes.append(sel)
            sel = self._list.GetNextSelected(sel)
        
        visit = len(del_indexes) - 1
        while (visit >= 0):
            print del_indexes[visit]
            self._list.DeleteItem(del_indexes[visit])
            visit -= 1
        
    def GetSvnService(self):
        if not hasattr(self, "_svnservice") or self._svnservice == None:
            pm = wx.GetApp().GetPluginMgr()
            p  = pm.GetPlugin('SvnPlugin')
            if p != None:
                self._svnservice = pm.GetPlugin('SvnPlugin').GetServiceInstance()
            else:
                self._svnservice = None
        
        return self._svnservice
                
    def DownloadPackages(self, callback):
        self._svnservice = self.GetSvnService()
        if self._svnservice == None: 
            callback()
            return
        
        self._svnservice.GetView().Activate()
        if self._list.GetItemCount() == 0:
            callback()
            return
            
        self._pd = wx.ProgressDialog("Download Packages from remote SVN repository",
                                     "Download Packages from remote SVN repository",
                                     self._list.GetItemCount() + 1,
                                     style=wx.PD_ELAPSED_TIME|wx.PD_APP_MODAL)
        str = "Checking out %s" % self._list.GetItemText(0)
        self._curr = 1
        self._curr_str = str
        self._pd.SetSize((len(str) * 7, 140))
        self._pd.Update(1, str)
        self._pd.CenterOnParent()
         
        for visit in range(self._list.GetItemCount()):
            url = self._list.GetItemText(visit)
            path = url[url.rfind("/") + 1:]
            path = os.path.join(self.GetParent().GetProjectLocation(), path)
            self._svnservice.SvnCheckoutURL(url, path, self.CheckoutCallback, (visit + 1, self._list.GetItemCount(), callback))
            
    def CheckoutCallback(self, visit, max, callback):
        if self._pd == None: return
        if visit == self._list.GetItemCount():
            self._pd.Destroy()
            self._pd = None
            callback()
            return
            
        str = "Checking out %s" % self._list.GetItemText(visit)        
        self._curr = visit + 1
        self._curr_str = str
        self._pd.SetSize((len(str) * 7, 120))
        self._pd.Update(visit + 1, "Checking out %s" % self._list.GetItemText(visit))
        self._pd.CenterOnParent()
        
    def OnTimer(self, event):
        if self._pd == None:
            return

        self._pd.Update(self._curr, self._curr_str)
        
class EdkIISelectExsitingPlatformPage(wx.wizard.WizardPageSimple):
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
        print 'refresh platform under %s' % path
        self._platformctrl.Clear()
        if not os.path.exists(path): return
        
        pd = wx.ProgressDialog("Search platform file under %s ..." % path, 
                               "Search platform under %s ..." % path, 
                               1, 
                               wx.GetApp().GetTopWindow(),
                               wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        pd.SetSize((500, 140))
        pd.CenterOnParent()
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if dir.lower() in ['cvs', '.svn', '_svn', 'packagedocument']:
                    dirs.remove(dir)
                    continue
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
                str = "Searching %s ..." % os.path.join(root, dir)
                pd.Pulse(str)
            for file in files:
                tfile = os.path.join(root, file)
                (name, ext) = os.path.splitext(tfile)
                if ext == '.dsc':
                    index = self._platformctrl.Append("%s (%s)" % (file, root))

        pd.Destroy()        