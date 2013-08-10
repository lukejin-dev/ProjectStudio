"""@file
manage SVN config setting:
1) create and maintain SVN config dir and file
2) config setting dialog.
"""
import wx
import os
import core.config as config
import ConfigParser

class ConfigDialog(wx.Dialog):
    """ Config dialog is launched by context menu.
    It contains config panel insider. 
    """
    
    def __init__(self, parent, id, conf):
        wx.Dialog.__init__(self, parent, id, 'SVN Setting', size=(500, 300))
        #self.SetFont(wx.GetApp().GetAppFont())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add config panel 
        self._configpanel = ConfigPanel(self, -1, conf)
        sizer.Add(self._configpanel, 1, wx.EXPAND, 2)
        
        # Add ok, cancel button
        btsizer = wx.BoxSizer(wx.HORIZONTAL)
        btsizer.Add((60, 20), 1, wx.EXPAND)
        self._okbt = wx.Button(self, -1, 'Ok')
        self._okbt.Bind(wx.EVT_BUTTON, self.OnOk)
        btsizer.Add(self._okbt, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
        self._cancelbt = wx.Button(self, -1, 'Cancel')
        self._cancelbt.Bind(wx.EVT_BUTTON, self.OnCancel)
        btsizer.Add(self._cancelbt, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
        
        sizer.Add(btsizer, 0, wx.ALIGN_BOTTOM|wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.CenterOnParent()
        
    def OnOk(self, event):
        if not self._configpanel.OnOk():
            event.Veto()
        else:
            self.EndModal(wx.ID_OK)
        
    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

class ConfigPanel(wx.Panel):
    """ Config panel contains all config setting for SVN,
        and it can easily to intergrated to dialog or notebook page.  
    """
    
    def __init__(self, parent, id, conf):
        wx.Panel.__init__(self, parent, id, size=(500, 250))
        self._config = conf
          
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._tb = wx.Treebook(self, -1, style=wx.BK_TOP)
        self._tb._general = GeneralPage(self._tb, -1, self._config)
        self._tb._network = NetworkPage(self._tb, -1, self._config)
       
        self._tb.AddPage(self._tb._general, 'General')
        self._tb.AddPage(self._tb._network, 'Network')
        
        sizer.Add(self._tb, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # Event Handling
        self._tb.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
    def GetConfig(self):
        return self._config
        
    def OnPageChanging(self, event):
        new = event.GetSelection()
        old = event.GetOldSelection()
        oldpage = self._tb.GetPage(old)
        newpage = self._tb.GetPage(new)
        if hasattr(oldpage, 'VerifyPage'):
            if not oldpage.VerifyPage():
                event.Veto()
                return
        if hasattr(newpage, 'InitPage'):
            newpage.InitPage()
            
    def GetSvnService(self):
        serv = None
        pm = wx.GetApp().GetPluginMgr()
        p  = pm.GetPlugin('SvnPlugin')
        if p != None:
            serv = pm.GetPlugin('SvnPlugin').GetServiceInstance()
        
        return serv
                            
    def OnOk(self):
        dirty = False
        for index in range(self._tb.GetPageCount()):
            page = self._tb.GetPage(index)
            if hasattr(page, 'VerifyPage'):
                if not page.VerifyPage():
                    return False
            if page._dirty: 
                dirty = True
        
        if not dirty: return True
        
        dlg = wx.MessageDialog(None, 'SVN configuration has been modified! SVN service will restart!',
                                     'Information', wx.YES_NO|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            serv = self.GetSvnService()
            serv.ReInitClients()
        dlg.Destroy()
        return True
        
class GeneralPage(wx.Panel):
    def __init__(self, parent, id, conf):
        wx.Panel.__init__(self, parent, id)
        self._config = conf
        self._dirty  = False
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        dirsizer = wx.BoxSizer(wx.HORIZONTAL)
        dirsizer.Add(wx.StaticText(self, -1, 'SVN Config Directory:'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 5)
        path = self._config.Get('SVNConfigDir', '')
        self._dir = wx.TextCtrl(self, -1, path)
        dirsizer.Add(self._dir, 1, wx.ALL|wx.ALIGN_CENTER, 5)
        self._dirbt = wx.Button(self, -1, 'Browser')
        dirsizer.Add(self._dirbt, 0, wx.ALL, 5)
        sizer.Add(dirsizer, 0, wx.TOP|wx.EXPAND, 0)
        self.SetSizer(sizer)
        
        # ========= Event table ===========
        wx.EVT_BUTTON(self, self._dirbt.GetId(), self.OnBrowser)
        
    def OnBrowser(self, event):
        defaultpath = self._config.Get('SVNConfigDir')
        dlg = wx.DirDialog(self, 'Choose SVN config directory:', defaultpath)
        if dlg.ShowModal() == wx.ID_OK:
            self._dir.SetValue(dlg.GetPath())
        dlg.Destroy()
        
    def VerifyPage(self):
        oldpath = self._config.Get('SVNConfigDir')
        newpath = self._dir.GetValue()
        if oldpath != newpath:
            self._dirty = True
            
        if not os.path.exists(newpath):
            wx.MessageBox('SVN config directory %s does not exists' % self._dir.GetValue())
            return False
        self._config.Set('SVNConfigDir', newpath)
        return True
        
class NetworkPage(wx.Panel):

    def __init__(self, parent, id, conf):
        wx.Panel.__init__(self, parent, id)
        self._config = conf
        self._dirty  = False
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._enable = wx.CheckBox(self, -1, 'Enable Proxy Server')
        sizer.Add(self._enable, 0, wx.ALIGN_LEFT|wx.ALL, 5)
       
        addrsizer = wx.BoxSizer(wx.HORIZONTAL)
        addrsizer.Add(wx.StaticText(self, -1, 'Service Address:'), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._addr = wx.TextCtrl(self, -1)
        addrsizer.Add(self._addr, 1, wx.ALL|wx.ALIGN_CENTER, 5)
        addrsizer.Add(wx.StaticText(self, -1, 'Port:'), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._port = wx.TextCtrl(self, -1, size=(30, 20))
        addrsizer.Add(self._port, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        sizer.Add(addrsizer, 0, wx.EXPAND)
        
        usersizer = wx.BoxSizer(wx.HORIZONTAL)
        usersizer.Add(wx.StaticText(self, -1, 'Username:          '), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._user = wx.TextCtrl(self, -1)
        usersizer.Add(self._user, 1, wx.ALL, 5)
        sizer.Add(usersizer, 0, wx.EXPAND)
        
        passsizer = wx.BoxSizer(wx.HORIZONTAL)
        passsizer.Add(wx.StaticText(self, -1, 'Password:          '), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._pass = wx.TextCtrl(self, -1, style=wx.TE_PASSWORD)
        passsizer.Add(self._pass, 1, wx.ALL, 5)
        sizer.Add(passsizer, 0, wx.EXPAND)
        
        timeoutsizer = wx.BoxSizer(wx.HORIZONTAL)
        timeoutsizer.Add(wx.StaticText(self, -1, 'Proxy timeout in second: '), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._timeout = wx.TextCtrl(self, -1, '0')
        timeoutsizer.Add(self._timeout, 1, wx.ALL, 5)
        sizer.Add(timeoutsizer, 0, wx.EXPAND)
                
        exceptsizer = wx.BoxSizer(wx.HORIZONTAL)
        exceptsizer.Add(wx.StaticText(self, -1, 'Exceptions:         '), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        self._exceptions = wx.TextCtrl(self, -1)
        exceptsizer.Add(self._exceptions, 1, wx.ALL, 5)
        sizer.Add(exceptsizer, 0, wx.EXPAND)
        
        filesizer = wx.BoxSizer(wx.HORIZONTAL)
        filesizer.Add(wx.StaticText(self, -1, 'Subversion server file : '), 0, wx.ALL|wx.ALIGN_CENTER, 5)
        path = self._config.Get('SVNConfigDir', '')
        path = os.path.join(path, 'servers')
        self._server = wx.StaticText(self, -1, path)
        filesizer.Add(self._server, 1, wx.ALL, 5)
        sizer.Add(filesizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
                
        # ======= Event table ===========
        wx.EVT_UPDATE_UI(self, self._addr.GetId(), self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, self._user.GetId(), self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, self._pass.GetId(), self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, self._port.GetId(), self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, self._timeout.GetId(), self.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, self._exceptions.GetId(), self.ProcessUpdateUIEvent)
        
    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id in [self._addr.GetId(), self._user.GetId(), self._pass.GetId(), self._port.GetId(),\
                  self._timeout.GetId(), self._exceptions.GetId()]:
            event.Enable(self._enable.GetValue())
            return True
        
        return False
              
    def GetServerConfigOption(self, path, config, flag=True):
        if not os.path.exists(path):
            try:
                f = open(path, 'w')
                f.close()
            except:
                wx.MessageBox('Fail to write svn server config file!')
                return None
                
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        if not parser.has_section('global'):
            parser.add_section('global')
            
        if parser.has_option('global', config):
            return parser.get('global', config)
        
        value = None
        if flag:
            appconf = wx.ConfigBase_Get()
            value = appconf.Read(config, '')
        return value
        
    def SetServerConfigOption(self, path, config, value):
        old = self.GetServerConfigOption(path, config, False)
        if old == value: return 
        
        self._dirty = True
            
        if not os.path.exists(path):
            try:
                f = open(path, 'w')
                f.close()
            except:
                wx.MessageBox('Fail to write svn server config file!')
                return None
                
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        if not parser.has_section('global'):
            parser.add_section('global')
            
        parser.set('global', config, value)
        parser.write(open(path, 'w'))
        
        appconf = wx.ConfigBase_Get()
        appconf.Write(config, value)
                    
    def InitPage(self):
        configpath = self._config.Get('SVNConfigDir')
        enable     = self._config.GetBoolean('SVNProxyEnable', False) 
        server = os.path.join(configpath, 'servers')
        
        self._server.SetLabel(server)
        self._enable.SetValue(enable)
        
        value = self.GetServerConfigOption(server, 'http-proxy-host') 
        if value != None:
            self._addr.SetValue(value)
        value = self.GetServerConfigOption(server, 'http-proxy-port') 
        if value != None:
            self._port.SetValue(value)
        value = self.GetServerConfigOption(server, 'http-proxy-username') 
        if value != None:
            self._user.SetValue(value)
        value = self.GetServerConfigOption(server, 'http-proxy-password') 
        if value != None:
            self._pass.SetValue(value)     
        value = self.GetServerConfigOption(server, 'http-timeout') 
        if value != None:
            self._timeout.SetValue(value)     
        value = self.GetServerConfigOption(server, 'http-proxy-exceptions') 
        if value != None:
            self._exceptions.SetValue(value)     
                
    def GetOption(self, parser, option):
        if not parser.has_option('global', option):
            return None
        return parser.get('global', option)
        
    def SetOption(self, parser, option, value):
        if len(value) == 0: return
        
        if not parser.has_section('global'):
            parser.add_section('global')
        parser.set('global', option, value)
        
    def VerifyPage(self):
        path = self._server.GetLabel()
        old = self._config.GetBoolean('SVNProxyEnable')
        new = self._enable.GetValue()
        if new != old:
            self._config.Set('SVNProxyEnable', new)
            self._dirty = True
        
        if not self._enable.GetValue():
            try:
                f = open(path, 'w')
                f.close()
            except:
                pass 
            return True
        self.SetServerConfigOption(path, 'http-proxy-host', self._addr.GetValue())
        self.SetServerConfigOption(path, 'http-proxy-port', self._port.GetValue())
        if len(self._user.GetValue()) != 0:
            self.SetServerConfigOption(path, 'http-proxy-username', self._user.GetValue())
        if len(self._user.GetValue()) != 0:
            self.SetServerConfigOption(path, 'http-proxy-password', self._pass.GetValue())
        self.SetServerConfigOption(path, 'http-timeout', self._timeout.GetValue())
        self.SetServerConfigOption(path, 'http-proxy-exceptions', self._exceptions.GetValue())
        
        return True
        