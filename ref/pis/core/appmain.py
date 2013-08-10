"""@file
This module provide PISApp application class.

Project Insignt Studio is designed for managing project source code
and help developer to navigator source.

@summary: Main Entry of Project Insight Studio

"""

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__svnid__    = "$Id$"
__revision__ = "$Revision$"

import os, wx, sys, wx.aui
import wx.lib.pydocview as pydocview
import wx.lib.docview as docview
import wx.lib.flatnotebook as fnb

import core.editor
import core.config
import core.auitabbedframe
import core.plugin
import core.images
import core.syntax
import core.search
import outline
import threading
import about
import images
from optparse import OptionParser
from version import *

from util.constant import *
from core.debug import *
import gaugesplash

_ = wx.GetTranslation

AppCallBackEvent, EVT_APP_CALLBACK = wx.lib.newevent.NewEvent()

class PISApp(pydocview.DocApp):
    """Application instance inherited from pydocview.DocApp.
    
    PISApp manages:
    a) Application's main frame
    b) Plugin
    c) Document templates
    d) Service
    """
    
    def _init__(self):
        self._debug  = True
        self._splash = None
        pydocview.DocApp.__init__(redirect=False)
        
    def OnInit(self):
        self._logger  = GetAppLogger()
        self._config  = core.config.AppConfig()
        self._art     = core.art.PISArtProvider(self._logger)
        self._plugmgr = core.plugin.PluginManager()
        self._mainthread = threading.currentThread()
        
        # allow multi instance of App object
        self.SetSingleInstance(True)

        # Set correct application at first.
        self.SetAppName('Project Insight Studio')
        
        if not pydocview.DocApp.OnInit(self):
            return True

        self._startSplash()
        self.SetDefaultIcon(core.images.getAppIcon())
        
        # create document manager and load all template plugin
        self.SetDocumentManager(PISDocManager(flags=wx.lib.docview.DOC_MDI|wx.lib.docview.DOC_OPEN_ONCE))
        
        self.UpdateSplash("Load document template...")
        # load all supported templates.
        self.GetDocumentManager().LoadTemplates()
                
        self.UpdateSplash('Create main frame for Project Insight Studio')
        # create application main frame.
        self.frame = core.auitabbedframe.AuiDocTabbedParentFrame(self.GetDocumentManager(), None, -1, 
                                                                 title=self.GetAppName())
        self.SetTopWindow(self.frame)
        self.frame.Show(False)
       
        EVT_APP_CALLBACK( self, self.OnAppCallBack)
        
        # init the syntax management.
        syntaxPath = core.config.AppConfig().Get('SyntaxPath', 'syntax')
        self.UpdateSplash("Initialize syntax ...")
        core.syntax.SyntaxMgr().Initialize(syntaxPath)
       
        # install plugin-manager menu 
        self._plugmgr.Install(self.frame)
        
        self.UpdateSplash('Load services...')
        
        # load all service plugins, LoadServices must be invoked after frame created.
        self.LoadServices()
                
        self._plugmgr.InstallGeneralPlugins()
        
        # process parameter input from command line.
        self.OpenCommandLineArgs()
        self._closeSplash()
        self.frame.Show(True)
        config = wx.ConfigBase_Get()
        
        #BUGBUG: work around for default status bar can not be displayed correctly
        if config.ReadInt('MainFrameMaximized', False):
            self.frame.Maximize()        
        return True
    
    def _startSplash(self):
        self._splash = gaugesplash.GaugeSplash(images.getAppSplashBitmap())
        self._splash.setTicks(20)
        self._splash.Show()
        self._splash.Update()
        wx.Yield()
        self._splash.Update()
        wx.Yield()  
        
    def DoBackgroundListenAndLoad(self):
        # use work around methods to avoid exception of wx.EVT_MOUSE_CAPTURE_LOST
        try:
            pydocview.DocApp.DoBackgroundListenAndLoad(self)
        except:
            pydocview.DocApp.DoBackgroundListenAndLoad(self)
                
    def UpdateSplash(self, str):
        if self._splash != None:
            self._splash.tick(str)
            
    def _closeSplash(self):
        if self._splash != None:
            self._splash.Destroy()  
            self._splash = None
             
    def GetArtProvider(self):
        """Get application global theme"""
        return self._art
    
    def OpenCommandLineArgs(self):
        """
        Called to open files that have been passed to the application from the
        command line.
        """
        parser = OptionParser(version="%s - Version %s" % (PROJECT_NAME, VERSION))
        parser.add_option('-p', '--profile', action='store', 
                          type='string', dest='profile_name',
                          help='Specific profile file name for getting profiling information')
        parser.add_option('-d', '--debug', action='store', dest='verbose', default='DEBUG',
                          help='Turn on debug message and specific debug level: [DEBUG|INFO|WARNING|ERROR|CRITICAL]')
        parser.add_option('-l', '--logfile', action='store', dest='logfile',
                          help='Specific log file or server address to hold log information under specific debug level.')
        parser.add_option('-s', '--logserver', action='store', dest='logserver',
                          help='Specific log server address to hold log information under specific debug level.')
        
        (options, args) = parser.parse_args()
        
        for arg in args:
            if (wx.Platform != "__WXMSW__" or arg[0] != "/") and arg[0] != '-' and os.path.exists(arg):
                self.GetDocumentManager().CreateDocument(os.path.normpath(arg), wx.lib.docview.DOC_SILENT)
    
    def GetLogger(self):
        """Get Application logger"""
        return self._logger
    
    def GetPluginMgr(self):
        """Get plugin manager instance"""
        return self._plugmgr
    
    def GetAppLocation(self):
        """Get Application location"""
        return core.config.GetPISDir()

    def GetAppFont(self):
        face = self._config.Get('AppFont', 'Courier')
        size = self._config.GetInt('AppFontSize', 10)
        return wx.Font(size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = face)
        
    def ForegroundProcess(self, function, args):
        wx.PostEvent(self, AppCallBackEvent(callback=function, args=args))
        
    def OnAppCallBack(self, event):
        try:
            event.callback(*event.args)
        except:
            self._logger.exception( 'OnAppCallBack<%s.%s>\n' %
                (event.callback.__module__, event.callback.__name__ ))
                
    def IsInMainThread(self):
        return self._mainthread is threading.currentThread()
        
    def LoadServices(self):
        """Install all service plugins."""
        self.UpdateSplash('Install Search Engine ...')
        findService = core.search.FindService()
        findService.SetFrame(self.frame)
        self.InstallService(findService)
        findService.Activate()
        
        self.UpdateSplash('Install System Editor ...')
        editorService = core.editor.EditorService()
        editorService.SetFrame(self.frame)
        self.InstallService(editorService)
        editorService.Activate()
        aboutService = self.InstallService(pydocview.AboutService(about.AboutDialog))

        self.UpdateSplash('Install outline services ...')
        outlineServ = core.outline.OutlineService()
        outlineServ.SetFrame(self.frame)
        self.InstallService(outlineServ)

        #Search service from plugin and install this services.
        plugins = self.GetPluginMgr().GetPlugins(core.plugin.IServicePlugin)
        for instance in plugins:
            try:
                self.UpdateSplash("Install plugin %s" % instance.GetName())
                instance.Install()   
            except core.plugin.PluginException, e:
                GetPluginLogger().error(e.GetMessage())
                wx.MessageDialog(None, e.GetMessage(), 
                                "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
            except:
                ETrace()
                wx.MessageDialog(None, 'Fail to activate service plugin: %s' % instance.__class__.__name__, 
                                "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()

           
class PISDocManager(docview.DocManager):   
    def GetLogger(self):
        return wx.GetApp().GetLogger()

    def CreateDocument(self, path, flags):
        """Inherit docview.DocManager.CreateDocument() interface"""
        # work around for bug in DocManager in wxPython. if doc exists, wxPython will return None
        # but in fact it need return same document.
        for document in self._docs:
            if document.GetFilename() and os.path.normcase(document.GetFilename()) == os.path.normcase(path):
                view = document.GetFirstView()
                if view != None:
                    view.Activate()
                    if hasattr(view, 'SetFocus'):
                        view.SetFocus()                    
                return document
            
        # Call super class.
        doc  = docview.DocManager.CreateDocument(self, path, flags)
                
        # Set app title for displaying full path name of opened file.
        if doc != None:
            appname = wx.GetApp().GetAppName()
            docname = doc.GetFilename()
            wx.GetApp().GetTopWindow().SetTitle(u'%s - %s' % (appname, docname))
            return doc
        return None
    
    def OnFileSave(self, event):
        docview.DocManager.OnFileSave(self, event)
        doc = self.GetCurrentDocument()
        appname = wx.GetApp().GetAppName()
        docname = doc.GetFilename()
        wx.GetApp().GetTopWindow().SetTitle('%s - %s' % (appname, docname))
        
    def OnFileSaveAs(self, event):
        docview.DocManager.OnFileSaveAs(self, event)
        doc = self.GetCurrentDocument()
        appname = wx.GetApp().GetAppName()
        docname = doc.GetFilename()
        wx.GetApp().GetTopWindow().SetTitle('%s - %s' % (appname, docname))
        
    def GetLatestDirectory(self):
        doc = self.GetCurrentDocument()
        if doc != None:
            try:
                path = doc.GetFilename()
            except:
                return ''
            if os.path.exists(path):
                return os.path.dirname(path)
            
        count =  self.GetHistoryFilesCount()
        if count == 0:
            return ''
        else:
            path = os.path.dirname(self.GetHistoryFile(0))
            if os.path.exists(path):
                return path
            return ''
        
    def SelectDocumentPath(self, templates, flags, save):
        """
        Under Windows, pops up a file selector with a list of filters
        corresponding to document templates. The wxDocTemplate corresponding
        to the selected file's extension is returned.

        On other platforms, if there is more than one document template a
        choice list is popped up, followed by a file selector.

        This function is used in wxDocManager.CreateDocument.
        """
        if wx.Platform == "__WXMSW__" or wx.Platform == "__WXGTK__" or wx.Platform == "__WXMAC__":
            descr = ''
            for temp in templates:
                if temp.IsVisible():
                    if len(descr) > 0:
                        descr = descr + _('|')
                    descr = descr + temp.GetDescription() + _(" (") + temp.GetFileFilter() + _(") |") + temp.GetFileFilter()  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
            descr = _("All|*.*|%s") % descr  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        else:
            descr = _("*.*")

        dlg = wx.FileDialog(self.FindSuitableParent(),
                               _("Select a File"),
                               wildcard=descr,
                               defaultDir=self.GetLatestDirectory(),
                               style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        # dlg.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
            
        if path:  
            theTemplate = self.FindTemplateForPath(path)
            return (theTemplate, path)
        
        return (None, None)           
     
    def LoadTemplates(self):
        """Load all support document templates including from plugin"""
        
        wx.GetApp().UpdateSplash("Install default document template ")
        # create default text editor template for all file type.
        defaultEditor = docview.DocTemplate(self,
                                            "Text Document",
                                            "*.*",
                                            "Any",
                                            "txt",
                                            "General edtior document for text file",
                                            "General edtior view for text file",
                                            core.editor.EditorDocument,
                                            core.editor.EditorView,
                                            icon=images.getBlankIcon())
        self.AssociateTemplate(defaultEditor)
        
        pMgr = wx.GetApp().GetPluginMgr()
        plugins = pMgr.GetPlugins(core.plugin.ITemplatePlugin)
        for instance in plugins:
            if not instance.GetConfig().GetBoolean('InstallAtStartup', instance.IsInstallAtStartup()):
                continue
            
            try:
                wx.GetApp().UpdateSplash("Install template %s" % instance.GetName())
                instance.Install()
            except core.plugin.PluginException, e:
                print e.GetMessage()
            except:
                ETrace()
                wx.MessageDialog(None, 'Fail to activate template plugin: %s' % instance.__class__.__name__, 
                                "Error", wx.OK | wx.ICON_INFORMATION).ShowModal()
                
    def ActivateView(self, view, activate=True, deleting=False):
        docview.DocManager.ActivateView(self, view, activate, deleting)
        frame = wx.GetApp().GetTopWindow()
        frame.ActivateNotebookPage(view.GetFrame())
        
def CheckOSAndPython(logger):
    # Print OS and python interpreter information for future debugging.
    os_type = sys.platform 
    logger.info('OS type            : %s' % os_type)
    if os_type == 'win32':
        logger.info('Windows version    : %d.%d.%d.%s [%s]' % (sys.getwindowsversion()))
    logger.info('Python interpreter : %s' % sys.version)
    logger.info('wxPython version   : %s' % wx.__version__)
    if wx.__version__ < '2.8.7.1':
        logger.error('The version of wxPython should larger than 2.8.7.1')
        
def main():
    """Configures environment and run an instance of PIS.
    1) Create/Load config setting file for PIS.
    2) Create instance of wx.App and Launch it.
    """
    # Collect platform information.
    logger = GetGlobalLogger()
    
    CheckOSAndPython(logger)
    
    # Load application config file.
    core.config.Config().Load('ProjectInsight.cfg')
    
    # Report all unhandled exception.
    if core.config.AppConfig().GetBoolean('REPORT_ERROR', True):
        sys.excepthook = UnhandleExceptionHook
        
    # Initialize plugin-manager and load plugins ...
    core.plugin.PluginManager().LoadPlugin()
    
    # Create application instance.
    app = PISApp()
    app.MainLoop()

    