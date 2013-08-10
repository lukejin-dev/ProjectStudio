""" PSArtProvide for ProjectStudio
    PSArtProvide is pushed into art provider's stack at startup of application.
    
    Lu, ken (ken.lu@intel.com)
"""

import os, wx

PS_ART_CLOSE        = "PS_ART_CLOSE"
PS_ART_MINIMUM      = "PS_ART_MINIMUM"
PS_ART_APP          = "PS_ART_APP"
PS_ART_HELP         = wx.ART_HELP
PS_ART_FILE_OPEN    = wx.ART_FILE_OPEN
PS_ART_FILE_SAVE    = wx.ART_FILE_SAVE
PS_ART_FILE_SAVEALL = "PS_ART_FILE_SAVEALL"
PS_ART_FILE_NEW     = wx.ART_NEW
PS_ART_FILE_CLOSE   = "PS_ART_FILE_CLOSE"
PS_ART_TEXT_FILE_NEW = "PS_ART_TEXT_FILE_NEW"
PS_ART_COPY         = wx.ART_COPY
PS_ART_CUT          = wx.ART_CUT
PS_ART_CLEAR        = "PS_ART_CLEAR"
PS_ART_UP           = "PS_ART_UP"
PS_ART_DOWN         = "PS_ART_DOWN"
PS_ART_LOG          = "PS_ART_LOG"
PS_ART_PASTE        = wx.ART_PASTE
PS_ART_UNDO         = wx.ART_UNDO
PS_ART_REDO         = wx.ART_REDO
PS_ART_SWITCHER_WINDOW = "PS_ART_SWITCHER_WINDOW"
PS_ART_SINGLE_VIEW_LIST = "PS_ART_SINGLE_VIEW_LIST"
PS_ART_SEARCH       = "PS_ART_SEARCH"
PS_ART_SEARCH_MENU  = "PS_ART_SEARCH_MENU"
PS_ART_SEARCH_IN_FILES = "PS_ART_SEARCH_IN_FILES"
PS_ART_SEARCH_SCOPE_FOLDER = "PS_ART_SEARCH_SCOPE_FOLDER"

_imgtable = {PS_ART_CLOSE     : {16:"close_16.bmp"},
             PS_ART_MINIMUM   : {16:"minimum_16.bmp"},
             PS_ART_APP       : {16:"app_16.png", 32:"app_32.png"},   
             PS_ART_HELP      : {16:"question_blue_16.png"},
             PS_ART_FILE_SAVE : {16:"save_16.ico"},
             PS_ART_FILE_NEW  : {16:"file_new_16.ico"},
             PS_ART_FILE_OPEN : {16:"folder_open_16.ico"},
             PS_ART_FILE_CLOSE: {16:"folder_close_16.ico"},
             PS_ART_TEXT_FILE_NEW: {16:"file_add_16.ico"},
             PS_ART_FILE_SAVEALL: {16:"save_all_16.ico"},
             PS_ART_CLEAR     : {16:"clear_16.ico"},
             PS_ART_COPY      : {16:"file_copy_16.ico"},
             PS_ART_CUT       : {16:"cut_16.png"},
             PS_ART_UP        : {16:"up_16.png"},
             PS_ART_DOWN      : {16:"down_16.png"},
             PS_ART_LOG       : {16:"log_16.ico"},
             PS_ART_PASTE     : {16:"paste_16.ico"},
             PS_ART_SWITCHER_WINDOW: {16:"switcher_window_16.ico"},
             PS_ART_SINGLE_VIEW_LIST: {16:"single_view_16.ico"},
             PS_ART_UNDO      : {16:"undo_16.ico"},
             PS_ART_REDO      : {16:"redo_16.ico"},
             PS_ART_SEARCH    : {16:"search_16.png"},
             PS_ART_SEARCH_MENU: {16:"search_menu_16.ico"},
             PS_ART_SEARCH_IN_FILES:{16:"search_in_files_16.ico"},
             PS_ART_SEARCH_SCOPE_FOLDER:{16:"search_scope_16.ico"}}

class PSArtProvider(wx.ArtProvider):
    def __init__(self, log):
        self._log       = log
        self._imgPath   = os.path.join(wx.GetApp().GetAppPath(), "img")
        wx.ArtProvider.__init__(self)
        
    def _GetBitmapPath(self, path):
        return os.path.join(self._imgPath, path)
    
    def CreateBitmap(self, id, client, size=(16, 16)):
        bmp    = wx.NullBitmap
        if id in _imgtable.keys():
            if size.width in _imgtable[id].keys():
                bmppath = self._GetBitmapPath(_imgtable[id][size.width])
                if not os.path.exists(bmppath):
                    self._log.error('Fail to find the bmp file %s' % bmppath)
                else:
                    bmp = wx.Bitmap(bmppath)
            
        return bmp
        