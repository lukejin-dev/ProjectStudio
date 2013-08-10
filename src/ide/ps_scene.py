""" This module provide scene management.

    Lu, Ken (tech.ken.lu@gmail.com)
"""
import wx
import interfaces.core

import ps_auiex
import ps_menu
import ps_mainframe
from ps_debug import *


SCENE_CONFIG_SECTION = "Scene"
_=wx.GetTranslation

class PSDefaultScene(interfaces.core.IBackgroundScene):
    PERSPECITVE_OPTION = "DefaultPerspectiveString"
    
    def __init__(self, parent):
        self._logger = wx.GetApp().GetLogger("DefaultScene")
        self._singleView = []
        self._menus = {}
        self._menuTitles = []
        self._parent = parent
        
    def AddSingleView(self, view):
        self._singleView.append(view)

    def AssociateMenu(self, title, menu):
        if title in self._menus.keys():
            self._logger.error("Menu %s has been exists in default scene")
            return False
        self._menus[title] = menu
        if title in self._parent.FIXED_MENU_TITLES:
            self._menuTitles.append(title)
        else:
            index = self._menuTitles.index(_(ps_mainframe.MENU_TITLE_WINDOW))
            self._menuTitles.insert(index, title)
        return True

    def CreateFirstPanesLayout(self):
        paneInfos = []
        for singleview in self._singleView:
            paneInfos.append(singleview.GetDefaultPaneInfo())
        return paneInfos

    def GetMenu(self, title):
        return self._menus[title]
    
    def GetMenuTitlesInOrder(self):
        return self._menuTitles
    
    def GetMenus(self):
        """Return menu list used in this scene.
        The menus will be installed after File menu but before window menu.
        """
        return self._menus

    def GetName(self):
        return "default"
    
