"""
 _template_attribute_ must be defined in template python code as
 [description, filter, dir, ext, docTypeName, viewTypeName, docType, viewType, flag, icon]
"""
"""
_plugin_module_info_ = [{"name":"MediaPlayer",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"Media player for media doc",
                         "class":"MediaDocPlugin"}]
"""
import wx.lib.docview as docview
import core.plugin
import wx
import  wx.lib.iewin    as  iewin
from wx.lib.pdfwin import PDFWindow

class MediaDocPlugin(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'MediaPlayer'
    
    def IGetDocumentClass(self):
        return MediaDocument
    
    def IGetViewClass(self):
        return MediaView
    
    def IGetFilter(self):
        #return '*.h;*.c;*.cpp;*.hpp;*.txt;*.text;*.bat;*.sh;*.py;*.pyw;*.bak;*.cfg;*.ini;*.inf;*.dsc;*.dec;*.lua;*.uni'
        return '*.wmv;*.avi;*.mpg;*.rm;*.rmvb'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'wmv'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'wmv'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_INVISIBLE
    
    #def IGetIcon(self):
    #    """Interface for child class provide template's icon"""
    #    return getPDFIcon()
    
class MediaDocument(docview.Document):
    def IsReadOnly(self):
        return True
    
    def IsDocumentModificationDateCorrect(self):
        return True
    
class MediaView(docview.View):
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self.log     = wx.GetApp().GetLogger()
        
        
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        frame.Freeze()
        sizer        = wx.BoxSizer(wx.VERTICAL)
        # Create some controls
        try:
            self.mc = wx.media.MediaCtrl(frame, style=wx.SIMPLE_BORDER,
                                         #szBackend=wx.media.MEDIABACKEND_DIRECTSHOW
                                         #szBackend=wx.media.MEDIABACKEND_QUICKTIME
                                         #szBackend=wx.media.MEDIABACKEND_WMP10
                                         )
        except NotImplementedError:
            self.Destroy()
            raise
        
        sizer.Add(self.mc, 1, wx.EXPAND, 2)
        
        frame.SetSizer(sizer)
        frame.Layout()
        frame.SetAutoLayout(True)
        frame.Thaw()
        self.frame = frame
        frame.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded)
        frame.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnFinish)
        frame.Bind(wx.media.EVT_MEDIA_STATECHANGED, self.OnStatusChanged)

        wx.CallAfter(self.LoadMedia)
        
        return True

    def ProcessUpdateUIEvent(self, evt):  
        return True    
    
    def LoadMedia(self):
        file = self.GetDocument().GetFilename()
        if not self.mc.Load(file):
            wx.MessageBox('Unable to load media file %s!' % file)
        else:
            self.log.info('loading media file %s!' % file)
            self.mc.SetInitialSize()
            
    def OnMediaLoaded(self, event):
        if not self.mc.Play():
            self.log.error('Fail to play media')
        else:
            self.log.info('playing media!')
            self.mc.ShowPlayerControls(wx.media.MEDIACTRLPLAYERCONTROLS_DEFAULT)
            
    def OnFinish(self, event):
        self.log.info('Finish play media')
        
    def OnStatusChanged(self, event):
        self.log.info('status changed!')
        
    def OnClose(self, deleteWindow):
        self.mc.Destroy()
                
        return docview.View.OnClose(self, deleteWindow)    
        
