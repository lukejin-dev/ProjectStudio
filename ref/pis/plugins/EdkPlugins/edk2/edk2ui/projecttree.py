import wx.lib.customtreectrl as CT
import wx
import plugins.EdkPlugins.edk2.model.baseobject as baseobject
import plugins.EdkPlugins.edk2.wizard.packagedoc as packagedoc
import wx.lib.docview as docview
import plugins.EdkPlugins.edk2.model.inf as inf
import plugins.EdkPlugins.edk2.model.dec as dec
import os, time
import image

from plugins.EdkPlugins.basemodel.message import *

PEI_ARR = ['PEIM', 'PEI_CORE']
DXE_ARR = ['DXE_DRIVER', 'DXE_RUNTIME_DRIVER', 'UEFI_DRIVER', 'DXE_CORE',
           'DXE_SMM_DRIVER', 'UEFI_APPLICATION', 'DXE_SAL_DRIVER']

ID_MENU_SVN_UPDATE        = wx.NewId()
ID_MENU_SVN_COMMIT        = wx.NewId()
ID_MENU_SVN_CLEANUP       = wx.NewId()
ID_MENU_PLATFORM_REFRESH  = wx.NewId()
ID_MENU_PACKAGE_REFRESH   = wx.NewId()
ID_MENU_PACKAGE_GENERATE_DOCUMENT = wx.NewId()
ID_MENU_MODULE_REFRESH    = wx.NewId()
ID_MENU_MODULE_BUILD      = wx.NewId()
ID_MENU_MODULE_BUILD_CLEAN = wx.NewId()
ID_MENU_PLATFORM_BUILD    = wx.NewId()
ID_MENU_PLATFORM_BUILD_CLEAN = wx.NewId()
ID_MENU_PLATFORM_GENERATE_FULL_REFERENCE_DSC = wx.NewId()
ID_MENU_PLATFORM_GENERATE_FDS = wx.NewId()
ID_MENU_PROJECT_BUILD_TAG = wx.NewId()
ID_MENU_PROJECT_VALIDATION = wx.NewId()
ID_MENU_RUN_ECC           = wx.NewId()
ID_MENU_RUN_FUNC_HEADER_SYNC = wx.NewId()
ID_MENU_RUN_FUNC_HEADER_SYNC2 = wx.NewId()
ID_MENU_MODULE_BUILD_CLEAN_ALL = wx.NewId()
           
class ProjectTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, projext, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SUNKEN_BORDER |CT.TR_HAS_BUTTONS |CT.TR_HAS_VARIABLE_ROW_HEIGHT|wx.WANTS_CHARS,
                 log=None):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.PrepareImageList()
        self._isModified   = False
        self._platformRoot = None
        self._packageRoot  = None
        self._svnservice   = None
        self._progress     = None
        self._progress_count = 0
        self._projext      = projext
        CT.EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnExpanding)
        CT.EVT_TREE_ITEM_GETTOOLTIP(self, self.GetId(), self.OnGetToolTip)
        CT.EVT_TREE_ITEM_ACTIVATED(self, self.GetId(), self.OnTreeItemActivated)
        CT.EVT_TREE_ITEM_MENU(self, self.GetId(), self.OnItemMenu)
        CT.EVT_TREE_KEY_DOWN(self, self.GetId(), self.OnKey)
        
    def GetSvnService(self):
        if not hasattr(self, "_svnservice") or self._svnservice == None:
            pm = wx.GetApp().GetPluginMgr()
            p  = pm.GetPlugin('SvnPlugin')
            if p != None:
                self._svnservice = pm.GetPlugin('SvnPlugin').GetServiceInstance()
            else:
                self._svnservice = None
        
        return self._svnservice  
            
    def InitProject(self, name):
        root = self.AddRoot(name)
        self.SetItemImage(root, self._iWorkspace, CT.TreeItemIcon_Normal)
        #self.SetItemImage(root, 1, CT.TreeItemIcon_Expanded) 
        
        self._platformRoot = self.AppendItem(root, "Platforms")
        self.SetItemImage(self._platformRoot, self._iPlatform, CT.TreeItemIcon_Normal)
                
        self._packageRoot  = self.AppendItem(root, "Packages")
        self.SetItemImage(self._packageRoot, self._iPackage, CT.TreeItemIcon_Normal)
        
        
    def AddItem(self, root, dispName, data=None, normalIndex=-1, openIndex=-1):
        if root == None:
            item = self.AddRoot(dispName)
        else:
            item = self.AppendItem(root, dispName)
            
        if data != None:
            self.SetItemPyData(item, data)
        
        if normalIndex == -1:
            normalIndex = self._iFolder
        self.SetItemImage(item, normalIndex, CT.TreeItemIcon_Normal)

        if openIndex != -1:
            self.SetItemImage(item, openIndex, CT.TreeItemIcon_Expanded)
            
        return item        
        
    def AddPlatform(self, pObj):
        if pObj.IsModified():
            str = '*' + pObj.GetName()
        else:
            str = pObj.GetName()
        pItem = self.AddItem(self._platformRoot, str, pObj, self._iPlatform)
        
        self.GetSvnInfo(pObj.GetFilename(), pItem)
        self.SetItemHasChildren(pItem)
         
    def GetSvnInfo(self, path, item):
        serv = self.GetSvnService()
        if serv == None: return
        serv.GetSvnInfo(path, self.CallbackPathSvnInfo, item)
        
    def CallbackPathSvnInfo(self, info, item):
        if item == None or not item.IsOk(): return
        timestr = time.strftime( '%d/%m/%y %H:%M', time.localtime(info.data['commit_time']))
        text = self.GetItemText(item)
        self.SetItemText(item, '%-15s (r%s, %s, %s)' %  
                         (text, 
                         info.data['commit_revision'].number, 
                         timestr, 
                         info.data['commit_author']))
                 
    def AddPackage(self, pObj):
        if pObj.IsModified():
            str = '*' + pObj.GetName()
        else:
            str = pObj.GetName()
        pItem = self.AddItem(self._packageRoot, str, pObj, self._iPackage)
        self.GetSvnInfo(pObj.GetFilename(), pItem)
        self.SetItemHasChildren(pItem)
        
    def AddModule(self, pItem, mObj):
        mType = mObj.GetModuleType()
        type = mType
        
        """
        if mType in PEI_ARR:
            type = "PEI"
        elif mType in DXE_ARR:
            type = "DXE"
        else:
            type = "Others"
        """
         
        (child, cookie) = self.GetFirstChild(pItem)
        typeItem = None
        while (child != None and child.IsOk()):
            mType = self.GetItemText(child)
            if mType.lower() == type.lower():
                typeItem = child
                break
            (child, cookie) = self.GetNextChild(pItem, cookie)
        
        if typeItem == None:
            typeItem = self.AddItem(pItem, type)
            self.SortChildren(pItem)
             
        if mObj.IsModified():
            str = "*%s [%s]" % (mObj.GetModuleName(), mObj.GetArch())
        else:
            str = "%s [%s]" % (mObj.GetModuleName(), mObj.GetArch())
            
        mItem = self.AddItem(typeItem, 
                             str, 
                             mObj,
                             self._iModule) 
        self.GetSvnInfo(mObj.GetFilename(), mItem)                     
        self.SetItemHasChildren(mItem)
        self.SortChildren(typeItem)
        
    def UpdatePlatform(self, pItem, pObj):
        if not self.IsExpanded(pItem):
            self.CollapseAndReset(pItem)
            #self.AddItem(pItem, 'PEI')
            #self.AddItem(pItem, 'DXE')
            #self.AddItem(pItem, 'Others')        
            for mObj in pObj.GetModules():
                self.AddModule(pItem, mObj)
        else:
            typeRoots = self.GetChildNodes(pItem)
            moduleItems = []
            for type in typeRoots:
                moduleItems += self.GetChildNodes(type)
            
            for mItem in moduleItems:
                mObj = self.GetPyData(mItem)
                if self.IsExpanded(mItem):
                    self.UpdateModule(mItem, mObj)
                    
    def UpdateModule(self, mItem, mObj):
        isExpanded = self.IsExpanded(mItem)
        
        self.CollapseAndReset(mItem)
        
        libRootItem = self.AddItem(mItem, 'Libraries')
        libObjsDict = mObj.GetLibraries()
 
       # Add librarys instances
        for libClass in libObjsDict.keys():
            lcItem = self.AddItem(libRootItem, libClass)
            instance = libObjsDict[libClass]
            if instance == None:
                self.AddItem(lcItem, 
                             '****Missing library instance in DSC file' 
                             )
            else:
                if instance.IsInherit():
                    self.SetItemBackgroundColour(lcItem, (0, 255, 0))
                instanceItem = self.AddItem(lcItem, 
                                            'Instance: %s' % instance.GetFilename(), 
                                            instance,
                                            self._iModule)
                self.GetSvnInfo(instance.GetFilename(), instanceItem)
                self.SetItemHasChildren(instanceItem)
        self.SortChildren(libRootItem)
                         
        # Add source
        sourceRoot = self.AddItem(mItem, "Sources")
        for obj in mObj.GetSourceObjs():
            sItem = self.AddItem(sourceRoot, obj.GetSourcePath(), obj, 2)
            self.GetSvnInfo(obj.GetSourceFullPath(), sItem)
        self.SortChildren(sourceRoot)
        
        # Add Pcds
        pcds = mObj.GetPcds().values()
        if len(pcds) != 0:
            pcdRoot =self.AddItem(mItem, "PCDs")
            for obj in pcds:
                self.AddItem(pcdRoot, obj.GetName().split('.')[1], obj, self._iNormalFile)
            self.SortChildren(pcdRoot)
    
        guids = mObj.GetGuids()
        if len(guids) != 0:
            guidRoot = self.AddItem(mItem, "GUIDs")
            for obj in guids:
                self.AddItem(guidRoot, obj.GetName(), obj, self._iNormalFile)
            self.SortChildren(guidRoot)
            
        ppis = mObj.GetPpis()
        if len(ppis) != 0:
            ppiRoot = self.AddItem(mItem, "PPIs")
            for obj in ppis:
                self.AddItem(ppiRoot, obj.GetName(), obj, self._iNormalFile)
            self.SortChildren(ppiRoot)
            
        protocols = mObj.GetProtocols()
        if len(protocols) != 0:
            protocolRoot = self.AddItem(mItem, "PROTOCOLs")
            for obj in protocols:
                self.AddItem(protocolRoot, obj.GetName(), obj, self._iNormalFile)
            self.SortChildren(protocolRoot)
            
        depexs = mObj.GetDepexs()
        if len(depexs) != 0:
            depexRoot = self.AddItem(mItem, "DEPEX")
            for dep in depexs:
                self.AddItem(depexRoot, dep.GetDepexString(), dep, self._iNormalFile)
            
    def UpdatePackage(self, pItem, pObj):
        self.CollapseAndReset(pItem)
        
        # library class
        libRoot = self.AddItem(pItem, 'LibraryClass', None)
        objs = pObj.GetLibraryClassObjs()
        for obj in objs:
            path = os.path.dirname(pObj.GetFilename())
            path = os.path.join(path, obj.GetHeaderFile())
            self.AddItem(libRoot, obj.GetClassName(), FilePathObject(path), self._iNormalFile)
        self.SortChildren(libRoot)
        
        # pcd
        pcdRoot = self.AddItem(pItem, 'PCD')
        objs    = pObj.GetPcdDefineObjs()
        typeDict = {}
        for obj in objs:
            if obj.GetPcdType() not in typeDict.keys():
                typeDict[obj.GetPcdType()] = self.AddItem(pcdRoot,
                                                          obj.GetPcdType())
            self.AddItem(typeDict[obj.GetPcdType()],
                         obj.GetPcdName().split('.')[1],
                         obj, self._iNormalFile)
        for pcdTypeRoot in typeDict.values():
            self.SortChildren(pcdTypeRoot)
        
        # guid
        guidRoot = self.AddItem(pItem, 'GUID')
        guids = pObj.GetGuids()
        for guid in guids:
            self.AddItem(guidRoot, guid.GetName(), guid, self._iNormalFile)
            
        # ppi
        ppiRoot = self.AddItem(pItem, 'PPI')
        ppis = pObj.GetPpis()
        for ppi in ppis:
            self.AddItem(ppiRoot, ppi.GetName(), ppi, self._iNormalFile)

        # protocol
        protocolRoot = self.AddItem(pItem, 'PROTOCOL')
        protocols = pObj.GetProtocols()
        for protocol in protocols:
            self.AddItem(protocolRoot, protocol.GetName(), protocol, self._iNormalFile)
            
    def OnExpanding(self, event):
        item = event.GetItem()
        data = self.GetPyData(item)
        if data == None: return
        
        if issubclass(data.__class__, baseobject.Platform):
            self.UpdatePlatform(item, data)
        if issubclass(data.__class__, baseobject.Module):
            self.UpdateModule(item, data)
        if issubclass(data.__class__, baseobject.Package):
            self.UpdatePackage(item, data)
            
    def SearchChildNode(self, root, childData=None, label=None):
        if childData == None and label == None: return None
        
        bFound = False
        (child, cookie) = self.GetFirstChild(root)
        while child != None and child.IsOk():
            bFound = True
            if label != None and label != self.GetItemText(child):
                bFound = False
                
            data = self.GetPyData(child)
            if childData != None and childData != data:
                bFound = False
            
            if bFound:
                break
            (child, cookie) = self.GetNextChild(root, cookie)
        
        if bFound:
            return child
        else:
            return None            
            
    def GetPlatformItem(self, pObj):
        pItem = self.SearchChildNode(self._platformRoot, pObj)
        return pItem
        
    def GetModuleItem(self, mObj):
        if mObj == None: return None
        
        pObj = mObj.GetPlatform()
        if pObj == None: return None
        
        pItem = self.SearchChildNode(self._platformRoot, pObj)
        if pItem == None: return None
        
        mType = mObj.GetModuleType()
        type = mType
        
        """
        if mType in PEI_ARR:
            type = "PEI"
        elif mType in DXE_ARR:
            type = "DXE"
        else:
            type = "Others"
        """
            
        typeRoot = self.SearchChildNode(pItem, None, type)
        if typeRoot == None: return None
        
        return self.SearchChildNode(typeRoot, mObj)
        
    def GetPackageItem(self, pObj):
        return self.SearchChildNode(self._packageRoot, pObj)
        
    def Modify(self, isModify=True, obj=None):
        cls = obj.__class__
        if issubclass(cls, baseobject.Platform):
            item = self.GetPlatformItem(obj)
        elif issubclass(cls, baseobject.Package):
            item = self.GetPackageItem(obj)
        elif issubclass(cls, baseobject.Module):
            item = self.GetModuleItem(obj)
        else:
            return None
        if item == None:
            return
            
        if isModify:
            str = self.GetItemText(item)
            if not str.startswith('*'):
                str = '*' + str
                self.SetItemText(item, str)
        else:
            str = self.GetItemText(item)
            if str.startswith('*'):
                str = str[1:]
                self.SetItemText(item, str) 

        if isModify and issubclass(cls, baseobject.Platform):
            objs = obj.GetModules()
            for mObj in objs:
                if mObj.IsModified():
                    self.Modify(isModify, mObj)
                                   
    def OnGetToolTip(self, event):
        item = event.GetItem()
        data = self.GetPyData(item)
        if data == None: return
        
        tipstr = None
        cls = data.__class__
        if issubclass(cls, baseobject.Platform) or \
           issubclass(cls, baseobject.Module) or \
           issubclass(cls, baseobject.Package):
            tipstr = data.GetFilename()
        if issubclass(cls, baseobject.ModulePcd):
            tipstr = data.GetName()
        if issubclass(cls, FilePathObject):
            tipstr = data.GetFilename()
        if issubclass(cls, dec.DECPcdObject):
            tipstr = data.GetPcdName()
            
        if tipstr != None:
            event.SetToolTip(wx.ToolTip(tipstr))
            
    def OnTreeItemActivated(self, event):
        event.Skip()
        item = event.GetItem()
        data = self.GetPyData(item)
        if data == None: return
        
        cls = data.__class__
        docmgr = wx.GetApp().GetDocumentManager()
        if issubclass(cls, baseobject.Platform) or \
           issubclass(cls, baseobject.Module):
            doc = docmgr.CreateDocument(data.GetFilename(), docview.DOC_SILENT)
        if issubclass(cls, baseobject.Package):
            path = os.path.dirname(data.GetFilename())
            path = os.path.join(path, 'PackageDocument', 'html', 'index.html')
            if not os.path.exists(path):
                path = data.GetFilename()
            doc = docmgr.CreateDocument(path, docview.DOC_SILENT)
        if issubclass(cls, inf.INFSourceObject):
            docmgr.CreateDocument(data.GetSourceFullPath(), docview.DOC_SILENT)
        if issubclass(cls, baseobject.PcdItem):
            buildObj = data.GetBuildObj()
            doc = docmgr.CreateDocument(buildObj.GetFilename(), docview.DOC_SILENT)
            view = doc.GetFirstView()
            if view != None:
                view.GotoLine(buildObj.GetStartLinenumber() + 1)
        if issubclass(cls, FilePathObject):
            doc = docmgr.CreateDocument(data.GetFilename(), docview.DOC_SILENT)
        if issubclass(cls, dec.DECPcdObject):
            doc = docmgr.CreateDocument(data.GetFilename(), docview.DOC_SILENT)
            view = doc.GetFirstView()
            if view != None:
                view.GotoLine(data.GetStartLinenumber() + 1)
        if issubclass(cls, baseobject.SurfaceItem):
            decObj = data.GetDecObject()
            if decObj != None:
                doc = docmgr.CreateDocument(decObj.GetFilename(), docview.DOC_SILENT)
                view = doc.GetFirstView()
                if view != None:
                    view.GotoLine(decObj.GetStartLinenumber() + 1)
        if issubclass(cls, baseobject.DepexItem):
            infObj = data.GetInfObject()
            if infObj != None:
                doc = docmgr.CreateDocument(infObj.GetFilename(), docview.DOC_SILENT)
                view = doc.GetFirstView()
                if view != None:
                    view.GotoLine(infObj.GetStartLinenumber() + 1)
        if issubclass(cls, baseobject.ModulePcd):
            obj = data.GetBuildObj()
            if obj == None:
                wx.MessageBox("Can not find PCD value for %s in platform %s" % \
                              (data.GetName(), data.GetParent().GetPlatform().GetFilename()))
            else:
                doc = docmgr.CreateDocument(obj.GetFilename(), docview.DOC_SILENT)
                view = doc.GetFirstView()
                if view != None:
                    view.GotoLine(obj.GetStartLinenumber() + 1)                
                    
    def AddMenuItem(self, menu, id, itemText, itemDesc, itemHandler, updatehandler=None, bitmap=None):
        item = wx.MenuItem(menu, id, itemText, itemDesc)
        if bitmap != None:
            item.SetBitmap(bitmap)
        menu.AppendItem(item)
        frame = wx.GetApp().GetTopWindow()
        wx.EVT_MENU(frame, id, itemHandler)
        if updatehandler != None:
            wx.EVT_UPDATE_UI(frame, id, updatehandler)
        return item
    
    def OnItemMenu(self, event):
        item = event.GetItem()
        if item == self.GetRootItem():
            menu = self.GetProjectRootMenu()
            self.PopupMenu(menu, event.GetPoint())
            menu.Destroy()
            return
            
        data = self.GetPyData(item)
        if data == None: return
        cls = data.__class__

        if issubclass(cls, baseobject.Platform):
            menu = self.GetPlatformContextMenu()
        elif issubclass(cls, baseobject.Module):
            menu = self.GetModuleContextMenu()
        elif issubclass(cls, baseobject.Package):
            menu = self.GetPackageContextMenu()
        elif issubclass(cls, inf.INFSourceObject):
            menu = self.GetGeneralFileContextMenu()
        elif issubclass(cls, FilePathObject):
            menu = self.GetGeneralFileContextMenu()
        else:
            return
        
        if menu.GetMenuItemCount() != 0:
            menu.AppendSeparator()

        serv = self.GetSvnService()
        if serv != None:
            menu.AppendSubMenu(self.GetSvnMenu(), 'SVN')

        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()
        
    def GetProjectRootMenu(self):
        menu = wx.Menu()
        self.AddMenuItem(menu, ID_MENU_PROJECT_BUILD_TAG, "ReBuild tags", "Build tags for project's source", self.OnProjectBuildTag)
        self.AddMenuItem(menu, ID_MENU_PROJECT_VALIDATION, "Validate EDKII Meta Files", "Validate meta files", self.OnProjectValidate)        
        return menu
        
    def OnProjectBuildTag(self, event):
        self._projext.BuildProjectTags()
        
    def OnProjectValidate(self, event):
        self._projext.ValidateProject()
    
    def GetPlatformContextMenu(self):
        menu = wx.Menu()
        self.AddMenuItem(menu, ID_MENU_PLATFORM_BUILD, "Build", "Build platform", self.OnPlatformBuild)
        self.AddMenuItem(menu, ID_MENU_PLATFORM_BUILD_CLEAN, 'Build Clean', 'Clean platform output', self.OnPlatformBuildClean)
        self.AddMenuItem(menu, ID_MENU_PLATFORM_GENERATE_FDS, 'Generate FD file', 'Generate Firmawre Device File', self.OnPlatformGenFds)
        self.AddMenuItem(menu, ID_MENU_PLATFORM_GENERATE_FULL_REFERENCE_DSC,\
                         "Generate Full Reference",
                         "Generate Full Library/Pcd reference DSC file for platform",
                         self.OnPlatformGenerateFullReference)
                         
        menu.AppendSeparator()
        self.AddMenuItem(menu, ID_MENU_PLATFORM_REFRESH, "Refresh\tF5", "Refresh", self.OnRefreshPlatform)
        self.AddMenuItem(menu, ID_MENU_RUN_ECC, "Run ECC", "Run ECC", self.OnRunEcc)
        return menu
    
    def OnPlatformBuild(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        self._projext._buildmgr.Build(obj.GetWorkspace(),
                                      obj.GetRelativeFilename(),
                                      obj.GetSupportArchs())
        
    def OnPlatformBuildClean(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        self._projext._buildmgr.Build(obj.GetWorkspace(),
                                      obj.GetRelativeFilename(),
                                      obj.GetSupportArchs(),
                                      reason='clean')
        
    def OnPlatformGenFds(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        self._projext._buildmgr.Build(obj.GetWorkspace(),
                                      obj.GetRelativeFilename(),
                                      obj.GetSupportArchs(),
                                      reason='fds')
        
    def OnPlatformGenerateFullReference(self, event):
        item    = self.GetSelection()
        obj     = self.GetPyData(item)
        dscObj  = obj.GenerateFullReferenceDsc()
        docmgr = wx.GetApp().GetDocumentManager()
        template = docmgr.FindTemplateForPath(obj.GetFilename())
        doc = template.CreateDocument(obj.GetName() + 'AllOveride.dsc', wx.lib.docview.DOC_NEW)
        view = doc.GetFirstView()
        if view != None:
            view.SetValue(str(dscObj))
            doc.Modify(True)
            
    def OnRefreshPlatform(self, event):
        if self._progress != None: return
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        if not issubclass(obj.__class__, baseobject.Platform):
            ErrorMsg("Invalid object data in tree item")
            return
        isExpand = self.IsExpanded(item)
        self.CollapseAndReset(item)
        max = obj.GetModuleCount()
        self._progress_count = 0
        self._progress_max   = max
        self._progress = wx.ProgressDialog("Reload Platform %s" % obj.GetFilename(),
                                           "Reload Platform %s" % obj.GetFilename(),
                                           max,
                                           wx.GetApp().GetTopWindow(),
                                           style=wx.PD_ELAPSED_TIME|wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
        self._progress.SetSize((500, 130))
        self._progress.CenterOnParent()
        obj.Reload(self.CallbackRefreshPlatform)
        self._progress.Destroy()
        self.Modify(False, obj)
        self._progress = None
        self._progress_count = 0
        self._progress_max   = 0
        
    def CallbackRefreshPlatform(self, pObj, filename):
        if self._progress != None:
            if self._progress_count <= self._progress_max:
                self._progress.Update(self._progress_count, "Reload module %s" % filename)
                self._progress_count += 1
        
    def GetModuleContextMenu(self):
        menu = wx.Menu()
        self.AddMenuItem(menu, ID_MENU_MODULE_BUILD, "Build", "Build Single Module", self.OnModuleBuild)
        self.AddMenuItem(menu, ID_MENU_MODULE_BUILD_CLEAN, 'Build Clean', 'Clean build for single module', self.OnModuleBuildClean)
        self.AddMenuItem(menu, ID_MENU_MODULE_BUILD_CLEAN_ALL, 'Build Clean All', 'Clean module and library output', self.OnModuleBuildCleanAll)
        menu.AppendSeparator()
        self.AddMenuItem(menu, ID_MENU_MODULE_REFRESH, "Refresh\tF5", "Refresh", self.OnRefreshModule)
        self.AddMenuItem(menu, ID_MENU_RUN_ECC, "Run ECC", "Run ECC", self.OnRunEcc)
        self.AddMenuItem(menu, ID_MENU_RUN_FUNC_HEADER_SYNC, "Run FuncHeaderSync[C->H]", "Run FuncHeaderSync[C->H]", self.OnRunFuncHeaderSync)
        self.AddMenuItem(menu, ID_MENU_RUN_FUNC_HEADER_SYNC2, "Run FuncHeaderSync[H->C]", "Run FuncHeaderSync[H->C]", self.OnRunFuncHeaderSync2)
        return menu
    
    def OnModuleBuild(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        pObj = obj.GetPlatform()
        self._projext._buildmgr.Build(pObj.GetWorkspace(),
                                      pObj.GetRelativeFilename(),
                                      [obj.GetArch()],
                                      module=obj.GetRelativeFilename())
    
    def OnModuleBuildClean(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        pObj = obj.GetPlatform()
        self._projext._buildmgr.Build(pObj.GetWorkspace(),
                                      pObj.GetRelativeFilename(),
                                      [obj.GetArch()],
                                      module=obj.GetRelativeFilename(),
                                      reason='clean')
        
    def OnModuleBuildCleanAll(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        pObj = obj.GetPlatform()
        self._projext._buildmgr.Build(pObj.GetWorkspace(),
                                      pObj.GetRelativeFilename(),
                                      [obj.GetArch()],
                                      module=obj.GetRelativeFilename(),
                                      reason='cleanall')

    def OnRefreshModule(self, event):
        if self._progress != None: return
        
        item = self.GetSelection()
        self.CollapseAndReset(item)
        obj  = self.GetPyData(item)
        if not issubclass(obj.__class__, baseobject.Module):
            ErrorMsg("Invalid object data in tree item")
            return
                
        self._progress = wx.ProgressDialog("Reload Module %s" % obj.GetFilename(),
                                           "Reload Module %s" % obj.GetFilename(),
                                           10,
                                           wx.GetApp().GetTopWindow(),
                                           style=wx.PD_ELAPSED_TIME|wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
        self._progress.SetSize((500, 130))
        self._progress.CenterOnParent()                                           
        obj.Reload(callback=self.CallbackModuleReload)
        self._progress.Destroy()
        self._progress = None
        self._progress_count = 0
        self._progress_max   = 0
        self.Modify(False, obj)
        
    def CallbackModuleReload(self, mObj, str):
        self._progress.Pulse(str)
        
    def GetPackageContextMenu(self):
        menu = wx.Menu()
        self.AddMenuItem(menu, ID_MENU_PACKAGE_GENERATE_DOCUMENT, "Generate Document", 
                         "Generate Package Reference Document", 
                         self.OnGeneratePackageDocument)
        menu.AppendSeparator()
        self.AddMenuItem(menu, ID_MENU_PACKAGE_REFRESH, "Refresh\tF5", "Refresh", self.OnRefreshPackage)
        self.AddMenuItem(menu, ID_MENU_RUN_ECC, "Run ECC", "Run ECC", self.OnRunEcc)
        return menu
        
    def OnGeneratePackageDocument(self, event):
        item = self.GetSelection()
        obj  = self.GetPyData(item)
        wiz = packagedoc.EDK2PackageDocumentWizard(wx.GetApp().GetTopWindow(), obj)
        wiz.RunWizard()
        
    def OnRefreshPackage(self, event):
        item = self.GetSelection()
        self.CollapseAndReset(item)
        obj  = self.GetPyData(item)
        obj.Reload()
        self.Modify(False, obj)
                
    def GetGeneralFileContextMenu(self):
        return wx.Menu()
    
    def GetSvnMenu(self):
        serv = self.GetSvnService()
        menu = wx.Menu()
        self.AddMenuItem(menu, serv.ID_UPDATE, "Update", "Update from svn", 
                         self.OnSvnUpdate, self.ProcessSvnMenuUIUpdate, 
                         serv.GetBitmapById(serv.ID_UPDATE))
        self.AddMenuItem(menu, serv.ID_COMMIT, "Commit", "Commit from svn", 
                         self.OnSvnCommit, self.ProcessSvnMenuUIUpdate, 
                         serv.GetBitmapById(serv.ID_COMMIT))
        menu.AppendSeparator()
        self.AddMenuItem(menu, serv.ID_CLEANUP, "Cleanup", "Cleanup from svn", 
                         self.OnSvnCleanup, self.ProcessSvnMenuUIUpdate, 
                         serv.GetBitmapById(serv.ID_CLEANUP)) 
        self.AddMenuItem(menu, serv.ID_REVERT, "Revert", "Revert from svn", 
                         self.OnSvnRevert, self.ProcessSvnMenuUIUpdate, 
                         serv.GetBitmapById(serv.ID_REVERT))                                                 
        return menu
        
    def ProcessSvnMenuUIUpdate(self, event):
        serv = self.GetSvnService()
        id = event.GetId()
        if serv != None:
            if id in [serv.ID_UPDATE, serv.ID_COMMIT, \
                      serv.ID_CHECKOUT, serv.ID_CLEANUP, \
                      serv.ID_REVERT]:
                event.Enable(not serv.IsBusy())
                return True        
        return False
        
    def OnSvnUpdate(self, event):
        serv = self.GetSvnService()
        if serv == None:
            wx.MessageBox("SvnService is not started!")
            return        
        item = self.GetSelection()
        obj = self.GetPyData(item)
        if obj == None: return
        cls = obj.__class__
        if issubclass(cls, baseobject.Platform) or \
           issubclass(cls, baseobject.Package)  or \
           issubclass(cls, baseobject.Module):
            path = os.path.dirname(obj.GetFilename())
        elif issubclass(cls, inf.INFSourceObject):
            path = obj.GetSourceFullPath()
        else:
            return
        
        if not os.path.exists(path):
            wx.MessageBox("Can not update for path %s" % path)
            return
        
        serv.SvnUpdate(path)
                
    def OnSvnCommit(self, event):
        serv = self.GetSvnService()
        if serv == None:
            wx.MessageBox("SvnService is not started!")
            return        
        item = self.GetSelection()
        obj = self.GetPyData(item)
        if obj == None: return
        path = os.path.dirname(obj.GetFilename())
        if not os.path.exists(path):
            wx.MessageBox("Can not update for path %s" % path)
            return

        serv.SvnCommit(path)
        
    def OnSvnCleanup(self, event):
        serv = self.GetSvnService()
        if serv == None:
            wx.MessageBox("SvnService is not started!")
            return
        
        item = self.GetSelection()
        obj = self.GetPyData(item)
        if obj == None: return
        path = os.path.dirname(obj.GetFilename())
        if not os.path.exists(path):
            wx.MessageBox("Can not update for path %s" % path)
            return

        serv.SvnCleanUp(path)
                
    def OnSvnRevert(self, event):
        serv = self.GetSvnService()
        if serv == None:
            wx.MessageBox("SvnService is not started!")
            return
        
        item = self.GetSelection()
        obj = self.GetPyData(item)
        if obj == None: return
        path = os.path.dirname(obj.GetFilename())
        if not os.path.exists(path):
            wx.MessageBox("Can not update for path %s" % path)
            return

        serv.SvnRevert(path)
                        
    def PrepareImageList(self):
        il = wx.ImageList(16, 16)
        art = wx.GetApp().GetArtProvider()
        self._iFolder      = il.Add(art.GetBitmap(wx.ART_FOLDER))
        self._iFolderOpen  = il.Add(art.GetBitmap(wx.ART_FILE_OPEN))
        self._iNormalFile  = il.Add(art.GetBitmap(wx.ART_NORMAL_FILE))
        self._iWorkspace   = il.Add(image.getWorkspaceBitmap())
        self._iPlatform    = il.Add(image.getPlatformBitmap())
        self._iModule      = il.Add(image.getModuleBitmap())
        self._iPackage     = il.Add(image.getPackageBitmap())
        
        self.AssignImageList(il)
        
    def OnKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_F5:
            item = self.GetSelection()
            obj  = self.GetPyData(item)
            if obj != None:
                if issubclass(obj.__class__, baseobject.Platform):
                    self.OnRefreshPlatform(event)
                elif issubclass(obj.__class__, baseobject.Module):
                    self.OnRefreshModule(event)
                elif issubclass(obj.__class__, baseobject.Package):
                    self.OnRefreshPackage(event)                    
            
    def OnRunEcc(self, event):
        item = self.GetSelection()
        data = self.GetPyData(item)
        if data == None:
            return
        
        path = os.path.dirname(data.GetFilename())
        if self._projext._EccInstance == None:
            import plugins.EdkPlugins.edk2.Ecc as Ecc
            self._projext._EccInstance = Ecc.ECCService()
            self._projext._EccInstance.SetFrame(wx.GetApp().GetTopWindow())
            wx.GetApp().InstallService(self._projext._EccInstance)
        self._projext._EccInstance.Run(data.GetWorkspace(), path)
        
    def OnRunFuncHeaderSync(self, event):
        item = self.GetSelection()
        data = self.GetPyData(item)
        if data == None:
            return
        
        path = os.path.dirname(data.GetFilename())
        if self._projext._FuncHeaderSyncInstance == None:
            import plugins.EdkPlugins.edk2.FuncHeaderSync as FuncHeaderSync
            self._projext._FuncHeaderSyncInstance = FuncHeaderSync.FuncHeaderSyncService()
            self._projext._FuncHeaderSyncInstance.SetFrame(wx.GetApp().GetTopWindow())
            wx.GetApp().InstallService(self._projext._FuncHeaderSyncInstance)
        self._projext._FuncHeaderSyncInstance.Run(data.GetWorkspace(), path)
        
    def OnRunFuncHeaderSync2(self, event):
        item = self.GetSelection()
        data = self.GetPyData(item)
        if data == None:
            return
        libclasspath = data.GetLibraryClassHeaderFilePath()
        if libclasspath == None:
            wx.MessageBox('This module is not library instance or Can find the library class header path for this library instance!')
            return
        path = os.path.dirname(data.GetFilename())
        if self._projext._FuncHeaderSyncInstance2 == None:
            import plugins.EdkPlugins.edk2.FuncHeaderSync2 as FuncHeaderSync2
            self._projext._FuncHeaderSyncInstance2 = FuncHeaderSync2.FuncHeaderSyncService()
            self._projext._FuncHeaderSyncInstance2.SetFrame(wx.GetApp().GetTopWindow())
            wx.GetApp().InstallService(self._projext._FuncHeaderSyncInstance2)
        self._projext._FuncHeaderSyncInstance2.Run(data.GetWorkspace(), path, libclasspath) 
               
class FilePathObject(object):
    def __init__(self, path):
        self._path = os.path.normpath(path)
    
    def GetFilename(self):
        return self._path        