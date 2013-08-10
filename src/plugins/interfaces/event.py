import wx
from wx.lib.newevent import *

def NewNotifyEvent():
    evttype = wx.NewEventType()       
    class _Event(wx.NotifyEvent):
        def __init__(self, **kw):
            wx.NotifyEvent.__init__(self, evttype)
            self.__dict__.update(kw)
    
    return _Event, wx.PyEventBinder(evttype, 0)

ID_FOCUS_UNDO = wx.NewId()
ID_FOCUS_REDO = wx.NewId()
ID_FOCUS_COPY = wx.NewId()
ID_FOCUS_CUT  = wx.NewId()
ID_FOCUS_PASTE = wx.NewId()
QueryFocusEditEvent, EVT_QUERY_FOCUS_EDIT_EVENT = NewCommandEvent()
FocusEditEvent, EVT_FOCUS_EDIT_EVENT = NewCommandEvent()

QueryViewSearchEvent, EVT_QUERY_VIEW_SEARCH_EVENT = NewCommandEvent()
QueryViewReplaceEvent, EVT_QUERY_VIEW_REPLACE_EVENT = NewCommandEvent()