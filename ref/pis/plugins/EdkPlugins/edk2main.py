import core.plugin
import core.service
import core.images as images
import plugins.EdkPlugins.edk2.wizard.workspace as workspace
import wx
import os
import plugins.ProjectPlugin.xmlparser as xmlparser
import plugins.ProjectPlugin.projext as projext
import plugins.EdkPlugins.edk2.model.baseobject as baseobject
import plugins.EdkPlugins.edk2.edk2ui.projecttree as projecttree 
import plugins.EdkPlugins.basemodel.inidocview as inidocview
import wx.lib.docview as docview
import wx.lib.pydocview as pydocview
import plugins.EdkPlugins.basemodel.ini as ini
import plugins.EdkPlugins.edk2.buildmgr as buildmgr
import plugins.EdkPlugins.edk2.edk2ui.SurfaceItemSearch as SurfaceItemSearch
from plugins.EdkPlugins.basemodel.message import *

_plugin_module_info_ = [{"name":"Edk2ProjectExtension",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide project management for edk2 project",
                         "class":"Edk2ProjectExtensionPlugin",
                         "dependencies":['Project']}]
                         
class Edk2ProjectExtensionPlugin(projext.ProjectExtensionPlugin):
    def IGetExtension(self):
        return Edk2ProjectExternsion
    
    def Install(self):
        ret = projext.ProjectExtensionPlugin.Install(self)
        
        # register doc template
        docmgr = wx.GetApp().GetDocumentManager()
        initemp = docview.DocTemplate(docmgr, 
                                      "INI document",
                                      "*.inf;*.dec;*.dsc",
                                      "Surface Document",
                                      ".inf;.dec;.dsc",
                                      "Document for INF/DEC/DSC",
                                      "View for INF/DEC/DSC",
                                      inidocview.INIDoc,
                                      inidocview.INIView,
                                      icon=images.getBlankIcon())
        
        docmgr.AssociateTemplate(initemp)
        return ret
        
