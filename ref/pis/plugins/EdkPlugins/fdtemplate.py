_plugin_module_info_ = [{"name":"FDTemplate",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide doc/view for EFI firmware Device file",
                         "class":"FDTemplatePlugin"}]
        
import core.plugin
import core.hexctrl
import wx, os
import wx.lib.docview as docview
import wx.lib.customtreectrl as CT
import plugins.EdkPlugins.basemodel.efibinary as efibinary
                          
class FDTemplatePlugin(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'EFI Firmware Device'
    
    def IGetDocumentClass(self):
        return FdDoc
    
    def IGetViewClass(self):
        return FdView
    
    def IGetFilter(self):
        #return '*.h;*.c;*.cpp;*.hpp;*.txt;*.text;*.bat;*.sh;*.py;*.pyw;*.bak;*.cfg;*.ini;*.inf;*.dsc;*.dec;*.lua;*.uni'
        return '*.fd'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'fd'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'fd'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_NO_CREATE 
        
    def IGetIcon(self):
        return getBlankIcon()
        
class FdDoc(docview.Document):
    def __init__(self):
        docview.Document.__init__(self)
        self._fdobj    = efibinary.EfiFd()
        self._maplines = None
        
    def LoadObject(self, fileObject):
        view = self.GetFirstView()
        binary = open(self.GetFilename(), 'rb')
        fstat  = os.stat(self.GetFilename())
        self._fdobj.Load(binary, fstat.st_size)
        binary.close()
        """
        mapfile = None
        mapfilepath = self.GetFilename() + '.map'
        if os.path.exists(mapfilepath):
            mapfile = efibinary.EfiFvMapFile()
            mapfile.Load(mapfilepath)
        """
        view.SetValue(self._fdobj)
        return True

    def IsReadOnly(self):
        return True
    
    def IsDocumentModificationDateCorrect(self):
        return True

    def OnCreateCommandProcessor(self):
        # Don't create a command processor, it has its own
        pass
        
class FdView(docview.View):
    PRINTABLE_CHAR = ['/', '\\', '#', '~', '!', '@', '$', '%', '^', '&', '*', '(', \
                      ')', '{', '}', '[', ']', '<', '>', ':', ';', '\"', '\'', '?',\
                      '-', '+', '=', '_']
    PRINTABLE_CHAR_INT = [ord(item) for item in PRINTABLE_CHAR]
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self._fvobj      = None
        self._focusChild = None
        self._mapfile    = None
        
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._tree = CT.CustomTreeCtrl(frame, -1, style= wx.SUNKEN_BORDER| CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT)
        self._tree.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = 'Courier New'))
        sizer.Add(self._tree, 1, wx.EXPAND, 5)
        frame.SetSizer(sizer)
        frame.Layout()
        self.frame = frame
        return True      
        
    def SetValue(self, fdobj):
        self._fdobj   = fdobj
        
        root  = self._tree.AddRoot(self.GetDocument().GetFilename())
        count = 0
        for fvobj in fdobj.GetFvs():
            fvItem = self._tree.AppendItem(root, "[FV %d]" % count)
            self.DisplayFv(fvItem, fvobj)
            count += 1
            
    def DisplayFv(self, root, fvobj):
        header = fvobj.GetHeader()
        self._tree.AppendItem(root, "Signature        : %s" % header.GetSigunature())
        attrItem = self._tree.AppendItem(root, "Attribute        : 0x%X" % header.GetAttribute())
        attrstrs = header.GetAttrStrings()
        if len(attrstrs) != 0:
            for attr in attrstrs:
                self._tree.AppendItem(attrItem, attr)
        self._tree.AppendItem(root, "Size             : 0x%X" % header.GetFvLength())
        self._tree.AppendItem(root, "File System Guid : %s" % str(header.GetFileSystemGuid()))
        self._tree.AppendItem(root, "Revision         : 0x%X" % header.GetRevision())
        dataItem = self._tree.AppendItem(root, 
                                         "Fv Header Raw",
                                         data=ItemRawData(fvobj.GetOffset(), 
                                                          fvobj.GetHeaderRawData()))
        self._tree.SetItemHasChildren(dataItem)
        
        ffsRoot = self._tree.AppendItem(root, "FFS")
        count = 1
        for ffs in fvobj.GetFfs():
            name = str(ffs.GetNameGuid())
            if self._mapfile != None:
                mapentry = self._mapfile.GetEntry(ffs.GetHeader().GetNameGuid())
                if mapentry != None:
                    name = mapentry.GetName()
            ffsItem = self._tree.AppendItem(ffsRoot, '[%02d] %s' % (count, name), data=ffs)
            self._tree.SetItemHasChildren(ffsItem)
            count += 1
        fvRawItem = self._tree.AppendItem(root, 
                                          'FV Raw Data',
                                          data=ItemRawData(0, fvobj.GetRawData()))
        self._tree.SetItemHasChildren(fvRawItem)
        CT.EVT_TREE_ITEM_EXPANDING(self._tree, self._tree.GetId(), self.OnExpanding)
        
    def OnClose(self, deleteWindow = True):
        self.Activate(False)
        
        if not docview.View.OnClose(self, deleteWindow):
            return False

        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True
                
    def ProcessEvent(self, event):
        id    = event.GetId()

        focus = self._tree.FindFocus()
        if issubclass(focus.__class__, core.hexctrl.HexCtrl):
            if id == wx.ID_COPY:
                focus.Copy()
                return True
            if id == wx.ID_SELECTALL:
                focus.SetSelection(0, -1)
                return True
                
        return docview.View.ProcessEvent(self, event)
        
    def ProcessUpdateUIEvent(self, event):
        id    = event.GetId()

        focus = self._tree.FindFocus()
        if issubclass(focus.__class__, core.hexctrl.HexCtrl):
            if id == wx.ID_COPY:
                hasSelection = focus.GetSelectionStart() != focus.GetSelectionEnd()
                event.Enable(hasSelection)
                return True
            if id == wx.ID_SELECTALL:
                hasText = focus.GetTextLength() > 0
                event.Enable(hasText)          
                return True      
        return docview.View.ProcessUpdateUIEvent(self, event)        
        
    def OnExpanding(self, event):
        item = event.GetItem() 
        data = self._tree.GetPyData(item)
        if data == None: return
        if issubclass(data.__class__, efibinary.EfiFfs):
            self.UpdateFfsItem(item, data)
        if issubclass(data.__class__, ItemRawData):
            self.UpdateRawData(item, data._base, data._data)
            
    def UpdateFfsItem(self, item, ffs):
        self._tree.CollapseAndReset(item)    
        header = ffs.GetHeader()
        self._tree.AppendItem(item, 'Name   : \t%s' % str(header.GetNameGuid()))
        self._tree.AppendItem(item, 'Offset : \t0x%X' % ffs.GetOffset())
        self._tree.AppendItem(item, 'Size   : \t0x%X' % header.GetFfsSize())
        self._tree.AppendItem(item, 'Type   : \t0x%X (%s)' % (header.GetType(), header.GetTypeString()))
        self._tree.AppendItem(item, 'State  : \t0x%X (%s)' % (header.GetState(), header.GetStateString()))
        if self._mapfile != None:
            entry = self._mapfile.GetEntry(header.GetNameGuid())
            if entry != None:
                self._tree.AppendItem(item, 'BaseAddress : 0x%X' % entry.GetBaseAddress())
                self._tree.AppendItem(item, 'EntryPoint  : 0x%X' % entry.GetEntryPoint())
        headerRawItem = self._tree.AppendItem(item, 
                                              "FFs Header Raw",
                                              data=ItemRawData(ffs.GetOffset(),
                                                               header.GetRawData()))
        self._tree.SetItemHasChildren(headerRawItem)
        
        sectionRootItem = self._tree.AppendItem(item, 'Sections')
        count = 0
        for sec in ffs.GetSections():
            count += 1
            sectionItem = self._tree.AppendItem(sectionRootItem, 
                                                '[%d] Type=0x%X (%s), size=0x%X' % (count, sec.GetHeader().GetType(), sec.GetHeader().GetTypeString(), sec.GetSize()),
                                                data=ItemRawData(sec.GetSectionOffset(), 
                                                                 sec.GetContent()))
            self._tree.SetItemHasChildren(sectionItem)
        
    def UpdateRawData(self, item, base, listdata):
        self._tree.CollapseAndReset(item)
        height = (len(listdata)/16 + 1) * 16 + 20
        if height > 300:
            height = 300
            
        textctrl = core.hexctrl.HexCtrl(self._tree, -1, size=(650, height))
        #textctrl.SetValue(base, listdata)
        
        self._tree.AppendItem(item, '', wnd=textctrl)
        
        self._tree.Freeze()
        lines = self._listToText(base, listdata)
        textctrl.SetReadOnly(False)
        textctrl.AddText('\n'.join(lines))
        textctrl.SetReadOnly(True)
        self._tree.Thaw()
        
    def _listToText(self, base, listdata):
        newlist    = []
        line       = ''
        linestr    = ''
        newstr     = ''
        linecount  = 0
        count      = 0
        for item in listdata:
            if count < 15:
                if count == 7:
                    line += '%02X-' % item
                else:
                    line += '%02X ' % item
                    
                if (item <= ord('z') and item >= ord('a')) or \
                   (item <= ord('Z') and item >= ord('A')) or \
                   (item <= ord('9') and item >= ord('0')) or \
                   (item in self.PRINTABLE_CHAR_INT):
                    linestr += chr(item)
                else:
                    linestr += '.'
                
                count += 1
            else:
                line += '%02X ' % item
                if (item < ord('z') and item > ord('a')) or \
                    (item < ord('Z') and item > ord('A')):
                    linestr += chr(item)
                else:
                    linestr += '.'
                newstr = '0x%08X: ' % (base + linecount * 16)
                newstr += line
                #self.AddText('0x%08X: ' % (base + linecount * 16))
                newstr += '  %s' % linestr
                newlist.append(newstr)
                line = ''
                linestr = ''
                count = 0
                linecount += 1
        
        if len(line) != 0 and count != 15:
            newstr = '0x%08X: ' % (base + (linecount) * 16)
            #self.AddText('0x%08X: ' % (base + (linecount) * 16))
            newstr += line
            while count <= 15:
                newstr += '   '
                count += 1
            newstr += '  %s' % linestr
            newlist.append(newstr)
            #self.AddText(line)
            #self.AddText('  %s' % linestr)
            #self.AddText('\n')   
        return newlist
             
