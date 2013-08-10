""" This module prepare amber runtime environment according to boot options.

    Copyright (C) 2008 ~ 2012. All Rights Reserved.
    The contents of this file are subject to the Mozilla Public License
    Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS"
    basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
    License for the specific language governing rights and limitations
    under the License.

    Initial Developer: Lu Ken <bluewish.ken.lu@gmail.com>
"""     

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__revision__ = "$Revision: 1 $"

#======================================  External Libraries ========================================
import wx
import wx.lib.docview as docview
import optparse
import os
import sys
import lib.gaugesplash as gaugesplash
import debug

#======================================  Internal Libraries ========================================
import mainframe 
import docmgr
import debug
import logger
import image
import task
import art
#============================================== Code ===============================================
APP_NAME       = 'Amber Editor'
APP_VERSION    = '0.01'

class AmberEdtiorApp(wx.PySimpleApp):
    """ Amber Editor application object.
    """
    def __init__(self, appPath, redirect=False, filename=None, useBestVisual=False, clearSigInt=True): 
        """ Constructor funtion by overriding DocApp class.
        
        AmberEditorApp.OnInit interface will be executed when invoke DocApp.__init__
        so all pre-app setting should be done before.
        
        @param params        Command parameters including options and args
        @param redirect      redirect all sys.stdin and sys.out to a message windows
        """
        self._appPath = appPath
        self._docmgr  = None
        self._splash  = None
        self._debug   = False
        wx.PySimpleApp.__init__(self, redirect, filename, useBestVisual, clearSigInt)
        
    #------------------------- Override Interface ------------------------
    def OnInit(self):
        """ Initializes the Amber editor application. Override pydocview.DocApp.OnInit(). """
        
        # invoke DocApp.OnInit to do default work.
        if not wx.PySimpleApp.OnInit(self):
            return False

        # process command line options
        params = _processCommandLine()
        
        # set debug option, DocApp provide SetDebug() and GetDebug() interface.
        self.SetDebug(params[0].debug)
       
        self.SetAppName(APP_NAME)
                    
        # Initialize logger for pre-boot phase.
        options = params[0] 
        logger.InitAmberEditorLogger(options.loglevel, options.logfile, options.logserver)
            
        # check runtime environment as early as possible, if does not
        # match, quit application at once.
        if not self._CheckEnvironment():
            return False
            
        self.SetUseBestVisual(True, True)
        
        # push Amber's art provide to wx library
        wx.ArtProvider.Push(art.AmberEditorArtProvider())
        
        # start splash window as early as possible.
        self._StartSplashScreen()
        
        # initialize configuration manager
        
        # initialize plug-in manager and load all plug-ins
        
        # invoke all PRE_BOOT plug-ins that need be dispatched as early as possible.
        
        # create document manager.object and main frame object
        
        #self._frame = mainframe.AmberEditorFrame(None)
        import appfrm
        self._frame = appfrm.AEFrame(None) 
        self.SetTopWindow(self._frame)
        
        self._docmgr = docmgr.AmberEditorDocMgr()
        self.SetDocumentManager(self._docmgr)

        # Install services 
        
        #tt.Terminate()

        # Install templates
        
        # Initialize task manager
        self._taskmgr = task.TaskManager()

        # start default task.
        #tt = SampleTask()
        #tt.setName("Automatically Update")
        #tt.Start()
        
        
        # destroy splash window and show main frame now.
        self._StopSplashScreen()
        self._frame.Show()

        return True
    
    def OnPreInit(self):
        """ Things that must be done after _BootstrapApp has done its thing, but would be nice if they 
            were already done by the time that OnInit is called.
        """
        wx.PySimpleApp.OnPreInit(self)

    
    #-------------------------- Public Interfaces ------------------------
    def ConfigRead(self, key, default):
        """ Read string config value via wx.ConfigBase_Get(). """
        config = wx.ConfigBase_Get()
        return config.Read(key, default)
        
    def ConfigWrite(self, key, value):
        """ Write string config value via wx.ConfigBase_Get(). """
        config = wx.ConfigBase_Get()
        config.Write(key, value)
        
    def ConfigReadInt(self, key, default):
        """ Read integer config value via wx.ConfigBase_Get(). """
        config = wx.ConfigBase_Get()
        return config.ReadInt(key, default)
        
    def ConfigWriteInt(self, key, value):
        """ Write integer config value via wx.ConfigBase_Get(). """
        config = wx.ConfigBase_Get()
        return config.WriteInt(key, value)
        
    def GetDebug(self):
        """ Get whether current application is in debug mode. """
        return self._debug
    
    def GetLogger(self, name=''):
        """ Get logger object according to logger's area name
        
        @param name    logger area name.
        """
        return logger.GetLogger(name) 
        
    def GetPath(self):
        """ Get Amber Editor execute location """
        return self._appPath
        
    def SetDebug(self, debug=True):
        """ Set debug mode for current application object. """
        self._debug = debug
        if self._debug:
            self.SetAssertMode(wx.PYAPP_ASSERT_EXCEPTION)
        else:
            self.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
        
    def SetDocumentManager(self, docmgr):
        """ Set document manager to application object. """
        self._docmgr = docmgr
        
    def UpdateSplashString(self, str):
        """ Update splash string if splash screen exists. """
        if self._splash != None:
            self._splash.tick(str)
            
    #-------------------------- Private Interfaces ------------------------        
    def _StartSplashScreen(self):
        """ Start splash screen and show the loading process.
        
        The splash screen will not destroyed until _StopSplashScreen is invoked.
        UpdateSplashString() interface could be used to update process message
        for Amber loading.
        """
        self._splash = gaugesplash.GaugeSplash(image.getlogoBitmap())
        self._splash.setTicks(20)
        self._splash.Show()
        self._splash.Update()
        wx.Yield()
        self._splash.Update()
        wx.Yield()  
        
    def _StopSplashScreen(self):
        """ Stop the splash screen.
        
        After all managers are initialized and loaded. Splash screen should be 
        destroyed explicitly, and main frame is prepared to shown.
        """
        if self._splash != None:
            self._splash.Destroy()  
            self._splash = None
        
    def _CheckEnvironment(self):
        """ Check whether requirement runtime environment is available.
        Please notes: Amber Editor could only run with wxWidget larget than 2.8.7.1.
        """
        os_type = sys.platform 
        logger  = self.GetLogger()
        logger.info('OS type            : %s' % os_type)
        if os_type == 'win32':
            logger.info('Windows version    : %d.%d.%d.%s [%s]' % (sys.getwindowsversion()))
        logger.info('Python interpreter : %s' % sys.version)
        logger.info('wxPython version   : %s' % wx.__version__)
        logger.info('System encoding    : %s' % sys.getfilesystemencoding())
        logger.info('wxPython encoding  : %s' % wx.GetDefaultPyEncoding())
        return True

