_plugin_module_info_ = [{"name":"PETemplate",
                         "author":"ken",
                         "version":"1.0",
                         "description":"Provide doc/view for PE Coff file",
                         "class":"PETemplatePlugin"}]
        
import core.plugin
import core.hexctrl
import core.pe
import wx, os
import wx.lib.docview as docview
import wx.lib.customtreectrl as CT
import time
                          
class PETemplatePlugin(core.plugin.ITemplatePlugin):
    def IGetDescription(self):
        return 'PE Coff File Template'
    
    def IGetDocumentClass(self):
        return PEDoc
    
    def IGetViewClass(self):
        return PEView
    
    def IGetFilter(self):
        #return '*.h;*.c;*.cpp;*.hpp;*.txt;*.text;*.bat;*.sh;*.py;*.pyw;*.bak;*.cfg;*.ini;*.inf;*.dsc;*.dec;*.lua;*.uni'
        return '*.efi;*.exe;*.dll'
    
    def IGetDir(self):
        """Interface for child class provide document's default dir
        """
        return 'fv'
    
    def IGetExt(self):
        """Interface for child class provide document's default postfix of file name
        """
        return 'efi;exe'
    
    def IGetFlag(self):
        """Interface for child class provide template's flag: TEMPLATE_VISIBLE/TEMPLATE_INVISIBLE
        TEMPLATE_NO_CREATE/DEFAULT_TEMPLATE_FLAGS
        """
        return wx.lib.docview.TEMPLATE_NO_CREATE 
        
    def IGetIcon(self):
        return getBlankIcon()
        
class PEDoc(docview.Document):
    def __init__(self):
        docview.Document.__init__(self)
        self._peobj    = core.pe.PEFile()
        
    def LoadObject(self, fileObject):
        view = self.GetFirstView()
        binary = open(self.GetFilename(), 'rb')
        fstat  = os.stat(self.GetFilename())
        self._peobj.Load(binary, fstat.st_size)
        binary.close()
        view.SetValue(self._peobj)
        return True

    def IsReadOnly(self):
        return True
    
    def IsDocumentModificationDateCorrect(self):
        return True

    def OnCreateCommandProcessor(self):
        # Don't create a command processor, it has its own
        pass
        
