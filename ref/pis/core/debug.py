
__author__ = "Lu Ken <bluewish.ken.lu@gmail.com>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

import logging, logging.handlers, time, traceback, os, sys, platform
import version
import wx
_ = wx.GetTranslation

LOGGER_AREA = ['',         # global root logger
               'app',     # PIS core logger
               'plugin'    # General plugin logger
               'ui',       # UI logger
               ]

LEVEL = {'NOTSET':logging.NOTSET, 'DEBUG':logging.DEBUG, 'INFO':logging.INFO, 
         'WARNING':logging.WARNING, 'ERROR':logging.ERROR, 'CRITICAL':logging.CRITICAL}

def IniLogging(level, file=None, server=None):
    """Init logging system according to command line argument.
    @param level    output information level string. 
    @param file     if file is specificed, all log message will be redirected to log
                    log file but not stdout.
    @param server   remote logging server IP address. 
    """
    logging.basicConfig(level=LEVEL[level], 
                        #format='%(asctime)s %(name)-8s %(levelname)s %(message)s',
                        format='%(name)-8s %(levelname)-8s %(message)s',
                        filename=file,
                        filemode='w')
    
    if server != None:
        socketHandler = logging.handlers.SocketHandler(server,
                                                       logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    
        # Bind socket handle to all message level.
        for area in LOGGER_AREA:
            logger = logging.getLogger(area)
            logger.addHandler(socketHandler)
    
def GetAppLogger():
    return logging.getLogger('app')
    
def GetGlobalLogger():
    return logging.getLogger()  

def GetPluginLogger():
    return logging.getLogger('plugin')

def GetDocMgrLogger():
	return logging.getLogger('DocManager')
	
def GetSyntaxLogger():
    return logging.getLogger('Syntax')
    
def ETrace():
    import traceback
    message = traceback.format_exception(*sys.exc_info())
    GetAppLogger().error('[Traceback] %s' % ''.join(message))    
    
def TimeStamp():
    """Create a formatted time stamp of current time
    @return: Time stamp of the current time (Day Month Date HH:MM:SS Year)
    @rtype: string

    """
    now = time.localtime(time.time())
    now = time.asctime(now)
    return now

def FormatTrace(etype, value, trace):
    """Formats the given traceback
    @return: Formatted string of traceback with attached timestamp

    """
    exc = traceback.format_exception(etype, value, trace)
    exc.insert(0, "*** %s ***%s" % (TimeStamp(), os.linesep))
    return "".join(exc)

def UnhandleExceptionHook(exctype, value, trace):
    """Handler for all unhandled exceptions
    @param exctype: Exception Type
    @param value: Error Value
    @param trace: Trace back info

    """
    ftrace = FormatTrace(exctype, value, trace)

    # Ensure that error gets raised to console as well
    print ftrace

    # If abort has been set and we get here again do a more forcefull shutdown
    
    if ErrorDialog.ABORT:
        os._exit(1)

    # Prevent multiple reporter dialogs from opening at once
    
    if not ErrorDialog.REPORTER_ACTIVE and not ErrorDialog.ABORT:
        ErrorDialog(ftrace)

def EnvironmentInfo():
    """Returns a string of the systems information
    @return: System information string

    """
    info = list()
    info.append("#---- Notes ----#")
    info.append("Please provide additional information about the crash here")
    info.extend(["", "", ""])
    info.append("#---- System Information ----#")
    info.append("%s Version: %s" % (version.PROJECT_NAME, version.VERSION))
    info.append("Operating System: %s" % wx.GetOsDescription())
    if sys.platform == 'darwin':
        info.append("Mac OSX: %s" % platform.mac_ver()[0])
    info.append("Python Version: %s" % sys.version)
    info.append("wxPython Version: %s" % wx.version())
    info.append("wxPython Info: (%s)" % ", ".join(wx.PlatformInfo))
    info.append("Python Encoding: Default=%s  File=%s" % \
                (sys.getdefaultencoding(), sys.getfilesystemencoding()))
    info.append("wxPython Encoding: %s" % wx.GetDefaultPyEncoding())
    info.append("System Architecture: %s %s" % (platform.architecture()[0], \
                                                platform.machine()))
    info.append("Byte order: %s" % sys.byteorder)
    info.append("Frozen: %s" % str(getattr(sys, 'frozen', 'False')))
    info.append("#---- End System Information ----#")
    info.append("#---- Runtime Variables ----#")
    return os.linesep.join(info)
    
class ErrorReporter(object):
    """Crash/Error Reporter Service
    @summary: Stores all errors caught during the current session and
              is implemented as a singleton so that all errors pushed
              onto it are kept in one central location no matter where
              the object is called from.

    """
    instance = None
    _first = True
    def __init__(self):
        """Initialize the reporter
        @note: The ErrorReporter is a singleton.

        """
        # Ensure init only happens once
        if self._first:
            object.__init__(self)
            self._first = False
            self._sessionerr = list()
        else:
            pass

    def __new__(cls, *args, **kargs):
        """Maintain only a single instance of this object
        @return: instance of this class

        """
        if not cls.instance:
            cls.instance = object.__new__(cls, *args, **kargs)
        return cls.instance

    def AddMessage(self, msg):
        """Adds a message to the reporters list of session errors
        @param msg: The Error Message to save

        """
        if msg not in self._sessionerr:
            self._sessionerr.append(msg)

    def GetErrorStack(self):
        """Returns all the errors caught during this session
        @return: formatted log message of errors

        """
        return "\n\n".join(self._sessionerr)

    def GetLastError(self):
        """Gets the last error from the current session
        @return: Error Message String

        """
        if len(self._sessionerr):
            return self._sessionerr[-1]
        
import wx
ID_SEND = wx.NewId()
class ErrorDialog(wx.Dialog):
    """Dialog for showing errors and and notifying Editra.org should the
    user choose so.

    """
    ABORT = False
    REPORTER_ACTIVE = False
    def __init__(self, message):
        """Initialize the dialog
        @param message: Error message to display

        """
        ErrorDialog.REPORTER_ACTIVE = True
        wx.Dialog.__init__(self, None, title="Error/Crash Reporter", 
                           style=wx.DEFAULT_DIALOG_STYLE)
        
        # Give message to ErrorReporter
        ErrorReporter().AddMessage(message)

        # Attributes
        self.err_msg = "%s\n\n%s\n%s\n%s" % (EnvironmentInfo(), \
                                             "#---- Traceback Info ----#", \
                                             ErrorReporter().GetErrorStack(), \
                                             "#---- End Traceback Info ----#")
        # Layout
        self._DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Auto show at end of init
        self.CenterOnParent()
        self.ShowModal()

    def _DoLayout(self):
        """Layout the dialog and prepare it to be shown
        @note: Do not call this method in your code

        """
        # Objects
        import core.art
        icon = wx.StaticBitmap(self, 
                               bitmap=core.art.PISArtProvider.GetBitmap(wx.ART_ERROR))
        mainmsg = wx.StaticText(self, 
                                label="Error: Unhandle exception bad happend\n"
                                        "Help improve PIS by clicking on "
                                        "Report Error\nto send the Error "
                                        "Traceback shown below.")
        t_lbl = wx.StaticText(self, label=_("Error Traceback:"))
        tctrl = wx.TextCtrl(self, value=self.err_msg, style=wx.TE_MULTILINE)
        abort_b = wx.Button(self, wx.ID_ABORT, _("Abort"))
        send_b = wx.Button(self, ID_SEND, _("Report Error"))
        send_b.SetDefault()
        close_b = wx.Button(self, wx.ID_CLOSE)

        # Layout
        sizer = wx.GridBagSizer()
        sizer.AddMany([(icon, (1, 1)), (mainmsg, (1, 2), (1, 2)), 
                       ((2, 2), (3, 0)), (t_lbl, (3, 1), (1, 2)),
                       (tctrl, (4, 1), (8, 5), wx.EXPAND), ((5, 5), (4, 6)),
                       ((2, 2), (12, 0)),
                       (abort_b, (13, 1), (1, 1), wx.ALIGN_LEFT),
                       (send_b, (13, 3), (1, 2), wx.ALIGN_RIGHT),
                       (close_b, (13, 5), (1, 1), wx.ALIGN_RIGHT),
                       ((2, 2), (14, 0))])
        self.SetSizer(sizer)
        self.SetInitialSize()

    def OnButton(self, evt):
        """Handles button events
        @param evt: event that called this handler
        @postcondition: Dialog is closed
        @postcondition: If Report Event then email program is opened

        """
        e_id = evt.GetId()
        if e_id == wx.ID_CLOSE:
            self.Close()
        elif e_id == ID_SEND:
            addr = version.CONTACT_EMAIL
            import email.Utils
            err_msg = email.Utils.encode_rfc2231(self.err_msg)
            msg  = "mailto:%s?subject=Error Report&body=%s" % (addr, err_msg)
            msg  = msg.replace("'", '')
            import webbrowser
            print msg
            webbrowser.open(msg)
            self.Close()
        elif e_id == wx.ID_ABORT:
            ErrorDialog.ABORT = True
            # Try a nice shutdown first time through
            wx.CallLater(500, wx.GetApp().OnExit)
            self.Close()
        else:
            evt.Skip()

    def OnClose(self, evt):
        """Cleans up the dialog when it is closed
        @param evt: Event that called this handler

        """
        ErrorDialog.REPORTER_ACTIVE = False
        self.Destroy()
        evt.Skip()
        