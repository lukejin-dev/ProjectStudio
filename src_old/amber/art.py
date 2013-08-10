""" This module provide task manager.

    The task in Amber is a execution thread.
    
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

#======================================  Internal Libraries ========================================
import image

ART_AMBER_APP_ICON          = "ART_AMBER_APP_ICON"
ART_AMBER_VIEW_SIDE_WINDOW  = "ART_AMBER_VIEW_SIDE_WINDOW"

#============================================== Code ===============================================
class AmberEditorArtProvider(wx.ArtProvider):
    """All bitmap for amber editor should be provided by this class.
    """
    def CreateBitmap(self, artid, client, size):
        bmp = wx.NullBitmap
        
        if artid == ART_AMBER_APP_ICON:
            if size.width == 16:
                bmp = image.getFrameBitmap()
        elif artid == ART_AMBER_VIEW_SIDE_WINDOW:
            if size.width == 16:
                bmp = image.getviewbookBitmap()
        return bmp