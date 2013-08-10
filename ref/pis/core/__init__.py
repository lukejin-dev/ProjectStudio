
import uuid
import wx.stc
import wx.lib.multisash
import wx.gizmos

import ui.MessageWindow
import debug
import wx.lib.throbber
import wx.lib.platebtn
import wx.media
import zlib, cStringIO
import threading
import ConfigParser
import xml.dom.minidom
import wx.wizard
import wx.lib.customtreectrl
if wx.Platform == '__WXMSW__':
    import wx.lib.iewin
import util.utility
try:
    import wx.lib.pdfwin
except:
    debug.GetAppLogger().error('Fail to find wx.lib.pdfwin library!')

try:
    import pysvn
except:
    debug.GetAppLogger().error('fail to import pysvn')
    
import core.hexctrl    
import core.pe