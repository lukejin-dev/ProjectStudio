import wx
import plugins.EdkPlugins.edk2.model.baseobject as baseobject
import plugins.EdkPlugins.edk2.model.dec as dec
import plugins.EdkPlugins.edk2.model.inf as inf
import wx.lib.customtreectrl as CT
import wx.lib.docview
import core.service

class SurfaceItemSearchService(core.service.PISService):
    def GetPosition(self):
        return 'bottom'
    
    def GetViewClass(self):
        return SurfaceItemSearchView    
    
    def GetName(self):
        return "EDKII Surface"
    
class SurfaceItemSearchView(core.service.PISServiceView):
    
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)

        self._searchCtl = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        self._ppiCtl    = wx.ToggleButton(self, -1, 'PPI')
        self._protocolCtl = wx.ToggleButton(self, -1, 'PROTOCOL')
        self._guidCtl   = wx.ToggleButton(self, -1, 'GUID')
        self._libCtl    = wx.ToggleButton(self, -1, 'Library Class')
        self._pcdCtl    = wx.ToggleButton(self, -1, 'PCD')
        style = wx.SUNKEN_BORDER|CT.TR_HIDE_ROOT|CT.TR_ROW_LINES|CT.TR_SINGLE|CT.TR_NO_LINES|CT.TR_FULL_ROW_HIGHLIGHT|CT.TR_HAS_BUTTONS
        self._resultCtl = CT.CustomTreeCtrl(self, -1, style=style)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        inputsizer = wx.BoxSizer(wx.HORIZONTAL)
        inputsizer.Add(self._searchCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        inputsizer.Add(self._ppiCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        inputsizer.Add(self._protocolCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        inputsizer.Add(self._guidCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        inputsizer.Add(self._libCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        inputsizer.Add(self._pcdCtl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        sizer.Add(inputsizer, 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self._resultCtl, 1, wx.EXPAND|wx.ALL, 2)
        self.SetSizer(sizer)
        self.Layout()
        
        
        self.Bind(wx.EVT_TEXT, self.OnDoSearch, self._searchCtl)
        wx.EVT_IDLE(self, self.OnIdle)
        self._needRefresh = True
        self._inRefresh   = False
        self._hasinput    = False
        self._ppiCtl.SetValue(False)
        self._protocolCtl.SetValue(False)
        self._guidCtl.SetValue(False)
        self._libCtl.SetValue(False)
        self._pcdCtl.SetValue(False)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle, self._ppiCtl)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle, self._protocolCtl)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle, self._guidCtl)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle, self._libCtl)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle, self._pcdCtl)
        CT.EVT_TREE_ITEM_EXPANDING(self, self._resultCtl.GetId(), self.OnExpand)
        CT.EVT_TREE_ITEM_ACTIVATED(self, self._resultCtl.GetId(), self.OnItemActivate)
        
        wx.EVT_CLOSE(self, self.OnClose)
        
    def OnToggle(self, event):
        self._needRefresh = True
        
    def OnDoSearch(self, event):
        if self._inRefresh:
            self._hasinput = True
        else:
            self._needRefresh = True
        
    def OnIdle(self, event):
        if self._needRefresh and not self._inRefresh:
            self.Refresh()
            
    def Refresh(self):
        self._inRefresh = True
        self.ClearResult()
        
        key = self._searchCtl.GetValue().lower()

        results = {} 
        # protocol
        if self._protocolCtl.GetValue():
            objdict = dec.DECProtocolObject.GetObjectDict()
            for objList in objdict.values():
                for obj in objList:
                    objname = obj.GetName()
                    if len(key) != 0 and not objname.lower().startswith(key):
                        continue
                    if results.has_key(objname):
                        results[objname].append(obj)
                    else:
                        results[objname] = [obj]
            
        # ppi
        if self._ppiCtl.GetValue():
            objdict = dec.DECPpiObject.GetObjectDict()
            for objList in objdict.values():
                for obj in objList:
                    objname = obj.GetName()
                    if len(key) != 0 and not objname.lower().startswith(key):
                        continue
                    if results.has_key(objname):
                        results[objname].append(obj)
                    else:
                        results[objname] = [obj]
        
        # guid
        if self._guidCtl.GetValue():
            objdict = dec.DECGuidObject.GetObjectDict()
            for objList in objdict.values():
                for obj in objList:
                    objname = obj.GetName()
                    if len(key) != 0 and not objname.lower().startswith(key):
                        continue
                    if results.has_key(objname):
                        results[objname].append(obj)
                    else:
                        results[objname] = [obj]      
                        
        #library class
        if self._libCtl.GetValue():
            objdict = dec.DECLibraryClassObject.GetObjectDict()
            for objList in objdict.values():
                for obj in objList:
                    objname = obj.GetName()
                    if len(key) != 0 and not objname.lower().startswith(key):
                        continue
                    if results.has_key(objname):
                        results[objname].append(obj)
                    else:
                        results[objname] = [obj]     
                        
        # pcd
        if self._pcdCtl.GetValue():
            objdict = dec.DECPcdObject.GetObjectDict()
            for objList in objdict.values():
                for obj in objList:
                    objname = obj.GetName()
                    if len(key) != 0 and not objname.lower().startswith(key):
                        continue
                    if results.has_key(objname):
                        results[objname].append(obj)
                    else:
                        results[objname] = [obj]          
        
        keynames = results.keys()
        keynames.sort()
        for objname in keynames:
            for item in results[objname]:
                self.AddResult(item)
        
        self._inRefresh = False
        if not self._hasinput:
            self._needRefresh = False
        else:
            self._needRefresh = True
            self._hasinput    = False
        
    def AddResult(self, obj):
        #self._resultCtl.Freeze()
        objItem = self._resultCtl.AppendItem(self._rootItem, 
                                             obj.GetName(), data=obj)
        self._resultCtl.SetItemHasChildren(objItem, True)
        #self._resultCtl.Thaw()     
        
    def ClearResult(self):
        self._resultCtl.DeleteAllItems()
        self._resultCtl.AddRoot('root')
        self._rootItem = self._resultCtl.GetRootItem()

    def OnClose(self, event):
        self._resultCtl.DeleteAllItems()
        self._resultCtl.Destroy()
        self._pcdCtl.Destroy()
        self._ppiCtl.Destroy()
        self._protocolCtl.Destroy()
        self._guidCtl.Destroy()
        self._libCtl.Destroy()
        self._searchCtl.Destroy()
        
    def OnExpand(self, event):
        item = event.GetItem()
        data = self._resultCtl.GetPyData(item)
        if data == None: return
        if issubclass(data.__class__, dec.DECGuidObject) or \
           issubclass(data.__class__, dec.DECProtocolObject) or \
           issubclass(data.__class__, dec.DECPpiObject):
            self.UpdateGuidOject(item, data)
        elif issubclass(data.__class__, dec.DECLibraryClassObject):
            self.UpdateLibrary(item, data)
        elif issubclass(data.__class__, dec.DECPcdObject):
            self.UpdatePcd(item, data)
            
    def UpdateGuidOject(self, root, obj):
        self._resultCtl.AppendItem(root, 'Defined at: %s (%d)' % (obj.GetFilename(), obj.GetStartLinenumber() + 1),
                                   data=FilenameObject(obj.GetFilename(), obj.GetStartLinenumber() + 1))
        objdict = baseobject.GuidItem.GetObjectDict()
        refobjList = {}
        for guidobj in objdict.values():
            if guidobj.GetDecObject() == obj:
                for refObj in guidobj.GetReference().values():
                    if refObj.GetFilename() not in refobjList.keys():
                        refobjList[refObj.GetFilename()] = refObj.GetStartLinenumber() + 1
        for name in refobjList.keys():
            self._resultCtl.AppendItem(root, 
                                       'Ref by: %s (%d)' % (name, refobjList[name]),
                                       data=FilenameObject(name, refobjList[name]))

    def UpdateLibrary(self, root, obj):
        self._resultCtl.AppendItem(root, 'Defined at  : %s (%d)' % (obj.GetFilename(), obj.GetStartLinenumber() + 1),
                                   data=FilenameObject(obj.GetFilename(), obj.GetStartLinenumber() + 1))
        objdict = inf.INFFile._libobjs
        if objdict.has_key(obj.GetName()):
            inflist = objdict[obj.GetName()]
            for item in inflist:
                self._resultCtl.AppendItem(root, 
                                           'Produce by: %s' % item.GetFilename(),
                                           data=FilenameObject(item.GetFilename()))
                
        # consume information
        objdict = inf.INFLibraryClassObject.GetObjectDict()
        if not objdict.has_key(obj.GetName()): return
        inflist = objdict[obj.GetName()]
        infdict = {}
        for item in inflist:
            if item.GetFilename() not in infdict.keys():
                infdict[item.GetFilename()] = item.GetStartLinenumber() + 1
                
        for name in infdict.keys():
            self._resultCtl.AppendItem(root, 
                                       'Reference by: %s (%d)' % (name, infdict[name]),
                                       data=FilenameObject(name, infdict[name]))
        
    def UpdatePcd(self, root, obj):
        self._resultCtl.AppendItem(root, 'Defined at  : %s (%d)' % (obj.GetFilename(), obj.GetStartLinenumber() + 1),
                                   data=FilenameObject(obj.GetFilename(), obj.GetStartLinenumber() + 1))
        
        objdict = inf.INFPcdObject.GetObjectDict()
        if not objdict.has_key(obj.GetName()): return
        inflist = objdict[obj.GetName()]
        infdict = {}
        for item in inflist:
            if item.GetFilename() not in infdict.keys():
                infdict[item.GetFilename()] = item.GetStartLinenumber() + 1
                        
        for name in infdict.keys():
            self._resultCtl.AppendItem(root, 
                                        'Reference by: %s (%d)' % (name, infdict[name]),
                                        data=FilenameObject(name, infdict[name]))
            
    def OnItemActivate(self, event):
        item = event.GetItem()
        data = self._resultCtl.GetPyData(item)
        if data == None: return       
        
        if issubclass(data.__class__, FilenameObject):
            docmgr = wx.GetApp().GetDocumentManager()
            doc = docmgr.CreateDocument(data.GetPath(), wx.lib.docview.DOC_SILENT)
            if doc != None:
                view = doc.GetFirstView()
                if view != None:
                    view.GotoLine(data.GetLineNum())
             
class FilenameObject:
    def __init__(self, path, linenum=1):
        self._path = path
        self._line = linenum
        
    def GetPath(self):
        return self._path     
    
    def GetLineNum(self):
        return self._line   