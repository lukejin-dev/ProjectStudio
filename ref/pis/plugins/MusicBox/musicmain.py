import core.plugin
import wx, re, array
import wx.lib.pydocview as pydocview
import core.service
import ui.MessageWindow
import os
import locale
import wx.media
import time

"""
 _plugin_info_ must be defined in plugin code, it is provide base information
 for plugin.
"""
"""
_plugin_module_info_ = [{"name":"MusicBoxPlugin",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Manage and play your music",
                         "class":"MusicBoxPlugin"}]
"""
class MusicBoxPlugin(core.plugin.IServicePlugin):
    def IGetClass(self):
        return MusicBoxService
        
class MusicBoxService(core.service.PISService):
    def GetPosition(self):
        return 'bottom'
    
    def GetName(self):
        return 'Music'
    
    def GetViewClass(self):
        return MusicBoxView
    
    def InstallControls(self, frame, menuBar=None, toolBar=None, statusBar=None, document=None):
        pass
    
    def GetIcon(self):
        return getMusicBoxIcon()
    
class MusicBoxView(core.service.PISServiceView):
    def __init__(self, parent, service):
        core.service.PISServiceView.__init__(self, parent, service)

        # Create some controls
        try:
            self.mc = wx.media.MediaCtrl(self, style=wx.SIMPLE_BORDER,
                                         #szBackend=wx.media.MEDIABACKEND_DIRECTSHOW
                                         #szBackend=wx.media.MEDIABACKEND_QUICKTIME
                                         #szBackend=wx.media.MEDIABACKEND_WMP10
                                         )
        except NotImplementedError:
            self.Destroy()
            raise

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        art = wx.GetApp().GetArtProvider()
        filesizer = wx.BoxSizer(wx.VERTICAL)
        self._adddir = wx.BitmapButton(self, -1, bitmap=art.GetBitmap(wx.ART_NEW_DIR))
        filesizer.Add(self._adddir, 0, wx.LEFT, 2)
        self._addfile = wx.BitmapButton(self, -1, bitmap=art.GetBitmap(wx.ART_NEW))
        filesizer.Add(self._addfile, 0, wx.LEFT, 2)
                
        self._remove = wx.BitmapButton(self, -1, bitmap=art.GetBitmap(wx.ART_DELETE))
        filesizer.Add(self._remove, 0, wx.LEFT, 2)
        self._removeall = wx.BitmapButton(self, -1, bitmap=getGarbageBitmap())
        filesizer.Add(self._removeall, 0, wx.LEFT, 2)
        
        sizer.Add(filesizer, 0, wx.LEFT, 0)
        
        #self._list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.BORDER_NONE|wx.LC_NO_HEADER)
        self._list = wx.ListBox(self, -1)
        sizer.Add(self._list, 1, wx.EXPAND, 5)
        
        ctrlsizer = wx.BoxSizer(wx.VERTICAL)
        self._play = wx.BitmapButton(self, -1, bitmap=getPlayBitmap())
        ctrlsizer.Add(self._play, 0, wx.RIGHT, 2)
        self._pause = wx.BitmapButton(self, -1, bitmap=getPauseBitmap())
        ctrlsizer.Add(self._pause, 0, wx.RIGHT, 2)
        self._stop = wx.BitmapButton(self, -1, bitmap=getStopBitmap())
        ctrlsizer.Add(self._stop, 0, wx.RIGHT, 2)  
        self._next = wx.BitmapButton(self, -1, bitmap=getNextBitmap())
        ctrlsizer.Add(self._next, 0, wx.RIGHT, 2)        
        self._prev = wx.BitmapButton(self, -1, bitmap=getPrevBitmap())
        ctrlsizer.Add(self._prev, 0, wx.RIGHT, 2)
        sizer.Add(ctrlsizer, 0, wx.RIGHT, 0) 
             
        #self._dos = DosWindow(self, -1)
        #sizer.Add(self._dos, 1, wx.EXPAND, 2)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
        #wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_BUTTON(self._adddir, self._adddir.GetId(), self.OnAddDir)
        wx.EVT_BUTTON(self._addfile, self._addfile.GetId(), self.OnAddFile)
        wx.EVT_BUTTON(self._pause, self._pause.GetId(), self.OnPause)
        wx.EVT_BUTTON(self._stop, self._stop.GetId(), self.OnStop)
        wx.EVT_BUTTON(self._next, self._next.GetId(), self.OnNext)
        wx.EVT_BUTTON(self._prev, self._prev.GetId(), self.OnPrev)
        wx.EVT_BUTTON(self._remove, self._remove.GetId(), self.OnRemove)
        wx.EVT_BUTTON(self._removeall, self._removeall.GetId(), self.OnRemoveAll)
        wx.EVT_UPDATE_UI(self, self._play.GetId(), self.OnUpdateUI)
        wx.EVT_BUTTON(self._play, self._play.GetId(), self.OnDoubleClick)
        wx.EVT_UPDATE_UI(self, self._stop.GetId(), self.OnUpdateUI)
        wx.EVT_UPDATE_UI(self, self._pause.GetId(), self.OnUpdateUI)
        wx.EVT_LISTBOX_DCLICK(self._list, self._list.GetId(), self.OnDoubleClick)
        self.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded)
        self.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnFinish)
        wx.EVT_CLOSE(self, self.OnClose)
        config = wx.ConfigBase_Get()
        listStr = config.Read('music_list')
        for item in listStr.split(';'):
            if len(item) != 0:
                self._list.Insert(os.path.basename(item), self._list.GetCount(), item)

        self._cursel = config.ReadInt('music_last_selection', -1)
        if self._list.GetCount() != 0:
            if self._cursel >= self._list.GetCount() :
                self._cursel = 0
            self._list.Select(self._cursel)
            self.SetTitle('Loading music file %s' % self._list.GetClientData(self._cursel))
            self.mc.Load(self._list.GetClientData(self._cursel))
        self._inClosing = False
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)
                
    def OnUpdateUI(self, event):
        if self._inClosing:
            return
            
        id = event.GetId()
        if id == self._stop.GetId() or \
           id == self._pause.GetId():
            event.Enable(self.mc.GetState() != 0)
        elif id == self._play.GetId():
            event.Enable(self.mc.GetState() == 0 or \
                         self.mc.GetState() == 1)
            
    def OnPause(self, event):
        self.mc.Pause()
        
    def OnTimer(self, evt):
        if self._list.GetCount() == 0: return  
        
        if self.mc.Length() == 0: return
        if self._cursel < 0 or self._cursel > self._list.GetCount():
            self._cursel = 0 
            return
        
        offset = self.mc.Tell()
        per = offset * 100 / (self.mc.Length())
        
        self.SetTitle('Playing music file %s ... %d' % (self._list.GetClientData(self._cursel), per) + '%')
                                
    def OnAddDir(self, event):
        dlg = wx.DirDialog(self, 
                           "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
        if dlg.ShowModal() == wx.ID_OK:
            rootPath = dlg.GetPath()
            for root, dirs, files in os.walk(rootPath):
                for file in files:
                    (name, ext) = os.path.splitext(file)
                    if ext in [u'.mp3', u'.wma', u'.wmv', u'.rm']:
                        self._list.Insert(file, 0, os.path.join(root, file))
            
        dlg.Destroy()   
        
    def OnAddFile(self, event):
        ws = 'Supported Media Files (*.mp3;*.wma;*.wmv;*.rm)|*.mp3;*.wma;*.wmv;*.rm'
        fd = wx.FileDialog(self, 'Select music files:', wildcard=ws,
                           style=wx.FD_OPEN|wx.FD_MULTIPLE)
        if fd.ShowModal() == wx.ID_OK:
            for path in fd.GetPaths():
                self._list.Insert(os.path.basename(path), self._list.GetCount(), path)
        fd.Destroy()
        
    def OnRemove(self, event):
        sel = self._list.GetSelection()
        if sel != -1:
            self._list.Delete(sel)
                   
    def OnRemoveAll(self, event):
        self._list.Clear()
        
    def OnDoubleClick(self, event):
        self._cursel = self._list.GetSelection()
        self.SetTitle('Loading music file %s' % self._list.GetClientData(self._cursel))
        self.mc.Load(self._list.GetClientData(self._cursel))
        
    def OnMediaLoaded(self, event):
        self.SetTitle('Playing music file %s' % self._list.GetClientData(self._list.GetSelection()))
        if not self.mc.Play():
            self.OnNext(event)
        
    def OnStop(self, event):
        self.mc.Stop()
        
    def OnFinish(self, event):
        self.OnNext(event)
        
    def OnNext(self, event):
        index = self._cursel
        if index == self._list.GetCount() - 1:
            index = 0
        else:
            index += 1
        self._list.Select(index)
        self._cursel = index
        self.SetTitle('Loading music file %s' % self._list.GetClientData(index))
        if not self.mc.Load(self._list.GetClientData(index)):
            self.OnNext(event)
        
    def OnPrev(self, event):
        index = self._list.GetSelection()
        if index == 0:
            index = self._list.GetCount() - 1
        else:
            index -= 1
        self._list.Select(index)
        self.SetTitle('Loading music file %s' % self._list.GetClientData(index))
        self._cursel = index
        if not self.mc.Load(self._list.GetClientData(index)):
            self.OnPrev(event)
        
    def OnClose(self, event):
        self.timer.Stop()
        del self.timer        
        self._inClosing = True
        pathArr = []
        for x in xrange(self._list.GetCount()):
            pathArr.append(self._list.GetClientData(x))
        config = wx.ConfigBase_Get()
        config.Write('music_list', ';'.join(pathArr))
        config.WriteInt('music_last_selection', self._cursel)
        self.mc.Stop()
        self.mc.Destroy()
#----------------------------------------------------------------------
# This file was generated by M:\tree\PIS\trunk\src\util\img2py.py
#
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getMusicBoxData():
    return zlib.decompress(
'x\xda\x01S\x04\xac\xfb\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\

def getMusicBoxBitmap():
    return BitmapFromImage(getMusicBoxImage())

def getMusicBoxImage():
    stream = cStringIO.StringIO(getMusicBoxData())
    return ImageFromStream(stream)

def getMusicBoxIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getMusicBoxBitmap())
    return icon
        
def getPlayData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2k=]\x1cC"Z\
\xdf^\xbb\xcbu@\x81\x835ak\\\xf5\xe9\\\xfew\xef\xda\xca\x8bo\xd6%\xb8\x0bp-\
\xfa\xac\x18{D\xa7\xf5\x9eN\xa5\xa9,P=\xc3\x03\xee\x06)\xcb+\xcfN\xfe\xa9\
\x8b4\xaf\x13qpYr\xeb\xce,\xbe\x001a\xb6;\xad/\x99x\x8en\x98r9,Ty\x93wn\x9a\
\xd8Nk[\xc6\xf8g\xf3VM\x91\x9a\xe5 uAx\x16[\x8a\xf3n\x06e\xe7Z\xc3\x7f- \x83\
\x18\xf6\xb3\xbf\xc9\xffj\x15\xce\xc3*\xbb\x01\xc4\xf5t\xf5sY\xe7\x94\xd0\
\x04\x00>\xfbA\x93' )

