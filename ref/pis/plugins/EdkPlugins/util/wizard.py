import wx
import wx.wizard as wizard
import plugins.EdkPlugins.resource as resource
    
class EDKWizard(wizard.Wizard):
    def __init__(self, parent, id, title, pos=(-1,-1)):
        wx.wizard.Wizard.__init__(self, parent, id, 
                                  title, 
                                  resource.getTianoCoreLogoBitmap(), 
                                  pos=pos)
        self.CenterOnParent()