class ItemRawData:
    def __init__(self, base, listdata):
        self._base = base
        self._data = listdata  
                      
from wx import ImageFromStream, BitmapFromImage, EmptyIcon
import cStringIO, zlib
import wx
                      
def getBlankData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x04IDAT8\x8d\xa5\x93\xbdj\x02A\x10\xc7\x7f{gme\xe5c\xe4\t\x82\x85\
\x85\x85oa\xe5+\xd8Z\xd8'e\xfa\x80\xd8\xd8X\x19R\xc4\x07\x90\x04\xd1J\x08\
\x17\x0cr\\V\xe1\xe4\xfc\x80\xb58\xf7\xd8\xbd\x0f\xa280\xec\xec2\xbf\xff\xce\
\xcc\xb2B8.\xf7X\xc9\xdc|L\x97J\xc7\xbe\x0c\x01\xf0\xd6\x01\x00RFtZu\x91Q\
\x10\x8e\x9b\xf8\xe4\xf3[-w*\xf1\xafm\xec\xcf\x83\x89\x1a\xad\x94\xea\xbe\
\x8c\x95\x99/\x1c\x17\xe7\xdaR\xcb%xh\xd4hw_\x95yn\xb5\xe0\xcb\x90\xea%\x0eO\
\xf1\xba\xd9\xc7\xe5\xbf\x0f\xdfX]\xda)\x140A\r\x03<6klO\xf0w\x84~\xef\xc9\
\xca/lA\xc3@\x02\xe7\x99U\x81\xb7\x0e\xa8\xec\xed\x04\x13\xde\x1c\xfe\x11\
\x902\xb2@\xc8\xc2\x8b\xd9\xbcX\xc0\x045\xac\xc1 Jg\xe6\x08\xe8)\xa7o\xd5\
\xb0\xbf\xcb\nd\x86x\x0b\x9c+p\x0b\x0c\xa9\x16~\xbc_\xeb\x9d\xd3\x03\xcb3q\
\xefo\xbc\xfa/\x14\xd9\x19\x1f\xfb\x8aa\x87\xf2\xf7\x16\x00\x00\x00\x00IEND\
\xaeB`\x82" 


def getBlankBitmap():
    return BitmapFromImage(getBlankImage())

def getBlankImage():
    stream = cStringIO.StringIO(getBlankData())
    return ImageFromStream(stream)

def getBlankIcon():
    return wx.IconFromBitmap(getBlankBitmap())                      