class Edk2ProjectExternsion(projext.ProjectExtension):
    def __init__(self):
        projext.ProjectExtension.__init__(self)
        self._platforms              = []
        self._packages               = []
        self._pd_load_module         = None
        self._pd_index               = 0
        self._project_tree           = None
        self._svnservice             = None
        self._isModified             = False
        self._buildmgr               = buildmgr.BuildManager(self)
        self._valmgr                 = None
        self._surfaceView            = None
        self._surfaceServ            = None
        self._EccInstance            = None
        self._FuncHeaderSyncInstance = None
        self._FuncHeaderSyncInstance2= None
        
    def IGetName(self):
        return "EDKII Project"
    
    def IGetProjectName(self):
        return self._projectName
    
    def GetPlatforms(self):
        return self._platforms
        
    def GetPackages(self):
        return self._packages
    
    def GetWorkspace(self):
        return self._projectPath
        
    def GetPlatformObjByName(self, name):
        for obj in self._platforms:
            if obj.GetName() == name:
                return obj
        return None
        
    def INewProject(self):
        
        #wx.MessageBox("%s project extension does not provide INewProject interface!" % self.IGetName())
        """This interface need be overide by extension plugin"""
        wiz = workspace.EDK2NewProject(wx.GetApp().GetTopWindow(), -1)
        
        if not wiz.RunWizard(): return None
            
        dscPaths            = wiz.GetPlatforms()
        self._projectPath   = wiz.GetProjectLocation()
        self._toolPath      = wiz.GetToolConfigFilePath()
        self._projectName   = wiz.GetProjectName()
 
        pfilename = os.path.join(self._projectPath, self._projectName + '.ews')
        doc = self.GetService().CreateProjectDoc(pfilename)
 
        if doc == None:
            wx.MessageBox("Fail to create project document!")
            return None
        try:
            f = open(pfilename, 'w')
            f.close()
        except:
            pass
        
        doc.SetExtensionName(self.IGetName())
        doc.SetDocumentModificationDate()
        doc.SetDocumentSaved(True)
        doc.Modify(True)
        self.LoadPlatforms(dscPaths)
        doc.Save()
        doc.Modify(False)

        doc.UpdateAllViews()
        self._buildmgr.ShowToolbar(True)
        self._buildmgr.RefreshToolbar()
        
        self.EnableSurfaceItemView(self._platforms, self._packages)
        return doc
    
    def ICloseProject(self):
        LogMsg('Close project %s' % self._projectName)
        for platform in self._platforms:
            platform.Destroy()
        del self._platforms[:]
        for package in self._packages:
            package.Destroy()
        del self._packages[:]
        self.GetService().RemoveAllMonitorFiles()
        self._buildmgr.ShowToolbar(False)
        self._buildmgr.RefreshToolbar()
        self.EnableSurfaceItemView()
        if self._EccInstance != None:
            self._EccInstance.DeActivate()
        if self._FuncHeaderSyncInstance != None:
            self._FuncHeaderSyncInstance.DeActivate()
            
    def ILoadExtension(self, dom, filename):
        self._projectPath = os.path.dirname(filename)
        self._projectName = xmlparser.XmlElement(dom, '/Project/Name')
        
        rootPath = "/Project/Extension"
        self._toolPath = xmlparser.XmlElement(dom, rootPath + '/EdkIIToolDefFile')
        dscPaths = []
        for platform in xmlparser.XmlList(dom, rootPath + "/Platforms/File"):
            path = xmlparser.XmlElementData(platform)
            dscPaths.append(path)
            
        self.LoadPlatforms(dscPaths)
        self._buildmgr.ShowToolbar(True)
        self._buildmgr.RefreshToolbar()
        self.EnableSurfaceItemView(self._platforms, self._packages)
        return True
    
    def ISaveExtension(self, root, dom):
        # create edk tool item
        edktoolitem = dom.createElement('EdkIIToolDefFile')
        edktoolitem.appendChild(dom.createTextNode(self._toolPath))
        root.appendChild(edktoolitem)
        
        pRootItem = dom.createElement('Platforms')
        root.appendChild(pRootItem)
        
        for platform in self._platforms:
            pItem = dom.createElement('File')
            pItem.appendChild(dom.createTextNode(platform.GetRelativeFilename()))
            pRootItem.appendChild(pItem)
        return True   
        
    def ICreateProjectNavigateView(self, docView, serviceView):
        """This interface need be overide by extension plugin"""
        serviceView.Activate()
        serviceView.DestroyChildren()
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._project_tree = projecttree.ProjectTreeCtrl(serviceView, self, -1)
        sizer.Add(self._project_tree, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 2)
        serviceView.SetSizer(sizer)
        serviceView.Layout()
        serviceView.SetAutoLayout(True)
        frame = wx.GetApp().GetTopWindow()
        
        doc = docView.GetDocument()
        
        self._projectPath = os.path.dirname(doc.GetFilename())
        self._project_tree.InitProject(self._projectName)
        for platform in self._platforms:
            self._project_tree.AddPlatform(platform)
        
        for package in self._packages:
            self._project_tree.AddPackage(package)
            
    def EnableSurfaceItemView(self, platformObjs=None, packageObjs=None):
        frame = wx.GetApp().GetTopWindow()
        pwin  = frame._sidenb['bottom']
        if platformObjs == None or packageObjs == None:
            if self._surfaceServ != None and self._surfaceServ.IsActivated():
                self._surfaceServ.DeActivate()
        else:
            if self._surfaceServ == None:
                self._surfaceServ = SurfaceItemSearch.SurfaceItemSearchService()
                self._surfaceServ.SetFrame(wx.GetApp().GetTopWindow())
                wx.GetApp().InstallService(self._surfaceServ)
            if not self._surfaceServ.IsActivated():
                self._surfaceServ.Activate()
            
    def LoadPlatforms(self, dscs):
        # compute max count of progress dialog
        count = 0
        for path in dscs:
            pObj = baseobject.Platform(self, self._projectPath)
            if pObj.Load(path):
                count += pObj.GetModuleCount()
                self._platforms.append(pObj)
                self.GetService().AddMonitorFile(pObj.GetFilename())
                
        self._pd_load_module = wx.ProgressDialog("Load platforms",
                                                 "Load platforms",
                                                 count,
                                                 wx.GetApp().GetTopWindow(),
                                                 style=wx.PD_ELAPSED_TIME|wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
        self._pd_load_module.SetSize((500, 130))
        self._pd_load_module.CenterOnParent()
        self._pd_index = 0
        for pObj in self._platforms:
            self._pd_load_module.SetTitle('Load platform %s ...' % pObj.GetFilename())
            pObj.LoadModules(self.CallbackPreModuleLoad)
        self._pd_load_module.Destroy()
                                
        for file in ini.BaseINIFile._objs.keys():
            self.GetService().AddMonitorFile(file)
            
    def CallbackPreModuleLoad(self, pObj, modpath):
        self._pd_index += 1
        self._pd_load_module.Update(self._pd_index, "Load module %s" % modpath)
        path = os.path.join(self._projectPath, modpath)
        path = os.path.normpath(path)
        self.GetService().AddMonitorFile(path)
        
    def GetPackage(self, path):
        path = os.path.normpath(path)
        for package in self._packages:
            if package.GetRelativeFilename() == path:
                return package
        LogMsg ('Create package %s' % path)
        package = baseobject.Package(self, self._projectPath)
        if not package.Load(path): return None
        self._packages.append(package)
        path = os.path.join(self._projectPath, path)
        self.GetService().AddMonitorFile(path)
        return package
                         
    def Modify(self, isModified=False, modifiedObj=None):
        #LogMsg("Project is modified, object is %s" % modifiedObj)
        self._project_tree.Modify(isModified, modifiedObj)
        
    def SearchObjByPath(self, path):
        # use object's dict to fast search
        if path not in ini.BaseINIFile._objs.keys():
            LogMsg("Can not find changed project file", path)
            return None
    
    def OnProjectFileChanged(self, path):
        if path not in ini.BaseINIFile._objs.keys():
            LogMsg("Can not find changed project file", path)
            return None
            
        ini.BaseINIFile._objs[path].Modify(True)

    def BuildProjectTags(self):
        paths = []
        for obj in self._platforms:
            path = os.path.dirname(obj.GetFilename())
            if path not in paths:
                paths.append(path)
        
        for obj in self._packages:
            path = os.path.dirname(obj.GetFilename())
            if path not in paths:
                paths.append(path)
        
        tagPath = self._projectPath + os.sep + self._projectName + '.tag'
        self.GetService().BuildTags(tagPath, paths)
        
    def ValidateProject(self):
        import plugins.EdkPlugins.edk2.wizard.validate as validate
        wiz = validate.EDK2ValidateMain(wx.GetApp().GetTopWindow(), self)
        if not wiz.RunWizard(): return
        import plugins.EdkPlugins.edk2.validatemgr as validatemgr
        if self._valmgr == None:
            self._valmgr = validatemgr.ValidateManager(self)
        #self._valmgr.GetView().Clear()
        self._valmgr.StartCheckingLibraryClass(wiz.GetTemporaryPath())
        #self._valmgr.StartCheckingProtocol(wiz.GetTemporaryPath())
        