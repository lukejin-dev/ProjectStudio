"""
 _template_attribute_ must be defined in template python code as
 [description, filter, dir, ext, docTypeName, viewTypeName, docType, viewType, flag, icon]
"""

_plugin_module_info_ = [{"name":"ITPPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"ITP plugin",
                         "class":"ITPPlugin"}]
import core.plugin                         
import core.service
import wx, re, wx.stc
import time
from itpapi_i import *

class ITPPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return ITPService
        
    def IGetIcon(self):
        """Interface for child class provide template's icon"""
        return getdebugIcon()      
          
class ITPService(core.service.PISService):       
    ITP_START_ID        = wx.NewId()
    ITP_GO_ID           = wx.NewId()
    ITP_RESET_ID        = wx.NewId()
    ITP_HALT_ID         = wx.NewId()
    ITP_STEP_INTO_ID    = wx.NewId()
    ITP_STEP_OUT_ID     = wx.NewId()
    ITP_STEP_OVER_ID    = wx.NewId()
    ITP_STEP_BRANCH_ID  = wx.NewId()
    ITP_VIEW_REGISTER   = wx.NewId()
    ITP_VIEW_MEMORY     = wx.NewId()
    
    def __init__(self):
        core.service.PISService.__init__(self)
        self._itpApiObj     = None
        self._itpConfigObj  = None
        self._isRun         = False
        self._needReset     = False
        self._registerView  = None
        self._memoryView    = None
        self._isRunning     = True
        self._diassembleView = None
        
    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        viewIndex = menuBar.FindMenu('View')
        
        itpMenu = wx.Menu()
        menuBar.Insert(viewIndex + 1, itpMenu, 'Debug')
        
        item = wx.MenuItem(itpMenu, self.ITP_START_ID, 'Connect', 'Connect ITP!')
        item.SetBitmap(getdebugBitmap())
        itpMenu.AppendItem(item)
        itpMenu.AppendSeparator()
        
        item = wx.MenuItem(itpMenu, self.ITP_GO_ID, 'Go\tF5', 'Go!')
        item.SetBitmap(getgoBitmap())
        itpMenu.AppendItem(item)

        item = wx.MenuItem(itpMenu, self.ITP_HALT_ID, 'Halt', 'Halt!')
        item.SetBitmap(gethaltBitmap())
        itpMenu.AppendItem(item)

        item = wx.MenuItem(itpMenu, self.ITP_RESET_ID, 'Reset', 'Reset!')
        item.SetBitmap(getresetBitmap())
        itpMenu.AppendItem(item)
        
        item = wx.MenuItem(itpMenu, self.ITP_STEP_INTO_ID, 'Step Into\tF11', 'Step Into!')
        item.SetBitmap(getStepIntoBitmap())
        itpMenu.AppendItem(item)        

        item = wx.MenuItem(itpMenu, self.ITP_STEP_OVER_ID, 'Step Over\tF10', 'Step Over!')
        item.SetBitmap(getStepOverBitmap())
        itpMenu.AppendItem(item)        

        item = wx.MenuItem(itpMenu, self.ITP_STEP_OUT_ID, 'Step Out', 'Step Out!')
        item.SetBitmap(getStepOutBitmap())
        itpMenu.AppendItem(item)        

        item = wx.MenuItem(itpMenu, self.ITP_STEP_BRANCH_ID, 'Step Branch', 'Step Branch!')
        #item.SetBitmap(getresetBitmap())
        itpMenu.AppendItem(item)        
        
        itpMenu.AppendSeparator()
        
        item = wx.MenuItem(itpMenu, self.ITP_VIEW_MEMORY, 'Memory', 'View Memory')
        item.SetBitmap(getmemoryBitmap())
        itpMenu.AppendItem(item)
        
        item = wx.MenuItem(itpMenu, self.ITP_VIEW_REGISTER, 'Register', 'View Register')
        item.SetBitmap(getregisterBitmap())
        itpMenu.AppendItem(item)
        
        wx.EVT_MENU(frame, self.ITP_START_ID, self.OnStartITP)
        wx.EVT_MENU(frame, self.ITP_GO_ID, self.OnITPGo)
        wx.EVT_MENU(frame, self.ITP_RESET_ID, self.OnITPResetAll)
        wx.EVT_MENU(frame, self.ITP_HALT_ID, self.OnITPHaltAll)
        wx.EVT_MENU(frame, self.ITP_STEP_INTO_ID, self.OnITPStepInto)
        wx.EVT_MENU(frame, self.ITP_STEP_OVER_ID, self.OnITPStepOver)
        wx.EVT_MENU(frame, self.ITP_STEP_OUT_ID, self.OnITPStepOut)
        wx.EVT_MENU(frame, self.ITP_STEP_BRANCH_ID, self.OnITPStepBranch)
        wx.EVT_MENU(frame, self.ITP_VIEW_MEMORY, self.OnITPViewMemory)
        wx.EVT_MENU(frame, self.ITP_VIEW_REGISTER, self.OnITPViewRegister)
        
        wx.EVT_UPDATE_UI(frame, self.ITP_START_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_GO_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_RESET_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_HALT_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_STEP_INTO_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_STEP_OVER_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_STEP_OUT_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_STEP_BRANCH_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_VIEW_MEMORY, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, self.ITP_VIEW_REGISTER, self.ProcessUpdateUIEvent)

        # event for children view
        """
        wx.EVT_MENU(frame, wx.ID_COPY, self.ProcessEvent)
        wx.EVT_MENU(frame, wx.ID_SELECTALL, self.ProcessEvent)
        wx.EVT_MENU(frame, ZOOM_NORMAL_ID, self.ProcessEvent)
        wx.EVT_MENU(frame, ZOOM_IN_ID, self.ProcessEvent)
        wx.EVT_MENU(frame, ZOOM_OUT_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, wx.ID_COPY, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, wx.ID_SELECTALL, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_NORMAL_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_IN_ID, self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_OUT_ID, self.ProcessUpdateUIEvent)
        """
        
    def GetCustomizeToolBars(self):
        toolbar = wx.ToolBar(wx.GetApp().GetTopWindow(),
                              -1, wx.DefaultPosition, wx.DefaultSize,
                             wx.TB_FLAT | wx.TB_NODIVIDER)
        bitmap = getdebugBitmap()
        bitmap.SetSize((16,16))
        toolbar.AddLabelTool(self.ITP_START_ID,
                             'Connect ITP',
                             bitmap,
                             shortHelp = "Connect ITP", 
                             longHelp =  "Connect ITP")
        toolbar.AddLabelTool(self.ITP_GO_ID,
                             'Go',
                             getgoBitmap(),
                             shortHelp = "Go",
                             longHelp  = "Go")
        toolbar.AddLabelTool(self.ITP_HALT_ID,
                             'Halt',
                             gethaltBitmap(),
                             shortHelp = 'Halt All',
                             longHelp  = 'Halt All')
        toolbar.AddLabelTool(self.ITP_RESET_ID,
                             'Reset',
                             getresetBitmap(),
                             shortHelp = 'Reset target',
                             longHelp  = 'Reset target')  
        toolbar.AddLabelTool(self.ITP_STEP_OVER_ID,
                             'Step Over',
                             getStepOverBitmap(),
                             shortHelp = 'Step Over',
                             longHelp  = 'Step Over')  
        toolbar.AddLabelTool(self.ITP_STEP_INTO_ID,
                             'Step Into',
                             getStepIntoBitmap(),
                             shortHelp = 'Step Into',
                             longHelp  = 'Step Into')  
        toolbar.AddLabelTool(self.ITP_STEP_OUT_ID,
                             'Step Out',
                             getStepOutBitmap(),
                             shortHelp = 'Step Out',
                             longHelp  = 'Step Out') 
        toolbar.AddSeparator()
        
        toolbar.AddLabelTool(self.ITP_VIEW_MEMORY,
                             'View Memory',
                             getmemoryBitmap(),
                             shortHelp = 'View Memory',
                             longHelp  = 'View Memory') 
        toolbar.AddLabelTool(self.ITP_VIEW_REGISTER,
                             'View Register',
                             getregisterBitmap(),
                             shortHelp = 'View Register',
                             longHelp  = 'View Register')
                                                                 
        toolbar.Realize()
        return [toolbar]

    def DeActivate(self):
        if self._registerView != None:
            self._registerView.Close()
        if self._memoryView != None:
            self._memoryView.Close()
            
        core.service.PISService.DeActivate(self)
        
    def OnITPViewMemory(self, event):
        self._memoryView.Activate()
    
    def OnITPViewRegister(self, event):
        self._registerView.Activate()
        
    def OnStartITP(self, event):
        self._itpApiObj = ITPApiCOM()
        wx.GetApp().GetTopWindow().CloseAllDocumentWindows()
        self.CreateDebugView()
        
        if not self._itpApiObj.ConnectITP():
            self.RemoveDebugView()
            wx.MessageBox("Fail to connect ITP, please make sure ITP software is installed correctly!")
            return
        self._itpApiObj.PutMessage('=================================================')
        self._itpApiObj.PutMessage('>============= EDES2008 connected! =============<')
        self._itpApiObj.PutMessage('=================================================')
        if self.IsITPReady() and not self.IsRunning():
            self._diassembleView.Clear()
            self._diassembleView.PutCode(self._itpApiObj.GetDiasm())
    
    def OnItpQuit(self, event):
        self.RemoveDebugView()
        
    def OnITPGo(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
        
        self._itpApiObj.Go(0, 1)
                
    def OnITPResetAll(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
                
        self._itpApiObj.Reset()
        self.GetDisassembleView().Clear()
        self.GetDisassembleView().PutCode(self._itpApiObj.GetDiasm())
                        
    def OnITPHaltAll(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
                
        self._itpApiObj.Halt(0, 1)
        self.GetDisassembleView().Clear()
        self.GetDisassembleView().PutCode(self._itpApiObj.GetDiasm())
        
    def OnITPStepInto(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
        try:
            self._itpApiObj.StepInto()
        except:
            wx.MessageBox("ITP fail to execute step into command!")
            return
        
        self.GetDisassembleView().Clear()
        self.GetDisassembleView().PutCode(self._itpApiObj.GetDiasm())
        
    def OnITPStepOver(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
        try:
            self._itpApiObj.StepOver()
        except:
            wx.MessageBox("ITP fail to execute step over command!")
            return
        
        self.UpdateRegisters()
        self.GetDisassembleView().Clear()
        self.GetDisassembleView().PutCode(self._itpApiObj.GetDiasm())
        
    def OnITPStepOut(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
        try:
            self._itpApiObj.StepOut()
        except:
            wx.MessageBox("ITP fail to execute step out command!")
            return
        
        self.UpdateRegisters()
        self.GetDisassembleView().Clear()
        self.GetDisassembleView().PutCode(self._itpApiObj.GetDiasm())
                
    def OnITPStepBranch(self, event):
        if not self.IsTargetPowerOn():
            wx.MessageBox("Target is power off! Please turn on and retry!")
            return
        self._itpApiObj.StepBranch()
        self.UpdateRegisters()
                     
    def IsITPReady(self):
        if self._itpApiObj == None:
            return False
        try:
            ret = self._itpApiObj.IsITPReady()
        except:
            return False
        return ret
    
    def IsRunning(self):
        ret = self._itpApiObj.GetTargetProcessorStatus() == 'Running'
        if not ret and self._isRunning:
            self.UpdateRegisters()
        self._isRunning = ret
        return ret
    
    def IsTargetPowerOn(self):
        return (self._itpApiObj.GetTargetPowerStatus() == 'On')
    
    def IsNeedReconnect(self):
        if self._itpApiObj == None:
            return True
        return self._itpApiObj.IsNeedReconnect()
    
    def UpdateRegisters(self):
        if not self.IsITPReady():
            return
        
        regs = self._itpApiObj.GetAllRegisterValue()
        if self._registerView != None:
            self._registerView.UpdateRegisters(regs) 
            
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
            
        if self.IsNeedReconnect():
            if id == self.ITP_START_ID:
                event.Enable(True)
                self.RemoveDebugView()
            else:
                event.Enable(False)
            return True
        
        if self.IsITPReady() and self._needReset:
            self._needReset = False
            self._itpApiObj.Reset()
            return True
        
        if id == self.ITP_START_ID:
            event.Enable(not self.IsITPReady())
        elif id == self.ITP_GO_ID or \
             id == self.ITP_VIEW_MEMORY or \
             id == self.ITP_VIEW_REGISTER:
            if not self.IsITPReady():
                event.Enable(False)
                self._memoryView.Enable(False)
            else:
                event.Enable(not self.IsRunning())
                if self._memoryView != None:
                    self._memoryView.Enable(not self.IsRunning())
            return True
        elif id == self.ITP_HALT_ID:
            if not self.IsITPReady():
                event.Enable(False)
            else:
                event.Enable(self.IsRunning())
        elif id == self.ITP_RESET_ID:
            event.Enable(self.IsITPReady())    
        elif id in [self.ITP_STEP_INTO_ID, self.ITP_STEP_OUT_ID, self.ITP_STEP_BRANCH_ID, self.ITP_STEP_OVER_ID]:
            if not self.IsITPReady() or self.IsRunning():
                event.Enable(False)
            else:
                event.Enable(True)
            return True
        elif id in [wx.ID_COPY]:
            frame = wx.GetApp().GetTopWindow()
            focus = frame.FindFocus()
            if focus == None: return False
            print focus
            return False
        return False

    def CreateDebugView(self):
        frame = wx.GetApp().GetTopWindow()
        if self._memoryView == None:
            self._memoryView = MemoryView(frame, self)
            frame.AddSideWindow(self._memoryView, 
                                'Memory',
                                'bottom',
                                getmemoryIcon())         
        if self._registerView == None:
            self._registerView = RegisterView(frame, self)
            frame.AddSideWindow(self._registerView, 
                                'Register',
                                'bottom',
                                getregisterIcon()) 
        if self._diassembleView == None:
            frame = wx.GetApp().GetTopWindow()
            nb    = frame.GetNotebook()            
            self._diassembleView = DisassembleView(nb, self)
            frame.AddNotebookPage(self._diassembleView,'Disassemble')
            self._diassembleView.Bind(wx.EVT_CLOSE, self.OnDiasmViewClose)
            
    def OnDiasmViewClose(self, event):
        self._diassembleView = None
        
    def GetDisassembleView(self):
        if self._diassembleView == None:
            self.CreateDebugView()
        return self._diassembleView
    
    def RemoveDebugView(self):
        frame = wx.GetApp().GetTopWindow()
        if self._registerView != None:
            frame.RemoveSideWindow(self._registerView, 'bottom')
            self._registerView.Destroy()
            self._registerView = None
            
        if self._memoryView != None:
            frame.RemoveSideWindow(self._memoryView, 'bottom')
            self._memoryView.Destroy()
            self._memoryView = None
            
        if self._diassembleView != None:
            wx.GetApp().GetTopWindow().CloseAllDocumentWindows()
            self._diassembleView = None
            
    def GetMemory(self, addr, width=1, count=128, addrType='IA32_PHY_PTR', dtSel=0, segSel=0):
        return self._itpApiObj.GetMemory(addr, 0, width, count, addrType, dtSel, segSel)
        
    def DeActivate(self):
        if self._itpApiObj != None and self._itpApiObj.IsITPReady():
            self._itpApiObj.PutMessage('=================================================')
            self._itpApiObj.PutMessage('>============== EDES2008 bye bye! ==============<')
            self._itpApiObj.PutMessage('=================================================')
        core.service.PISService.DeActivate(self)
                    
import  wx.lib.mixins.listctrl  as  listmix        
class RegisterListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self) 
        self._cachedvalue = None
                        
    def OpenEditor(self, col, row):
        if col != 1: return
        listmix.TextEditMixin.OpenEditor(self, col, row)
        item = self.GetItem(row, col)
        self._cachedvalue = item.GetText()
        
    def CloseEditor(self, evt=None):
        listmix.TextEditMixin.CloseEditor(self, evt)
        if evt == None:
            self.GetParent().OnEndEditor(self.curRow, self._cachedvalue)
        
class RegisterView(wx.Panel):
    regtable = ['EAX', 'EBX', 'ECX', 'EDX', 
                'ESI', 'EDI', 'EBP', 'ESP', 
                'CR0', 'CR2', 'CR3', 'CR4',
                'EIP', 'EFLAGS']
    
    def __init__(self, parent, service, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Panel'):    
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self._service = service
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._regList = RegisterListCtrl(self, -1, style=wx.LC_REPORT)
        sizer.Add(self._regList, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        
        self._regList.InsertColumn(0, 'Register')
        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
        info.m_format = wx.LIST_FORMAT_RIGHT
        info.m_text = "Value"
        self._regList.InsertColumnInfo(1, info)
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
        info.m_format = wx.LIST_FORMAT_RIGHT
        info.m_text = "Length"        
        self._regList.InsertColumnInfo(2, info)
        
        self._regList.SetColumnWidth(1, 200)
        self._cache = {}
        
        for reg in REG_TABLE:
            self._regList.InsertStringItem(self._regList.GetItemCount(), reg)
          
    def OnEndEditor(self, row, oldvalue):
        print oldvalue
        nameItem = self._regList.GetItem(row, 0)
        regname = nameItem.GetText()
        valueItem = self._regList.GetItem(row, 1)
        valuestr = valueItem.GetText()
        lenItem = self._regList.GetItem(row, 2)
        length = int(lenItem.GetText())
        if valuestr.startswith('0x'):
            value = int(valuestr, 16)
        else:
            value = int(valuestr)
            
        if not self._service._itpApiObj.PutRegisterValue(0, regname, value, length):
            valueItem.SetText(oldvalue)
            
    def UpdateRegisterValue(self, regname, value):
        count = self._regList.GetItemCount()
        found = False
        for index in range(count):
            text = self._regList.GetItemText(index)
            if text.lower() == regname.lower():
                found = True
                break
        if found:
            self._regList.SetStringItem(index, 1, self.GetValueString(value))
            self._regList.SetStringItem(index, 2, '%d' % value[1])
            if not self._cache.has_key(regname):
                self._cache[regname] = value
                return
            if self._cache[regname][0] != value[0]:
                item = self._regList.GetItem(index)
                item.SetTextColour(wx.RED)
                self._regList.SetItem(item)
            else:
                item = self._regList.GetItem(index)
                item.SetTextColour(wx.BLACK)
                self._regList.SetItem(item)
                
            self._cache[regname] = value
    
    def GetValueString(self, value):
        v = value[0]
        l = value[1]
        if l <= 8:
            return '0x%08X' % v
        if l <= 16:
            return '0x%016X' % v
        if l <= 32:
            return '0x%032X' % v
        return '0x%064X' % v
    
    def UpdateRegisters(self, dict):
        for key in dict.keys():
            self.UpdateRegisterValue(key, dict[key])
         
    def Activate(self):
        frame = wx.GetApp().GetTopWindow()
        frame.ActivatePageInSideWindow(self)
                    
class MemoryView(wx.Panel):
    ADDR_TYPE_DICT = {'IA32_PHY_PTR': 'IA32 Physical',
                      'IA32_LIN_PTR': 'IA32 Linear'}
    def __init__(self, parent, service, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL|wx.NO_BORDER, name='Panel'):    
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self._service = service
        self._addrInput        = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
        self._memory           = core.hexctrl.HexCtrl(self, -1)
        self._addrTypeSelector = wx.ComboBox(self, -1, value='IA32 Physical', choices=self.ADDR_TYPE_DICT.values(), style=wx.CB_READONLY)
        self._refresh          = wx.Button(self, -1, 'Refresh')
        self._refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self._lenctl           = wx.TextCtrl(self, -1, '128', style=wx.TE_PROCESS_ENTER)
        self._lenctl.Bind(wx.EVT_TEXT_ENTER, self.OnRefresh)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(wx.StaticText(self, -1, 'Address:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer1.Add(self._addrInput, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 20)
        sizer1.Add(wx.StaticText(self, -1, 'Address Type:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer1.Add(self._addrTypeSelector, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 20)
        sizer1.Add(wx.StaticText(self, -1, 'Lenght:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer1.Add(self._lenctl, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 20)
        sizer1.Add(self._refresh, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 20)
        
        sizer.Add(sizer1, 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self._memory, 1, wx.EXPAND|wx.ALL, 2)
        self.SetSizer(sizer)
        self.Layout()
        self._addrInput.Bind(wx.EVT_TEXT_ENTER , self.OnRefresh)
        self._addrInput.SetFocus()
        wx.EVT_CLOSE(self, self.OnClose)
        
    def OnRefresh(self, event):
        self._memory.ClearAll()
        text = self._addrInput.GetLabel()
        if len(text) == 0: return
        if text.lower().startswith('0x'):
            value = int(text, 16)
        else:
            value = int(text)
        lenstr = self._lenctl.GetLabel()
        lenval = 128
        if len(lenstr) != 0:
            if lenstr.lower().startswith('0x'):
                lenval = int(lenstr, 16)
            else:
                lenval = int(lenstr)
                
        data = self._service.GetMemory(value, count=lenval, addrType=self.GetAddressType())
        self._memory.SetRawData(value, data)
        
    def GetAddressType(self):
        text = self._addrTypeSelector.GetLabel()
        
        for key in self.ADDR_TYPE_DICT.keys():
            if self.ADDR_TYPE_DICT[key] == text:
                break
        return key
    
    def Enable(self, bEnable=True):
        if bEnable:
            self._addrInput.Enable()
            self._addrTypeSelector.Enable()
            self._lenctl.Enable()
        else:
            self._addrInput.Enable(False)
            self._addrTypeSelector.Enable(False)
            self._lenctl.Enable(False)
            
    def Activate(self):
        frame = wx.GetApp().GetTopWindow()
        frame.ActivatePageInSideWindow(self)        
        
    def OnClose(self, event):
        self._memory.Destroy()
        
from core.editor import ZOOM_ID, ZOOM_NORMAL_ID, ZOOM_IN_ID, ZOOM_OUT_ID        
class DisassembleView(wx.Panel):
    BREAKPOINT_MARKER_NUM       = 1
    CURRENT_LINE_MARKER_NUM     = 2
    CURRENT_LINE_MARKER_MASK    = 0x4
    BREAKPOINT_MARKER_MASK      = 0x2
        
    def __init__(self, parent, service):
        wx.Panel.__init__(self, parent)
        self._service = service         
        self._ctrl = core.hexctrl.HexCtrl(self, -1)
        
        # set break pointer marker
        self._ctrl.SetMarginType(self.BREAKPOINT_MARKER_NUM, wx.stc.STC_MARGIN_SYMBOL)
        self._ctrl.SetMarginMask(self.BREAKPOINT_MARKER_NUM, self.BREAKPOINT_MARKER_MASK)
        self._ctrl.SetMarginSensitive(self.BREAKPOINT_MARKER_NUM, True)
        self._ctrl.SetMarginWidth(self.BREAKPOINT_MARKER_NUM, 12)
        
        # set current line marker 
        self._ctrl.SetMarginType(self.CURRENT_LINE_MARKER_NUM, wx.stc.STC_MARGIN_SYMBOL)
        self._ctrl.SetMarginMask(self.CURRENT_LINE_MARKER_NUM, self.CURRENT_LINE_MARKER_MASK)
        self._ctrl.SetMarginSensitive(self.CURRENT_LINE_MARKER_NUM, False)
        self._ctrl.SetMarginWidth(self.CURRENT_LINE_MARKER_NUM, 12)

        self._ctrl.MarkerDefine(self.BREAKPOINT_MARKER_NUM, wx.stc.STC_MARK_CIRCLE, wx.BLACK, (255,0,0))
        # Define the current line marker
        self._ctrl.MarkerDefine(self.CURRENT_LINE_MARKER_NUM, wx.stc.STC_MARK_SHORTARROW, wx.BLACK, (255,255,128))
        
        wx.stc.EVT_STC_MARGINCLICK(self, self._ctrl.GetId(), self.OnMarginClick)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        
        self._breaklist = []
        #self._ctrl.MarkerAdd(0, self.BREAKPOINT_MARKER_MASK)
        #self._ctrl.MarkerAdd(1, self.CURRENT_LINE_MARKER_MASK)
        wx.EVT_CLOSE(self, self.OnClose)
        frame = wx.GetApp().GetTopWindow()
                
    def OnMarginClick(self, event):
        line = self._ctrl.LineFromPosition(event.GetPosition())
        cs, addr = self.GetAddress(line)
        if len(addr) == 0: return
        cs_val   = int(cs, 16)
        addr_val = int(addr, 16)
        self._breaklist.append((cs_val, addr_val))
        if cs_val > 0xFF:
            self._service._itpApiObj.PutHardwareBreakPointer(0, addr_val)
        else:
            self._service._itpApiObj.PutHardwareBreakPointer(0, addr_val, segsel=cs_val)

        self._ctrl.MarkerAdd(self._ctrl.LineFromPosition(event.GetPosition()), self.BREAKPOINT_MARKER_NUM)
    
    def GetAddress(self, line):
        text = self._ctrl.GetLine(line)
        if len(text) == 0: return (u'', u'')
        cs, addr = text.split(' ')[0].split(':')
        return cs, addr
        
    
    def GetView(self):
        return self
    
    def GetDocument(self):
        return None
    
    def PutCode(self, list):
        if list == None:
            self._ctrl.Clear()
            return
        
        self._ctrl.MarkerDeleteAll(self.BREAKPOINT_MARKER_NUM)        
        
        self._ctrl.SetReadOnly(False)
        codeseg = self._service._itpApiObj.GetRegisterValue(0, 'cs')
        index = 0
        for item in list:
            addr = int(item[0])
            self._ctrl.AddText('0x%02X:0x%08X  %2s %20s  %s\n' % (codeseg[0], addr, item[1], item[3], item[2]))
            for bk_cs, bk_addr in self._breaklist:
                if bk_cs == codeseg[0] and bk_addr == addr:
                    self._ctrl.MarkerAdd(index, self.BREAKPOINT_MARKER_NUM)
            index += 1
            
        self._ctrl.SetReadOnly(True)
        self._ctrl.GotoLine(0)
        self._ctrl.SetFocus()
        #self._ctrl.MarkerAdd(1, self.CURRENT_LINE_MARKER_MASK) 
        
        self._ctrl.MarkerAdd(0, self.CURRENT_LINE_MARKER_NUM)
        
    def Clear(self):
        self._ctrl.SetReadOnly(False)
        self._ctrl.ClearAll()
        self._ctrl.SetReadOnly(True)
        
    def OnClose(self, event):
        self._ctrl.Destroy()
        self._ctrl = None
        
    def ProcessEvent(self, event):
        id = event.GetId()

        if id == wx.ID_SELECTALL:
            self._ctrl.SetSelection(0, -1)
            return True        
        elif id == wx.ID_COPY:
            self._ctrl.Copy()
            return True
        elif id == ZOOM_NORMAL_ID:
            self._ctrl.SetZoom(0)
            return True
        elif id == ZOOM_IN_ID:
            self._ctrl.CmdKeyExecute(wx.stc.STC_CMD_ZOOMIN)
            return True
        elif id == ZOOM_OUT_ID:
            self._ctrl.CmdKeyExecute(wx.stc.STC_CMD_ZOOMOUT)
            return True        
                
        return False
        
    def ProcessUpdateUIEvent(self, event):
        if self._ctrl == None: return False
        
        id = event.GetId()
        
        if id == wx.ID_SELECTALL:
            hasText = self._ctrl.GetTextLength() > 0
            event.Enable(hasText)
            return True        
        elif id == wx.ID_COPY:
            hasSelection = self._ctrl.GetSelectionStart() != self._ctrl.GetSelectionEnd()
            event.Enable(hasSelection)
            return True
        elif id == ZOOM_ID:
            event.Enable(True)
            return True
        elif id == ZOOM_NORMAL_ID:
            event.Enable(self._ctrl.GetZoom() != 0)
            return True
        elif id == ZOOM_IN_ID:
            event.Enable(self._ctrl.GetZoom() < 20)
            return True
        elif id == ZOOM_OUT_ID:
            event.Enable(self._ctrl.GetZoom() > -10)
            return True        
        return False
#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

debug = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAeVJ"
    "REFUKJGFkz9oU1EUh7+bWtNKwb1LoCJWrKYVQ6oSpRmMlFCqhiwObqIOCoKo2CKiUKs4qEgH"
    "F5FO+nwmGpA4WOxQsa2QIQpqRQeRSGxITMp7L3/ecRBfm9jQA2e4h/Pdc3/nnItytbDS+6ND"
    "0hhr5i4azDKrdWd/ZFgac/5ZHRzTdKmWi8Q03QEs83czFtUXHRRMqFKhUjZp7d4PwLV9Ps5P"
    "XGf85AWGI4fVqrBytThVR6bneHn1GN8yaY7fe+ckpe+MKY/fK21tbj6+nl2+aGUDtp0ekTcL"
    "T2XHqS75nJ2X9z+mZWZBl54zlySuxyWux2X7UED6ooN/m9ofPSIAb7WYimm6XJyaJT56iI72"
    "jZTMAvlShsXiT87e/8rYgK9OgvPs3nBQDKOEbA6ij4ZYv24DLz48Z1enl7yRJW/kuPKwyKeJ"
    "cQd2up1KvFIVy6JmC4WlX+RLGXydXp7MP8Kqmlh2mVoNPH6v9IT3yH+janW7uXXAz9GbcywW"
    "M+SMLHu37GZy6jFG1cS24fa5y6QTM6o3HJJ6uL0DANuGE3e/UDByFKw8QV+AyeQzarbtaE4l"
    "kmpZcyQkKS3p6PH4vVLbGgIlgAKB7w9u1M+72d5uGtjpjKdZTlO4+2BgzQ+yatBZgjX8D3AI"
    "0/4M4B9uAAAAAElFTkSuQmCC")
getdebugData = debug.GetData
getdebugImage = debug.GetImage
getdebugBitmap = debug.GetBitmap
getdebugIcon = debug.GetIcon      

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

go = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAABHNCSVQICAgIfAhkiAAAAO1J"
    "REFUKJGNzrFOAkEQxvH/7vEA9whXGg0xWJnoK9hbXinE4goQnsKKhER8EStPNIAcMRIoEDXZ"
    "knLK7dYCMCzcJWwyxcz+vskopQMOfXq7yX777mDcfuqQ/bwVBvTuoP5Q5f37NTewg4UkTrjr"
    "1hjlBDwsFtLlJ0mc0OjWGC5eXCHGCrAKREcRzcdbBvPU5WKxgAhiDMYYxArX91eMJz0HUPIv"
    "FkRkBUUwYnhuDDgrX6o9jPVh2hxSOblQm29/s10HxNBrZZwenytvmdLBf0U3oQtj3GSeue35"
    "prwmjEM3/Rrnwj08W3wUQqUD/gCVCm4XrOguIgAAAABJRU5ErkJggg==")
getgoData = go.GetData
getgoImage = go.GetImage
getgoBitmap = go.GetBitmap
getgoIcon = go.GetIcon      

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

halt = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAABHNCSVQICAgIfAhkiAAAAI9J"
    "REFUGJVjZGRiZiAWsMAY/ev+/GdgYGB4/uYhQ1eaMiOM/+zNA4buNBVGBgYGBiZknQ4GDAw7"
    "91xA4e/acxHOhyv+wPCRQYCDgeHDjw9Y+agm/2Bg+PADQmPloyuGKPiAnY/uZnSTcJr84ccH"
    "qOQHrHwsJn9k+ICHD1fMzsLAkFAwgQEXn4GBgYGRlBgEABs+S+nb4fxdAAAAAElFTkSuQmCC")
gethaltData = halt.GetData
gethaltImage = halt.GetImage
gethaltBitmap = halt.GetBitmap
gethaltIcon = halt.GetIcon  

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

reset = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAABHNCSVQICAgIfAhkiAAAALdJ"
    "REFUGJWVkbFtwzAURB9lJU4nBymyQAbICJ7Gy6RwRtAEnkGjqFSKII8diwByQVJSUtkf+MUH"
    "ju/uwBCaHbdOC3C+/M4AEiGRFzAJwGM783F6C219dXwH6LCITeU28tkPK1kih6cOBa3iiAnU"
    "xSGTC2lZ4+qgS6zm5/trZmud1twmGaeV3Dy/vIZc5j/dHGlLrq2tOd3cigB/MlOE01hKisXe"
    "BAKhivcP0PdDplhdXHLXCff84BXEpo7e6x79iQAAAABJRU5ErkJggg==")
getresetData = reset.GetData
getresetImage = reset.GetImage
getresetBitmap = reset.GetBitmap
getresetIcon = reset.GetIcon
             
#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

StepOver = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQCAYAAADJViUEAAAABHNCSVQICAgIfAhkiAAAAS5J"
    "REFUKJFjPHXx+f9r974zHLj4iuHBgxcMDBwCDFoKnAzTq6wYGQgAxp4FF/+//vSXwUyLl0FH"
    "gZNBQ02eoCYYYHnw6hdDpLM4g42pIoam///+/ser+e3X71g1MjAwMDAyMeN1Bcv3j/+IciI2"
    "V7AQpROHK4jWjN3mHxTY/IHhAwU2Ewmw2szFwUySbciAiZuRhWHRpvP/GRgYGDxLz/3PbDv+"
    "f//xW/9htuHFOS37/3PzsTC4mUszPHr6jWHhqT8MIv+/MGjL/GewN+JncLY1xJlQGHcduf1/"
    "4/4nDE+/MjJwsgkyfP/0nuHDhwcMHz58YGD48YHh4q5m3JoZmRB+Pnvhzv+kuo0MDD8+MIgJ"
    "8zBkxFgwBHvbE6c5vnDV/3/Mbxiywq0YLE0NCOYuANPBcZz9END6AAAAAElFTkSuQmCC")
getStepOverData = StepOver.GetData
getStepOverImage = StepOver.GetImage
getStepOverBitmap = StepOver.GetBitmap
getStepOverIcon = StepOver.GetIcon

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

StepOut = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABHNCSVQICAgIfAhkiAAAAP9J"
    "REFUKJHlkS9Ig3EQhp/7fRO2gYLFuDKwTFaWBItxgmI0iVmTWCbIgsxoNwsGg8GBMFa0KYLi"
    "gh8W8RMXNCgHKvzEP2dSFPd9Kth84S3He/ccdyIu4E0TtVN7Qpgppxgu5YRvJB+b91uXtrRx"
    "j3oYGVDKpW6Khf7YIbLeOLPmseP61iANeNDoCPUReGjV52Kb3XYoDOW72FzMS3XU0JMdVCP6"
    "slmq04PJe88un5u4AHEBU/NNm1xYs73D8L2WZMYrUWwQsCS7TA+s1kPreBAXSKK3dq+scfDA"
    "RfsGVQWv4OExfUcx18tKbUwA7OX5C+DTq36r1E+D/4XcifZn5FfgImex6hZtdAAAAABJRU5E"
    "rkJggg==")
getStepOutData = StepOut.GetData
getStepOutImage = StepOut.GetImage
getStepOutBitmap = StepOut.GetBitmap
getStepOutIcon = StepOut.GetIcon

#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

StepInto = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAOCAYAAADwikbvAAAABHNCSVQICAgIfAhkiAAAARdJ"
    "REFUKJGtkjFLw1AURs9LImhFrFrc7CBYA61KqIMKDm7WsS7ddBLRSR2ci45u/gb/gA5CN8VB"
    "BEHRGlADQXAqyotIDaXJcy1KWlv85ns4H/deITSdTiOuyhV1fl/Ddt5xXgJAgg+JnioZM05x"
    "a15EwgdHT6r6EWKZ3ZjJLlJjI5HDP2PYjz5r+SFmrN+QCgPVFH7zArzPEIDCvqPqCDZzBgvZ"
    "pBCa3rSFWC2W1WiiTno8Rnygl8OTGtKHpYwkl+1jMp0SUS1E6cJVlw8e9it8iX4ApHuD9F3w"
    "4fZ4J3phjae6vntW23tnSF8yPBhjvTDF8uJctLkRXtk9VaFeYSNvMTs90XLr4q9P0tLcbox2"
    "bf9m1jomgW9WkWXydz8mZQAAAABJRU5ErkJggg==")
getStepIntoData = StepInto.GetData
getStepIntoImage = StepInto.GetImage
getStepIntoBitmap = StepInto.GetBitmap
getStepIntoIcon = StepInto.GetIcon

             
#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

memory = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA4AAAANCAYAAACZ3F9/AAAABHNCSVQICAgIfAhkiAAAATRJ"
    "REFUKJGVkS1IBGEQhp/VtVlFQYtFrIJiNqlg0qCYDsx2m8FyYBAUjAZBFH8OLP4VEeuF03Qc"
    "WATBn7refd83szuGxfMEg/vCMDDw8sy8E20evxsdEgUvRisYTW80O7oL4MQQNWKA/oE+0syQ"
    "1FA1ghq9YngxvBpBMoIYXkE0o1pr5Ma31w8gJzUDJC4jaRmJM5JWRtOD15/FslSIh3qfWZ6b"
    "jCig8emSxaoKwMj8mTUqC9HU2ov5IEgQVD1pcDzujUejS1eWhU+2VodZL2/DXuXeoq5u/lsX"
    "dw82MbtisYoUIra1e3BTiHhyXcuJaZoWIjrJ042/yY3KQgRwWx78M+H60Uw+L1Xtl7HojW3j"
    "eXmMsPFkTlp4BRcMJz0EjQmL9fb31ScARDv7l7Z/eFrk/wB8AbEgBXemHmxSAAAAAElFTkSu"
    "QmCC")
getmemoryData = memory.GetData
getmemoryImage = memory.GetImage
getmemoryBitmap = memory.GetBitmap
getmemoryIcon = memory.GetIcon


#----------------------------------------------------------------------
# This file was generated by M:\tools\Python25\Lib\site-packages\wx-2.8-msw-unicode\wx\tools\img2py.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

register = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA4AAAANCAYAAACZ3F9/AAAABHNCSVQICAgIfAhkiAAAAXdJ"
    "REFUKJGVkj9rVFEQxX/37StTGhTJlxAjsmlF/MMmH8BKCBvS+xXsxMZ02oS1EE26XRMw+KcQ"
    "04TETkhhERCiFjbP3fvu3PeOxct7+1YRcZo7zMw5c2buuAcvvomWWYTcxCSIcS7GrdcH8CYs"
    "ihTg/IV5ilJYIWIUIYo5E7mJPIpgJcFEHsFiycHH4wr49fQ7UHUaB8h8STYRmRfZpGScQx6n"
    "wsrCSBfmTrjTu+r4D1u8cVdJjLEJ7Lw+0vPRvja33gng4eOh7j/antnBy7eHAkgtWhO8fe3S"
    "TOd7a8t/VZJEmwK7vb66vb4AhnsHjV/n2sC0ltrt9bU/euJqf/n6omsD6txPX+GToigaluHe"
    "h4Z1a/ReO2+qeYqibGq8nZVsDHblkg5fTn9oaWVdSyvrckkHl3Ro+5dvrsolHZ6OjnTl1qrS"
    "mmnh4rk/FlHLAzh8tTmTb4Cfjj8rmPBnF+JDibfqisL0x4h5BoDbGOxq8Gz792b/tF/nkt/W"
    "KB78zgAAAABJRU5ErkJggg==")
getregisterData = register.GetData
getregisterImage = register.GetImage
getregisterBitmap = register.GetBitmap
getregisterIcon = register.GetIcon

             