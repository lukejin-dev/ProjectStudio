import core.plugin
import core.service
import wx
import core.debug
import sys
import svnimage
import ui.MessageWindow
import SvnConfig
import threading
import os
from util.utility import *

try:
    import pysvn
except:
    core.debug.GetPluginLogger().error('Fail to import pysvn, svn service can not be installed')
    
_plugin_module_info_ = [{"name":"SvnPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "class":"SvnPlugin"}]
from SvnThread import *

wc_notify_action_map = {
pysvn.wc_notify_action.add: 'A',
pysvn.wc_notify_action.commit_added: 'A',
pysvn.wc_notify_action.commit_deleted: 'D',
pysvn.wc_notify_action.commit_modified: 'M',
pysvn.wc_notify_action.commit_postfix_txdelta: None,
pysvn.wc_notify_action.commit_replaced: 'R',
pysvn.wc_notify_action.copy: 'c',
pysvn.wc_notify_action.delete: 'D',
pysvn.wc_notify_action.failed_revert: 'F',
pysvn.wc_notify_action.resolved: 'R',
pysvn.wc_notify_action.restore: 'R',
pysvn.wc_notify_action.revert: 'R',
pysvn.wc_notify_action.skip: 'skip',
pysvn.wc_notify_action.status_completed: None,
pysvn.wc_notify_action.status_external: 'X',
pysvn.wc_notify_action.update_add: 'A',
pysvn.wc_notify_action.update_completed: None,
pysvn.wc_notify_action.update_delete: 'D',
pysvn.wc_notify_action.update_external: 'X',
pysvn.wc_notify_action.update_update: 'U',
pysvn.wc_notify_action.annotate_revision: 'A',
}
if hasattr( pysvn.wc_notify_action, 'locked' ):
    wc_notify_action_map[ pysvn.wc_notify_action.locked ] = 'locked'
    wc_notify_action_map[ pysvn.wc_notify_action.unlocked ] = 'unlocked'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_lock ] = 'failed_lock'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_unlock ] = 'failed_unlock'
    
class SvnPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return SvnService
        
