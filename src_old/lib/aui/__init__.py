"""
AUI is an Advanced User Interface library that aims to implement "cutting-edge"
interface usability and design features so developers can quickly and easily create
beautiful and usable application interfaces.


Vision and Design Principles
----------------------------

AUI attempts to encapsulate the following aspects of the user interface:

* **Frame Management**: Frame management provides the means to open, move and hide common
controls that are needed to interact with the document, and allow these configurations
to be saved into different perspectives and loaded at a later time. 

* **Toolbars**: Toolbars are a specialized subset of the frame management system and should
behave similarly to other docked components. However, they also require additional
functionality, such as "spring-loaded" rebar support, "chevron" buttons and end-user
customizability. 

* **Modeless Controls**: Modeless controls expose a tool palette or set of options that
float above the application content while allowing it to be accessed. Usually accessed
by the toolbar, these controls disappear when an option is selected, but may also be
"torn off" the toolbar into a floating frame of their own. 

* **Look and Feel**: Look and feel encompasses the way controls are drawn, both when shown
statically as well as when they are being moved. This aspect of user interface design
incorporates "special effects" such as transparent window dragging as well as frame animation. 

AUI adheres to the following principles:

- Use native floating frames to obtain a native look and feel for all platforms;
- Use existing wxPython code where possible, such as sizer implementation for frame management; 
- Use standard wxPython coding conventions.


Usage:
------

The following example shows a simple implementation that uses `AuiManager` to manage
three text controls in a frame window::

class MyFrame(wx.Frame):

    def __init__(self, parent, id=-1, title="AUI Test", pos=wx.DefaultPosition,
                 size=(800, 600), style=wx.DEFAULT_FRAME_STYLE):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = aui.AuiManager()
        
        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)

        # create several text controls
        text1 = wx.TextCtrl(self, -1, "Pane 1 - sample text",
                            wx.DefaultPosition, wx.Size(200,150),
                            wx.NO_BORDER | wx.TE_MULTILINE)
                                           
        text2 = wx.TextCtrl(self, -1, "Pane 2 - sample text",
                            wx.DefaultPosition, wx.Size(200,150),
                            wx.NO_BORDER | wx.TE_MULTILINE)
                                           
        text3 = wx.TextCtrl(self, -1, "Main content window",
                            wx.DefaultPosition, wx.Size(200,150),
                            wx.NO_BORDER | wx.TE_MULTILINE)
        
        # add the panes to the manager
        self._mgr.AddPane(text1, AuiPaneInfo().Left().Caption("Pane Number One"))
        self._mgr.AddPane(text2, AuiPaneInfo().Bottom().Caption("Pane Number Two"))
        self._mgr.AddPane(text3, AuiPaneInfo().CenterPane())
                              
        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def OnClose(self, event):

        # deinitialize the frame manager
        self._mgr.UnInit()

        self.Destroy()        
        event.Skip()        


# our normal wxApp-derived class, as usual

app = wx.PySimpleApp()

frame = MyFrame(None)
app.SetTopWindow(frame)
frame.Show()

app.MainLoop()


What's New
----------

Current wxAUI Version Tracked: wxWidgets 2.9.0 (SVN HEAD)

The wxPython AUI version fixes the following bugs or implement the following
missing features (the list is not exhaustive):

- Visual Studio 2005 style docking: http://www.kirix.com/forums/viewtopic.php?f=16&t=596
- Dock and Pane Resizing: http://www.kirix.com/forums/viewtopic.php?f=16&t=582 
- Patch concerning dock resizing: http://www.kirix.com/forums/viewtopic.php?f=16&t=610 
- Patch to effect wxAuiToolBar orientation switch: http://www.kirix.com/forums/viewtopic.php?f=16&t=641 
- AUI: Core dump when loading a perspective in wxGTK (MSW OK): http://www.kirix.com/forums/viewtopic.php?f=15&t=627 
- wxAuiNotebook reordered AdvanceSelection(): http://www.kirix.com/forums/viewtopic.php?f=16&t=617 
- Vertical Toolbar Docking Issue: http://www.kirix.com/forums/viewtopic.php?f=16&t=181 
- Patch to show the resize hint on mouse-down in aui: http://trac.wxwidgets.org/ticket/9612 
- The Left/Right and Top/Bottom Docks over draw each other: http://trac.wxwidgets.org/ticket/3516 
- MinSize() not honoured: http://trac.wxwidgets.org/ticket/3562 
- Layout problem with wxAUI: http://trac.wxwidgets.org/ticket/3597 
- Resizing children ignores current window size: http://trac.wxwidgets.org/ticket/3908 
- Resizing panes under Vista does not repaint background: http://trac.wxwidgets.org/ticket/4325 
- Resize sash resizes in response to click: http://trac.wxwidgets.org/ticket/4547 
- "Illegal" resizing of the AuiPane? (wxPython): http://trac.wxwidgets.org/ticket/4599 
- Floating wxAUIPane Resize Event doesn't update its position: http://trac.wxwidgets.org/ticket/9773
- Don't hide floating panels when we maximize some other panel: http://trac.wxwidgets.org/ticket/4066 
- wxAUINotebook incorrect ALLOW_ACTIVE_PANE handling: http://trac.wxwidgets.org/ticket/4361 
- Page changing veto doesn't work, (patch supplied): http://trac.wxwidgets.org/ticket/4518 
- Show and DoShow are mixed around in wxAuiMDIChildFrame: http://trac.wxwidgets.org/ticket/4567 
- wxAuiManager & wxToolBar - ToolBar Of Size Zero: http://trac.wxwidgets.org/ticket/9724 
- wxAuiNotebook doesn't behave properly like a container as far as...: http://trac.wxwidgets.org/ticket/9911
- Serious layout bugs in wxAUI: http://trac.wxwidgets.org/ticket/10620

Plus the following features:

- AuiManager:
  (a) Implementation of a simple minimize pane system: Clicking on this minimize button causes a new
      AuiToolBar to be created and added to the frame manager, (currently the implementation is such
      that panes at West will have a toolbar at the right, panes at South will have toolbars at the
      bottom etc...) and the pane is hidden in the manager.
      Clicking on the restore button on the newly created toolbar will result in the toolbar being
      removed and the original pane being restored;
  (b) Panes can be docked on top of each other to form `AuiNotebooks`; `AuiNotebooks` tabs can be torn
      off to create floating panes;
  (c) On Windows XP, use the nice sash drawing provided by XP while dragging the sash;
  (d) Possibility to set an icon on docked panes;
  (e) Possibility to draw a sash visual grip, for enhanced visualization of sashes;
  (f) Implementation of a native docking art (`ModernDockArt`). Windows XP only, **requires** Mark Hammond's
      pywin32 package (winxptheme);
  (g) Possibility to set a transparency for floating panes (a la Paint .NET);
  (h) Snapping the main frame to the screen in any positin specified by horizontal and vertical
      alignments;
  (i) Snapping floating panes on left/right/top/bottom or any combination of directions, a la Winamp.

- AuiNotebook:
  (a) Implementation of the style ``AUI_NB_HIDE_ON_SINGLE_TAB``, a la `wx.lib.agw.flatnotebook`;
  (b) Implementation of the style ``AUI_NB_SMART_TABS``, a la `wx.lib.agw.flatnotebook`;
  (c) Implementation of the style ``AUI_NB_USE_IMAGES_DROPDOWN``, which allows to show tab images
      on the tab dropdown menu instead of bare check menu items (a la `wx.lib.agw.flatnotebook`);
  (d) 6 different tab arts are available, namely:
      (1) Default "glossy" theme (as in `wx.aui.AuiNotebook`)
      (2) Simple theme (as in `wx.aui.AuiNotebook`)
      (3) Firefox 2 theme
      (4) Visual Studio 2003 theme (VC71)
      (5) Visual Studio 2005 theme (VC81)
      (6) Google Chrome theme (only ``AUI_NB_TOP`` at the moment)
  (e) Enabling/disabling tabs;
  (f) Setting the colour of the tab's text.
  
- AuiToolBar:
  (a) ``AUI_TB_PLAIN_BACKGROUND`` style that allows to easy setup a plain background to the AUI toolbar,
      without the need to override drawing methods. This style contrasts with the default behaviour
      of the `wx.aui.AuiToolBar` that draws a background gradient and this break the window design when
      putting it within a control that has margin between the borders and the toolbar (example: put
      `wx.aui.AuiToolBar` within a `wx.StaticBoxSizer` that has a plain background);
  (b) `AuiToolBar` allow item alignment: http://trac.wxwidgets.org/ticket/10174;
  (c) `AUIToolBar` `DrawButton()` improvement: http://trac.wxwidgets.org/ticket/10303;
  (d) `AuiToolBar` automatically assign new id for tools: http://trac.wxwidgets.org/ticket/10173;
  (e) `AuiToolBar` Allow right-click on any kind of button: http://trac.wxwidgets.org/ticket/10079;
  (f) `AuiToolBar` idle update only when visible: http://trac.wxwidgets.org/ticket/10075.


TODOs
-----

- Documentation, documentation and documentation;
- Fix `tabmdi.AuiMDIParentFrame` and friends, they do not work correctly at present;
- Allow specification of `CaptionLeft()` to `AuiPaneInfo` to show the caption bar of docked panes
  on the left instead of on the top (with caption text rotated by 90 degrees then). This is
  similar to what `wxDockIt` did;
- Make developer-created `AuiNotebooks` and automatic (framemanager-created) `AuiNotebooks` behave
  the same way (undocking of tabs);
- Find a way to dock panes in already floating panes (`AuiFloatingFrames`), as they already have
  their own `AuiManager`;
- Add events for panes when they are about to float or to be docked (something like
  ``EVT_AUI_PANE_FLOATING/ED`` and ``EVT_AUI_PANE_DOCKING/ED``);
- Implement the 4-ways splitter behaviour for horizontal and vertical sashes if they intersect;
- Extend `tabart.py` with more aui tab arts;
- Allow controls in tabs (a la Eclipse) as described here:
  http://lists.wxwidgets.org/pipermail/wxpython-users/2007-January/060451.html
  and especially here:
  http://archives.devshed.com/forums/attachment.php?attachmentid=4337;
- Harmonize the `AuiNotebook` API with the `wx.Notebook` one, especially regarding setting/getting
  tab images (i.e., using `wx.ImageList`);
- Implement ``AUI_NB_LEFT`` and ``AUI_NB_RIGHT`` tab locations in `AuiNotebook`, and support
  ``AUI_NB_BOTTOM`` for the Google Chrome tab art;
- Move `AuiDefaultToolBarArt` into a separate module (as with `tabart.py` and `dockart.py`) and
  provide more arts for toolbars (maybe from `wx.lib.agw.flatmenu`?)
- Support multiple-rows/multiple columns toolbars;
- Integrate as much as possible with `wx.lib.agw.flatmenu`, from dropdown menus in `AuiNotebook` to
  toolbars and menu positioning;
- Possibly handle minimization of panes in a different way (or provide an option to switch to
  another way of minimizing panes);
- Clean up/speed up the code, especially time-consuming for-loops;
- Possibly integrate `wxPyRibbon` (still on development), at least on Windows.


License And Version:
--------------------

AUI library is freeware and distributed under the wxPython license. 

Latest revision: Andrea Gavana @ 31 Mar 2009, 21.00 GMT
Version 1.0. 

"""

__author__ = "Andrea Gavana <andrea.gavana@gmail.com>"
__date__ = "31 March 2009"


from aui_constants import *
from aui_utilities import *
from auibar import *
from auibook import *
from tabart import *
from dockart import *
from framemanager import *
from tabmdi import *
