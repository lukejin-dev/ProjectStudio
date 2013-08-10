import core.plugin
import core.service
import plugins.EdkPlugins.edk.wizard.workspace as workspace
import wx
import os
import plugins.ProjectPlugin.xmlparser as xmlparser
import plugins.EdkPlugins.edk.model.dsc as dsc
    
_plugin_module_info_ = [{"name":"EdkProjectExtension",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide project management for edk project",
                         "class":"EdkProjectExtensionPlugin",
                         "dependencies":['Project']}]
                 
import plugins.ProjectPlugin.projext as projext
                         
class EdkProjectExtensionPlugin(projext.ProjectExtensionPlugin):
    def IGetExtension(self):
        return EdkProjectExternsion
    
class EdkProjectExternsion(projext.ProjectExtension):
    def __init__(self):
        projext.ProjectExtension.__init__(self)
        
        self._platforms     = []
        self._projectPath   = None # This is also EFI_SOURCE path
        self._toolPath      = None
        self._projectName   = None
        self._edkPath       = None
         
    def IGetName(self):
        return "EDK Project"
                
    def IGetProjectName(self):
        return self._projectName
        
    def IProperties(self):
        wx.MessageBox("%s project extension does not provide IProperties interface!" % self.IGetName())
        return None
        
    def INewProject(self):
        #wx.MessageBox("%s project extension does not provide INewProject interface!" % self.IGetName())
        """This interface need be overide by extension plugin"""
        wiz = workspace.EDKNewProject(wx.GetApp().GetTopWindow(), -1)
        
        if not wiz.RunWizard(): return
            
        self._platforms         = wiz.GetPlatforms()
        self._projectPath       = wiz.GetProjectLocation()
        self._toolPath          = wiz.GetEdkToolsPath()
        self._projectName       = wiz.GetProjectName()
        self._edkPath           = wiz.GetEdkSourcePath()
        
        pfilename = os.path.join(self._projectPath, self._projectName + '.ews')
        doc = self.GetService().CreateProjectDoc(pfilename)
        doc.UpdateAllViews()
        
        if doc == None:
            wx.MessageBox("Fail to create project document!")
            return
        try:
            f = open(pfilename, 'w')
            f.close()
        except:
            pass
            
        doc.SetExtensionName(self.IGetName())
        doc.SetDocumentModificationDate()
        doc.SetDocumentSaved(True)
        doc.Modify(True)
        doc.Save()
        doc.Modify(False)
        doc.UpdateAllViews()
        
    def ILoadExtension(self, dom):
        self._projectName = xmlparser.XmlElement(dom, '/Project/Name')
        
        rootPath = "/Project/Extension"
        self._toolPath = xmlparser.XmlElement(dom, rootPath + '/EdkToolsPath')
        self._edkPath  = xmlparser.XmlElement(dom, rootPath + '/EdkSourcePath')
        self._platforms = []
        for platform in xmlparser.XmlList(dom, rootPath + "/Platforms/File"):
            self._platforms.append(xmlparser.XmlElementData(platform))
        
        """This interface need be overide by extension plugin"""
        return True

    def ISaveExtension(self, root, dom):
        # create edk tool item
        edktoolitem = dom.createElement('EdkToolsPath')
        edktoolitem.appendChild(dom.createTextNode(self._toolPath))
        root.appendChild(edktoolitem)
        
        # create edk source item
        edksourceitem = dom.createElement('EdkSourcePath')
        edksourceitem.appendChild(dom.createTextNode(self._edkPath))
        root.appendChild(edksourceitem)
        
        pRootItem = dom.createElement('Platforms')
        root.appendChild(pRootItem)
        
        for platform in self._platforms:
            pItem = dom.createElement('File')
            pItem.appendChild(dom.createTextNode(platform))
            pRootItem.appendChild(pItem)
        return True
        
    def ICreateProjectNavigateView(self, docView, serviceView):
        """This interface need be overide by extension plugin"""
        serviceView.DestroyChildren()
        sizer = wx.BoxSizer(wx.VERTICAL)
        #treectl = wx.TreeCtrl(view, -1)
        treectl = wx.TreeCtrl(serviceView, -1)
        sizer.Add(treectl, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 2)
        serviceView.SetSizer(sizer)
        serviceView.Layout()
        serviceView.SetAutoLayout(True)
        frame = wx.GetApp().GetTopWindow()
        
        doc = docView.GetDocument()
        self._projectPath = os.path.dirname(doc.GetFilename())
        
        for p in self._platforms:
            iniFile = dsc.EDKDSCFile(self._projectPath, self._edkPath)
            iniFile.Parse(os.path.join(self._projectPath, p))
        self.InitProjectTree(treectl)
        
    def InitProjectTree(self, treectrl):
        root = treectrl.AddRoot(self._projectName)
        for p in self._platforms:
            treectrl.AppendItem(root, p) 
                          