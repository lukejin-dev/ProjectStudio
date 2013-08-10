import wx
import re, os
import service
import wx.lib.customtreectrl as CT
import threading
import wx.lib.docview as docview
#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
FIND_MATCHPATTERN = "FindMatchPattern"
FIND_MATCHREPLACE = "FindMatchReplace"
FIND_MATCHCASE = "FindMatchCase"
FIND_MATCHWHOLEWORD = "FindMatchWholeWordOnly"
FIND_MATCHREGEXPR = "FindMatchRegularExpr"
FIND_MATCHWRAP = "FindMatchWrap"
FIND_MATCHUPDOWN = "FindMatchUpDown"
FIND_LISTALL     = "FindListAll"
FIND_SYNTAXERROR = -2
FIND_FILE_EXTENSION = "FindFileExtension"
FIND_LAST_FILE_EXTENSION = "FindLastFileExtension"
FIND_DIR_EXCLUDE    = "FindDirExclude"
FIND_LAST_DIR_EXCLUDE = "FindLastDirExclude"
FIND_DIRS           = "FindDirs"
FIND_LAST_DIR       = "FindLastDir"
FIND_IN_SUB_DIRS    = "FindInSubDirs"
SPACE = 5
HALF_SPACE = 3

_ = wx.GetTranslation
gKeywordArr = []

