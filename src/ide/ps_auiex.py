import wx
from lib.aui import *
from lib.aui.aui_switcherdialog import *
import ps_art

class PSToolbar(AuiToolBar):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=AUI_TB_DEFAULT_STYLE):
        AuiToolBar.__init__(self, parent, id, pos, size, style)
        self.SetArtProvider(PSToolBarArt())
         
    def OnPaint(self, event):
        return AuiToolBar.OnPaint(self, event)
         
    
class PSAuiManager(AuiManager):
    
    def GetPanes(self):
        return self._panes
     
    def CreateNotebook(self):
        """
        Creates an automatic L{auibook.AuiNotebook} when a pane is docked on
        top of another pane.
        """
        style = AUI_NB_TAB_MOVE|AUI_NB_BOTTOM|AUI_NB_SUB_NOTEBOOK|AUI_NB_TAB_EXTERNAL_MOVE|wx.NO_BORDER
        notebook = AuiNotebook(self._frame, -1, wx.Point(0, 0), wx.Size(0, 0), style=style)
        notebook.SetArtProvider(VC71TabArt()) 
        notebook.SetTabCtrlHeight(25)
        #notebook.SetArtProvider(FF2TabArt())
        # This is so we can get the tab-drag event.
        notebook.GetAuiManager().SetMasterManager(self)
        self._notebooks.append(notebook)
        notebook.Bind(EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChanged)
        return notebook
    
    def ResetNotebook(self):
        notebooks = []
        for child_pane in self._panes:
            if child_pane.IsNotebookPage():
                child_pane.SetDockPos(GetNotebookRoot(self._panes, child_pane.notebook_id))
                child_pane.window.Reparent(self._frame)
                child_pane.frame = None
                child_pane.notebook_id = -1
            if child_pane.IsNotebookControl():
                notebooks.append(child_pane)
                
        for notebook in notebooks:
            self.DetachPane(notebook.window)
            del notebook.buttons[:]
            notebook.window.Destroy()

        self._notebooks = []
        
    def OnNotebookPageChanged(self, event):
        notebook = event.GetEventObject()
        pageWnd  = notebook.GetPage(event.GetSelection())
        paneinfo = self.GetPane(pageWnd)
        notebookpane = self.GetPane(notebook)
        notebookpane.icon_name = paneinfo.icon_name
        notebookpane.icon = wx.ArtProvider_GetBitmap(paneinfo.icon_name, size=(16, 16))
        wx.CallAfter(self.Update)
        
