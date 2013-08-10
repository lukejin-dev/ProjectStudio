import wx
import wx.lib.docview as docview
import core.plugin
import core.service
import os
import xml.dom.minidom as minidom
import xmlparser
import time
    
_plugin_module_info_ = [{"name":"Project",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide basic project management",
                         "class":"ProjectPlugin",
                         "dependencis":"ProjectTemplate"},
                         {"name":"Project document template",
                          "author":"ken",
                          "version":"1.0",
                          "description":"Provide general project document template",
                          "class":"ProjectTemplate"}]
  
class ProjectException(Exception):
    def __init__(self, message):
        self._message = message
        
    def GetMessage(self):
        return '[Project Failure]: %s' %self._message
                                 
class ProjectPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return ProjectService
    
class ProjectTemplate(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'EWS'
    
    def IGetDocumentClass(self):
        return ProjectDocument
    
    def IGetViewClass(self):
        return ProjectView
    
    def IGetFilter(self):
        return '*.ews'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'ews'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'ews'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_INVISIBLE
    
    def IGetIcon(self):
        """Interface for child class provide template's icon"""
        return getWorkspaceIcon()
                
class ProjectDocument(docview.Document):
    def __init__(self):
        docview.Document.__init__(self)
        self._name      = None
        self._extension = None
        self._extension_name = None
        
    def SetExtensionName(self, extname):
        self._extension_name = extname
        
    def GetExtension(self):
        if self._extension != None: return self._extension
        
        if self._extension_name == None: return None
        
        serv = wx.GetApp().GetService(ProjectService)
        if serv == None:
            raise ProjectException("Fail to get project service!")
            return False
        self._extension = serv.GetExtensionByName(self._extension_name)        
        return self._extension
        
    def GetService(self):
        serv = wx.GetApp().GetService(ProjectService)
        if serv == None:
            raise ProjectException("Fail to get project service!")
            return None
        return serv
        
    def OnOpenDocument(self, filename):
        self.GetService().GetLogger().info("Open project file %s" % filename)
        docmgr  = wx.GetApp().GetDocumentManager()
        docs    = docmgr.GetDocuments()
        
        for doc in docs:
            if doc != self and issubclass(doc.__class__, ProjectDocument):
                self.GetService().GetLogger().info("Close project doc %s" % doc.GetFilename())
                docmgr.CloseDocument(doc)
        ret = docview.Document.OnOpenDocument(self, filename)
        if ret:
            wx.GetApp().GetDocumentManager().AddFileToHistory(filename)
        return ret
            
    def LoadObject(self, fileobject):
        dom = minidom.parse(fileobject)
        self._name = xmlparser.XmlElement(dom, '/Project/Name')
        extName = xmlparser.XmlElement(dom, '/Project/ExtensionName')

        self.SetExtensionName(extName)
        self.GetExtension()
        
        if self._extension == None:
            wx.MessageBox("Can not detect project type, please check ExtensionName section in project ews file!",
                          "Fail to open project!",
                          wx.OK | wx.ICON_EXCLAMATION)
            raise ProjectException("Can not detect project type, please check ExtensionName section in project ews file!")
            return False
        
        if not self._extension.ILoadExtension(dom, self.GetFilename()):
            return False
            
        return True
        
    def SaveObject(self, fileobject):
        impl = minidom.getDOMImplementation()
        dom  = impl.createDocument(None, "Project", None)
        
        root = dom.documentElement
        nameItem = dom.createElement('Name')
        nameItem.appendChild(dom.createTextNode(self.GetExtension().IGetProjectName()))
        root.appendChild(nameItem)
        
        extnameItem = dom.createElement('ExtensionName')
        extnameItem.appendChild(dom.createTextNode(self.GetExtension().IGetName()))
        
        root.appendChild(extnameItem)
        
        extrootItem = dom.createElement('Extension')
        self.GetExtension().ISaveExtension(extrootItem, dom)
        root.appendChild(extrootItem)
        
        #try:
        dom.writexml(fileobject, indent="  ", addindent="  ", newl='\n')
        #except:
        #    wx.MessageBox("Fail to save project file!")
        
    def OnCloseDocument(self):
        ret = docview.Document.OnCloseDocument(self)
        self.GetExtension().ICloseProject()
        return ret
        
class ProjectView(docview.View):
    def __init__(self):
        service = wx.GetApp().GetService(ProjectService)
        if service == None:
            raise ProjectExcept("Fail to get project service instance for creating project view!")
        self._service = service
        self._service_view = service.GetView()
        docview.View.__init__(self)
        
        self._extension = None
        
    def OnUpdate(self, sender, hint):
        # if send and hint = none, means view is just created
        if sender == None and  hint == None:
            self._extension = self.GetDocument().GetExtension()
            if self._extension == None: return
            self._service_view = self._service.CreateView()
            self._extension.ICreateProjectNavigateView(self, self._service_view)
        
    def ProcessEvent(self, event):
        return docview.View.ProcessEvent(self, event)
        
    def ProcessUpdateUIEvent(self, event):
        return docview.View.ProcessUpdateUIEvent(self, event)
        
    def OnClose(self, deleteWindow):
        docview.View.OnClose(self, deleteWindow)
        self._service.DestroyView()
        #self._service_view.CreateDefaultControl()
        
class ProjectService(core.service.PISService):  
    ID_PROJECT_MENU_NEW         = wx.NewId()
    ID_PROJECT_MENU_OPEN        = wx.NewId()
    ID_PROJECT_MENU_CLOSE       = wx.NewId()
    ID_PROJECT_MENU_PROPERTIES  = wx.NewId()
    ID_PROJECT_SUBMENU_PROJECTS = wx.NewId()
    ID_PROJECT_MENU_RECENT_OPEN = wx.NewId()
    
    def __init__(self):
        core.service.PISService.__init__(self)
        self._extension         = {}  # menu id: extension
        self._menu_project_type = wx.Menu()
        self._menu_recent_open  = wx.Menu()
        self._id_mapping        = []
        config = wx.ConfigBase_Get()
        str    = config.Read("RecentlyOpenedProject", "")
        if len(str) != 0:
            arr = str.split(";")
            for path in arr:
                if not os.path.exists(path): continue
                id = wx.NewId()
                item = self._menu_recent_open.Append(id, path)
                self._id_mapping.append((id, item))
                wx.EVT_MENU(wx.GetApp().GetTopWindow(), id, self.OnOpenRecentProject)
        
        self._synThread = None   
        self._currext   = None   
        
    def GetPosition(self):
        return 'right'
    
    def GetName(self):
        return 'Workspace'
    
    def GetViewClass(self):
        return ProjectServiceView
    
    def GetIcon(self):
        """Interface for child class provide template's icon"""
        return getWorkspaceIcon()  
        
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        viewIndex = menuBar.FindMenu('View')
        
        projectMenu = wx.Menu()
        menuBar.Insert(viewIndex + 1, projectMenu, 'Project')
        
        #projectMenu.AppendMenu(self.ID_PROJECT_MENU_NEW, 'New Project', self._menu_project_type)
        item = wx.MenuItem(projectMenu, self.ID_PROJECT_MENU_NEW, 'New Project')
        item.SetSubMenu(self._menu_project_type)
        item.SetBitmap(getNewProjectBitmap())  
        projectMenu.AppendItem(item)                         
        item = wx.MenuItem(projectMenu, self.ID_PROJECT_MENU_OPEN, 'Open Project', 'Open existing project!')
        projectMenu.AppendItem(item)                                     
        item = wx.MenuItem(projectMenu, self.ID_PROJECT_MENU_CLOSE, 'Close Project', 'Close current project!')
        projectMenu.AppendItem(item)                                
        projectMenu.AppendMenu(self.ID_PROJECT_MENU_RECENT_OPEN, "Recently Opened Project", self._menu_recent_open)
        projectMenu.AppendSeparator()

        item = wx.MenuItem(projectMenu, self.ID_PROJECT_MENU_PROPERTIES, 'Project Properties', 'Setting Project Properties!')
        projectMenu.AppendItem(item)                       
        
        wx.EVT_UPDATE_UI(frame, self.ID_PROJECT_MENU_NEW, self.OnUpdateUI)
        wx.EVT_UPDATE_UI(frame, self.ID_PROJECT_MENU_CLOSE, self.OnUpdateUI)
        wx.EVT_UPDATE_UI(frame, self.ID_PROJECT_MENU_PROPERTIES, self.OnUpdateUI)
        wx.EVT_UPDATE_UI(frame, self.ID_PROJECT_MENU_RECENT_OPEN, self.OnUpdateUI)
        wx.EVT_MENU(frame, self.ID_PROJECT_MENU_OPEN, self.OnOpenProject)
        wx.EVT_MENU(frame, self.ID_PROJECT_MENU_CLOSE, self.OnCloseProject)
        wx.EVT_MENU(frame, self.ID_PROJECT_MENU_PROPERTIES, self.OnProjectProperties)
        
    def OnUpdateUI(self, event):
        id = event.GetId()
        if id == self.ID_PROJECT_MENU_NEW:
            event.Enable(len(self._extension.keys()))
        elif id == self.ID_PROJECT_MENU_CLOSE or \
             id == self.ID_PROJECT_MENU_PROPERTIES:
            event.Enable(self.GetCurrentProjectDoc() != None)
        elif id == self.ID_PROJECT_MENU_RECENT_OPEN:
            event.Enable(self._menu_recent_open.GetMenuItemCount())
            
    def RegisterProjectExtension(self, extension):
        frame = wx.GetApp().GetTopWindow()
        id = wx.NewId()
        self._menu_project_type.Append(id, extension.IGetName(), extension.IGetName())
        self._extension[id] = extension
        wx.EVT_MENU(frame, id, self.OnNewProjectExtension)
        
    def CreateProjectDoc(self, filename):
        docmgr   = wx.GetApp().GetDocumentManager()
        template = docmgr.FindTemplateForPath('*.ews')
        doc      = template.CreateDocument(filename, docview.DOC_NEW)
        
        return doc
        
    def OnNewProjectExtension(self, event):
        id = event.GetId()
        if not self._extension.has_key(id): return
        
        self.CloseCurrentProjectDoc()
        
        ext = self.GetExtensionByName(self._extension[id].IGetName())
        doc = ext.INewProject()
        if doc == None: return
        dir = os.path.dirname(doc.GetFilename())
        self.AddProjectToHistory(os.path.join(dir, '%s.ews' % ext._projectName))
        self.OpenProjectTag(ext.IGetProjectPath(), ext.IGetProjectName())
        
    def CloseCurrentProjectDoc(self):
        doc = self.GetCurrentProjectDoc()
        if doc != None:
            docmgr = wx.GetApp().GetDocumentManager()
            docmgr.CloseDocument(doc)
            self.CloseProjectTag()
            
    def GetCurrentProjectDoc(self):
        docmgr = wx.GetApp().GetDocumentManager()
        docs   = docmgr.GetDocuments()
        for doc in docs:
            if issubclass(doc.__class__, ProjectDocument):
                return doc
        return None
        
    def OnOpenRecentProject(self, event):
        id = event.GetId()
        for map in self._id_mapping:
            if id == map[0]:
                path = map[1].GetText()
                if os.path.exists(path):
                    docmgr = wx.GetApp().GetDocumentManager()
                    doc = docmgr.CreateDocument(path, docview.DOC_SILENT)
                    if doc != None:
                        ext = doc.GetExtension()
                        self.OpenProjectTag(ext.IGetProjectPath(),
                                            ext.IGetProjectName())
                return
        
    def AddProjectToHistory(self, path):
        for item in self._menu_recent_open.GetMenuItems():
            if item.GetText() == path:
                return
        if self._menu_recent_open.GetMenuItemCount() >= 10:
            id, item = self._id_mapping[9] 
            self._menu_recent_open.Delete(id)
        
        id   = wx.NewId()
        item = self._menu_recent_open.Insert(0, id, path)
        self._id_mapping.insert(0, (id, item)) 
        wx.EVT_MENU(wx.GetApp().GetTopWindow(), id, self.OnOpenRecentProject)
        
        arr = []
        for item in self._menu_recent_open.GetMenuItems():
            arr.append(item.GetText())
        config = wx.ConfigBase_Get()
        config.Write("RecentlyOpenedProject", ";".join(arr))
            
    def OnOpenProject(self, event):
        frame  = wx.GetApp().GetTopWindow()
        docmgr = wx.GetApp().GetDocumentManager()

        dlg = wx.FileDialog(wx.GetApp().GetTopWindow(),
                            "Open existing project",
                            os.getcwd(),
                            wildcard="Project file (*.ews)|*.ews",
                            style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            docmgr = wx.GetApp().GetDocumentManager()
            ret = docmgr.CreateDocument(dlg.GetPath(), docview.DOC_SILENT)
            if ret == None:
                docmgr.CloseDocument(self.GetCurrentProjectDoc())
            else:
                self.AddProjectToHistory(dlg.GetPath())
                ext = ret.GetExtension()
                self.OpenProjectTag(ext.IGetProjectPath(),
                                    ext.IGetProjectName())
                                    
    def OnCloseProject(self, event):
        self.CloseCurrentProjectDoc()
            
    def GetExtensionByName(self, name):
        if name == None: return None
        
        for ext in self._extension.values():
            if ext.IGetName().lower() == name.lower():
                return ext
        return None

    def OnProjectProperties(self, event):
        doc = self.GetCurrentProjectDoc()
        ext = doc.GetExtension()
        if ext == None:
            wx.MessageBox("Can not get project extension for setup project properties dialog!")
            return
        ext.IProperties()

    def Activate(self, show=True):
        core.service.PISService.Activate(self, show)
        self._synThread = ProjectSynchronizeThread(self.GetLogger(), self.OnProjectFileChanged)
        self._synThread.start()
                
    def OnCloseFrame(self, event):
        if self._synThread != None:
            self._synThread.Shutdown()
        return True
        
    def AddMonitorFile(self, path):
        self._synThread.AddMonitorFile(path)
        
    def RemoveMonitorFile(self, path):
        self._synThread.RemoveMonitorFile(path)
        
    def RemoveAllMonitorFiles(self):
        self._synThread.RemoveAllFiles()
        
    def OnProjectFileChanged(self, path):
        self.GetLogger().info("Project file %s is changed!" % path)
        doc = self.GetCurrentProjectDoc()
        if doc == None: return
        ext = doc.GetExtension()
        if hasattr(ext, "OnProjectFileChanged"):
            ext.OnProjectFileChanged(path)
            
    def OpenProjectTag(self, path, name):
        serv = self.GetTagService()
        if serv == None:
            return
        serv.OpenTag(os.path.join(path, '%s.tag' % name))
        
    def CloseProjectTag(self):
        serv = self.GetTagService()
        if serv == None:
            return
        serv.CloseTag()
        
    def GetTagService(self):
        pm = wx.GetApp().GetPluginMgr()
        p  = pm.GetPlugin('TagPlugin')
        if p != None:
            serv = p.GetServiceInstance()
            return serv        
        return None
                    
    def BuildTags(self, path, files):
        pm = wx.GetApp().GetPluginMgr()
        p  = pm.GetPlugin('TagPlugin')
        if p != None:
            serv = p.GetServiceInstance()
            
        serv.BuildTags(path, files)
                
import threading, os
class ProjectSynchronizeThread(threading.Thread):
    def __init__(self, logger, callback):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self._files            = {} # It is a file and time tuple
        self._files_queue_lock = threading.Lock()
        self._running          = True
        self._work_semaphore   = threading.Semaphore(0)
        self._callback         = callback
        self._logger           = logger
        
    def AddMonitorFile(self, path):
        if not os.path.exists(path):
            return
        path = os.path.normpath(path)
        time = os.path.getmtime(path)
        
        self._files_queue_lock.acquire()
        if not self._files.has_key(path):
            self._files[path] = time
            if len(self._files.keys()) == 1:
                self._work_semaphore.release()
        self._files_queue_lock.release()
        
    def RemoveMonitorFile(self, path):
        if not os.path.exists(path):
            return
        path = os.path.normpath(path)
        
        self._files_queue_lock.acquire()
        if self._files.has_key(path):
            del self._files[path]
        self._files_queue_lock.release()
        
    def RemoveAllFiles(self):
        if len(self._files.keys()) == 0: return
        self._files_queue_lock.acquire()
        self._files.clear()
        self._files_queue_lock.release()
        
    def run(self):
        self._logger.info("Project file synchronize thread is started!")
        app = wx.GetApp()
        while self._running:
            # sleep can make other threads been schedual.
            time.sleep(5)

            if len(self._files.keys()) == 0:
                self._logger.info("Monitor thread is hand up, because no files required to be monitor!")
                self._work_semaphore.acquire()
            self._files_queue_lock.acquire()
            for file in self._files.keys():
                if not os.path.exists(file):
                    continue 
                if self._files[file] != os.path.getmtime(file):
                    self._files[file] = os.path.getmtime(file)
                    if self._callback != None:
                        app.ForegroundProcess(self._callback, (file, ))
            self._files_queue_lock.release()

        self._logger.info("Project file synchronize thread is shutdown!")
    
    def Shutdown(self):
        self._work_semaphore.release()
        self._running = False
        
class ProjectServiceView(core.service.PISServiceView):   
    def __init__(self, parent, service, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name='Panel'):
        core.service.PISServiceView.__init__(self, parent, service, id, pos, size, style, name)
        self.CreateDefaultControl()
        
    def CreateDefaultControl(self):
        self.DestroyChildren()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, "No Project is opened!"), 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.Layout()
        self.SetAutoLayout(True)
        
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib
        
def getWorkspaceData():
    return zlib.decompress(
'x\xda\x01\xd4\x07+\xf8\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x07\x8bIDATX\x85\xc5\x97Mo\x1b\xd7\x15\x86\x9f\xe1\x90\x1c\
\xcd\x90&%jDQ\x92\xad\xda\xb1"\xc4\x89\xa5\xb8F\xe3\x08\x0e\xb2i\x9a\x06\xe8\
\xa2m\xda\x02FvYv\x91\x1f\xd1\xbf\xd0}\x17]\x14-` (\\\x07E\xea\xc4\x81\x1b\
\xc4\n\x1d\xc9\x92Z\xdbR$\xda\xa6>BR#r\xf8\xa5\xe1\x8c\xe6\x8b\xd3\xc5\xd0\
\x8c?\xa4\xd6\xed"=\x00A\x82s\xe7\x9e\xe7\xbc\xf7\x9ds\xe7\n\xf0\x9b\x00\x02\
\xbe\x9b\xd8E\x88\xfcNx\xfc\x9f\xc8w\x94\xf9\xc8\xf8\xbf\x03Dgf@UUTU%\x16\
\x8b\x1d:\xa8\xdb\xedb\x9a&\xa6i"\xcb\x03(J\x02Q\x14\x9f\x18\xe3\xfb>\xa6ibY\
\x16\x8a\xa2\xa0(\n\xb6mc\x9a&\x9a\xa6\xb1\xb5\xb5E\xa3Q|\x16\xe0\xe2E\x98\
\x9d\x1dgvv\x16YV\x0e\x05\xf0}\x9f\xbd=\x8d\xdd]\rU\x1dft4G<\x1e\x7fb\x8c\
\xe38h\x9aF\xadV#\x97\x1b%\x9b\x1d\xa5\xd9l\xa2i\xbb,,\xe8X\xd6\x03\x1a\x8d;\
\xcf\x02\x8c\x8d\xc1\xd4T\x92W_\x1d%\x99L\x1e\tP\xadF\xd9\xdb\x8b\x91H$H\xa5\
\xc2\n%I\x02\xe8W\x9a\xcd\xaa\x18\xc6\x00\xa9T\x8ac\xc7d,\x0b&&"\xb4Z\xc7\
\xc8\xe7;\x80\x0e<\xa9\\\xf4\xd0\x8cO\x85 \x08\xa4R)\xe2\xf18\x86aP\xadVI&\
\x93\xa8\xaa\n\x80\xae\xeb\x18\x86A2\x99d||\x1c\xc30\xa8T*\xc8\xb2\xcc\xf0\
\xf00\xaa\xaa\xf6a\x9fQ\xe0\xa8\x8a]\xd7%\x08\x02b\xb1\x18\xd1h\xb4\xbf\xae\
\x9e\xe7\xd1h4\xb0,\x0b\xd34\x01\xb0,\x0b\xc7q\x10\x04\x81\x81\x81\x01\x0c\
\xc3\xc0\xb6m$I"\x1e\x8f\x13\x8f\xc7\x89D\x0e\xf7\xfb\xa1\x00\xb6m\xd3h4p]\
\x97\xa1\xa1!\xd2\xe9t\xffZ"\x91`ll\x8c\x83\x83\x03\x9a\xcd&\x00\xb2,\x93L&q\
\x1c\x87R\xa9\x84$I\x8c\x8d\x8d\xe1y\x1e\xb5Z\x8dZ\xad\x86m\xdb\x87\x02\x1c\
\x8a\xe5\xba.\xadV\x8bz\xbd\x8ei\x9ax\x9e\x87\xef\xfb\x04A\x80,\xcbd2\x19$I\
\xa2\xd3\xe9\xd0\xe9t\x90$\x89t:\x8d\xef\xfb\xe8\xba\x0e@&\x93!\x16\x8b\xd1n\
\xb7i\xb5Z\xb8\xae\xfb\xfc\nH\x92\x84\xaa\xaaX\x96\x85m\xdb\x94J%R\xa9\x14\
\xe9t\x1a\xc30h\xb5Z\xf8\xbe\xcf\xe0\xe0`\x7f\tL\xd3$\x1a\x8d211A\x10\x04T*\
\x15\x04A@UUFFF\x8e\xf4\xc0\xa1\n<\x02\xc8d2}\x80v\xbb\r\xd07\x98i\x9a\xa4\
\xd3i\xd2\xe94\xa6iR\xadV\xfb\x00\x00\x95J\x05\xdb\xb6\xff7\x13\n\x82\x80 \
\x08\xc4\xe3q\x06\x07\x07\x11E\xb1_\x95\xe7yd2\x19"\x91\x08\xfb\xfb\xfb\x00\
\x0c\x0c\x0c\x10\x8f\xc7\xf1}\x1fM\xd3\x00\xc8f\xb3\x88\xa2H\xa3\xd1\xa0\xdb\
\xedr\xea\xd4)\xaa\xd5*\xabk_\xffg\x05\x1eE,\x16chh\x88\\.\x07@\xa9T\xc2u]FF\
FP\x14\x85f\xb3I\xb3\xd9DQ\x14FFF\xf0<\x8fR\xa9\x04@.\x97C\x92$t]\xc7\xf7}N\
\x9f>\xcd\xec\xec\xec\xf3)\xf0(\x0c\xd7\xa0\xa0\x17xX}\x88^\xd0\xa9\xad\xd7x\
\xe1\xd4 \xd3\xd3*\x8a\x92!\x12\xc9\x10\x8b\xa5\xf0<\x0f\xcb\xb2\x10\x04\x81\
\x84\xa2`no\xb3\xbd\xb2\xc2\xa6\xae\xb3\xa1\xebTt\x9dj\xb5J\xadV\xfb\xef\x00\
\xeaf\x9dk\x0f\xaeq\xf5\xceU\x9c\xdb\x0e\xf6m\x9b\xd9Wbh\x9a\xc4\x993o2=\xfd\
\x0b\x92\xc9A\x9a\xcd&\xb6m\x93N\xa7\x19\xcf\xe5X\xbfy\x93\x8d\x0f?d\xa5\xd1\
`\xd1q\xa8:\x0e\xb6mcY\xd6\xf3\x01\xb4\x0eZ\x94\xf7\xcb,\xd7\x96\x99\xef\xcc\
\x93\xf7\xf3\xb0\x07\xac\xc2H\x06\\\x17\xda\xed\x01\x8a\xc5)\x12\t\x88F\xa3\
\xc4"\x11\x0e*\x15\x02\xcb\xc2^Z\x82|\x9e\x86\xa1p\x9fqv\xc9\xf4f\xee D\x9eT\
\xe1P\x80\xed\xf66W\xd7\xafr\xa3~\x83\x82Z\x80\x0bar"\x90\xcb\xc1\xf9\xf3\
\xd0l\x16\xf8\xe8\xa3?\x11\x8d\x16x\xfb\xed\xb7939\xc9\xf6\'\x9fP\xfe\xec3\
\xd4B\x81\xf3\xb6\xcd6\x17P\xf8)p\xbc7\xf3C\x82\xee_\x02\xf8\x02!"\n\xcf\x00\
\x18\x8eA\xeb\xa0\xc5\x1d\xfd\x0e\x9fj\x9fr\xc3\xba\x01S\xbd\xfb\x8f\x03C\
\x90\x99\x80\xa9i\xf8z\xb5\xcc\xceN\x19\xcfn37\xf3\x02\xc82\xc6\xe2"\xda\x95\
+\xa8\xc0\x08\x90f\x8c(\xaf\x03\xaf\x00\x12\xb0\x01\x94\x80-\xa0\xfc\xac\x02\
k\xd55\xae\x17\xafs\xcb\xbaE1W\x844\x90%\xdc\xc0&\x819\xe0T8\xd7\x8b/\xc2{\
\xefA\xa3X\xa6\xbbv\x95{\xd7\xf3(\xcb\xcb\\\x00L`\tx\xc0\x1e&+\xa1t\xbc\xd0\
\x9b\xec\'@\x96\xa0{=\x80\xcfB\x80 \x08\xe8v\xbb\xac\xd7\xd6\xb9|\xef2+\x03+\
p\x91\xb0\xfa.`A\xf4x\x14\xf1u\x11\xf1\xa4\x8f/\xfaL\x9e\x08\x98\x9c\x80R^c\
\xe1\xb7\x1fs\xff\n\xbc\x06\xcc\x00\xf3\xc0m`S\xd4\xe9\x8ak\xc4\x82c\xf8~\
\x86n\xf7{\xc0[\xbdQu\xfa\x00\xedv\x9br\xb9L\xbd^\x0f{\xf6@O\x123TL\xda\x95\
\x98\x13\xe6\x98\xbb0\xc7\xc9\xc8\n\xf7W\xf3\x94j-\xf8\x06\x82{\xa0\x16`8\
\xe4\xe4K \xdf\xfbN\x9d\xcdri\xee\x1c\xe5\xe6\x18\xf9\xfc7lm\xb5\x1e\xf3\xc3\
c&\xdc\xdf\xdf\xa7\\.\xa3\xd7u\x1c\xc7\xf9\xf6\xaa\x05<\x00i]\xe2\x8d\xef\
\xbf\xc1\x07\x17>\xe0\xfe\xbd?\xf0\xcf\xa5U\xf6\x17Z\xf0\x15\x8cm\xc3y;\\\
\xf3\xe5^\xe5_\xf6>??\x9b\xe5\xd2\xfb\xe7\xd8\xda\x1e\xa0T\xba\xcd\xd6\x96\
\xdb\xf3\xc2\xf0\xb7\x00KKKt:\x1d\x00\xeaZ\x1dg\xdd\x81\xc8\x18\x94\xce\x822\
\x02\x0f\xf6\x88\xe8\x0e\xf2\xf8I\x06\xe3CH\xba\x82\xbb,"\xdd\x85l\x052\x06\
\xb4\x08\x9f\xd2\xdb\xc0\x82\x08\xa9\xb3\xf0\xee\x0c\xbc\xf9\xc3(\xc7OH\xe8^\
\x87\xd8\x995\xe8\xee@v\x1b\xe4$\xdc\xb9\x03w!:??\x8f\xe38\xc8\xb2\x8c\xbe\
\xa5\xe3.\xb8\xd08\x01\xf2\xbb \xce\x80\xb5\x02\xd2&\xfc\xe08t#\xb0\x1bf\x1a\
\xbe\x0f3V(\xe1\x06p\xb7\xb7\xf6\xff\x10\xe1\xd2\x1c\\z\x1f\x8e\x9f\x80\xe1a\
\xa0\xd9\x80\x97Wa<\x0f\xe7\xbe\x80\xa1(\xfc^\x0f\x01j\xb5\x1a\x9b\x9b\x9b\
\xc8\xb2\x8c\xa6iX\x15\x0b\x1a\x89\x9e\xed\xcf\x02"nb\x88\xf5\x95\x0e\x1f\
\x7f|\x8d\xe0\xf6=\xb2%\x93\xc1}p\x81j/\xf9=\x19\xa4S\xf0\xda\x8bp\xee"\xbc\
\xfc\n4\x1a;\xdc\xba\xf59\x0b\r\r=\xf7\x10\xa6w\xe1\x0c\xa1\xc7z\xab\x10\x15\
"\xa2\xb0\xbeQ`}\xa3\x00@,*>vL\x92\x81\xd3\xd8\xf61n\xde\xfc\x1b;;\xd7x\xab\
\xb2\xc9;\xbd\xady\x8b\xb0?\xcd\x03\xd5\x14\xfc\xf8-\xf8\xd1\xbb09\t\x92\x04\
w\xef\xde\xe5\xf2\xe5\x16\xcb\xe9\x03\xb6\xdf\xd9\x86Y\xc2G\xdbx\xca\x84\x8f\
Gh\xc2\xfd\xd0}\x9c\x04F\xf1\xbc\t\x8a\xc5\x06\xc5\xe2\xe7\x9c\xe4\x80\xa07\
\xc7*\xb0\x08|\r\xb81PF\xe1\xa5\x97 \x91\x00Q\x0c\xdf\t\xbe\xfa\xaa\xc2\xdaI\
\xe0g\xc0P\xcf,\x05@;\x02 l\x91\xcb\x04\xddD\x00;\x84\x8d\xe3\\\xff\xfa.a\
\x93\xd1{\x95o\x00\x9b\x11Q\xa0\x0c\xc5\xa2\x1f\xe4\xf30=\rSSO\xcf\xdcK\xfeW\
\xe0:\x08WD\x81\xc8\xbf\xdd\r\xffN\xd8.s\xbd\x8f\x01\x04}\x00\rX\x01*\xc0\
\xa3\xd3f\xb1\x08\xf9<x\x1e(\n4\x9b\xe1o\x0ez\xc4^\x98\x9c?\xd3\x7f\x13\x11\
\x84\xc8\x93\x07\x85\xc3"\xe8\xfe:\x08\xc5^d\x14\x9f\x89\x1eN\xa1\xb7\xa1<\
\x1d\xbf\xfa\xa5\x1f\x8c\x8f\xc3\xda\x1a,.B=E\xd8&%\x10\xfe\xf8\xe4=\xcf\t\
\xe0\x1fz~\x17\x8e\x008j\xfca\xf7\xfc\x0b\x19\xc1\x80q\xe0\xa4\xd7]\x00\x00\
\x00\x00IEND\xaeB`\x82F\xdc\xb9.' )

def getWorkspaceBitmap():
    return BitmapFromImage(getWorkspaceImage().Scale(16, 16))

def getWorkspaceImage():
    stream = cStringIO.StringIO(getWorkspaceData())
    return ImageFromStream(stream)

def getWorkspaceIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getWorkspaceBitmap())
    return icon     
    
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getNewProjectData():
    return zlib.decompress(
'x\xda\x01\x82\x03}\xfc\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x039IDATX\x85\xd5\x97[\x88NQ\x14\xc7\x7fg\x8c\xf9\xbe\x8c\
\x861C\xc8e\xe4R\xc2\x03\xa2\xc6\xbddD\x94\x94"eP\x12j\x9e<\x10J\x9e\xc6\xe5\
\x85\x07\x97\x88\x9aG\xb77Qr+yB\xc6u\\\x1a\xd3P\x18\xd3\xccg\xe6\xbb\x9cs\
\xf69g{X\xfb|3\xc77#$\xdfg\xbd\xec}\xf6m\xad\xff\x7f\xad\xbd\xd6>V2\xa9\xc9\
\xa7\x14\xe5U;P\x1cv:\x1a\xeb4@\xd9\xf01\x94\x96\x97\x03\xd0r\xff\x18\x00U\
\xf3v\x01`\xdb1\xba:\xba\x01\x182y\xb7\xf57\x0c(\x1c\x06\x86\x8d\x9b\r@\xfb\
\x8b\xe3\x0c\xa9\xde\x08@\xbcb\x96,\x8aK\x9c\xb4?:EKl;\x00w\xaf\xb4i\x80\x8c\
+si\xc7\xb4\xae\x8e\xf4\x01lWt\xd8J\xa3<\x19\xbbyh\xac\x151\xa0$\xe6\x000~\
\xfe6\x88\xcf\x04`\xe8\xc4\t29h\x04\x00U\x0bK\x18\xf0%\x0e@\xa3=\x0c\x80\xc1\
J\x0et\xc2\xd6\xd3\xb8*\x00\xc0\xcd\x8e\xc91\xca\x0bx\xf8\xe4\x8d\xd18\x16($\
\x17\xbc\xbfw\x18\x80x\xe5L*\xa6\x8e\x02`\xd0\xe8\xa5\x00d\xda\xef\x03\xf0\
\xf5\xf9-,\xf7\x03\x00\xcd\xad+\x00Hf\x04e\xd26m& -d\xe2x\xb9W<\xf0U\xe4;\
\xef\x0cXa"\x1a\x98>\xa3\x01Jb\nb\xd3\x01H%\x12\x00\x94V\x8c\x94\xd5\xe9\x87\
\xa0\x07\xcb\\\xf1\xe6_\xbe\x86I\x13\x0c\xca\xd3\xac\xad\xdd\t\xc0\x9dK\xe7,\
(\x00\x06\xb21\xf0V\\Ki\xdby\xc6\xcdZ\x05@Ws\x8b\x8c\xc5\xe7\x02\xd0\xf2\xe0\
\x1c\xa9\xcaM\x00\xbcI\xbd\xd0\x005s\xa6\xf5\xcbD\xca \xf7L,<{\xd5\xd4\xbf\
\x01\xe96\x99\x1c?i!h\x1f\x00\xcb}\'\x8a?/\x00\xa0r\xf2bb\x9d\x8d\x00\xd4\
\x1f}\x05@\xcd\xc5\xb3\xb9\x8a\x95Q\xec\x8bb?\xe8\xbf\xde\x14\x8e\x0b\xde\
\x17\xd5\x020\xa3\xe2%\xd7\x9eKV\xa4H\xe8\xf6>I&)\x1e\xb08\xbbq\xff\x1eio?~m\
\xd0\xca\x9a\x9a9\xd3,\xdf \x0f\x19P\xfe\xff\xc0\x80\xeb\xd8\x00\x04\xdd\xad\
\x800\xb0b\xde\x14\x00\x8a,\x893OkBt\xbe\x17E\xb9|\xfd\x0e\x00\xaa\x1bN\xeap\
\xcc3\xbe\x0f\xf7\xa4\xec\\&\xf2\xcf@\xb2\xab\x15\x00\xc7\x91\x92\x15$\x9a\
\xc8d2@\x8f\xef\x0e4\xb4\x03R\xd52&\x93\x86\x15n\xdf\x9ahjU\x81\xce"\xef\xb9\
\x05f\x8f\xeaa \xd4\x9b\x7f\x06\x82@\xccSJ \xf9\x89\x97\xd9x\x08\xcb\xe9\xde\
u\xf2BR\xbe\xc63p\\\x13\x03\xdf:\xdb\x00\xd0:D\x1d`.\x04\xbe\xa4\x93,#\xbd%\
\xd4[\\6\xb4J\x16y\x92\x88\xbcD3\x8e\xeb\x1a\x03d\xd1\xe1\xcbR\x13\xfarA\xdd\
2/r\xb0\xef\xe7\x06__\x06\x84z\xf3\xef\x82\x1f\x07\xbct\x07J\x0b<\xdb<\xa9v\
\xae,\x03@\xf9A60\xc3\xa7UwGgd\xff\xd3\xb7\x1fq\xa3\xa4\xfcT\n\x8f\x81\xd5\r\
[\xd9\xb4A 8&\x06N_\x97\xa7x_1\xb0\xa5:z\r\xeb\x8f\xd4\xff\x96\x01yg\xc0\xea\
\xeb\xd7\xec\xc2\xd5\x1b\x1a`\xc9\x82E\x00\xa4\xbb>\x03\xa0<\x1f\xa5\xfcl\
\xbfw{\xf0\xc8\t\xa0\xe7\xa5\xf3\xab\x92\xe3\x82\xde\xb2uW\xdd\xef\x9c\xf5GR\
\x98.\xf8\x97\x92w\x06\xbe\x03\xe6\x90\xa9\xb6\xb7\xa0\xf3W\x00\x00\x00\x00I\
END\xaeB`\x82\xf1l\x92&' )

def getNewProjectBitmap():
    return BitmapFromImage(getNewProjectImage().Scale(16,16))

def getNewProjectImage():
    stream = cStringIO.StringIO(getNewProjectData())
    return ImageFromStream(stream)

def getNewProjectIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getNewProjectBitmap())
    return icon
       