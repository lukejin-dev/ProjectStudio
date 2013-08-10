import plugins.EdkPlugins.basemodel.ini as ini
import re, os
from plugins.EdkPlugins.basemodel.message import *

class EDKDSCFile(ini.BaseINIFile):
    def __init__(self, efisource, edksource):
        ini.BaseINIFile.__init__(self)
        self._efisource = efisource
        self._edksource = edksource
        self._cached_makefile = []
        
    def GetEdkSource(self):
        return self._edksource
        
    def GetEfiSource(self):
        return self._efisource
        
    def GetCacheMakefile(self):
        if len(self._cached_makefile) != 0: return self._cached_makefile
        path = os.path.dirname(self.GetFilename())
        path = os.path.join(path, "makefile")
        if not os.path.exists(path): return self._cached_makefile
        try:
            f = open(path, 'r')
            self._cached_makefile = f.readlines()
            f.close()
        except:
            ErrorMsg("Fail to read file", path)
        
        return self._cached_makefile
        
    def GetMacro(self, name):
        if name == 'EFI_SOURCE':
            return self._efisource
        if name == 'EDK_SOURCE':
            return self._edksource
        
        ret = self.GetDefine(name)
        if ret != None: return ret
        
        # find from makefile
        lines = self.GetCacheMakefile()
        valuere = re.compile(r"^%s[ ]*=(.+)" % name)
        for line in lines:
            line = line.strip()
            m = valuere.match(line)
            if m != None:
                return m.groups()[0].strip()
        return None
        
    def GetDefine(self, name):
        defsects = self.GetSectionByName('defines')
        if len(defsects) == 0: return None
        for sect in defsects:
            ret = sect.GetDefine(name)
            if ret != None:
                return ret
        return None
        
    def GetSectionInstance(self, parent, name, isCombined=False):
        arr = name.split(".")
        if arr[0].lower() == "defines":
            return EDKDSCDefineSection(parent, name, isCombined)
            
        return EDKDSCCommonSection(parent, name, isCombined)
        
class EDKDSCCommonSection(ini.BaseINISection):
    def GetSectionINIObject(self, parent):
        return EDKDSCCommonObject(parent)

refstr_re = re.compile("^!include[ ]+\"(.+)\"")
macro_re = re.compile("\$\((\w+)\)")

class EDKDSCCommonObject(ini.BaseINISectionObject):
    def __init__(self, parent):
        ini.BaseINISectionObject.__init__(self, parent)
        self._isRef = False
        
    def IsRef(self):
        return self._isRef
        
    def Parse(self):
        line = self.GetLineByOffset(self._start).strip()

        m = refstr_re.match(line)
        if m != None:
            self._isRef = True
            newdscpath = self._expandMacro(m.groups()[0])
            self._ref  = EDKDSCFile(self.GetFileObj().GetEfiSource(), 
                                    self.GetFileObj().GetEdkSource())
            self._ref.Parse(newdscpath)
            
        return True
        
    def _expandMacro(self, str):
        dscfile = self.GetParent().GetParent()
        m = macro_re.findall(str)
        if m == None: return str
        for item in m:
            value = dscfile.GetMacro(item)
            if value == None:
                ErrorMsg("Fail to expand macro %s in DSC context!" % item,
                         self.GetFilename(),
                         self.GetStartLinenumber() + 1)
            else:
                str = str.replace("$(%s)" % item, value)
        return str
        
class EDKDSCDefineSection(EDKDSCCommonSection):
    def GetDefine(self, name):
        #for obj in self._objs:
        #    if not obj.IsRef():
        for obj in self._objs:
            if not obj.IsRef():
                line = obj.GetLineByOffset(self._start)
                arr = line.split('=')
                if arr == None or len(arr) != 2: continue
                defname = arr[0].strip()
                if defname.lower() == name.lower():
                    return arr[1]
        return None
                    
            