class PEView(docview.View):
    PRINTABLE_CHAR = ['/', '\\', '#', '~', '!', '@', '$', '%', '^', '&', '*', '(', \
                      ')', '{', '}', '[', ']', '<', '>', ':', ';', '\"', '\'', '?',\
                      '-', '+', '=', '_']
    PRINTABLE_CHAR_INT = [ord(item) for item in PRINTABLE_CHAR]
    
    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self._peobj      = None
        
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._tree = CT.CustomTreeCtrl(frame, -1, style= wx.SUNKEN_BORDER| CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT)
        self._tree.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = 'Courier New'))
        sizer.Add(self._tree, 1, wx.EXPAND, 5)
        frame.SetSizer(sizer)
        frame.Layout()
        self.frame = frame
        
        CT.EVT_TREE_ITEM_EXPANDING(self._tree, self._tree.GetId(), self.OnExpanding)
        return True      
        
    def SetValue(self, peobj):
        self._peobj   = peobj
       
        root = self._tree.AddRoot(self.GetDocument().GetFilename())
        dosItem   = self._tree.AppendItem(root, "Dos Header", data=peobj.GetDosHeader())
        self._tree.SetItemHasChildren(dosItem)
        imageItem   = self._tree.AppendItem(root, "Image Header", data=peobj.GetImageHeader())
        self._tree.SetItemHasChildren(imageItem)

        optheader = peobj.GetImageOptionalHeader()
        if optheader != None:
            optItem = self._tree.AppendItem(root, "Image Optional Header", data=optheader)
            self._tree.SetItemHasChildren(optItem)

        sectionheaders = peobj.GetSectionHeaders()
        if sectionheaders != None:
            shItem = self._tree.AppendItem(root, "Sections")
            for sec in sectionheaders:
                secItem = self._tree.AppendItem(shItem, '%-08s offset:0x%08X  size:0x%08X' % (sec.GetShortName(), 
                                                                                                sec.GetPointerToRawData(),
                                                                                                sec.GetSizeOfRawData()), data=sec)
                self._tree.SetItemHasChildren(secItem)
        
        debugentries = peobj.GetDebugSection()
        if debugentries != None:
            debugItem = self._tree.AppendItem(root, 'Debug Data')
            index = 0
            for item in debugentries:
                entryItem = self._tree.AppendItem(debugItem, 'Entry %d' % index)
                index +=1
                self._tree.AppendItem(entryItem, 'Type                : 0x%X' % item.GetType())
                self._tree.AppendItem(entryItem, 'Time                : %s' % time.strftime('%d/%m/%y %H:%M', time.localtime(item.GetTimeDateStamp())))
                self._tree.AppendItem(entryItem, 'Size                : 0x%X' % item.GetSizeOfData())
                self._tree.AppendItem(entryItem, 'Address of raw data : 0x%X' % item.GetAddressOfRawData())
                self._tree.AppendItem(entryItem, 'Point to raw data   : 0x%X' % item.GetPointerToRawData())
                debugrawitem = self._tree.AppendItem(entryItem, 'Raw data:', data=ItemRawData(item.GetPointerToRawData(), 
                                                                                              item.GetRawData()))
                self._tree.SetItemHasChildren(debugrawitem)
        rawItem   = self._tree.AppendItem(root, "File Raw Data",
                              data=ItemRawData(0, peobj.GetRawData()))
        self._tree.SetItemHasChildren(rawItem)
            
        
    def OnClose(self, deleteWindow = True):
        self.Activate(False)
        
        if not docview.View.OnClose(self, deleteWindow):
            return False

        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True
     
    def OnExpanding(self, event):
        item = event.GetItem() 
        data = self._tree.GetPyData(item)
        if data == None: return
        cls = data.__class__
        if issubclass(cls, core.pe.DosHeader):
            self.UpdateDosHeader(item, data)
        if issubclass(cls, ItemRawData):
            self.UpdateRawData(item, data._base, data._data)
        if issubclass(cls, core.pe.ImageHeader):
            self.UpdateImageHeader(item, data)
        if issubclass(cls, core.pe.ImageOptionalHeader32):
            self.UpdateOptionalHeader(item, data)
        if issubclass(cls, core.pe.ImageOptionalHeader64):
            self.UpdateOptionalHeader(item, data)
        if issubclass(cls, core.pe.ImageSectionHeader):
            self.UpdateSection(item, data)
            
    def UpdateDosHeader(self, root, header):
        self._tree.CollapseAndReset(root)
        self._tree.AppendItem(root, 'Magic Number         : 0x%X (\"%s\")' % (header.GetMagicNumber(), header.GetMagicString()))
        self._tree.AppendItem(root, 'PE Header Offset     : 0x%X' % header.GetPeHeaderOffset())
        
    def UpdateImageHeader(self, root, header):
        self._tree.CollapseAndReset(root)
        self._tree.AppendItem(root, 'Machine              : 0x%X (%s)' % (header.GetMachine(), header.GetMachineString()))
        self._tree.AppendItem(root, 'Number of sections   : 0x%X' % header.GetNumberOfSections())
        self._tree.AppendItem(root, 'TimeDateStamp        : %s' % time.strftime('%d/%m/%y %H:%M', time.localtime(header.GetTimeDateStamp())))
        self._tree.AppendItem(root, 'Number of symbols    : 0x%X' % header.GetNumberOfSymbols())
        self._tree.AppendItem(root, 'Pointer to symbols table : 0x%X' % header.GetPointerToSymbolTable())
        self._tree.AppendItem(root, 'Size of Optional header  : 0x%X' % header.GetSizeOfOptionalHeader())
        charItem = self._tree.AppendItem(root, 'Characteristics      : 0x%X' % header.GetCharacteristics())
        for item in header.GetGetCharacteristicsSrtings():
            self._tree.AppendItem(charItem, item)
            
    def UpdateOptionalHeader(self, root, header):
        self._tree.CollapseAndReset(root)
        self._tree.AppendItem(root, 'Magic                : 0x%X' % header.GetMagic())
        self._tree.AppendItem(root, 'Linker Major Version : 0x%X' % header.GetMajorLinkerVersion())
        self._tree.AppendItem(root, 'Linker Minor Version : 0x%X' % header.GetMinorLinkerVersion())        
        self._tree.AppendItem(root, 'Size of Code         : 0x%X' % header.GetSizeOfCode())
        self._tree.AppendItem(root, 'Size of Initialize   : 0x%X' % header.GetSizeOfInitializedData())
        self._tree.AppendItem(root, 'Size of UnInitialize : 0x%X' % header.GetSizeOfUninitializedData())
        self._tree.AppendItem(root, 'Entry Point          : 0x%X' % header.GetAddressOfEntryPoint())
        self._tree.AppendItem(root, 'Base of Code         : 0x%X' % header.GetBaseOfCode())
        self._tree.AppendItem(root, 'Image Base           : 0x%X' % header.GetImageBase())
        self._tree.AppendItem(root, 'Section Alignment    : 0x%X' % header.GetSectionAlignment())
        self._tree.AppendItem(root, 'File Alignment       : 0x%X' % header.GetFileAlignment())
        self._tree.AppendItem(root, 'MajorOperatingSystemVersion : 0x%X' % header.GetMajorOperatingSystemVersion())
        self._tree.AppendItem(root, 'MinorOperatingSystemVersion : 0x%X' % header.GetMinorOperatingSystemVersion())
        self._tree.AppendItem(root, 'MajorImageVersion    : 0x%X' % header.GetMajorImageVersion())
        self._tree.AppendItem(root, 'MinorImageVersion    : 0x%X' % header.GetMinorImageVersion())
        self._tree.AppendItem(root, 'Image size           : 0x%X' % header.GetSizeOfImage())
        self._tree.AppendItem(root, 'Header size          : 0x%X' % header.GetSizeOfHeaders())
        self._tree.AppendItem(root, 'Subsystem            : 0x%X [%s]' % (header.GetSubsystem(), header.GetSubsystemString()))
        self._tree.AppendItem(root, 'Stack reserve size   : 0x%X' % header.GetSizeOfStackReserve())
        self._tree.AppendItem(root, 'Stack commit size    : 0x%X' % header.GetSizeOfStackCommit())
        self._tree.AppendItem(root, 'Heap reserve size    : 0x%X' % header.GetSizeOfHeapReserve())
        self._tree.AppendItem(root, 'Heap commit size     : 0x%X' % header.GetSizeOfHeapCommit())
        self._tree.AppendItem(root, 'Loader flags         : 0x%X' % header.GetLoaderFlags())
        
        
        self._tree.AppendItem(root, 'NumberOfRvaAndSizes  : 0x%X' % header.GetNumberOfRvaAndSizes())
        dir = header.GetDataDirectory()
        dirItem = self._tree.AppendItem(root, 'DataDirectory')
        index = 0 
        for item in dir:
            str = header.GetDataDirectoryTypeString(index)
            if str == None:
                entryItem = self._tree.AppendItem(dirItem, '[%02d] Vritual Address = 0x%08X,  Size = 0x%08X' % (index, item[0], item[1]))
            else:
                entryItem = self._tree.AppendItem(dirItem, '[%02d %14s] Vritual Address = 0x%08X,  Size = 0x%08X' % (index, str, item[0], item[1]))
            
            value = header.GetParent().GetDirectoryEntryContent(index)
            if value != None:
                rawItem = self._tree.AppendItem(entryItem, 'Entry Raw Data', data=ItemRawData(value[0], value[1]))
                self._tree.SetItemHasChildren(rawItem)
            index += 1
        
    def UpdateSection(self, item, data):
        self._tree.CollapseAndReset(item)
        self._tree.AppendItem(item, 'Virtual Size           : 0x%08X' % data.GetPhysicalAddress())
        self._tree.AppendItem(item, 'Virtual Address        : 0x%08X' % data.GetVirtualAddress())
        self._tree.AppendItem(item, 'Point to Relocation    : 0x%08X' % data.GetPointerToRelocations())
        self._tree.AppendItem(item, 'Number of Relocations  : 0x%08X' % data.GetNumberOfRelocations())
        self._tree.AppendItem(item, 'Point to line number   : 0x%08X' % data.GetPointerToLinenumbers())
        self._tree.AppendItem(item, 'Number of line numbers : 0x%08X' % data.GetNumberOfLinenumbers())
        charItem = self._tree.AppendItem(item, 'Characteristics        : 0x%08X' % data.GetCharacteristics())
        for str in data.GetCharacteristicStrings():
            self._tree.AppendItem(charItem, str)
            
        rawItem   = self._tree.AppendItem(item, "Section Raw Data",
                              data=ItemRawData(data.GetPointerToRawData(), 
                                               data.GetRawData()))
        self._tree.SetItemHasChildren(rawItem)
                
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