def getPlayBitmap():
    return BitmapFromImage(getPlayImage().Scale(16, 16))

def getPlayImage():
    stream = cStringIO.StringIO(getPlayData())
    return ImageFromStream(stream)

def getPlayIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getPlayBitmap())
    return icon
    
def getPauseData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2s<]\x1cC"Z\
\xdf^;\xc8u@\x81\x87\xf9\xc2\x96_\xb7g\xffzz31\xe7\xc1\x8d\x85\xf3\xac"\xb8l\
%\\\xe4;\x16\xcd\x14O\x99\xb6\xfc\x9d^\x03\x03\x13\xc7\x07V\x87^\xbf\x9c\xdf\
\xc72\xefH\x1d\x93\xa8H\x8b[\xa5\xcby\xc6{E\xf5{\x96\ns\xcf}\xa9\x17\xbf\xae\
\xf3\xb3gbd\xf1`o\xb9\xcf\xf8`O\xce\xc4\x9c\xa5>\xf5N\x8c,\x02\x0e\r\xf7\x99\
\xf9\xfa\xd8T\xb6\x87\x9e_\xa3\x07\xb4\x97\xc1\xd3\xd5\xcfe\x9dSB\x13\x00\
\x0e,>\xae' )

def getPauseBitmap():
    return BitmapFromImage(getPauseImage().Scale(16, 16))

def getPauseImage():
    stream = cStringIO.StringIO(getPauseData())
    return ImageFromStream(stream)

def getPauseIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getPauseBitmap())
    return icon


def getStopData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2\x93<]\x1cC"Z\
\xdf^;\xc8\xd5\xe0\xc0\xc1r!\xf0\xfbv\xef\xff5V%zBL\xcdn\x1f\xb6t\xffv\x881\
\xf9| \xe5\xc7\x8b\xd7L\x1c\n\r\x0c\xf1\x0ck\xce=\xbdc~o^\xfa\xa1\xe4H\xef\
\x04\xb9\xfe\xcd\xab8>\x18yn\n>o\xf3,\x1a(\xff\xb8\xe1\x9a=\xc3\x1c\xe6\xefi\
3\xca\x9c\x18Y\x04\x1c\x1a\xee3\xf3\x1d;#\xedT!!\xe9\x0b\xb4\x8d\xc1\xd3\xd5\
\xcfe\x9dSB\x13\x00t\xbd:\xa7' )

