"""
 _template_attribute_ must be defined in template python code as
 [description, filter, dir, ext, docTypeName, viewTypeName, docType, viewType, flag, icon]
"""

_plugin_module_info_ = [{"name":"PDFViewer",
                         "author":"ken",
                         "version":"1.0",
                         "minversion":"0.0.1",
                         "description":"web browser base IE",
                         "class":"PDFViewerPlugin"}]

import wx.lib.docview as docview
import core.plugin
import wx
if wx.Platform == '__WXMSW__':
    from wx.lib.pdfwin import PDFWindow

class PDFViewerPlugin(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'PDF'
    
    def IGetDocumentClass(self):
        return PDFDocument
    
    def IGetViewClass(self):
        return PDFView
    
    def IGetFilter(self):
        #return '*.h;*.c;*.cpp;*.hpp;*.txt;*.text;*.bat;*.sh;*.py;*.pyw;*.bak;*.cfg;*.ini;*.inf;*.dsc;*.dec;*.lua;*.uni'
        return '*.pdf'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'pdf'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'pdf'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_INVISIBLE
    
    def IGetIcon(self):
        """Interface for child class provide template's icon"""
        return getPDFIcon()
    
class PDFDocument(docview.Document):
    def IsReadOnly(self):
        return True
    
    def IsDocumentModificationDateCorrect(self):
        return True
    
class PDFView(docview.View):
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self.log     = wx.GetApp().GetLogger()
        
        
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        frame.Freeze()
        sizer        = wx.BoxSizer(wx.HORIZONTAL)
        self.pdf     = PDFWindow(frame, style=wx.SUNKEN_BORDER)
        self.pdf.AddEventSink(self)
        sizer.Add(self.pdf, 1, wx.EXPAND, 2)
        
        frame.SetSizer(sizer)
        frame.Layout()
        frame.SetAutoLayout(True)
        frame.Thaw()
        
        self.pdf.LoadFile(self.GetDocument().GetFilename())
        
        return True
    
    def ProcessUpdateUIEvent(self, evt):      
        #evt.Enable(False)
        id = evt.GetId()
        if id == wx.ID_COPY or\
           id == wx.ID_CUT  or\
           id == wx.ID_PASTE:
            #if not self.ie.GetStringSelection():
            evt.Enable(False)
            return True
        
        return True    
    
    def OnMessage(self):
        pass
    
    def OnError(self):
        pass
    
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib


def getPDFData():
    return zlib.decompress(
'x\xda\x01\xcc\x013\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x01\x83IDATX\x85\xc5\x97a\x92\xc2 \x0c\x85C\xf5^\xe6b\xdax\
\xb3\xd7\x83i\xf6O\xa3\x91\x92\x05Z\xdc}3\x1dK\x84\xe6#\x84\x0c\xa44\x9d(\
\x92>\x1f\x1a\xfe\xb9Ci:\xa5\xdcv\xae\r\x02p\xd813\x93\x12Qz>4\x87HD4t\x96^\
\x06o\x00\xe6\xd0C\x9c\xe9K\x04\x9bX\xaf\xca#1\x95{\xe9\xfbi\xb5\xe9v\x1a\
\xd1\xf2)\xbd\xf3+\xce\x81\x94\xdeN\xec\xfd7[EQ\xaf\x18\xc0fTs\xd0\xd0\x0f\
\xc0&\x1a"B\xf3\xed\xaa\xf5\x08\xd4\xd4\xd8\x8f\x99\x8b\xf6\xea6\xfcPkT:T\
\x06(9h\xb5\xed\x01\x187\x9f\x1d\x00\xa5\xf2h\xd2\xe7CE\xa4\xf9c\xb3\x08\xdd\
;\xfa\x135\xe4@\x94<\xa3\xc6\x94\x0b\xd1\x01\xf5\x02\x0f\x07\xb8\xfc7@\xaf\
\x86\x03,\x85\xaa\xf7\'\x00\x17fZV\xc7\xb3H3D_%\x0c\x04\x80\xc89\\\x00\x9a\
\xd7\\\xc8\xb7e\x9e\xa4C\x00\xe6\xc2\xde\xbf\x8b\x103\xbf@\x0c\x0c\xc0\x07\
\xc4a\x00\xcb\xfa%\x0b\xb9\xb9\xf0\xf6\x0b3!\x83=\x04\x109\x8f\xb4\x00/0\xd3\
\xee$\xecu\x1e\xa9\x19\xc0\xaf\x9dw\x1eU\xbe\xd6\x8a\xb8;\x02Gg\xde\r "$\xeb\
\xfe.e\xb3\xb5\xfd\xfe\xf7m;\x96m\xeaC\x9aN\xe1CD\n@ED\xfd;\x80W\xfb\xc8\xaf\
\x88h\xd7\x12\x00\xa0\x9e\xf3\x81\x97E/\x8f@\x13\x80\r\xf6!\x97\xb5\xd0\xe4m\
\x03\xcc\xdb\xfe;^\xa9v9\x1dq7,\xc9\xe0\xber"\xea\xd1\xaf\x110\xcd\xb7\xeb\
\xd7.\xb0?\t\x91\xffhS1z\xd4\x00\x00\x00\x00IEND\xaeB`\x82\x8a\x19\xc6\x13' )

def getPDFBitmap():
    return BitmapFromImage(getPDFImage().Scale(16, 16))

def getPDFImage():
    stream = cStringIO.StringIO(getPDFData())
    return ImageFromStream(stream)

def getPDFIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getPDFBitmap())
    return icon
    