class PSSceneManager:
    def __init__(self, auimgr):
        # avoid conflict with PSMainFrame's member's name
        self._smAuiMgr = auimgr
        self._smLogger = wx.GetApp().GetLogger("SceneManager")
        self._smConfig = wx.GetApp().GetConfig(SCENE_CONFIG_SECTION)

        #
        # Background Scene:
        # A background scene can be seems a job such as Java/Python/Debug Development environment.
        # When IDE enter a backgrond scene, a set of float/side pane/menu/toolbar would be shown.
        # Also the background navigator is fixed at right toolbar for user switching in different background
        # scene.
        #
        self._backgroundScenes  = {}
        for scenecls in wx.GetApp().GetIfImpClasses(interfaces.core.IBackgroundScene):
            instance = scenecls(self)
            assert instance.GetName().lower() not in self._backgroundScenes.keys(), "Fail to create scene instance due to name already exist!"""
            self._backgroundScenes[instance.GetName().lower()] = instance
    
        self._currentBgName = None
            
        #
        # Foreground Scene: current working page, maybe a HTML page, a editor, a PDF.
        # Foreground scene is changed when user switching in different center document page.  
        #
        self._foregroundScenes  = {}
        for scenecls in wx.GetApp().GetIfImpClasses(interfaces.core.IForegroundScene):
            instance = scenecls(self)
            assert instance.GetName().lower() not in self._foregroundScenes.keys(), "Fail to create scene instance due to name already exist!"""
            self._foregroundScenes[instance.GetName().lower()] = instance
        self._currentFgName = None

    def __del__(self):
        self._LeaveCurrentBackgroundScene()

    def GetBackgroundScene(self, name):
        """Get background scene according given scene's name. 
        If scene has not been register, return None.
        
        @param name     scene's name
        @return object implement interfaces.core.IBackgroundScene
        """
        if name not in self._backgroundScenes.keys():
            return None
        return self._backgroundScenes[name.lower()]
        
    def GetCurrentBackgroundSceneName(self):
        if self._currentBgName == None:
            return "default"
        return self._currentBgName
    
    def GetCurrentForegroundSceneName(self):
        return self._currentFgName
    
    def GetBackgroundScenes(self):
        return self._backgroundScenes.values()
    
    def CreateBackgroundScene(self, name):
        return PSScene(name, self._smLogger)
    
    def EnterBackgroundScene(self, name, renew=False):
        if self._currentBgName != None:
            if name.lower() == self._currentBgName.lower() and not renew:
                return
        
        # Leave current background
        if self._currentBgName != None: 
            self._LeaveCurrentBackgroundScene()

        # Get background scene instance
        instance = self.GetBackgroundScene(name)
        
        
        # layout default scene's menu first
        defaultScene = self.GetBackgroundScene("default")
        menudict = defaultScene.GetMenus()
        for title in defaultScene.GetMenuTitlesInOrder():
            if title in self.GetMenuBar().GetMenuTitles():
                continue
            
            self.GetMenuBar().Append(defaultScene.GetMenu(title), title)
            
        if self.GetCurrentBackgroundSceneName() != "default":
            # add scene-related menus
            InsertPos = self.GetMenuBar().FindMenu(_(ps_mainframe.MENU_TITLE_FILE)) + 1
            menudict = instance.GetMenus()
            for title in menudict.keys():
                if title in self.GetMenuBar().GetMenuTitles():
                    self._smLogger.error("The menu %s already exists in menu bar!" % title)
                    continue
                self.GetMenuBar().Insert(InsertPos, menudict[title], title)
                InsertPos += 1

        # re-construct the new sub menu according to background and foreground context
        self.ReConstructNewMenu()
            
        # add scene-related toolbar
        
        # generate the perspective string
        if renew:
            sceneper = ""
        else:
            sceneper = self._smConfig.Get(name + "_perspective", "")

        if len(sceneper) == 0:
            # If first time creating a perspective, create perspective string by manual
            sceneper = self._CreateFirstTimePerspective(instance)
            
        self._smAuiMgr.LoadPerspective(sceneper)
        
        self._currentBgName = name
        return None
    
    def EnterLastBackgroundScene(self):
        currentBgName = self._smConfig.Get("LastBackgroundSceneName", "default").lower()
        if not self._backgroundScenes.has_key(currentBgName):
            currentBgName = "default"

        self.EnterBackgroundScene(currentBgName)
        
    def ResetCurrentBackgroundScene(self):
        assert self._currentBgName != None
         
    def _LeaveCurrentBackgroundScene(self):
        """Leave current background scene. Save all pane information to perspective."""
        if self._currentBgName != None:
            instance = self.GetBackgroundScene(self._currentBgName)
            assert instance != None, "Invalid name of background scene"
            try:
                self._smConfig.Set(self._currentBgName + "_perspective", self._smAuiMgr.SavePerspective())
            except Exception, e:
                print e
            self.ResetMenuBar()
            self.ResetToolBar()
            
    def _CreateFirstTimePerspective(self, scene):
        newper = "layout2|"
        
        # Add menu bar firstly
        newper += "%s|" % self._smAuiMgr.SavePaneInfo(self.GetMenuBar().GetPaneInfo())
        
        # Add general tool bar
        genericToolPaneInfo = ps_auiex.AuiPaneInfo().Name(ps_mainframe.TOOLBAR_NAME_GENERAL).ToolbarPane().Top().Row(1).Gripper(False).\
                              BestSize(self.GetToolBar().GetMinSize())
        newper += "%s|" % self._smAuiMgr.SavePaneInfo(genericToolPaneInfo)
        
        # Add center document notebook
        newper += "%s|" % self._smAuiMgr.SavePaneInfo(self.GetChildFrame().GetPaneInfo())

        # Add all panes defined by scene object
        dockedpanes = {}
        for paneinfo in scene.CreateFirstPanesLayout():
            if paneinfo.IsDocked():
                dockedpanes.setdefault(paneinfo.dock_direction, []).append(paneinfo)
            else:
                newper += "%s|" % self._smAuiMgr.SavePaneInfo(paneinfo)
        
        # close all existing notebook pane
        self._smAuiMgr.ResetNotebook()
            
        framesize = wx.GetApp().GetMainFrame().GetSize()
        framepos  = wx.GetApp().GetMainFrame().GetPosition()

        id = 0
        for dir in dockedpanes.keys():
            if len(dockedpanes[dir]) > 1:
                notebookpane = ps_auiex.AuiPaneInfo().NotebookControl(id)
                notebookpane = notebookpane.SetNameFromNotebookId()
                notebookpane = notebookpane.MinSize((100, 100))
                notebookpane = notebookpane.FloatingPosition((framepos[0] + framesize[0] / 4, framepos[1] + framesize[1] / 4))
                notebookpane = notebookpane.BestSize((framesize[0] / 2, framesize[1] / 2))
                notebookpane.dock_direction = dir
                newper += "%s|" % self._smAuiMgr.SavePaneInfo(notebookpane)
                for paneinfo in dockedpanes[dir]:
                    paneinfo = paneinfo.NotebookPage(id)
                    newper += "%s|" % self._smAuiMgr.SavePaneInfo(paneinfo)
                id += 1
            else:
                newper += "%s|" % self._smAuiMgr.SavePaneInfo(dockedpanes[dir][0])
                
        return newper
    