def getStopBitmap():
    return BitmapFromImage(getStopImage().Scale(16, 16))

def getStopImage():
    stream = cStringIO.StringIO(getStopData())
    return ImageFromStream(stream)

def getStopIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getStopBitmap())
    return icon           
     
def getNextData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b\'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2\x1b=]\x1cC"Z\
\xdf^;\xc8\xd5\xa0 \xc0r!\xf2\xed\xf6\xd5k\xedjv\xa9\x94\x08L\x9f\xf2\xc1\
\x88{\x92\xc1\xc5=\'\x9c\xd34\x93\x9f-Y\xf9\x96\x89C\xa1\x81\x81\x89!b\x91\
\xf4\xb7\xdc\xd4\x9b\xf2\xcfS\xe3?\'20\xecx\x7f^t\x8d\xa8\xebO\x83\x07\xe1\
\x1dK\xef\xc4\xbc\xf3k\xb8\xea:)P\xcev\xffk\x81i]S\xa6\xbf\x92v\xfbYmW\xcbdw\
|m\xe8\x9dS\xbb\x19\xebE\xa6\x1b\xfe\x9d\xc4\t2\x89\xc3@\xba\x80\xb9 .\xf0\
\xe2\xb2\xaeK\x97\x81\x8ea\xf0t\xf5sY\xe7\x94\xd0\x04\x00\xe6\xe7J\x1a' )