class SvnService(core.service.PISService):
    ID_CHECKOUT    = wx.NewId()
    ID_COMMIT      = wx.NewId()
    ID_UPDATE      = wx.NewId()
    ID_CLEANUP     = wx.NewId()
    ID_CONFIG      = wx.NewId()
    ID_REVERT      = wx.NewId()
    ID_ADD         = wx.NewId()
    ID_REMOVE      = wx.NewId()
          
    def __init__(self):
        core.service.PISService.__init__(self)
        self.client = None
        self.pysvn_testing = False        
        self.notify_message_list = []        

        self._isInit = False
        self._current_remote_server = None
        self._is_cancel = False
        
        self._client             = None
        self._client_thread      = None
        self._info_client        = None
        self._info_client_thread = None
        self._bitmap_dict    = {self.ID_CHECKOUT:svnimage.getCheckoutBitmap(),
                                self.ID_COMMIT:svnimage.getCommitBitmap(),
                                self.ID_UPDATE:svnimage.getUpdateBitmap(),
                                self.ID_CLEANUP:svnimage.getCleanupBitmap(),
                                self.ID_CONFIG:svnimage.getSettingBitmap(),
                                self.ID_REVERT:svnimage.getRevertBitmap(),
                                self.ID_ADD:svnimage.getAddBitmap(),
                                self.ID_REMOVE:svnimage.getRemoveBitmap()}        
    def IsBusy(self):
        return self._client_thread.IsBusy()
        
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Subversion'
    
    def GetViewClass(self):
        return SvnServiceView
    
    def GetIcon(self):
        return svnimage.getSvnTabIcon()
        
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        # initialize the default svn config dir firstly
        path = os.path.join(wx.GetApp().GetAppLocation(), self.GetPlugin().GetDir())
        self.GetConfig().Get('SVNConfigDir', path)
        
        menubar = frame.GetMenuBar()
        toolmenu = menubar.GetMenu(menubar.FindMenu('Tools'))
        item = wx.MenuItem(toolmenu, self.ID_CONFIG, 'SVN Setting', 'Configure SVN')
        wx.EVT_MENU(frame, self.ID_CONFIG, self.Config)
        toolmenu.InsertItem(0, item)
        
        self.ReInitClients()
        
    def GetSvnNoChangeImage(self):
        return svnimage.getSvnNoChangeImage().Scale(16, 16)
        
    def GetSvnModifiedImage(self):
        return svnimage.getSvnModifiedImage().Scale(16, 16)
        
    def CombineImage(self, img1, img2):
        data1 = img1.GetData()
        data2 = img2.GetData()
        
        index = 0
        newstr   = []
        while (index + 3 <= len(data2)):
            if (ord(data2[index]) == 1 and \
                ord(data2[index + 1]) == 0 and \
                ord(data2[index + 2]) == 0):
                newstr.append(data1[index:index+3])
                index += 3
            else:
                newstr.append(data2[index:index+3])
                index += 3
        img1.SetData(''.join(newstr))
        return img1
            
    def GetSvnMenu(self):
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.ID_UPDATE, 'Update')
        item.SetBitmap(svnimage.getUpdateBitmap())
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.ID_COMMIT, 'Commit')
        item.SetBitmap(svnimage.getCommitBitmap())
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.ID_CHECKOUT,'Checkout')
        item.SetBitmap(svnimage.getCheckoutBitmap())
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.ID_CLEANUP, 'Cleanup')
        item.SetBitmap(svnimage.getCleanupBitmap())
        #item.SetBitmap(svnimage.getSvnNoChangeBitmap())
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.ID_REVERT, 'Revert')
        item.SetBitmap(svnimage.getRevertBitmap())
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.ID_ADD, 'Add')
        item.SetBitmap(svnimage.getAddBitmap())
        menu.AppendItem(item)
        item = wx.MenuItem(menu, self.ID_REMOVE, 'Remove')
        item.SetBitmap(svnimage.getRemoveBitmap())
        menu.AppendItem(item)
        
        menu.AppendSeparator()
        item = wx.MenuItem(menu, self.ID_CONFIG, 'Setting')
        item.SetBitmap(svnimage.getSettingBitmap())
        menu.AppendItem(item)
        return menu

    def ReInitClients(self):
        if self._client_thread != None:
            self._is_cancel = True
            self._client_thread.Shutdown()
        if self._info_client_thread != None:
            self._is_cancel = True
            self._info_client_thread.Shutdown()
            
        self._client, self._client_thread  = self.InitClientObject()
        self._info_client, self._info_client_thread = self.InitClientObject()
        
    def InitClientObject(self):
        path = os.path.join(wx.GetApp().GetAppLocation(), self.GetPlugin().GetDir())
        client = pysvn.Client(self.GetConfig().Get('SVNConfigDir', path))
        client.exception_style = 1
        client.callback_notify      = RunFunctionOnMainApp(wx.GetApp(), self.ClientCallBackNotify)
        client.callback_get_login   = RunFunctionOnMainApp(wx.GetApp(), self.ClientCallbackGetLogin)
        client.callback_ssl_server_trust_prompt = \
                                      RunFunctionOnMainApp(wx.GetApp(), self.ClientCallbackSSLServerTrustPrompt)
        client.callback_get_log_message = self.ClientCallbackGetLogMessage
        client.callback_cancel      = self.ClientCallBackCancel 
         
        thread = SVNThread(self)
        thread.start()       
        return client, thread
       
    def ClientCallBackCancel(self):
        return self._is_cancel 
         
    def ClientCallBackNotify(self, arg_dict):
        #print 'SVN Notify: %r' % arg_dict
        if arg_dict['path'] == '':
            return
            
        action = arg_dict['action']
        #print action
        if( action == pysvn.wc_notify_action.commit_postfix_txdelta
         or action == pysvn.wc_notify_action.annotate_revision ):
            #print 'process ...'
            return    
                            
        if hasattr(pysvn.wc_notify_action, 'failed_lock'):
            if action in [pysvn.wc_notify_action.failed_lock,
                          pysvn.wc_notify_action.failed_unlock]:
                wx.GetApp().ForegroundProcess(self._LogError, (arg_dict['error'], 'Lock Error'))
                return         
        
        if (action == pysvn.wc_notify_action.update_completed):
            return

        if wc_notify_action_map[arg_dict['action']] is None:
            return
                    
        # reject updates for paths that have no change
        if (action == pysvn.wc_notify_action.update_update
        and arg_dict['content_state'] == pysvn.wc_notify_state.unknown
        and arg_dict['prop_state'] == pysvn.wc_notify_state.unknown ):
            return
            
        # print anything that gets through the filter
        msg = '%s %s' % (wc_notify_action_map[ action ], arg_dict['path'])
        self._LogInfo(msg)
                                                   
    def ClientCallbackGetLogin( self, realm, username, may_save ):
        dlg = LoginDialog(wx.GetApp().GetTopWindow(), username, self._current_remote_server)
        ret = dlg.ShowModal()
        name, password = dlg.GetLogin()
        #print name, password
        return 1, str(name), str(password), True
                
    def ClientCallbackSSLServerTrustPrompt( self, trust_data ):
        texts = []
        for key,value in trust_data.items():
            texts.append('%s: %s' % (key, value))
        dlg = TrustPromptDialog(wx.GetApp().GetTopWindow(), texts, self._current_remote_server)
        ret = dlg.ShowModal()
        if ret == dlg.PERM_ID:
            return True, trust_data['failures'], True
        elif ret == dlg.TEMP_ID:
            return True, trust_data['failures'], False
        
        return False, 0, False
               
    def ClientCallbackGetLogMessage(self):
        print 'get log message'
                 
    def Config(self, event):
        """Show config dialog"""
        frame = wx.GetApp().GetTopWindow()
        dlg = SvnConfig.ConfigDialog(frame, -1, self.GetConfig())
        dlg.ShowModal()
        dlg.Destroy()
        
    def SvnCheckout(self, dir, callback=None, callback_param=None):
        self._is_cancel = False
                    
        dlg = URLInputDialog(wx.GetApp().GetTopWindow())
        if dlg.ShowModal() == dlg.CANCEL_ID:
            return
        self.GetView().Activate()
        self._current_remote_server = dlg.GetURL()
        self._client_thread.AddWork(self._CheckOutWork, (dlg.GetURL(), dir, callback, callback_param))
    
    def SvnCheckoutURL(self, url, dir, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._CheckOutWork, (url, dir, callback, callback_param))
                
    def SvnUpdate(self, dir, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._UpdateWork, (dir, callback, callback_param))
                 
    def SvnCleanUp(self, dir, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._CleanupWork, (dir, callback, callback_param))
    
    def SvnRevert(self, dir, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._RevertWork, (dir, callback, callback_param))
        
    def SvnAdd(self, path, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._AddWork, (path, callback, callback_param))
        
    def SvnRemove(self, path, callback=None, callback_param=None):
        self.GetView().Activate()
        self._is_cancel = False
        self._client_thread.AddWork(self._RemoveWork, (path, callback, callback_param))
        
    def _LogAction(self, message):
        self.GetView().Clear()
        self.SetTitle(message)
        self.GetView().AddMessage(message)        
        self.GetView().AddMessage('Starting ...')
                
    def _CheckOutWork(self, remote, dir, callback, callback_param):
        str = 'SVN Check out from %s to folder %s' % (remote, dir)
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))

        try:
            self._client.checkout(remote, dir, recurse=True)
        except pysvn.ClientError, e:
            wx.GetApp().ForegroundProcess(self._LogError, (e, 'Error'))
        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))
        
    def _WorkCallback(self, callback, callback_param):
        self.GetView().AddMessage('Finished!')
        if callback != None:
            callback(*callback_param)
        
        self._is_cancel = False
        
    def _UpdateWork(self, dir, callback, callback_param):
        str = 'SVN Update %s' % dir
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))
         
        try:
            self._client.update(dir)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))
        
    def _CleanupWork(self, dir, callback, callback_param):
        str = 'SVN Cleanup %s' % dir
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))
        
        try:
            self._client.cleanup(dir)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
                        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))
    
    def _RevertWork(self, path, callback, callback_param):
        str = "SVN Revert %s" % path
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))
        try:
            self._client.revert(path)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
                        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))
            
    def _AddWork(self, path, callback, callback_param):
        str = "SVN Add %s" % path
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))
        try:
            self._client.add(path)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
                        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))

    def _RemoveWork(self, path, callback, callback_param):
        str = "SVN Remove %s" % path
        wx.GetApp().ForegroundProcess(self._LogAction, (str, ))
        try:
            self._client.remove(path)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
                        
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))

    def _LogInfo(self, msg):
        view = self.GetView()
        if view != None:
            view.AddMessage(msg)
        
    def _LogError(self, e, title='Error'):
        view = self.GetView()
        if view == None: return
                
        self._last_error = []
        for message, _ in e.args[1]:
            self._last_error.append(message)
        
        self.GetView().AddMessage('\n'.join( self._last_error ))    
        if e.args[1][0][1] == 155004:
            self.GetView().AddMessage('Please execute Cleanup command!')

        wx.MessageBox('\n'.join( self._last_error ), title, style=wx.OK|wx.ICON_ERROR );
        
    def GetSvnInfo(self, path, callback, param):
        self._info_client_thread.AddWork(self._GetSvnInfoWork, (path, callback, param))
        
    def _GetSvnInfoWork(self, path, callback, param):
        try:
            info = self._info_client.info(path)
        except pysvn.ClientError, message:
            return

        if info != None and callback != None:
            callback(info, param)
        
    def GetSvnStatus(self, path, recurse=False, get_all=False, callback=None, param=None):
        self._info_client_thread.AddWork(self._GetSvnStatus, (path, recurse, get_all, callback, param))
        
    def _GetSvnStatus(self, path, recurse, get_all, callback, param):
        try:
            status = self._info_client.status(path, recurse=recurse, get_all=get_all)
        except pysvn.ClientError, message:
            return

        if status != None and callback != None:
            if param == None:
                try:
                    callback(status)
                except:
                    pass
            else:
                try:
                    callback(status, *param)
                except:
                    pass
                    
    status_dict = {pysvn.wc_status_kind.unversioned:'unversioned',
                   pysvn.wc_status_kind.none:'none',
                   pysvn.wc_status_kind.normal:'normal',
                   pysvn.wc_status_kind.added:'added',
                   pysvn.wc_status_kind.missing:'missing',
                   pysvn.wc_status_kind.deleted:'deleted',
                   pysvn.wc_status_kind.replaced:'replaced',
                   pysvn.wc_status_kind.modified:'modified',
                   pysvn.wc_status_kind.merged:'merged',
                   pysvn.wc_status_kind.conflicted:'conflicted',
                   pysvn.wc_status_kind.ignored:'ignored',
                   pysvn.wc_status_kind.obstructed:'obstructed',
                   pysvn.wc_status_kind.external:'external',
                   pysvn.wc_status_kind.incomplete:'incomplete',
                  }
    def TranslateTextStatus(self, text_status):
        if self.status_dict.has_key(text_status):
            return self.status_dict[text_status]
        return None
                                                                         
    def SvnCommit(self, path, callback=None, callback_param=None):
        self._is_cancel = False
        self.GetView().Clear()
        str = 'SVN Commit folder %s' % path
        dlg = SvnCommitDialog(wx.GetApp().GetTopWindow(), self, path)
        if dlg.ShowModal() == wx.ID_YES:
            self.GetView().AddMessage(str)
            self.SetTitle(str)
            self._client_thread.AddWork(self._CommitWork, (path, dlg.GetLogMessage(), callback, callback_param))
        dlg.Destroy()
    
    def _CommitWork(self, dir, log, callback, callback_param):
        self.GetView().AddMessage('Starting...')
        try:
            self._client.checkin(dir, log)
        except pysvn.ClientError, message:
            wx.GetApp().ForegroundProcess(self._LogError, (message, 'Error'))
            
        wx.GetApp().ForegroundProcess(self._WorkCallback, (callback, callback_param))
        
    def TerminateWoringThread(self):
        self._is_cancel = True
        self._client_thread.Shutdown()
        
    def RestartWorkingThread(self):
        self.TerminateWoringThread()
        self._client_thread.start()
        self._is_cancel = False

    def DeActivate(self):
        self._is_cancel = True
        self._client_thread.Shutdown()
        self._info_client_thread.Shutdown()
        
        core.service.PISService.DeActivate(self)
        
    def OnCloseFrame(self, event):
        self.DeActivate()
        #self._is_cancel = True
        #self._client_thread.Shutdown()
        #self._info_client_thread.Shutdown()
        
        return core.service.PISService.OnCloseFrame(self, event)
     
    def GetBitmapById(self, id):
        if id in self._bitmap_dict.keys():
            return self._bitmap_dict[id]
        return None
        