class PSToolBarArt(AuiDefaultToolBarArt):
    def Clone(self):
        return PSToolBarArt()
    
    def DrawPlainBackground(self, dc, wnd, _rect):
        """
        Draws a toolbar background with a plain colour.

        This method contrasts with the default behaviour of the AuiToolBar that
        draws a background gradient and this break the window design when putting
        it within a control that has margin between the borders and the toolbar
        (example: put AuiToolBar within a wx.StaticBoxSizer that has a plain background).
      
        :param `dc`: a L{wx.DC} device context;
        :param `wnd`: a wx.Window derived window;
        :param `_rect`: the L{AuiToolBar} rectangle;
        :param `horizontal`: True if the toolbar is horizontal, False if it is vertical.
        """
        
        rect = wx.Rect(*_rect)
        rect.height += 1

        dc.SetBrush(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)))
        dc.DrawRectangle(rect.x - 1, rect.y - 1, rect.width + 2, rect.height + 1)
                
    def DrawGripper(self, dc, wnd, rect):
        """
        Override original griper drawing function.
        """
        if self._flags & AUI_TB_VERTICAL:
            startx = rect.x + 1
            endx   = rect.x + rect.GetWidth() - 1
            starty = rect.y + 1
            if endx < startx: return
            dc.SetPen(self._gripper_pen3)
            dc.DrawLine(startx, starty + 1, startx, starty + 5)
            dc.DrawLine(startx, starty + 1, endx - 1, starty + 1)
            dc.DrawLine(startx, starty + 2, endx - 1, starty + 2)
            dc.SetPen(self._gripper_pen2)
            dc.DrawLine(startx + 1, starty + 3, endx, starty + 3)
            dc.SetPen(self._gripper_pen1)
            dc.DrawLine(startx, starty + 4, endx, starty + 4)
            dc.DrawLine(endx, starty + 1, endx, starty + 5)
        else:
            starty = rect.y + 1
            endy   = rect.y + rect.GetHeight() - 1
            startx = rect.x + 1
            if endy < starty: return
            dc.SetPen(self._gripper_pen3)
            dc.DrawLine(startx + 1, endy, startx + 5, endy)
            dc.DrawLine(startx + 1, starty, startx + 1, endy - 1)
            dc.DrawLine(startx + 2, starty, startx + 2, endy - 1)
            dc.SetPen(self._gripper_pen2)
            dc.DrawLine(startx + 3, starty + 1, startx + 3, endy)
            dc.SetPen(self._gripper_pen1)
            dc.DrawLine(startx + 4, starty, startx + 4, endy)
            dc.DrawLine(startx + 1, endy, startx + 5, endy)
            
    def DrawOverflowButton(self, dc, wnd, rect, state):
        """
        Draws the overflow button for the L{AuiToolBar}.
        
        :param `dc`: a L{wx.DC} device context;
        :param `wnd`: a wx.Window derived window;
        :param `rect`: the L{AuiToolBar} rectangle;
        :param `state`: the overflow button state.
        """
        if state & AUI_BUTTON_STATE_HOVER:
            cli_rect = wnd.GetClientRect()
            light_gray_bg = self._highlight_colour
            if self._flags & AUI_TB_VERTICAL:
                dc.SetPen(wx.WHITE_PEN)
                dc.DrawLine(rect.x, rect.y, rect.x, rect.y + rect.width)
                dc.DrawLine(rect.x, rect.y, rect.x + rect.width, rect.y)
                dc.SetPen(wx.Pen(light_gray_bg))
                dc.DrawLine(rect.x + 1, rect.y + rect.height - 1, rect.x + rect.width, rect.y + rect.height - 1)
                dc.DrawLine(rect.x + rect.width - 1, rect.y + 1, rect.x + rect.width - 1, rect.y + rect.height)
            else:
                dc.SetPen(wx.WHITE_PEN)
                dc.DrawLine(rect.x, rect.y, rect.x+rect.width, rect.y)
                dc.DrawLine(rect.x, rect.y, rect.x, rect.y + rect.height)
                dc.SetPen(wx.Pen(light_gray_bg))
                dc.DrawLine(rect.x + rect.width - 1, rect.y - 1, rect.x + rect.width - 1, rect.y + rect.height)
                dc.DrawLine(rect.x, rect.y + rect.height - 1, rect.x + rect.width, rect.y + rect.height - 1)
        elif state & AUI_BUTTON_STATE_PRESSED:
            """
            TODO: add style of button press
            """
            pass
        x = rect.x + 1 + (rect.width-self._overflow_bmp.GetWidth())/2
        y = rect.y + 1 + (rect.height-self._overflow_bmp.GetHeight())/2
        dc.DrawBitmap(self._overflow_bmp, x, y, True)            


class PSDockArt(AuiDefaultDockArt):
    def __init__(self):
        AuiDefaultDockArt.__init__(self)
        self.SetCustomPaneBitmap(wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)), AUI_BUTTON_CLOSE, False)
        self.SetCustomPaneBitmap(wx.ArtProvider.GetBitmap(ps_art.PS_ART_CLOSE, size=(16, 16)), AUI_BUTTON_CLOSE, True)
        self.SetCustomPaneBitmap(wx.ArtProvider.GetBitmap(ps_art.PS_ART_MINIMUM, size=(16, 16)), AUI_BUTTON_MINIMIZE, False)
        self.SetCustomPaneBitmap(wx.ArtProvider.GetBitmap(ps_art.PS_ART_MINIMUM, size=(16, 16)), AUI_BUTTON_MINIMIZE, True)
        
    def DrawCaptionBackground(self, dc, rect, active):
        AuiDefaultDockArt.DrawCaptionBackground(self, dc, rect, active)
        if not active:
            dc.SetPen(wx.MEDIUM_GREY_PEN)
            dc.DrawLine(rect.x, rect.y, rect.x + rect.width, rect.y)
            dc.DrawLine(rect.x, rect.y, rect.x, rect.y + rect.height)
            dc.DrawLine(rect.x, rect.y + rect.height - 1, rect.x + rect.width, rect.y + rect.height - 1)
            dc.DrawLine(rect.x + rect.width - 1, rect.y, rect.x + rect.width - 1, rect.y + rect.height)
        