#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------
import core.service as service
class FindService(service.PISService):

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    FIND_ID = wx.NewId()            # for bringing up Find dialog box
    FINDONE_ID = wx.NewId()         # for doing Find
    FIND_PREVIOUS_ID = wx.NewId()   # for doing Find Next
    FIND_NEXT_ID = wx.NewId()       # for doing Find Prev
    REPLACE_ID = wx.NewId()         # for bringing up Replace dialog box
    REPLACEONE_ID = wx.NewId()      # for doing a Replace
    REPLACEALL_ID = wx.NewId()      # for doing Replace All
    GOTO_LINE_ID = wx.NewId()       # for bringing up Goto dialog box
    FIND_SYNTAXERROR = wx.NewId()
    # Extending bitmasks: wx.FR_WHOLEWORD, wx.FR_MATCHCASE, and wx.FR_DOWN
    FR_REGEXP = max([wx.FR_WHOLEWORD, wx.FR_MATCHCASE, wx.FR_DOWN]) << 1
    FR_WRAP = FR_REGEXP << 1
    FR_LISTALL = FR_WRAP << 1
    
    FIND_IN_FILES_ID = wx.NewId()
    
    def __init__(self):
        service.PISService.__init__(self)
        self._replaceDialog = None
        self._findDialog = None
        self._findReplaceData = wx.FindReplaceData()
        self._findReplaceData.SetFlags(wx.FR_DOWN)
        self._findDirThread   = None
        
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Search Results'
    
    def GetViewClass(self):
        return FindView

    def GetIcon(self):
        return getFindIcon()
        
    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        """ Install Find Service Menu Items """
        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        editMenuIndex = menuBar.FindMenu(_("&Edit"))
        searchMenu = wx.Menu()
        menuBar.Insert(editMenuIndex + 1, searchMenu, 'Search')
        
        #searchMenu.Append(FindService.FIND_ID, _("&Find...\tCtrl+F"), _("Finds the specified text"))
        item = wx.MenuItem(searchMenu, FindService.FIND_ID, _("&Find...\tCtrl+F"), _("Finds the specified text"))
        item.SetBitmap(getFindBitmap())
        searchMenu.AppendItem(item)
        wx.EVT_MENU(frame, FindService.FIND_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindService.FIND_ID, frame.ProcessUpdateUIEvent)
        searchMenu.Append(FindService.FIND_PREVIOUS_ID, _("Find &Previous\tShift+F3"), _("Finds the specified text"))
        wx.EVT_MENU(frame, FindService.FIND_PREVIOUS_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindService.FIND_PREVIOUS_ID, frame.ProcessUpdateUIEvent)
        searchMenu.Append(FindService.FIND_NEXT_ID, _("Find &Next\tF3"), _("Finds the specified text"))
        wx.EVT_MENU(frame, FindService.FIND_NEXT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindService.FIND_NEXT_ID, frame.ProcessUpdateUIEvent)
        searchMenu.Append(FindService.REPLACE_ID, _("R&eplace...\tCtrl+H"), _("Replaces specific text with different text"))
        wx.EVT_MENU(frame, FindService.REPLACE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindService.REPLACE_ID, frame.ProcessUpdateUIEvent)
        searchMenu.Append(FindService.GOTO_LINE_ID, _("&Go to Line...\tCtrl+G"), _("Goes to a certain line in the file"))
        wx.EVT_MENU(frame, FindService.GOTO_LINE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindService.GOTO_LINE_ID, frame.ProcessUpdateUIEvent)

        searchMenu.AppendSeparator()
        #searchMenu.Append(FindService.FIND_IN_FILES_ID, "Find in Files ...", "Find in Files")
        item = wx.MenuItem(searchMenu, FindService.FIND_IN_FILES_ID, "Find in Dir ...", "Find in Files")
        item.SetBitmap(getFindInFolderBitmap())
        searchMenu.AppendItem(item)
        
        wx.EVT_MENU(frame, self.FIND_IN_FILES_ID, self.OnFindInDir)
        
        frame.Bind(wx.EVT_FIND, frame.ProcessEvent)
        frame.Bind(wx.EVT_FIND_NEXT, frame.ProcessEvent)
        frame.Bind(wx.EVT_FIND_REPLACE, frame.ProcessEvent)
        frame.Bind(wx.EVT_FIND_REPLACE_ALL, frame.ProcessEvent)
        
    def GetCustomizeToolBars(self):
        ret = []
        toolbar = wx.ToolBar(wx.GetApp().GetTopWindow(),
                              -1, wx.DefaultPosition, wx.DefaultSize,
                             wx.TB_FLAT | wx.TB_NODIVIDER)
        toolbar.AddLabelTool(FindService.FIND_ID,
                             'Find',
                             getFindBitmap(),
                             shortHelp = _("Find"), 
                             longHelp = _("Finds the specified text"))
        toolbar.AddLabelTool(FindService.FIND_IN_FILES_ID,
                             'Find in Folder',
                             getFindInFolderBitmap(),
                             shortHelp = _("Find in folder"),
                             longHelp  = _("Find in folder"))
        toolbar.Realize()
        ret.append(toolbar)
        return ret
    
    def OnFindInDir(self, event):
        docmgr = wx.GetApp().GetDocumentManager()
        view   = docmgr.GetCurrentView()
        doc    = docmgr.GetCurrentDocument()
        dir    = None
        if doc != None:
            dir = os.path.dirname(doc.GetFilename())
        findStr    = ""
        if view != None and hasattr(view, "GetSelectedText"):
            findStr = view.GetSelectedText()
        self.ShowFindReplaceDialog(findStr, False, True, findDir=dir)
        
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if (id == FindService.FIND_ID
        or id == FindService.FIND_PREVIOUS_ID
        or id == FindService.FIND_NEXT_ID
        or id == FindService.REPLACE_ID
        or id == FindService.GOTO_LINE_ID):
            event.Enable(False)
            return True
        else:
            return False


    def ShowFindReplaceDialog(self, findString="", replace = False, isFindInDir=False, findDir=None):
        """ Display find/replace dialog box.
        
            Parameters: findString is the default value shown in the find/replace dialog input field.
            If replace is True, the replace dialog box is shown, otherwise only the find dialog box is shown. 
        """
        if replace:
            if self._findDialog != None:
                # No reason to have both find and replace dialogs up at the same time
                self._findDialog.DoClose()
                self._findDialog = None

            self._replaceDialog = FindReplaceDialog(self.GetDocumentManager().FindSuitableParent(), -1, _("Replace"), size=(320,200), findString=findString)
            self._replaceDialog.CenterOnParent()
            self._replaceDialog.Show(True)
        else:
            if self._replaceDialog != None:
                # No reason to have both find and replace dialogs up at the same time
                self._replaceDialog.DoClose()
                self._replaceDialog = None
            
            if self._findDirThread != None:
                msg = wx.MessageDialog(self.GetDocumentManager().FindSuitableParent(),
                                 "Searching thread is running ... You must terminate it before new searching. \nDo you want to terminate?",
                                 "Warning",
                                 wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
                result = msg.ShowModal()
                if result == wx.ID_OK:
                    self.TerminateSearchThread()
                else:
                    return
                    
            self._findDialog = FindDialog(self.GetDocumentManager().FindSuitableParent(), -1, 
                                          _("Find"), 
                                          size=(320,200), 
                                          findString=findString,
                                          isFindInDir=isFindInDir,
                                          findDir=findDir)
            self._findDialog.CenterOnParent()
            self._findDialog.Show(True)



    def OnFindClose(self, event):
        """ Cleanup handles when find/replace dialog is closed """
        if self._findDialog != None:
            self._findDialog = None
        elif self._replaceDialog != None:
            self._replaceDialog = None


    def GetCurrentDialog(self):
        """ return handle to either the find or replace dialog """
        if self._findDialog != None:
            return self._findDialog
        return self._replaceDialog


    def GetLineNumber(self, parent):
        """ Display Goto Line Number dialog box """
        line = -1
        dialog = wx.TextEntryDialog(parent, _("Enter line number to go to:"), _("Go to Line"))
        dialog.CenterOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            try:
                line = int(dialog.GetValue())
                if line > 65535:
                    line = 65535
            except:
                pass
        dialog.Destroy()
        # This one is ugly:  wx.GetNumberFromUser("", _("Enter line number to go to:"), _("Go to Line"), 1, min = 1, max = 65535, parent = parent)
        return line


    def DoFind(self, findString, replaceString, text, startLoc, endLoc, down, matchCase, wholeWord, regExpr = False, replace = False, replaceAll = False, wrap = False, listAll=False):
        """ Do the actual work of the find/replace.
        
            Returns the tuple (count, start, end, newText).
            count = number of string replacements
            start = start position of found string
            end = end position of found string
            newText = new replaced text 
        """
        if listAll:
            return self.ListAll(findString, text, wholeWord, matchCase, regExpr)
            
        flags = 0
        if regExpr:
            pattern = findString
        else:
            pattern = re.escape(findString)  # Treat the strings as a literal string
        if not matchCase:
            flags = re.IGNORECASE
        if wholeWord:
            pattern = r"\b%s\b" % pattern
            
        try:
            reg = re.compile(pattern, flags)
        except:
            # syntax error of some sort
            import sys
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Regular Expression Search")
            wx.MessageBox(_("Invalid regular expression \"%s\". %s") % (pattern, sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetView())
            return FIND_SYNTAXERROR, None, None, None

        if replaceAll:
            replaceString = replaceString.replace('\\', '\\\\')    
            newText, count = reg.subn(replaceString, text)
            if count == 0:
                return -1, None, None, None
            else:
                return count, None, None, newText

        start = -1
        if down:
            match = reg.search(text, endLoc)
            if match == None:
                if wrap:  # try again, but this time from top of file
                    match = reg.search(text, 0)
                    if match == None:
                        return -1, None, None, None
                else:
                    return -1, None, None, None
            start = match.start()
            end = match.end()
        else:
            match = reg.search(text)
            if match == None:
                return -1, None, None, None
            found = None
            i, j = match.span()
            while i < startLoc and j <= startLoc:
                found = match
                if i == j:
                    j = j + 1
                match = reg.search(text, j)
                if match == None:
                    break
                i, j = match.span()
            if found == None:
                if wrap:  # try again, but this time from bottom of file
                    match = reg.search(text, startLoc)
                    if match == None:
                        return -1, None, None, None
                    found = None
                    i, j = match.span()
                    end = len(text)
                    while i < end and j <= end:
                        found = match
                        if i == j:
                            j = j + 1
                        match = reg.search(text, j)
                        if match == None:
                            break
                        i, j = match.span()
                    if found == None:
                        return -1, None, None, None
                else:
                    return -1, None, None, None
            start = found.start()
            end = found.end()

        if replace and start != -1:
            newText, count = reg.subn(replaceString, text, 1)
            return count, start, end, newText

        return 0, start, end, None

    def IsThreadRunning(self):
        return self._findDirThread != None
        
    def DoFindInDir(self, findString, path, exts, excludes, inSub, matchCase, wholeWord, regExpr):
        self._findDialog.DoClose()
        self._findDialog = None
        
        self.GetView().Clear()
        self.GetView().Activate()
        self.SetTitle("Searching string \"%s\" in dir %s ..." % (findString, path))
        self._findDirThread  = FindDirThread(findString,
                                             path,
                                             exts,
                                             excludes,
                                             inSub,
                                             matchCase,
                                             wholeWord,
                                             regExpr,
                                             self.FindCallback,
                                             self.FinishCallback)
        self._findDirThread.start()
        
    def FindCallback(self, file, arr, str, path, scaned, found, files):
        view = self.GetView()
        view.AddResult(file, arr)
        self.SetTitle("Searching string \"%s\" in dir %s ...Scaned %d files, Found %d occur in %d files" % \
                      (str, 
                       path,
                       scaned,
                       found,
                       files))
        
    def FinishCallback(self, scaned, found, files):
        self._findDirThread = None
        self.SetTitle("Searching finished! Scaned %d files, found %s occurrence in %s files" % (scaned, found, files))
        
    def ListAll(self, findString, text, wholeWord, matchCase, regExpr=None):
        self._findDialog.DoClose()
        self._findDialog = None
        flags = 0
        if regExpr:
            pattern = findString
        else:
            pattern = re.escape(findString)  # Treat the strings as a literal string
        if not matchCase:
            flags = re.IGNORECASE
        if wholeWord:
            pattern = r"\b%s\b" % pattern
            
        try:
            reg = re.compile(pattern, flags)
        except:
            # syntax error of some sort
            import sys
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Regular Expression Search")
            wx.MessageBox(_("Invalid regular expression \"%s\". %s") % (pattern, sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_EXCLAMATION,
                          self.GetView())
        results = []
        start = 0
        match = reg.search(text, 0)
        while match != None:
            results.append((match.start(), match.end()))
            start = match.start() + 1
            match = reg.search(text, start)
        return results
    
    def ListResults(self, results, isCurr=False):
        view = self.GetView()
        view.Clear()
        view.Activate()
        if isCurr:
            self.SetTitle('Search in current file %s' % results[0][0])
            view.AddResult(results[0][0], results[0][1])
            view.Expand()
        
    def SaveFindConfig(self, findString, wholeWord, matchCase, regExpr = None, wrap = None, upDown = None, replaceString = None, listAll=None):
        """ Save find/replace patterns and search flags to registry.
        
            findString = search pattern
            wholeWord = match whole word only
            matchCase = match case
            regExpr = use regular expressions in search pattern
            wrap = return to top/bottom of file on search
            upDown = search up or down from current cursor position
            replaceString = replace string
        """
        config = wx.ConfigBase_Get()

        config.Write(FIND_MATCHPATTERN, findString)
        config.WriteInt(FIND_MATCHCASE, matchCase)
        config.WriteInt(FIND_MATCHWHOLEWORD, wholeWord)
        if replaceString != None:
            config.Write(FIND_MATCHREPLACE, replaceString)
        if regExpr != None:
            config.WriteInt(FIND_MATCHREGEXPR, regExpr)
        if wrap != None:
            config.WriteInt(FIND_MATCHWRAP, wrap)
        if upDown != None:
            config.WriteInt(FIND_MATCHUPDOWN, upDown)
        if listAll != None:
            config.WriteInt(FIND_LISTALL, listAll)

    def GetFindString(self):
        """ Load the search pattern from registry """
        return wx.ConfigBase_Get().Read(FIND_MATCHPATTERN, "")


    def GetReplaceString(self):
        """ Load the replace pattern from registry """
        return wx.ConfigBase_Get().Read(FIND_MATCHREPLACE, "")


    def GetFlags(self):
        """ Load search parameters from registry """
        config = wx.ConfigBase_Get()

        flags = 0
        if config.ReadInt(FIND_MATCHWHOLEWORD, False):
            flags = flags | wx.FR_WHOLEWORD
        if config.ReadInt(FIND_MATCHCASE, False):
            flags = flags | wx.FR_MATCHCASE
        if config.ReadInt(FIND_MATCHUPDOWN, False):
            flags = flags | wx.FR_DOWN
        if config.ReadInt(FIND_MATCHREGEXPR, False):
            flags = flags | FindService.FR_REGEXP
        if config.ReadInt(FIND_MATCHWRAP, False):
            flags = flags | FindService.FR_WRAP
        if config.ReadInt(FIND_LISTALL, False):
            flags = flags | FindService.FR_LISTALL
        return flags

    def OnCloseFrame(self, event):
        if self._findDirThread != None:
            self._findDirThread.Terminate()
        return service.PISService.OnCloseFrame(self, event)
        
    def TerminateSearchThread(self):
        if not self.IsThreadRunning(): return
        self._findDirThread.Terminate()
        str = "Searching thread is termniated! Scaned %d files, found %d occurrence in %d files" %  \
                        (self._findDirThread._countScan, 
                        self._findDirThread._countFound, 
                        self._findDirThread._countFile)
        self.SetTitle(str)
        self._findDirThread = None           
        
class FindView(service.PISServiceView):
    MENU_STOP_THREAD_ID      = wx.NewId()
    MENU_COPY_RESULT_ID      = wx.NewId()
    MENU_COPY_ALL_RESULT_ID  = wx.NewId()
    
    def __init__(self, parent, serv):
        service.PISServiceView.__init__(self, parent, serv) 
        sizer = wx.BoxSizer(wx.VERTICAL)
        #self._listCtrl = wx.TreeCtrl(self, -1, style=wx.TR_HIDE_ROOT|wx.TR_ROW_LINES )
        style = wx.SUNKEN_BORDER|CT.TR_HIDE_ROOT|CT.TR_ROW_LINES|CT.TR_SINGLE|CT.TR_NO_LINES|CT.TR_FULL_ROW_HIGHLIGHT|CT.TR_HAS_BUTTONS
        self._treeCtrl = ResultTreeCtrl(self, -1, style)
        self._treeCtrl.EnableSelectionVista(True)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = 'Courier New')
        self._treeCtrl.SetFont(font)
        sizer.Add(self._treeCtrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        self.Clear()
        CT.EVT_TREE_ITEM_ACTIVATED(self._treeCtrl, self._treeCtrl.GetId(), self.OnTreeItemActivate)
        CT.EVT_TREE_ITEM_MENU(self._treeCtrl, self._treeCtrl.GetId(), self.OnTreeItemMenu)
        
    def Expand(self):
        self._treeCtrl.ExpandAll()
        
    def Clear(self):
        self._treeCtrl.DeleteAllItems()
        self._treeCtrl.AddRoot('Search result')
        
    def AddResult(self, file, arr):
        self._treeCtrl.Freeze()
        fItem = self._treeCtrl.AppendItem(self._treeCtrl.GetRootItem(), 
                                          'file : %s' % file,
                                          data=(file, 1))
        for item in arr:
            self._treeCtrl.AppendItem(fItem, 
                                      '%-4d %s' % (item[0], item[1].rstrip()),
                                      data=(file, item[0]))
        self._treeCtrl.Thaw()

        #self._treeCtrl.ExpandAll()
        
    def OnTreeItemActivate(self, event):
        item = event.GetItem()
        data = self._treeCtrl.GetPyData(item)
        docmgr = wx.GetApp().GetDocumentManager()
        doc = docmgr.CreateDocument(data[0], docview.DOC_SILENT)
        if doc != None:
            view = doc.GetFirstView()
            if view != None and hasattr(view, 'GotoLine'):
                view.GotoLine(data[1])
        
    def OnTreeItemMenu(self, event):
        menu = wx.Menu()
        if self.GetService().IsThreadRunning():
            menu.Append(self.MENU_STOP_THREAD_ID, 'Stop searching')
            wx.EVT_MENU(self._treeCtrl, self.MENU_STOP_THREAD_ID, self.OnStopThread)
            menu.AppendSeparator()
        item = menu.Append(self.MENU_COPY_RESULT_ID, 'Copy current result to clipboard')
        wx.EVT_MENU(self._treeCtrl, self.MENU_COPY_RESULT_ID, self.OnCopyResult)
        menu.Append(self.MENU_COPY_ALL_RESULT_ID, 'Copy all results to clipboard')
        wx.EVT_MENU(self._treeCtrl, self.MENU_COPY_ALL_RESULT_ID, self.OnCopyAllResults)
        self._treeCtrl.PopupMenu(menu, event.GetPoint())
        
    def OnStopThread(self, event):
        self.GetService().TerminateSearchThread()
        
    def OnCopyResult(self, event):
        item = self._treeCtrl.GetSelection()
        text = self._treeCtrl.GetItemText(item)
        textobj = wx.TextDataObject()
        textobj.SetText(text)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(textobj)
        wx.TheClipboard.Close()
        
        
    def OnCopyAllResults(self, event):
        root = self._treeCtrl.GetRootItem()
        fileItems = self.GetChildNodes(root)
        text = ''
        for fileItem in fileItems:
            text += '%s\r\n' % self._treeCtrl.GetItemText(fileItem)
            resultItems = self.GetChildNodes(fileItem)
            for resultItem in resultItems:
                text += '    %s\r\n' % self._treeCtrl.GetItemText(resultItem)
        textobj = wx.TextDataObject()
        textobj.SetText(text)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(textobj)
        wx.TheClipboard.Close()
        
    def GetChildNodes(self, root):
        items = []
        (child, cookie) = self._treeCtrl.GetFirstChild(root)
        while child != None and child.IsOk():
            items.append(child)
            (child, cookie) = self._treeCtrl.GetNextChild(root, cookie)
        return items
            
class ResultTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id, style):
        CT.CustomTreeCtrl.__init__(self, parent, id, style=style)
        
    def ProcessEvent(self, event):
        # work around, view's control should not eat event
        return False
        
class FindDialog(wx.Dialog):
    """ Find Dialog with regular expression matching and wrap to top/bottom of file. """

    def __init__(self, parent, id, title, size, findString=None, isFindInDir=False, findDir=None):
        self._findDir = findDir
        wx.Dialog.__init__(self, parent, id, title, size=size)
        self.SetIcon(getFindInFolderIcon())
        config = wx.ConfigBase_Get()
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.GridBagSizer(SPACE, SPACE)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Find what:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, SPACE)
        if not findString:
            findString = config.Read(FIND_MATCHPATTERN, "")
        self._findCtrl = wx.ComboBox(self, -1, findString, size=(200, -1))
        for keyword in gKeywordArr:
            self._findCtrl.Append(keyword)
        lineSizer.Add(self._findCtrl, 0)
        gridSizer.Add(lineSizer, pos=(0,0), span=(1,2))
        choiceSizer = wx.BoxSizer(wx.VERTICAL)
        self._wholeWordCtrl = wx.CheckBox(self, -1, _("Match whole word only"))
        self._wholeWordCtrl.SetValue(config.ReadInt(FIND_MATCHWHOLEWORD, False))
        self._matchCaseCtrl = wx.CheckBox(self, -1, _("Match case"))
        self._matchCaseCtrl.SetValue(config.ReadInt(FIND_MATCHCASE, False))
        self._regExprCtrl = wx.CheckBox(self, -1, _("Regular expression"))
        self._regExprCtrl.SetValue(config.ReadInt(FIND_MATCHREGEXPR, False))
        self._wrapCtrl = wx.CheckBox(self, -1, _("Wrap"))
        self._wrapCtrl.SetValue(config.ReadInt(FIND_MATCHWRAP, False))
        #self._listAllCtrl = wx.CheckBox(self, -1, _("List all occurrences"))
        #self._listAllCtrl.SetValue(config.ReadInt(FIND_LISTALL, False))
        choiceSizer.Add(self._wholeWordCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._matchCaseCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._regExprCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._wrapCtrl, 0)
        gridSizer.Add(choiceSizer, pos=(1,0), span=(2,1))

        self._radioBox = wx.RadioBox(self, -1, _("Direction"), choices = ["Up", "Down"])
        self._radioBox.SetSelection(config.ReadInt(FIND_MATCHUPDOWN, 1))
        gridSizer.Add(self._radioBox, pos=(1,1), span=(1,1))
        self._listAllCtrl = wx.CheckBox(self, -1, _("List all occurrences"))
        self._listAllCtrl.SetValue(config.ReadInt(FIND_LISTALL, False))
        gridSizer.Add(self._listAllCtrl, pos=(2,1))
        
        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        findBtn = wx.Button(self, FindService.FINDONE_ID, _("Find"))
        findBtn.SetDefault()
        wx.EVT_BUTTON(self, FindService.FINDONE_ID, self.OnActionEvent)
        cancelBtn = wx.Button(self, wx.ID_CANCEL)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnClose)
        BTM_SPACE = HALF_SPACE
        if wx.Platform == "__WXMAC__":
            BTM_SPACE = SPACE
        buttonSizer.Add(findBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(cancelBtn, 0)
        gridSizer.Add(buttonSizer, pos=(0,2), span=(2,1))

        borderSizer.Add(gridSizer, 0, wx.ALL, SPACE)
        
        self._findDirCtrl = wx.CollapsiblePane(self, -1, 'Find in Directory', style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnFindDirChanged, self._findDirCtrl)
        self.MakeFindDirCtrls(self._findDirCtrl.GetPane())
        borderSizer.Add(self._findDirCtrl, 0, wx.EXPAND)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetSizer(borderSizer)
        self.Fit()
        
        self._findCtrl.SetFocus()
        if isFindInDir:
            self._findDirCtrl.Expand()
            self.OnFindDirChanged(None)
        
    def SaveConfig(self):
        """ Save find patterns and search flags to registry. """
        config = wx.ConfigBase_Get()
        if self._findDirCtrl.IsExpanded():
            curr = self._dirCtrl.GetValue()
            arr  = self._dirCtrl.GetStrings()
            if curr not in arr:
                if len(arr) >= 20:
                    del arr[0]
                arr.append(curr)
                config.Write(FIND_DIRS, "|".join(arr))
            config.Write(FIND_LAST_DIR, curr)
            
            curr = self._extCtrl.GetValue()
            arr  = self._extCtrl.GetStrings()
            if curr not in arr:
                if len(arr) >=20:
                    del arr[0]
                arr.append(curr)
                config.Write(FIND_FILE_EXTENSION, "|".join(arr))
            config.Write(FIND_LAST_FILE_EXTENSION, curr)
            
            curr = self._excludeCtrl.GetValue()
            arr  = self._excludeCtrl.GetStrings()
            if curr not in arr:
                if len(arr) >= 20:
                    del arr[0]
                arr.append(curr)
                config.Write(FIND_DIR_EXCLUDE, "|".join(arr))
            config.Write(FIND_LAST_DIR_EXCLUDE, curr)
            
            config.WriteInt(FIND_IN_SUB_DIRS, self._findSubDir.GetValue())
            
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.SaveFindConfig(self._findCtrl.GetValue(),
                                       self._wholeWordCtrl.IsChecked(),
                                       self._matchCaseCtrl.IsChecked(),
                                       self._regExprCtrl.IsChecked(),
                                       self._wrapCtrl.IsChecked(),
                                       self._radioBox.GetSelection(),
                                       None,
                                       self._listAllCtrl.GetValue()
                                       )


    def DoClose(self):
        self.SaveConfig()
        self.Destroy()


    def OnClose(self, event):
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.OnFindClose(event)
        self.DoClose()


    def OnActionEvent(self, event):
        currKeyword = self._findCtrl.GetValue()
        if len(currKeyword) == 0:
            wx.MessageBox('Please input keyword for searching!')
            return
            
        self.SaveConfig()
        
        # append current search keyword into history array.
        if currKeyword not in gKeywordArr:
            gKeywordArr.append(currKeyword)
        if currKeyword not in self._findCtrl.GetStrings():
            self._findCtrl.Append(currKeyword)

        if self._findDirCtrl.IsExpanded():
            self.DoFindInDir()
            return True
            
        # post event to current view control.
        view = wx.GetApp().GetDocumentManager().GetLastActiveView()
        if view and view.ProcessEvent(event):
            return True
        return False

    def OnFindDirChanged(self, event):
        self.Freeze()
        self.Fit()
        self.Layout()
        if self._findDirCtrl.IsExpanded():
            self._findDirCtrl.SetLabel("Find in current file")
            self._radioBox.Disable()
            self._listAllCtrl.Disable()
            self._wrapCtrl.Disable()
        else:
            self._findDirCtrl.SetLabel("Find in Directory")
            self._radioBox.Enable()
            self._listAllCtrl.Enable()
            self._wrapCtrl.Enable()
        self.Thaw()
        
    def MakeFindDirCtrls(self, pane):
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        self._dirCtrl = wx.ComboBox(pane, -1, size=(150, -1))
        self._dirBtCtrl = wx.Button(pane, -1, '...', size=(20, 20))
        self._dirBtCtrl.Bind(wx.EVT_BUTTON, self.OnDirClick)
        self._extCtrl = wx.ComboBox(pane, -1)
        self._excludeCtrl = wx.ComboBox(pane, -1, size=(150, -1))
        sizer = wx.FlexGridSizer(cols=3, hgap=SPACE, vgap=SPACE)
        sizer.AddGrowableCol(1)
        sizer.Add(wx.StaticText(pane, -1, "Directory"), 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._dirCtrl, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._dirBtCtrl, 0, wx.EXPAND)
        
        sizer.Add(wx.StaticText(pane, -1, "File Types"), 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._extCtrl, 0, wx.EXPAND)
        sizer.Add(wx.StaticText(pane, -1))
        
        sizer.Add(wx.StaticText(pane, -1, "Excludes"), 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._excludeCtrl, 0, wx.EXPAND)
        borderSizer.Add(sizer, 0, wx.ALL|wx.EXPAND, SPACE)
        
        self._findSubDir = wx.CheckBox(pane, -1, "Find in subfolders")
        borderSizer.Add(self._findSubDir, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, SPACE)
        pane.SetSizer(borderSizer)
        
        # set initialization value
        config = wx.ConfigBase_Get()
        str = config.Read(FIND_DIRS, "")
        if len(str) != 0:
            dirs = str.split('|')
            for dir in dirs:
                self._dirCtrl.Append(dir)
            self._dirCtrl.SetValue(config.Read(FIND_LAST_DIR, ""))
        
        if self._findDir != None and os.path.exists(self._findDir):
            self._dirCtrl.SetValue(self._findDir)
        
        str = config.Read(FIND_FILE_EXTENSION, "")
        if len(str) != 0:
            exts = str.split("|")
            for ext in exts:
                self._extCtrl.Append(ext)
            self._extCtrl.SetValue(config.Read(FIND_LAST_FILE_EXTENSION, ""))
            
        str = config.Read(FIND_DIR_EXCLUDE, "")
        if len(str) != 0:
            excludes = str.split("|")
            for exclude in excludes:
                self._excludeCtrl.Append(exclude)
        str = config.Read(FIND_LAST_DIR_EXCLUDE, "")
        if len(str) == 0:
            str = '.svn;build;cvs'
        self._excludeCtrl.SetValue(str)
            
        findInSub = config.ReadInt(FIND_IN_SUB_DIRS, False)
        if findInSub:
            self._findSubDir.SetValue(True)
    
    def OnDirClick(self, event):
        dlg = wx.DirDialog(wx.GetApp().GetDocumentManager().FindSuitableParent(),
                           "Choose directory to search",
                           "",
                           wx.DD_DIR_MUST_EXIST)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            self._dirCtrl.SetValue(dlg.GetPath())
        dlg.Destroy()
        
    def DoFindInDir(self):
        dir = self._dirCtrl.GetValue()
        if not os.path.exists(dir):
            wx.MessageBox("Directory %s does not exist!" % dir)
            return
        findService = wx.GetApp().GetService(FindService)
        findService.DoFindInDir(self._findCtrl.GetValue(), 
                                self._dirCtrl.GetValue(), 
                                self._extCtrl.GetValue(), 
                                self._excludeCtrl.GetValue(), 
                                self._findSubDir.GetValue(), 
                                self._matchCaseCtrl.GetValue(), 
                                self._wholeWordCtrl.GetValue(), 
                                self._regExprCtrl.GetValue())
                                
                 
class FindDirThread(threading.Thread):
    def __init__(self, str, path, exts, excludes, inSub, matchCase, wholeWord, regExpr, findCallBack, finishCallBack):
        threading.Thread.__init__(self)
        self._findString    = str
        self._path          = path
        self._exts          = exts.split(';')
        self._excludes      = excludes.split(';')
        self._excludes      = [dir.lower() for dir in self._excludes] 
        self._inSub         = inSub
        self._matchCase     = matchCase
        self._wholeWord     = wholeWord
        self._regExpr       = regExpr
        self._isTerminate   = False
        self._findCallBack  = findCallBack
        self._finishCallBack = finishCallBack
        self._countScan     = 0
        self._countFound    = 0
        self._countFile     = 0
        self._reg           = self.ComputePattern()
        
    def run(self):
        if self._reg == None:
            wx.GetApp().ForegroundProcess(self._finishCallBack, (self._countScan, self._countFound, self._countFile))            
            return
            
        if not self._inSub:
            files = os.listdir(self._path)
            for file in files:
                if self._isTerminate: return
                fullpath = os.path.join(self._path, file)
                if os.path.isdir(fullpath): continue
                self._countScan += 1
                if not self.MatchFile(file): continue
                self.FindInOneFile(fullpath)
        else:
            for root, dirs, files in os.walk(self._path):
                for dir in dirs:
                    if dir.lower() in self._excludes:
                        dirs.remove(dir)
                for file in files:
                    if self._isTerminate: return
                    fullpath = os.path.join(root, file)
                    if os.path.isdir(fullpath): continue
                    self._countScan += 1
                    if not self.MatchFile(file): continue
                    self.FindInOneFile(fullpath)  
        if self._isTerminate: return                  
        wx.GetApp().ForegroundProcess(self._finishCallBack, (self._countScan, self._countFound, self._countFile))
        
    def MatchFile(self, path):
        for ext in self._exts:
            if ext == '*.*': return True
            if ext.lower() == path.lower(): return True
            index1 = ext.rfind('.')
            index2 = path.rfind('.')
            if index1 == -1 or index2 == -1:
                return False
            if ext[index1 + 1:].lower() == path[index2 + 1:].lower():
                return True
        return False
               
    def ComputePattern(self):
        flags = 0
        if self._regExpr:
            pattern = self._findString
        else:
            pattern = re.escape(self._findString)  # Treat the strings as a literal string

        if not self._matchCase:
            flags = re.IGNORECASE
        if self._wholeWord:
            pattern = r"\b%s\b" % pattern
            
        try:
            reg = re.compile(pattern, flags)
            return reg
        except:
            return None
        
                         
    def FindInOneFile(self, path):
        lines = []
        try:
            file = open(path, 'r')
            lines = file.readlines()
            file.close()
        except:
            return
            
        results = []
        for index in range(len(lines)):
            if self._isTerminate: return
            match = self._reg.search(lines[index], 0)
            if match != None:
                results.append((index + 1, lines[index]))
                self._countFound += 1
                
        if len(results) != 0:
            self._countFile += 1
            if self._isTerminate: return
            wx.GetApp().ForegroundProcess(self._findCallBack, (path, results, self._findString, self._path, self._countScan, self._countFound, self._countFile))
        
    def Terminate(self):
        self._isTerminate = True
        
class FindReplaceDialog(FindDialog):
    """ Find/Replace Dialog with regular expression matching and wrap to top/bottom of file. """

    def __init__(self, parent, id, title, size, findString=None):
        wx.Dialog.__init__(self, parent, id, title, size=size)
        
        config = wx.ConfigBase_Get()
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.GridBagSizer(SPACE, SPACE)

        gridSizer2 = wx.GridBagSizer(SPACE, SPACE)
        gridSizer2.Add(wx.StaticText(self, -1, _("Find what:")), flag=wx.ALIGN_CENTER_VERTICAL, pos=(0,0))
        if not findString:
            findString = config.Read(FIND_MATCHPATTERN, "")
        self._findCtrl = wx.ComboBox(self, -1, findString, size=(200, -1))
        for keyword in gKeywordArr:
            self._findCtrl.Append(keyword)        
        gridSizer2.Add(self._findCtrl, pos=(0,1))
        gridSizer2.Add(wx.StaticText(self, -1, _("Replace with:")), flag=wx.ALIGN_CENTER_VERTICAL, pos=(1,0))
        self._replaceCtrl = wx.TextCtrl(self, -1, config.Read(FIND_MATCHREPLACE, ""), size=(200,-1))
        gridSizer2.Add(self._replaceCtrl, pos=(1,1))
        gridSizer.Add(gridSizer2, pos=(0,0), span=(1,2))
        choiceSizer = wx.BoxSizer(wx.VERTICAL)
        self._wholeWordCtrl = wx.CheckBox(self, -1, _("Match whole word only"))
        self._wholeWordCtrl.SetValue(config.ReadInt(FIND_MATCHWHOLEWORD, False))
        self._matchCaseCtrl = wx.CheckBox(self, -1, _("Match case"))
        self._matchCaseCtrl.SetValue(config.ReadInt(FIND_MATCHCASE, False))
        self._regExprCtrl = wx.CheckBox(self, -1, _("Regular expression"))
        self._regExprCtrl.SetValue(config.ReadInt(FIND_MATCHREGEXPR, False))
        self._wrapCtrl = wx.CheckBox(self, -1, _("Wrap"))
        self._wrapCtrl.SetValue(config.ReadInt(FIND_MATCHWRAP, False))
        choiceSizer.Add(self._wholeWordCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._matchCaseCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._regExprCtrl, 0, wx.BOTTOM, SPACE)
        choiceSizer.Add(self._wrapCtrl, 0)
        gridSizer.Add(choiceSizer, pos=(1,0), span=(2,1))

        self._radioBox = wx.RadioBox(self, -1, _("Direction"), choices = ["Up", "Down"])
        self._radioBox.SetSelection(config.ReadInt(FIND_MATCHUPDOWN, 1))
        gridSizer.Add(self._radioBox, pos=(1,1), span=(2,1))

        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        findBtn = wx.Button(self, FindService.FINDONE_ID, _("Find Next"))
        findBtn.SetDefault()
        wx.EVT_BUTTON(self, FindService.FINDONE_ID, self.OnActionEvent)
        cancelBtn = wx.Button(self, wx.ID_CANCEL)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnClose)
        replaceBtn = wx.Button(self, FindService.REPLACEONE_ID, _("Replace"))
        wx.EVT_BUTTON(self, FindService.REPLACEONE_ID, self.OnActionEvent)
        replaceAllBtn = wx.Button(self, FindService.REPLACEALL_ID, _("Replace All"))
        wx.EVT_BUTTON(self, FindService.REPLACEALL_ID, self.OnActionEvent)
        
        BTM_SPACE = HALF_SPACE
        if wx.Platform == "__WXMAC__":
            BTM_SPACE = SPACE
            
        buttonSizer.Add(findBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(replaceBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(replaceAllBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(cancelBtn, 0)
        gridSizer.Add(buttonSizer, pos=(0,2), span=(3,1))

        borderSizer.Add(gridSizer, 0, wx.ALL, SPACE)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetSizer(borderSizer)
        self.Fit()
        self._findCtrl.SetFocus()
        

    def SaveConfig(self):
        """ Save find/replace patterns and search flags to registry. """
        findService = wx.GetApp().GetService(FindService)
        if findService:
            findService.SaveFindConfig(self._findCtrl.GetValue(),
                                       self._wholeWordCtrl.IsChecked(),
                                       self._matchCaseCtrl.IsChecked(),
                                       self._regExprCtrl.IsChecked(),
                                       self._wrapCtrl.IsChecked(),
                                       self._radioBox.GetSelection(),
                                       self._replaceCtrl.GetValue()
                                       )

    def OnActionEvent(self, event):
        self.SaveConfig()
        
        #bugbug: replace dialog does not support list all feature...
        config = wx.ConfigBase_Get()
        oldvalue = config.ReadInt(FIND_LISTALL, False)
        if oldvalue:
            config.WriteInt(FIND_LISTALL, False)
            
        # post event to current view control.
        view = wx.GetApp().GetDocumentManager().GetLastActiveView()
        if view and view.ProcessEvent(event):
            if oldvalue:
                config.WriteInt(FIND_LISTALL, True)
            return True
        if oldvalue:
            config.WriteInt(FIND_LISTALL, True)          
        return False
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib

def getFindData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\xb1IDAT8\x8d\xa5\x93=o\xd3P\x14\x86\x1f\xa7\x11\x95<\xdc\xc6\xecN+5\
[\x86B\x99\xacLQ2Zr[\x89\xa1\xfd\x0b%\x95\x90\x00\xf1\x03\x80\x01\x98\x80\
\x19G\xac\x0cm\xff@Y\xd9:\xd9Ck\x94\xd6\xddb\x94\x9b\x98\xc8\xd2e1C\xe5\x8b\
\xdd\x14\x96\xbe\xdb=\x1f\xefy\xef\xf90\x8c\xda\x12wA\xbd\xfc\x18\xfa\x9fs\
\x80\xf9|\x0e\xc0\x93\xc1\x81\x01\xf0\xe6\xf5\xab\x1c`:\x9d\x02\xf0\xf6\xdd{\
\xa3\xc8\xa9\xddd\xec\xf5z\xb4Z\xeb\x00\x1c\x1f\x1d\xe6\x85\xdd\xf3<\x06\x83\
\xc1\x82\xbd\xa2 \x0cCL\xd3d<\x1e\x13\xc71\xb6m\x030\x1a\x8d\x08\x82\x00\x80\
\xb3\xb3s:\x9d\x8e\xce\xa9(h6\x9b8\x8e\x83m\xdb4\x1a\r\x82 \xe0\xc5\xf3g\xb9\
eY\xb4\xdbm\x1c\xc7Y\xe8\x81&\xf8\xf4\xf1C\xde\xedv+\xce\x97Owx\xfc\xe8k\xc5\
\xb6\xb7\xb7\x8b\xef\x0foW \x84\xe0\xea\xea\x02\xa5\x94n\x18\x80\x94\x92\xd9\
l\x02@\x96e\x95>\xd4nVO\xd3\xb9\x0e\xba\r\xa6i\xd2\xef\xf7\xf0\xfd!\xc7G\x87\
y\xed:)\xd5\x01J\xfd\xd6c\xfc~\x9a\xfc\x93\xe8\xf2\xf2\x02(Ma6\x9b \x84@)\
\xa5\t}\xff\x0b\xd0\'I~R\x14\xca\xb2L\xfb\x97\x97\xef-\xeeA!_J\x89\xeb\xba\
\xb8\xae\xab\xbf\x06\x7f\x97\xacP[\x87\xeb9\x0b!H\x92\ta\x18"\xa5\xd4U\xbd\
\xadm\xe3\xe1\x83\x8d<\x8a~\x90\xa6\xbf\x88\xe3\x18)\xa5&\xa9\x03X\x96E\xab\
\xb5\x8em7\xf5\xc2\x94\xb1\xba\xba\xc6\xe6\xe6\x06++\xf7\x89\xa2\xa8\xe2\xd3\
=89\xf9Va.\x14\x14\xd8\xdf?X VJa\x14\xd7X\xde\xef2\xbc\xadm\xe3\x7f~\xe3\xae\
\xe7\xfc\x07\x84;\xc5\x82\xa1m&\x95\x00\x00\x00\x00IEND\xaeB`\x82' 


def getFindBitmap():
    return BitmapFromImage(getFindImage())

def getFindImage():
    stream = cStringIO.StringIO(getFindData())
    return ImageFromStream(stream)
        
def getFindIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getFindBitmap())
    return icon        

def getFindInFolderData():
    return zlib.decompress(
'x\xda\x01\x8a\x02u\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\
\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x02AIDAT8\x8d\xa5\x92MKUQ\x14\x86\x9fu\xbe\
\xbc\x9a\xa7\x14\xc3\xee-\xc2t\x92J\x83 (\n\x8c\xc2 \xa2Q\x7f\xa0\x1aT\xff \
\x9a\x894t\xd8\xa4\x865\x8bF\x11\x11\x18H9mP\xd1D\t\xcbRB\xaf\x8aW\xef\xf7\
\xd9g\x9f\xbd\x1a\\\xf2\x83\xc2\x88\x1e\xd8\x93\xc5~\x1f\xde\xbdY\xf0\x9f\
\xc8\xec\xcbS\x1f\xdb\xe3\xe1a\x11o\xc7XI\xaa_\x17\xa5Q>+Y\x98\xecJt\xc3B\
\xd0Y\xbbxq\xda\x02\x04\xe2\xfc\xc1\xa3#\x8fC\x11\x01m\x85\x11\xc16\xd7\x06\
\x8a\x1f\xc6\x17UZS\x00?\xda\xaf\xce\xa6+\x85\xe57w\x81g\x00\x01\x996q\xa6-Y\
~Hf|\xf0\xf6#\x12\x93;<\xca\xe13\x13\x11\xaa\x80\x03u\x80"\xb2/\xff\xf9\xc5\
\xc8\xd8\x96@\x0c\x9e:Cf"\xd4)\xae\xb1@Z+R]yK\x98+\x80\xa6\xe0\x0c\xaa\x16\
\xb0\xc4\x83\xf7"\xc1\xf5\xfdj\x15\xe0\x91s\xb6\x81\xa9\x83\x9a\x1ai\xa5L<x\
\x83\\\xcf\x10 \xad\'\xe1h5Q$\xe8B3\t\xb6\x05\xa9G\xd0\xdeK\xd7\xd0\xad\xad\
\x8b\x8a\xc3\x99\x1f\xd8\x8d)\xe6\xd6\x0f2_\xeec\xb5\x91\xa7\xbd-\xa4g_\x95B\
\xda-\xdb\x02\xa3\xaaY\x13W\xff\x84f\x9bhVA\xed\x06.-1W\xca\xf3=\xbd\xc0`\
\x7f\'\'B\x9f\x95MC\xa9\x920\x1f\xdf\x0c\xe05\x00\x9e\x1aT\x9d\xc5\xa5\xab8\
\xb3\x8a3E\x9c)\xa2\xe9*3\xd5Q\x06\x0euPJ\x84\xa5r\x86\x15\x9f#\xbd1\xf5\x03\
\xe7\xfc\xed\x06\x89S!C\xed:j7Z\'\xdbD\xed&\xd5\x86!\x8aBlbq\n\x89Ur\x81\x8f\
\xd5\xad/ \xc0h)\xad\xafu\x98J\x14\x8b\xc6\x9ej\x08.\x06=HG[\x88I3\xd2\x0c\
\xack\xad\x83\n\xd4k\xb5m\x81&\xcd\x89\xf9G\xd7N\xabr\t\x91x\xe7\xd2\xc5\xc7\
\xfb\xc3J\xfe\xaa\x1f\xb7G$\x99\x12x\xc2\xd2z\x8a[\x9b\xd5\xc9\xb1\xd1\x1b\
\x97\xefO=\x11\xf6\xe0\xc1\xe4\xb7\xfe\x9cp\xbd\xbb3\x1aw\n\xe5Z\xd3\xa5\xcb\
32\xd2\xbb$\xb5\xb9\xe9\xca\x97\x99\xf7w\xf6\x14\xfc\x89\xe7cWn\xe7\x0b\x85\
\x89\xde\x81\x93]\xb3\xef^\xd5\xfd\xbfGv\xf3tz\xee\xfd\xf9c\xd5\xefi\xd2\xbc\
\xea\xf9~\xc7\xbf\xe6\x7f\xe3\'\n\xc0*\xd5\x1cv\xea\xe1\x00\x00\x00\x00IEND\
\xaeB`\x82ZN*\xd2' )

def getFindInFolderBitmap():
    return BitmapFromImage(getFindInFolderImage())

def getFindInFolderImage():
    stream = cStringIO.StringIO(getFindInFolderData())
    return ImageFromStream(stream)

def getFindInFolderIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getFindInFolderBitmap())
    return icon    