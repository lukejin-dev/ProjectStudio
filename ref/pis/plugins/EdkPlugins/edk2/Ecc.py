import os
import wx
import  wx.grid as  Grid
import core.service

class ECCService(core.service.PISService):
    ECC_TOOLS_PATH = 'IntelRestrictedTools\\Bin\\Win32\\Ecc.exe'
    
    def __init__(self):
        core.service.PISService.__init__(self)
        self._process = None
        self._pid     = None
        self._input   = None
        self._output  = None
        self._error   = None
        self._workspace = None
        
    def GetPosition(self):
        return 'bottom'
    
    def GetViewClass(self):
        return ECCView    
    
    def GetName(self):
        return "ECC Progress"
    
    def Run(self, workspace, folder):
        if not os.path.exists(workspace):
            wx.MessageBox('ECC fail: Workspace path %s does not exist!' % worksapce)
            return
        if not os.path.exists(os.path.join(workspace, folder)):
            wx.MessageBox('ECC fail: Folder path %s does not exist!' % folder)
            return
        self._workspace = workspace
        self.DeActivate()
        self.Activate()
        wx.EVT_IDLE(self.GetView(), self.OnViewIdle)
        wx.EVT_CLOSE(self._view, self.OnViewClose)
        
        os.putenv('WORKSPACE', workspace)
        # locate ecc tool 
        path = os.path.join(workspace, self.ECC_TOOLS_PATH)
        if not os.path.exists(path):
            wx.MessageBox('ECC Fail: ECC execute file does *not* exist at %s' % path)
            return 
                
        oldPath = os.getcwd()
        os.chdir(os.path.dirname(path))
                   
        command = '%s -t %s' % (path, folder)
        try:
            self._process = ECCProcess()
            self._process.SetParent(self)
            self._process.Redirect()
            self._pid = wx.Execute(command, wx.EXEC_ASYNC, self._process)
            self._input = self._process.GetInputStream()
            self._output = self._process.GetOutputStream()
            self._error  = self._process.GetErrorStream()
        except:
            self._process = None
            os.chdir(oldPath)
            dlg = wx.MessageDialog(None, "There are some problems when running the program!\nPlease run it in shell. The command is: %s" % command,
                    "Stop running", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal() 
        os.chdir(oldPath)

    def OnViewIdle(self, event):
        if self._process != None:
            if self._error:
                if self._error.CanRead():
                    text = self._error.read()
                    self.GetView().AppendText(text)
                    #self.GetView().AppendText('\n')
            if self._input:
                if self._input.CanRead():
                   text = self._input.read()
                   self.GetView().AppendText(text)
                   
    def OnViewClose(self, event):
        if self._process != None:
            wx.Process.Kill(self._pid, wx.SIGKILL, wx.KILL_CHILDREN)
                               
    def OnProcessTerminate(self, id, status):
        self._process = None
        self._pid     = None
        if status != 0:
            wx.MessageBox("ECC tool does not run correctly! Please kill ECC.exe from your task manager and try again!")
            return
        
        path = os.path.join(self._workspace, os.path.dirname(self.ECC_TOOLS_PATH), 'Report.csv')
        file = open(path, 'r')
        lines = file.readlines()
        file.close()
        colnames = [name.strip() for name in lines[0].split(',')[1:]]
        griddata = []
        rowindex = 0
        for line in lines[1:]:
            data = {}
            rawarr = line.split('\"')
            arr = []
            #arr.append(rawarr[0].split(',')[0])
            arr.append(rawarr[0].split(',')[1])
            arr.append(rawarr[1])
            arr.append(rawarr[2].split(',')[1])
            arr.append(rawarr[2].split(',')[2])
            arr.append(rawarr[3])
            
            for index in range(5):
                data[colnames[index]] = arr[index]
            griddata.append((str(rowindex), data))
            rowindex += 1
        
        self.DestroyView()
        reportview =  ECCReportView(self.GetFrame(), 
                                    self,
                                    griddata, 
                                    colnames)
        wx.GetApp().GetTopWindow().AddSideWindow(reportview, 
                                                 'ECC Report',
                                                 'bottom')
        self.SetView(reportview)        
           
class ECCProcess(wx.Process):
    def OnTerminate(self, id, status):
        self._parent.OnProcessTerminate(id, status)
        
    def SetParent(self, parent):
        self._parent = parent
        
import ui.MessageWindow        
class ECCView(core.service.PISServiceView):
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)
        self._ctrl = ui.MessageWindow.MessageWindow(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout() 
        wx.EVT_CLOSE(self, self.OnClose)
        
    def AppendText(self, text):
        self._ctrl.AppendText(text)           
        self._ctrl.DocumentEnd()   
        
    def Clear(self):
        self._ctrl.ClearAll()
   
    def OnClose(self, event):
        self._ctrl.Destroy()
        
class ECCReportView(core.service.PISServiceView):
    def __init__(self, parent, service, data, colnames):
        core.service.PISServiceView.__init__(self, parent, service)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._ctrl = MegaGrid(self, data, colnames)
        self._ctrl.Reset()
        sizer.Add(self._ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        wx.EVT_CLOSE(self, self.OnClose)
        
    def OnClose(self, event):
        self._ctrl.Destroy()
        
class MegaTable(Grid.PyGridTableBase):
    """
    A custom wx.Grid Table using user supplied data
    """
    def __init__(self, data, colnames, plugins):
        """data is a list of the form
        [(rowname, dictionary),
        dictionary.get(colname, None) returns the data for column
        colname
        """
        # The base class must be initialized *first*
        Grid.PyGridTableBase.__init__(self)
        self.data = data
        self.colnames = colnames
        self.plugins = plugins or {}
        # XXX
        # we need to store the row length and column length to
        # see if the table has changed size
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

    def GetNumberCols(self):
        return len(self.colnames)

    def GetNumberRows(self):
        return len(self.data)

    def GetColLabelValue(self, col):
        return self.colnames[col]

    def GetRowLabelValue(self, row):
        return "%03d" % int(self.data[row][0])

    def GetValue(self, row, col):
        return str(self.data[row][1].get(self.GetColLabelValue(col), ""))

    def GetRawValue(self, row, col):
        return self.data[row][1].get(self.GetColLabelValue(col), "")

    def SetValue(self, row, col, value):
        self.data[row][1][self.GetColLabelValue(col)] = value

    def ResetView(self, grid):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        grid.BeginBatch()

        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), Grid.GRIDTABLE_NOTIFY_ROWS_DELETED, Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), Grid.GRIDTABLE_NOTIFY_COLS_DELETED, Grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:

            if new < current:
                msg = Grid.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = Grid.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)

        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        # update the column rendering plugins
        self._updateColAttrs(grid)

        # update the scrollbars and the displayed part of the grid
        #grid.AutoSize()
        #grid.AutoSizeRows(False)
        #grid.AutoSizeColumns()
        grid.AdjustScrollbars()
        grid.ForceRefresh()


    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = Grid.GridTableMessage(self, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    def _updateColAttrs(self, grid):
        """
        wx.Grid -> update the column attributes to add the
        appropriate renderer given the column name.  (renderers
        are stored in the self.plugins dictionary)

        Otherwise default to the default renderer.
        """
        col = 0
        colsize = {'No':20, 'Error Code':80, 'Error Message': 500, 'File':300, 'LineNo':50, 'Other Error Message':500}
        for colname in self.colnames:
            attr = Grid.GridCellAttr()
            if colname in colsize.keys(): 
                grid.SetColSize(col, colsize[colname])

            if colname in self.plugins:
                renderer = self.plugins[colname](self)

                if renderer.colSize:
                    grid.SetColSize(col, renderer.colSize)

                if renderer.rowSize:
                    grid.SetDefaultRowSize(renderer.rowSize)

                attr.SetReadOnly(True)
                attr.SetRenderer(renderer)

            grid.SetColAttr(col, attr)
            col += 1

    # ------------------------------------------------------
    # begin the added code to manipulate the table (non wx related)
    def AppendRow(self, row):
        #print 'append'
        entry = {}

        for name in self.colnames:
            entry[name] = "Appended_%i"%row

        # XXX Hack
        # entry["A"] can only be between 1..4
        entry["A"] = random.choice(range(4))
        self.data.insert(row, ["Append_%i"%row, entry])

    def DeleteCols(self, cols):
        """
        cols -> delete the columns from the dataset
        cols hold the column indices
        """
        # we'll cheat here and just remove the name from the
        # list of column names.  The data will remain but
        # it won't be shown
        deleteCount = 0
        cols = cols[:]
        cols.sort()

        for i in cols:
            self.colnames.pop(i-deleteCount)
            # we need to advance the delete count
            # to make sure we delete the right columns
            deleteCount += 1

        if not len(self.colnames):
            self.data = []

    def DeleteRows(self, rows):
        """
        rows -> delete the rows from the dataset
        rows hold the row indices
        """
        deleteCount = 0
        rows = rows[:]
        rows.sort()

        for i in rows:
            self.data.pop(i-deleteCount)
            # we need to advance the delete count
            # to make sure we delete the right rows
            deleteCount += 1

    def SortColumn(self, col):
        """
        col -> sort the data based on the column indexed by col
        """
        name = self.colnames[col]
        _data = []

        for row in self.data:
            rowname, entry = row
            _data.append((entry.get(name, None), row))

        _data.sort()
        self.data = []

        for sortvalue, row in _data:
            self.data.append(row)

    # end table manipulation code
    # ----------------------------------------------------------

class MegaGrid(Grid.Grid):
    def __init__(self, parent, data, colnames, plugins=None):
        """parent, data, colnames, plugins=None
        Initialize a grid using the data defined in data and colnames
        (see MegaTable for a description of the data format)
        plugins is a dictionary of columnName -> column renderers.
        """

        # The base class must be initialized *first*
        Grid.Grid.__init__(self, parent, -1)
        self._table = MegaTable(data, colnames, plugins)
        self.colnames = colnames
        self.data     = data
        self.SetTable(self._table)
        self._plugins = plugins
        self.Bind(Grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClicked)
        self.Bind(Grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(Grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.OnCellLeftDoubleClick)
        
    def OnCellLeftClick(self, event):
        row = event.GetRow()
        col = event.GetCol()
        self.SelectRow(row, False)
        self.GetParent().SetTitle('%s  %s' % (self._table.GetValue(row, 1), self._table.GetValue(row, 4)))
        
        
    def OnCellLeftDoubleClick(self, event):
        row = event.GetRow()
        col = event.GetCol()
        fname = self._table.GetValue(event.GetRow(), 2)
        line  = self._table.GetValue(event.GetRow(), 3)
        docmgr = wx.GetApp().GetDocumentManager()
        doc = docmgr.CreateDocument(fname, wx.lib.docview.DOC_SILENT)
        if doc != None:
            view = doc.GetFirstView()
            if view != None:
                wx.CallAfter(view.GotoLine, int(line))
        
    def Reset(self):
        """reset the view based on the data in the table.  Call
        this when rows are added or destroyed"""
        self._table.ResetView(self)

    def OnLabelRightClicked(self, evt):
        # Did we click on a row or a column?
        row, col = evt.GetRow(), evt.GetCol()
        if row == -1: self.colPopup(col, evt)
        elif col == -1: self.rowPopup(row, evt)

    def rowPopup(self, row, evt):
        """(row, evt) -> display a popup menu when a row label is right clicked"""
        return
        appendID = wx.NewId()
        deleteID = wx.NewId()
        x = self.GetRowSize(row)/2

        if not self.GetSelectedRows():
            self.SelectRow(row)

        menu = wx.Menu()
        xo, yo = evt.GetPosition()
        menu.Append(appendID, "Append Row")
        menu.Append(deleteID, "Delete Row(s)")

        def append(event, self=self, row=row):
            self._table.AppendRow(row)
            self.Reset()

        def delete(event, self=self, row=row):
            rows = self.GetSelectedRows()
            self._table.DeleteRows(rows)
            self.Reset()

        self.Bind(wx.EVT_MENU, append, id=appendID)
        self.Bind(wx.EVT_MENU, delete, id=deleteID)
        self.PopupMenu(menu)
        menu.Destroy()
        return


    def colPopup(self, col, evt):
        """(col, evt) -> display a popup menu when a column label is
        right clicked"""
        x = self.GetColSize(col)/2
        menu = wx.Menu()
        id1 = wx.NewId()
        sortID = wx.NewId()

        xo, yo = evt.GetPosition()
        self.SelectCol(col)
        cols = self.GetSelectedCols()
        self.Refresh()
        #menu.Append(id1, "Delete Col(s)")
        menu.Append(sortID, "Sort Column")

        def delete(event, self=self, col=col):
            cols = self.GetSelectedCols()
            self._table.DeleteCols(cols)
            self.Reset()

        def sort(event, self=self, col=col):
            self._table.SortColumn(col)
            self.Reset()

        self.Bind(wx.EVT_MENU, delete, id=id1)

        if len(cols) == 1:
            self.Bind(wx.EVT_MENU, sort, id=sortID)

        self.PopupMenu(menu)
        menu.Destroy()
        return
        
"""        
class EccReportCtrl(Grid.PyGridTableBase):
    def __init__(self, data, colnames, plugins):  
        Grid.PyGridTableBase.__init__(self)
"""              