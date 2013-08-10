import os, sys
import wx
import xml.dom.minidom

import ps_utility
from interfaces.core import IPlugin

class PSPluginManager:
    def __init__(self):
        self._logger  = wx.GetApp().GetLogger("plugin")
        self._plugins = {}
        
    def LoadPlugins(self, rootPath):
        """Load plugin meta xml under the plugin root path.
        
        plugin meta xml file always under the first level sub directory.
        """
        if not os.path.exists(rootPath):
            wx.GetApp().NotifyError("PluginError", "The plug-in root directory %s does not exist!" % rootPath)
            return False
        
        for pluginPath in os.listdir(rootPath):
            # Skip source control directory
            if pluginPath.lower() in ps_utility.PS_IGNORE_DIRS:
                continue
            
            # Skip file path
            if os.path.isfile(pluginPath):
                continue
            
            # Check whether plugin.xml exists.
            for file in os.listdir(os.path.join(rootPath, pluginPath)):
                # Skip the directory.
                if os.path.isdir(file):
                    continue
                
                if file.lower() == "plugin.xml":
                    fullpath = os.path.join(rootPath, pluginPath, file)
                    try:
                        instance = PSPlugin(fullpath, self._logger)
                    except Exception, e:
                        self._logger.exception(str(e))
                        self._logger.error("Fail to load plugin meta file from %s" % fullpath)
                        continue
                    else:
                        if self._plugins.has_key(instance._name.lower()):
                            self._logger.error("Fail to load plugin, there already exists a plugin %s in same name!" % self._plugins[instance._name.lower()]._metafile)
                            continue
                        
                        import imp
                        for point, location in instance._exts:
                            sys.path.insert(0, os.path.join(instance._path, location))
                            
                            try:
                                file, path, description = imp.find_module(point, [os.path.join(instance._path, location)])
                            except Exception:
                                self._logger.exception("Fail to find entry module %s under %s" % (point, location))
                                continue
                            
                            try:
                                mod = imp.load_module(point, file, path, description)
                            except Exception:
                                self._logger.exception("Fail to load module %s" % point)
                                continue
                               
                            if not hasattr(mod, "__extension_main__"):
                                self._logger.error("Fail to find __extension_main__ in module %s" % point)
                                continue
                            
                            try:
                                mod.__extension_main__(instance)
                            except Exception, e:
                                import traceback
                                traceback
                                traceStr = traceback.format_exc()
                                self._logger.error("Fail to execute the extension point %s\n%s\n%s\n" % (point, str(e), traceStr))
                            
                        self._plugins[instance._name.lower()] = instance
        
                    
class PSPlugin(IPlugin):
    def __init__(self, metafile, logger):
        self._path           = os.path.dirname(metafile)
        self._metafile       = metafile
        self._PSversion      = None         # the PS version which plugin required
        self._name           = None         # plug-in name key
        self._author         = None
        self._homepage       = None
        self._license        = None        
        self._description    = None  
        self._exts           = []
        self._libs           = []
        self._logger         = logger
        self._load()
    
    def GetPath(self):
        return self._path
    
    def GetMetaFilePath(self):
        return self._metafile
    
    def GetName(self):
        return self._name
    
    def _load(self):
        assert os.path.exists(self._metafile), "[MetaFile] Plugin metafile %s does not exist!"
        doc = xml.dom.minidom.parse(self._metafile)
        for node in doc.childNodes:
            if isinstance(node, xml.dom.minidom.ProcessingInstruction):
                if node.target.lower() != "projectstudio":
                    raise PSPluginException("[MetaFile] Invalid target %s, should be ProjectStudio!" % node.target)
                for data in node.data.split():
                    if data.split("=")[0].lower() == "version":
                        self._PSversion = data.split("=")[1]
            else:
                if node.tagName.lower() == "plugin":
                    # Process <plugin> section
                    for pluginnode in node.childNodes:
                        if pluginnode.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
                            if pluginnode.tagName.lower() == "name":
                                self._name = self._getNodeText(pluginnode)
                                continue
                            if pluginnode.tagName.lower() == "description":
                                self._description = self._getNodeText(pluginnode)
                                continue
                            if pluginnode.tagName.lower() == "author":
                                self._author = self._getNodeText(pluginnode)
                                continue
                            if pluginnode.tagName.lower() == "homepage":
                                self._homepage = self._getNodeText(pluginnode)
                                continue
                            if pluginnode.tagName.lower() == "license":
                                self._license = self._getNodeText(pluginnode)
                                continue
                            if pluginnode.tagName.lower() == "extension":
                                self._exts.append(self._getExtension(pluginnode))
                                continue
                            if pluginnode.tagName.lower() == "library":
                                self._libs.append(self._getLibrary(pluginnode))
                                continue
        self._validate()
        
    def _getNodeText(self, node):
        if len(node.childNodes) == 0 or node.childNodes[0].nodeType != xml.dom.minidom.Node.TEXT_NODE:
            raise PSPluginException("[MetaFile] Missing content in %s section!" % node.tagName)
        textnode = node.childNodes[0]
        return textnode.nodeValue.strip()
    
    def _getExtension(self, extRoot):
        point = None
        location = None
        for node in extRoot.childNodes:
            if node.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                continue
            if node.tagName.lower() == "point":
                point = self._getNodeText(node)
            elif node.tagName.lower() == "location":
                location = self._getNodeText(node)
        if point == None or location == None:
            raise PSPluginException("[MetaFile] Externsion section must contains point and location subsection!")
        
        return (point, location)
    
    def _getLibrary(self, libRoot):
        ostype = None
        location = None
        for node in libRoot.childNodes:
            if node.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                continue
            if node.tagName.lower() == "ostype":
                ostype = self._getNodeText(node)
            elif node.tagName.lower() == "location":
                location = self._getNodeText(node)
        if ostype == None or location == None:
            raise PSPluginException("[MetaFile] Library section must contains <ostype> and <location> subsection!")
        
        return (ostype, location)
        
    def _validate(self):
        if self._name == None:
            raise PSPluginException("Invalid plugin name!")
        for point, location in self._exts:
            fullpath = os.path.join(self._path, location)
            if not os.path.exists(fullpath):
                raise PSPluginException("Extension location %s does not exist!" % fullpath)
            pathlist = point.split(".")
            if len(pathlist) == 1:
                continue
            subpath = os.sep.join(pathlist[0:-1])
            subpath = os.path.join(fullpath, subpath)
            if not os.path.exists(subpath):
                raise PSPluginException("Extension path %s does not exist!" % subpath)
                
        for ostype, location in self._libs:
            if ostype not in ps_utility.PS_OS_TYPE:
                raise PSPluginException("The os type %s of libraries does not in %s" % (ostype, " ".join(ps_utility.PS_OS_TYPE)))
            if not os.path.exists(os.path.join(self._path, location)):
                raise PSPluginException("The location of libraries %s does not exist!" % os.path.join(self._path, location))
            
class PSPluginException(Exception):               
    def __init__(self, message):
        self._message = "[PluginException] %s" % message
        
    def __str__(self):
        return self._message