def getNextBitmap():
    return BitmapFromImage(getNextImage().Scale(16, 16))

def getNextImage():
    stream = cStringIO.StringIO(getNextData())
    return ImageFromStream(stream)

def getNextIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getNextBitmap())
    return icon
    

def getPrevData():
    return zlib.decompress(
"x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\n \xcc\xc1\x06\
$\x8b\xab\xaa\xbe\x00)\x96b'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2\xa7y\xba8\x86\
D\xb4\xbe\x9dz\x96\xef\xb0\x02O\xb3\xec\x8b\xec\xcf\x9f\x1f\xdc\xdds\xd8\x85\
\xffn\xc6\x82\xdb!\xbe\x9b\x96\xce\xd19*\xdf\xc9\xb0Y\xa0p\xe9\xa1\xa5/\x99\
\x04\x1a\x18X\x14\x1a\x8c\x19T\xd5\xa7\xcd\xa9\xd8\xbf\xd6\xe6\xf1\xfb\xd4\
\xc5\xf3\x03Ov2\x04d32Lp\xe8\xe8\xee\xfde\xab\xbb\xf9\xe0\xe6}\xda\xdc\x1b\
\xa3\xb7\x86\xd9\x9d\xff\x14\xa5\xf2\xf2\xa7\xfb\xde\xed\x9f\xc2.\x94e\xeeN\
\xdc&X\xbd\xcf\x9c\xa1\x9cu-\xe7O\xbb\x13\x9f\xed\xd9^\xb0\x9e\xfde\xcb{\xbf\
)\xfe\xe5\x7f9%F\x0e\x07\x06&\x81\x03\xdb\xbf2\xc4?OO\xdf:5\xe7\x00\xd0\x85\
\x0c\x9e\xae~.\xeb\x9c\x12\x9a\x00\xbcAV\xa7" )

def getPrevBitmap():
    return BitmapFromImage(getPrevImage().Scale(16, 16))

def getPrevImage():
    stream = cStringIO.StringIO(getPrevData())
    return ImageFromStream(stream)

def getPrevIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getPrevBitmap())
    return icon    
    