class SvnServiceView(core.service.PISServiceView):
    ID_TERMINATE = wx.NewId()
    
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._message = ui.MessageWindow.MessageWindow(self, -1)
        self._message.SetCaretLineVisible(False)
        #self.SetCaretLineBack('#000000') 
        self._message.SetCaretForeground('#FFFFFF')        
        sizer.Add(self._message, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self._message.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        
    def GetFontName(self):
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        
        return font
            
    def Clear(self):
        self._message.SetReadOnly(False)
        self._message.ClearAll()
        self._message.SetReadOnly(True)
        
    def AddMessage(self, text):
        #self._message.DocumentEnd()
        self._message.AddMessage(text)
        self._message.AddMessage(os.linesep)
        
    def OnRightUp(self, event):
        if self.GetService()._client_thread.IsBusy():
            self.PopupMenu(self.CreatePopupMenu(), event.GetPosition())
        
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.ID_TERMINATE, 'Terminate', 'Terminate current SVN operation')
        wx.EVT_MENU(self, self.ID_TERMINATE, self.OnTerminate)
        return menu
        
    def OnTerminate(self, event):
        serv = self.GetService()
        serv.ReInitClients()
    
class SvnProcessThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
class URLInputDialog(wx.Dialog):
    OK_ID         = wx.NewId()
    CANCEL_ID     = wx.NewId()
    
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'Input URL for checking out')
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._combo = wx.ComboBox(self, -1, size=(300, 20))
        sizer.Add(self._combo, 1, wx.EXPAND, 2)
        btSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._okbt = wx.Button(self, self.OK_ID, 'OK')
        self._cancelbt = wx.Button(self, self.CANCEL_ID, 'Cancel')
        btSizer.Add(self._okbt, 0, wx.RIGHT|wx.ALL, 10)
        btSizer.Add(self._cancelbt, 0, wx.RIGHT|wx.ALL, 10)
        sizer.Add(btSizer, 0, wx.EXPAND, 2)

        # layout
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Fit()        
        self.CenterOnParent()

        # load history from register
        histroy = wx.ConfigBase_Get().Read('SvnUrlHistory', '')

        if histroy != '':
            self._history = histroy.split(';')
            for item in self._history:
                self._combo.Insert(item, 0)
        else:
            self._history = []
        
        # Event mapping.
        wx.EVT_BUTTON(self._okbt, self.OK_ID, self.OnOk)
        wx.EVT_BUTTON(self._cancelbt, self.CANCEL_ID, self.OnCancel)
        wx.EVT_CLOSE(self, self.OnCancel)

    def OnOk(self, event):
        if len(self._history) > 10:
            self._history.pop(0)
        if self._combo.GetValue() not in self._history:
            self._history.append(self._combo.GetValue())
        wx.ConfigBase_Get().Write('SvnUrlHistory', ';'.join(self._history))
        self.EndModal(self.OK_ID)
    
    def OnCancel(self, event):
        self.EndModal(self.CANCEL_ID)
        
    def GetURL(self):
        return self._combo.GetValue()