class SampleTask(task.Task):
    def Run(self):
        index = 0
        while index < 20 and not self.IsWantStop():
            import time
            time.sleep(1)
            index += 1    
        print 'quit task'
 
def _processCommandLine():
    """ Internal function to process all value from command line.
    
    Options and arguments will be set to global variable.
    """
    parser = optparse.OptionParser(version="%s - Version %s" % (APP_NAME, APP_VERSION))
    parser.add_option("-d", '--debug', action="store_true", dest="debug", default=True,
                      help='Debug mode?')
    parser.add_option('-l', '--loglevel', action='store', dest='loglevel', default='DEBUG',
                      help='Turn on debug message and specific debug level: [DEBUG|INFO|WARNING|ERROR|CRITICAL]')
    parser.add_option('-f', '--logfile', action='store', dest='logfile',
                      help='Specific log file or server address to hold log information under specific debug level.')
    parser.add_option('-s', '--logserver', action='store', dest='logserver',
                      help='Specific log server address to hold log information under specific debug level.')
    
    (_param_options, _param_args) = parser.parse_args()
    return [_param_options, _param_args]
    
def loadAmber(appPath):
    """ Amber loader. 
    
    1, Prepare logging system before all actions are taken.
    2, Get command line's options and args.
    3, Create app object and enter main loop.
    
    @param appPath  in source code, the path is same with amber.py
                    in frozed binary, the path is same with amber.exe
    """
    sys.excepthook = debug.UnhandleExceptionHook
    
    # create application object
    app = AmberEdtiorApp(appPath)
    
    # loop/dispatch application message
    app.MainLoop()