#----------------------------------------------------------------------
# This file was generated by M:\tree\PIS\trunk\src\util\img2py.py
#
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getGarbageData():
    return zlib.decompress(
'x\xda\x01X\x02\xa7\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x02\x0fIDATX\x85\xbdW[v\x85 \x0c\x9cx\xdd\x17l\xac5\xb4\
\x1b\x0b\x0bk\xd3\x0f\x0c\n\xc2\x15{m\xe7\x1c\xce}h2C\x1e<\x88\xa6\x07F\xb0\
\xbc\xbf\xe9\xd0\x8b\x15\x98\x194=\xa8\xfb\x02M\x8f\xd3\xc1\xcc\xfa[0\xb3\
\x02\xd0\x9e\xef\xe9\xd9\x8c\xf3X\x96\xbdd\xc4\x18\x87>CH\x13W\x05\xf4\xfb\
\xab\x19A\xaaS`\xa16\xd2\x10\xc2i\x98\xb3\xed\xc2\x88Q\xe0\x9cG\x8c\x02\x11\
\x0f\x80\xe1\xbd\x87s\x1eD8\xa4c>\xcc\xbaA\\F\xa0\x8d\x10\x02\x88\x00U\x9fE\
\x88\xa4g&\x08\xf0\x07\xbbf\n\xae\xccz\x0f\x11\x01\xd1\x9e0\xc1\x04\xb5\xd0\
\x1402\xe3\x11\x11\x86ZP\x81\xba\xdaEDE\xa4\xa8\xe2\x11\x008\x0cf\xa8\xf9T\
\xb5\xff\xb8\xe8\x88\xb9-\x0bk%o\xd1\xb0\xdf\xde\xbb\xc3\xbb\xaa\x80\xaa\x16\
\xa9c\xe6F\x04\xbc\xf9S\x00\x08\x1f\x9f\xd4\xec\x02\xef=j8\xe7\n!\xf6\xbb\
\x07"B\xd2\x90\xba\xc0{\x0fY\xab\xd2l\x89\xa8]\x03-\x01!\x04\x84\x10\n!1\xc6\
\xd4Z\xbb\xd1\xf3g\xe45\x9am\xb8\x0f_m\x18B(\x8aT\xe4<""R<\xdf\xa7*\x0b0r\
\x0b\xb1\x19\xd6\x1d\x91fM\x87p\xee\xed\xb2\xcfe[\xfcz\xad=\xd7\xe4"\x02\x11\
\x81\xf7\xbe\x88D\x0f\xbd\x9a\xa8\x8b\xb2\x86mRsMn\xf9\xdf\x7f\x1fA\x1d\xb9Q\
\xccf\\\x13\x8a\x08\x98m\x1d\xdffG\xbdJ\xfb%f#{V\xa91F8\xe7Vr^\xc7M\x02\xc2\
\xc7\'-\xefo\xda*8\x00\xb9\xe06\xf2\xd7\xb1?\xa4L@Z\x91\x9e\x19\xa4\xd4\xdcC\
^#/D\xcc8,*[\xba\xff\x86\xbc\x10\xd0GI>\xd0\x99w\x0b\xd8\x90N8\xaf\xa1>\xa4\
\x0e\x0b\xb8\x83\xbc\x85!\x01\x7fE^\x08`\xb6}\xbd\x1cw\xe7\xbc+\xe0?\xd0\xba\
\xa4\xfc\xab\x80\x16.v\x81\xe4\x1d\xd2v\xcdW\xd1=\x13\xf6\xc8-\x84\xeb\x95+\
\x0b\xba\xb2s^\x16P\x93\x03\xb8$\xc4\x9e\xb5.\xa9\x85\x80\xd6\xa9\xc6\x1c\
\xf4n\xb8=!g\xc4\xd9\xdeN\xc5\xbd\xcb\xe3\x99\x83\x1a{?#v?\xab\xd3\xbf?\xc6{\
\xee\xec\x00\x00\x00\x00IEND\xaeB`\x82\xc8q\x04\x8f' )

def getGarbageBitmap():
    return BitmapFromImage(getGarbageImage().Scale(16, 16))

def getGarbageImage():
    stream = cStringIO.StringIO(getGarbageData())
    return ImageFromStream(stream)

def getGarbageIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getGarbageBitmap())
    return icon

    