class SvnCommitDialog(wx.Dialog):
    def __init__(self, parent, service, path):
        wx.Dialog.__init__(self, parent, -1, 'Commit Dialog', size = (400, 500))
        
        self._service = service
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._textctl = wx.TextCtrl(self, -1, size = (370, 100), style=wx.TE_MULTILINE)
        sizer.Add(self._textctl, 0, wx.LEFT|wx.TOP|wx.RIGHT, 10)
        
        historysizer = wx.BoxSizer(wx.HORIZONTAL)
        historysizer.Add(wx.StaticText(self, -1, "Recently Message: "), 0, wx.CENTER|wx.LEFT, 10)
        self._historyctrl = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        self._historyctrl.Bind(wx.EVT_COMBOBOX, self.OnHistroy)
        historysizer.Add(self._historyctrl, 1,wx.EXPAND|wx.RIGHT, 10)
        sizer.Add(historysizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        self._fileList = FileListCtrl(self, service)
        sizer.Add(self._fileList, 1, wx.CENTER|wx.EXPAND, 10)
        
        btsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._ok = wx.Button(self, -1, 'OK')
        self._cancel = wx.Button(self, -1, 'Cancel')
        btsizer.Add((100, 20), 1, wx.EXPAND)
        btsizer.Add(self._ok, 0, wx.EXPAND, 5)
        btsizer.Add(self._cancel, 0, wx.LEFT|wx.RIGHT, 10)
        
        sizer.Add(btsizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
        self.SetSizer(sizer)          
        self.CenterOnParent()
        self.SetAutoLayout(True)
        
        self._ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self._cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self._service.GetSvnStatus(path, True, True, self.StatusCallback)
        
        config = wx.ConfigBase_Get()
        for count in range(20):
            key   = "SvnLogMessage%d" % count
            value = config.Read(key, '')
            if len(value) != 0:
                self._historyctrl.Append(value)
        
    def StatusCallback(self, status):
        if self.IsBeingDeleted(): return
        
        for s in status:
            self._fileList.AddPathStatus(s)
        
    def OnOk(self, event):
        str = self._textctl.GetValue()
        if str != None and len(str) != 0:
            config   = wx.ConfigBase_Get()
            hasBlank = False
            cache    = []
            for count in range(20):
                key = "SvnLogMessage%d" % count
                value = config.Read(key, '')
                if len(value) == 0:
                    hasBlank = True
                    config.Write(key, str)
                    break;
                cache.append(value)
            if not hasBlank:
                del cache[0]
                cache.append(str)
                for count in range(len(cache)):
                    key = "SvnLogMessage%d" % count
                    config.Write(key, cache[count])
        self.EndModal(wx.ID_YES)
        
    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def GetLogMessage(self):
        str = self._textctl.GetValue()
        if len(str) == 0:
            return ' '
        return str
        
    def OnHistroy(self, event):
        self._textctl.SetValue(self._historyctrl.GetValue())
        
from wx.lib.mixins.listctrl import CheckListCtrlMixin                
class FileListCtrl(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent, service):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        CheckListCtrlMixin.__init__(self)
        self._service = service
        self.InsertColumn(0, 'File')
        self.InsertColumn(1, 'Status')
        self.InsertColumn(2, 'Extension')
                         
        self.SetColumnWidth(0, 250)
        
    def OnCheckItem(self, index, flag):
        if not flag:
            wx.MessageBox('Does not support de-select modified item yet!')
            self.CheckItem(index)
                
    def AddPathStatus(self, status):
        path = status.data['path']
        statusstr = self._service.TranslateTextStatus(status.data['text_status'])
        if statusstr in ['modified', 'added', 'missing']:
            index = self.InsertStringItem(0, path)
            self.CheckItem(index)
        else:
            index = self.InsertStringItem(sys.maxint, path)

        name, ext = os.path.splitext(path)
        self.SetStringItem(index, 1, statusstr)
        self.SetStringItem(index, 2, ext)
        
class TrustPromptDialog(wx.Dialog):
    PERM_ID = wx.NewId()
    TEMP_ID = wx.NewId()
    REJ_ID  = wx.NewId()
    
    def __init__(self, parent, textList, server):
        wx.Dialog.__init__(self, parent, -1, 'SSL Server Trust Prompt')
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, 'Server : %s' % server), 0, wx.CENTER|wx.ALIGN_LEFT, 5)
        for item in textList:
            name = item[0: item.find(':')]
            value = item[item.find(':') + 1:]
            itemsizer = wx.BoxSizer(wx.HORIZONTAL)
            itemsizer.Add(wx.StaticText(self, -1, '%-15s : ' % name), 0, wx.LEFT|wx.ALIGN_CENTER, 5)
            tc = wx.TextCtrl(self, -1, value, style=wx.TE_READONLY)
            itemsizer.Add(tc, 1, wx.EXPAND|wx.ALIGN_RIGHT|wx.LEFT, 5) 
            sizer.Add(itemsizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        btSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._permbt = wx.Button(self, self.PERM_ID, 'Permanent accept')
        btSizer.Add(self._permbt, 0, wx.ALIGN_LEFT, 5)
        wx.EVT_BUTTON(self._permbt, self.PERM_ID, self.OnPermClick)
        self._tempbt = wx.Button(self, self.TEMP_ID, 'Temporary accept')
        btSizer.Add(self._tempbt, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 5)
        wx.EVT_BUTTON(self._tempbt, self.TEMP_ID, self.OnTempClick)
        self._rejbt = wx.Button(self, self.REJ_ID, 'Reject')
        btSizer.Add(self._rejbt, 0, wx.ALIGN_RIGHT|wx.EXPAND, 5)
        wx.EVT_BUTTON(self._rejbt, self.REJ_ID, self.OnRejClick)
        wx.EVT_CLOSE(self, self.OnRejClick)
        
        sizer.Add(btSizer, 0, wx.CENTER|wx.EXPAND, 5)
        self.SetSizer(sizer)          
        self.CenterOnParent()
        self.Fit() 
        self.Layout()
        
    def OnPermClick(self, event):
        self.EndModal(self.PERM_ID)
        
    def OnTempClick(self, event):
        self.EndModal(self.TEMP_ID)
        
    def OnRejClick(self, event):
        self.EndModal(self.REJ_ID)

class LoginDialog(wx.Dialog):
    OK_ID = wx.NewId()
    CANCEL_ID = wx.NewId()
    
    def __init__(self, parent, name, server):
        wx.Dialog.__init__(self, parent, -1, 'SSL SVN Login', size=(300, 150))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, 'Server: %s' % server), 0, wx.CENTER|wx.ALIGN_LEFT, 5)
        sizer.Add((300, 7), 1, wx.EXPAND)
        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        nameSizer.Add(wx.StaticText(self, -1, 'Login Name :'), 0, wx.ALIGN_CENTRE|wx.LEFT, 5)
        self._name = wx.TextCtrl(self, -1, name)
        nameSizer.Add(self._name, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(nameSizer, 0, wx.CENTER|wx.EXPAND)
        sizer.Add((300, 7), 1, wx.EXPAND)
        passSizer = wx.BoxSizer(wx.HORIZONTAL)
        passSizer.Add(wx.StaticText(self, -1, 'Password    :'), 0, wx.ALIGN_CENTRE|wx.LEFT, 5)
        self._pass = wx.TextCtrl(self, -1, style=wx.TE_PASSWORD)
        passSizer.Add(self._pass, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(passSizer, 0, wx.CENTER|wx.EXPAND)
        sizer.Add((300, 7), 1, wx.EXPAND)
        btSizer = wx.BoxSizer(wx.HORIZONTAL)
        btSizer.Add((50, 20), 1, wx.EXPAND)
        self._okbt = wx.Button(self, self.OK_ID, 'OK')
        btSizer.Add(self._okbt, 0, wx.BOTTOM, 5)
        self._cancelbt = wx.Button(self, self.CANCEL_ID, 'Cancel')
        btSizer.Add(self._cancelbt, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(btSizer, 0, wx.EXPAND, 5)

        wx.EVT_BUTTON(self._okbt, self.OK_ID, self.OnOk)
        wx.EVT_BUTTON(self._cancelbt, self.CANCEL_ID, self.OnCancel)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Layout()
        self.CenterOnParent()
        
    def OnOk(self, event):
        self.EndModal(self.OK_ID)
        
    def OnCancel(self, event):
        self.EndModal(self.CANCEL_ID)
        
    def GetLogin(self):
        return self._name.GetValue(), self._pass.GetValue()
    
