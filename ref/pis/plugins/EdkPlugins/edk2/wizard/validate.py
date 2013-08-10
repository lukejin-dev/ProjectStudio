import plugins.EdkPlugins.util.wizard
import wx
import os, sys

SPACE = 10

class EDK2ValidateMain(plugins.EdkPlugins.util.wizard.EDKWizard):
    def __init__(self, parent, projext, id=-1, title="EDKII Project Validation", pos=(-1,-1)):
        plugins.EdkPlugins.util.wizard.EDKWizard.__init__(self, parent, id, title, pos)
        self.SetPageSize((450, 200))
        self._projext  = projext
        self._typePage = TypeSelectionPage(self, projext)
        
        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def RunWizard(self):
        return wx.wizard.Wizard.RunWizard(self, self._typePage)
    
    def OnPageChanging(self, event):
        page = event.GetPage()

    def GetTemporaryPath(self):
        return self._overspecPage.GetTemporaryPath()
    
class TypeSelectionPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent, projext):
        wx.wizard.WizardPageSimple.__init__(self, parent)            
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._typeradio = wx.RadioBox(self, -1, "Select Validation Type", choices=["Search over specific usage for library class/PPI/PROTOCOL/GUID"])
        sizer.Add(self._typeradio, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, SPACE)
        self.SetSizer(sizer)
        self.Layout()     
        
        parent._overspecPage = OverSpecifcConfigPage(parent, projext)
        self.SetNext(parent._overspecPage)
        self.GetNext().SetPrev(self)

    def GetSelection(self):
        return self._typeradio.GetStringSelection()
                
class OverSpecifcConfigPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent, projext):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.GridBagSizer(SPACE, SPACE)
        wsPath    = projext.GetWorkspace()
        defaultTemp = os.path.join(wsPath, 'ValidationTemp')
        self._tempPathCtl = wx.TextCtrl(self, -1, defaultTemp, size=(250, -1))
        self._tempPathBt  = wx.Button(self, -1, '...', style=wx.BU_EXACTFIT)
        gridSizer.Add(wx.StaticText(self, -1, 'Searching over specific usage for library class/PPI/PROTOCOL/GUID:'), pos=(0,0), span=(1,3))
        
        gridSizer.Add(wx.StaticText(self, -1, 'Temporary File Path:'), pos=(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self._tempPathCtl, pos=(1,1), span=(1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self._tempPathBt, pos=(1,3), span=(1,1), flag = wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(gridSizer, 0, wx.EXPAND|wx.ALL, SPACE)
        self.SetSizer(sizer)
        self.Layout()
        
    def GetTemporaryPath(self):
        return self._tempPathCtl.GetValue()