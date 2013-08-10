import wx
import wx.lib.docview as docview
import ui.MessageWindow
import os
import threading
import re
import array

class ValidateManager(wx.EvtHandler):
    def __init__(self, projext):
        wx.EvtHandler.__init__(self)
        self._view      = None
        self._projext   = projext
        
    def GetView(self):
        if self._view != None:
            return self._view
        frame = wx.GetApp().GetTopWindow()
        self._view = ValidateView(frame)
        frame.AddSideWindow(self._view, 
                            'EDKII Validation',
                            'bottom')
        return self._view

    def StartCheckingLibraryClass(self, tempPath):
        self.GetView().Clear()
        self.GetView().AddText('Start validate project for over specific library class!')
        
        if not os.path.exists(tempPath):
            os.makedirs(tempPath)
            
        pObjs = self._projext.GetPlatforms()
        doneModules = []
        libtags     = {}
        protDicts   = {}
        guidDicts   = {}
        ppiDicts    = {}
        for platform in pObjs:
            wx.Yield()
            self.GetView().AddText('\n=== Validate Overspecified usage in Module INF: %s ===' % platform.GetFilename())
            for module in platform.GetModules():
                path = module.GetFilename()
                if path in doneModules:
                    continue
                doneModules.append(path)
                
                self.GetView().AddText('## Validate Module: %s' % module.GetFilename())
                
                # library class
                libdict = module.GetLibraries()
                moduleLibs = {}
                for libName in libdict.keys():
                    wx.Yield()
                    if libdict[libName] != None and libdict[libName].IsInherit():
                        continue
                    if libName not in libtags.keys():
                        libpath = self.GetHeaderFilePathByLibName(libName)
                        if libpath == None:
                            self.GetView().AddText('......Fail to find library class header for %s' % libName)
                            continue
                        self.GetView().AddText('......Process library class %s in file %s' % (libName, libpath))
                        incname = libpath[len(self._projext.GetWorkspace()) + 1:]
                        incname = incname[incname.lower().find('include') + 8:].replace('\\', '/')
                        libtags[libName] = (incname, self.GetTag(tempPath, libpath))
                    moduleLibs[libName] = libtags[libName]

                moduleProts = {}
                prots = module.GetFileObj().GetSectionObjectsByName('protocol')
                for prot in prots:
                    wx.Yield()
                    protPath = None
                    if prot.GetName() not in protDicts.keys():
                        for pObj in self._projext.GetPackages():
                            protPath = self.FindHeaderFileForGuid(pObj, prot.GetName())
                            if protPath != None:
                                break
                        if protPath == None:
                            self.GetView().AddText('......Fail to find header file for PROTOCOL %s' % prot.GetName())
                            continue
                        incname = protPath[len(self._projext.GetWorkspace()) + 1:]
                        incname = incname[incname.lower().find('include') + 8:].replace('\\', '/')
                        protDicts[prot.GetName()] = (incname, self.GetTag(tempPath, protPath))
                    moduleProts[prot.GetName()] = protDicts[prot.GetName()]
                    
                moduleGuids = {}
                guids = module.GetFileObj().GetSectionObjectsByName('guid')
                for guid in guids:
                    wx.Yield()
                    guidPath = None
                    if guid.GetName() not in guidDicts.keys():
                        for pObj in self._projext.GetPackages():
                            guidPath = self.FindHeaderFileForGuid(pObj, guid.GetName())
                            if guidPath != None:
                                break
                        if guidPath == None:
                            self.GetView().AddText('......Fail to find header file for GUID %s' % guid.GetName())
                            continue
                        incname = guidPath[len(self._projext.GetWorkspace()) + 1:]
                        incname = incname[incname.lower().find('include') + 8:].replace('\\', '/')
                        guidDicts[guid.GetName()] = (incname, self.GetTag(tempPath, guidPath))
                    moduleGuids[guid.GetName()] = guidDicts[guid.GetName()]  
                    
                modulePpis = {}
                ppis = module.GetFileObj().GetSectionObjectsByName('ppi')
                for ppi in ppis:
                    wx.Yield()
                    ppiPath = None
                    if ppi.GetName() not in ppiDicts.keys():
                        for pObj in self._projext.GetPackages():
                            ppiPath = self.FindHeaderFileForGuid(pObj, ppi.GetName())
                            if ppiPath != None:
                                break
                        if ppiPath == None:
                            self.GetView().AddText('......Fail to find header file for PPI %s' % ppi.GetName())
                            continue
                        incname = ppiPath[len(self._projext.GetWorkspace()) + 1:]
                        incname = incname[incname.lower().find('include') + 8:].replace('\\', '/')
                        ppiDicts[ppi.GetName()] = (incname, self.GetTag(tempPath, ppiPath))
                    modulePpis[ppi.GetName()] = ppiDicts[ppi.GetName()]                                        
                    
                #for key in moduleLibs.keys():
                sObjs = module.GetSourceObjs()
                texts = []
                for sObj in sObjs:
                    wx.Yield()
                    fullpath = sObj.GetSourceFullPath()
                    try:
                        f = open(fullpath, 'r')
                        texts.append(f.read())
                        f.close()
                    except:
                        self.GetView().AddText('......Fail to open source file %s' % fullpath)
                        continue
                        
                for libname in moduleLibs.keys():
                    wx.Yield()
                    # search whether contains include
                    incname = moduleLibs[libname][0]
                    found   = False
                    incre   = re.compile(r'#include[ \"\<]+%s' % incname, re.IGNORECASE)
                    for text in texts:
                        ret = incre.search(text)
                        if ret != None:
                            found = True
                            break
                    if not found:
                        self.GetView().AddText('......[Issue]: INF ref library class %s, source code do not include header file %s' % (libname, incname))
                        continue
                    found = False
                    for symbol in moduleLibs[libname][1]:
                        for text in texts:
                            if text.find(symbol) != -1:
                                found = True
                                break
                    if not found:
                        self.GetView().AddText('......[Issue]: Source code does not reference any symbol for library class %s' % libname)
                         
                for protname in moduleProts.keys():
                        wx.Yield()
                        # search whether contains include
                        incname = protDicts[protname][0]
                        found   = False
                        incre   = re.compile(r'#include[ \"\<]+%s' % incname, re.IGNORECASE)
                        for text in texts:
                            ret = incre.search(text)
                            if ret != None:
                                found = True
                                break
                        if not found:
                            self.GetView().AddText('......[Issue]: INF ref protocol %s, source code do not include header file %s' % (protname, incname))
                            continue
                        found = False
                        for symbol in protDicts[protname][1]:
                            for text in texts:
                                if text.find(symbol) != -1:
                                    found = True
                                    break
                        if not found:
                            self.GetView().AddText('......[Issue]: Source code does not reference any symbol for protocol %s' % protname)
                         
                for guidname in moduleGuids.keys():
                        wx.Yield()
                        # search whether contains include
                        incname = guidDicts[guidname][0]
                        found   = False
                        incre   = re.compile(r'#include[ \"\<]+%s' % incname, re.IGNORECASE)
                        for text in texts:
                            ret = incre.search(text)
                            if ret != None:
                                found = True
                                break
                        if not found:
                            self.GetView().AddText('......[Issue]: INF ref GUID %s, source code do not include header file %s' % (guidname, incname))
                            continue
                        found = False
                        for symbol in guidDicts[guidname][1]:
                            for text in texts:
                                if text.find(symbol) != -1:
                                    found = True
                                    break
                        if not found:
                            self.GetView().AddText('......[Issue]: Source code does not reference any symbol for GUID %s' % guidname)
                
                for ppiname in modulePpis.keys():
                        wx.Yield()
                        # search whether contains include
                        incname = ppiDicts[ppiname][0]
                        found   = False
                        incre   = re.compile(r'#include[ \"\<]+%s' % incname, re.IGNORECASE)
                        for text in texts:
                            ret = incre.search(text)
                            if ret != None:
                                found = True
                                break
                        if not found:
                            self.GetView().AddText('......[Issue]: INF ref GUID %s, source code do not include header file %s' % (ppiname, incname))
                            continue
                        found = False
                        for symbol in ppiDicts[ppiname][1]:
                            for text in texts:
                                if text.find(symbol) != -1:
                                    found = True
                                    break
                        if not found:
                            self.GetView().AddText('......[Issue]: Source code does not reference any symbol for protocol %s' % ppiname)
            
        self.GetView().AddText('<==== Finish validate overspecified usage! ====>')
        
   
    def FindHeaderFileForGuid(self, pObj, name):
        """
        For declaration header file for GUID/PPI/Protocol.
        
        @param pObj         package object
        @param name         guid/ppi/protocol's name
        @param configFile   config file object
        
        @return full path of header file and None if not found.
        """
        startPath  = pObj.GetFileObj().GetPackageRootPath()
        incPath    = os.path.join(startPath, 'Include').replace('\\', '/')
        # if <PackagePath>/include exist, then search header under it.
        if os.path.exists(incPath):
            startPath = incPath
            
        for root, dirs, files in os.walk(startPath):
            for dir in dirs:
                if dir.lower() in ['.svn', '_svn', 'cvs']:
                    dirs.remove(dir)
            for file in files:
                fPath = os.path.join(root, file)
                if not IsCHeaderFile(fPath):
                    continue
                try:
                    f = open(fPath, 'r')
                    lines = f.readlines()
                    f.close()
                except IOError:
                    self.GetView().AddText('Fail to open file %s' % fPath)
                    continue
                for line in lines:
                    if line.find(name) != -1 and \
                       line.find('extern') != -1:
                        return fPath.replace('\\', '/')
        return None                 
        
    def GetHeaderFilePathByLibName(self, libname):
        for pkg in self._projext._packages:
            path = pkg.GetLibraryClassHeaderPathByName(libname)
            if path != None:
                path = os.path.join(pkg.GetFileObj().GetPackageRootPath(), path)
                path = os.path.normpath(path)
                
                return path
        return None
    
    def GetCTagsPath(self):
        path = wx.GetApp().GetAppLocation()
        path = os.path.join(path, 'ctags.exe')
        return path
        
    def GetTag(self, root, filename):
        wsPath = self._projext.GetWorkspace()
        tagfilePath = os.path.join(root, filename[len(wsPath) + 1:]) + '.txt'
        if not os.path.exists(os.path.dirname(tagfilePath)):
            os.makedirs(os.path.dirname(tagfilePath))
        
        if os.path.exists(tagfilePath):
            if os.path.getmtime(tagfilePath) > os.path.getmtime(filename):
                return self.ReadtagFile(tagfilePath)
                
        cmd =  self.GetCTagsPath()
        cmd += ' -o ' + tagfilePath + ' '
        cmd += ' --languages=C++'
        cmd += ' --c-kinds=+lpx '
        cmd += ' --excmd=number '
        cmd += ' -V '
        cmd += filename
        
        self.GetView().AddText('......Building tag file for file %s' % filename)
        try:
            self._process = wx.Process(self)
            self._process.Redirect()
            self._pid = wx.Execute(cmd, wx.EXEC_SYNC, self._process)
            self._input = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self._process = None
            dlg = wx.MessageDialog(wx.GetApp().GetTopWindow(), "There are some problems when running the program!\nPlease run it in shell." ,
                    "Stop running", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal() 
        
        return self.ReadtagFile(tagfilePath)
                 
    def ReadtagFile(self, path):
        try:
            file  = open(path, 'r')
            lines = file.readlines()
            file.close()
        except:
            self.GetView().AddText('Fail to load tag file %s' % path)
            return None
        if len(lines) <= 6:
            return None
        symbos = []
        for line in lines[6:]:
            symbos.append(line.split()[0])
            
        return symbos
            
class CreateTagThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)    
    
class ValidateView(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Panel'):    
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._message = ui.MessageWindow.MessageWindow(self, -1)
        #self._message.SetCaretLineVisible(False)
        #self._message.SetCaretForeground('#FFFFFF')    
        
        sizer.Add(self._message, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def Clear(self):
        self._message.ClearAll()

    def AddText(self, text):
        self._message.AddText(text)
        self._message.AddText(os.linesep)
        self._message.DocumentEnd()

def IsCHeaderFile(path):
    return CheckPathPostfix(path, 'h')   
    
def CheckPathPostfix(path, str):
    index = path.rfind('.')
    if index == -1:
        return False
    if path[index + 1:].lower() == str.lower():
        return True
    return False           