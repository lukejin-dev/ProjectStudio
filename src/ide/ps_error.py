import os, traceback, logging
import wx
import wx.lib.agw.genericmessagedialog as gmd

def hookUnhandleException(type, value, trace):
    # log the exception firstly
    traceStr = "".join(traceback.format_exception(type, value, trace))
    logging.getLogger("").exception(traceStr)
    
    # pop up the message box
    messageStr = "Project Studio meets with unhandle exception as follows:\n\n%s \n Please ref log.txt for detail information." % traceStr
    dlg = gmd.GenericMessageDialog(None, messageStr,
                                   caption=">>>> Unhandled Exception <<<<", style=wx.ICON_ERROR|wx.OK)
    dlg.ShowModal()
    dlg.Destroy()
    
def notifyError(caption, message):
    logging.getLogger("").error("[NotifyError]: %s" % message)
    dlg = gmd.GenericMessageDialog(None, message, caption, style=wx.ICON_ERROR|wx.OK)
    dlg.ShowModal()
    dlg.Destroy()   
    
    
def notifyConfirm(caption, message):
    ret = False
    dlg = gmd.GenericMessageDialog(None, message, caption, style=wx.ICON_ASTERISK|wx.OK|wx.CANCEL)
    if dlg.ShowModal() == wx.ID_OK:
        ret = True
    dlg.Destroy()
    return ret