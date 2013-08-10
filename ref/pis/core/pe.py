import array
import logging
import uuid

IMAGE_DOS_SIGNATURE             =   0x5A4D
IMAGE_OS2_SIGNATURE             =   0x454E
IMAGE_OS2_SIGNATURE_LE          =   0x454C

IMAGE_NT_SIGNATURE              =   0x00004550  # "PE"

IMAGE_ROM_OPTIONAL_HDR_MAGIC    = 0x107
IMAGE_NT_OPTIONAL_HDR32_MAGIC   = 0x10B
IMAGE_NT_OPTIONAL_HDR64_MAGIC   = 0x20B

IMAGE_FILE_MACHINE_I386     =    0x14c   # Intel 386.
IMAGE_FILE_MACHINE_R3000    =    0x162   # MIPS* little-endian, 0540 big-endian
IMAGE_FILE_MACHINE_R4000    =    0x166   # MIPS* little-endian
IMAGE_FILE_MACHINE_ALPHA    =    0x184   # Alpha_AXP*
IMAGE_FILE_MACHINE_POWERPC  =    0x1F0   # IBM* PowerPC Little-Endian
IMAGE_FILE_MACHINE_TAHOE    =    0x7cc   # Intel EM machine
IMAGE_FILE_MACHINE_IA64     =    0x0200
IMAGE_FILE_MACHINE_EBC      =    0x0EBC
IMAGE_FILE_MACHINE_X64      =    0x8664

EFI_IMAGE_FILE_RELOCS_STRIPPED      =   0x0001  # Relocation info stripped from file.
EFI_IMAGE_FILE_EXECUTABLE_IMAGE     =   0x0002  # File is executable  (i.e. no unresolved externel references).
EFI_IMAGE_FILE_LINE_NUMS_STRIPPED   =   0x0004  # Line nunbers stripped from file.
EFI_IMAGE_FILE_LOCAL_SYMS_STRIPPED  =   0x0008  # Local symbols stripped from file.
EFI_IMAGE_FILE_BYTES_REVERSED_LO    =   0x0080  # Bytes of machine word are reversed.
EFI_IMAGE_FILE_32BIT_MACHINE        =   0x0100  # 32 bit word machine.
EFI_IMAGE_FILE_DEBUG_STRIPPED       =   0x0200  # Debugging info stripped from file in .DBG file
EFI_IMAGE_FILE_SYSTEM               =   0x1000  # System File.
EFI_IMAGE_FILE_DLL                  =   0x2000  # File is a DLL.
EFI_IMAGE_FILE_BYTES_REVERSED_HI    =   0x8000  # Bytes of machine word are reversed.

_machine_mapping = {IMAGE_FILE_MACHINE_I386: "IMAGE_FILE_MACHINE_I386",
                    IMAGE_FILE_MACHINE_R3000: "IMAGE_FILE_MACHINE_R3000",
                    IMAGE_FILE_MACHINE_R4000: "IMAGE_FILE_MACHINE_R4000",
                    IMAGE_FILE_MACHINE_ALPHA: "IMAGE_FILE_MACHINE_ALPHA",
                    IMAGE_FILE_MACHINE_POWERPC: "IMAGE_FILE_MACHINE_POWERPC",
                    IMAGE_FILE_MACHINE_TAHOE: "IMAGE_FILE_MACHINE_TAHOE",
                    IMAGE_FILE_MACHINE_IA64: "IMAGE_FILE_MACHINE_IA64",
                    IMAGE_FILE_MACHINE_EBC: "IMAGE_FILE_MACHINE_EBC",
                    IMAGE_FILE_MACHINE_X64: "IMAGE_FILE_MACHINE_X64"}

EFI_IMAGE_DIRECTORY_ENTRY_EXPORT      = 0
EFI_IMAGE_DIRECTORY_ENTRY_IMPORT      = 1
EFI_IMAGE_DIRECTORY_ENTRY_RESOURCE    = 2
EFI_IMAGE_DIRECTORY_ENTRY_EXCEPTION   = 3
EFI_IMAGE_DIRECTORY_ENTRY_SECURITY    = 4
EFI_IMAGE_DIRECTORY_ENTRY_BASERELOC   = 5
EFI_IMAGE_DIRECTORY_ENTRY_DEBUG       = 6
EFI_IMAGE_DIRECTORY_ENTRY_COPYRIGHT   = 7
EFI_IMAGE_DIRECTORY_ENTRY_GLOBALPTR   = 8
EFI_IMAGE_DIRECTORY_ENTRY_TLS         = 9
EFI_IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG = 10
                 
_data_directory_entry_type_mapping = {EFI_IMAGE_DIRECTORY_ENTRY_EXPORT: 'Export',
                                      EFI_IMAGE_DIRECTORY_ENTRY_IMPORT: 'Import',
                                      EFI_IMAGE_DIRECTORY_ENTRY_RESOURCE: 'Resource',
                                      EFI_IMAGE_DIRECTORY_ENTRY_EXCEPTION: 'Exception',
                                      EFI_IMAGE_DIRECTORY_ENTRY_SECURITY: 'Security',
                                      EFI_IMAGE_DIRECTORY_ENTRY_BASERELOC: 'Base Reloc',
                                      EFI_IMAGE_DIRECTORY_ENTRY_DEBUG: 'debug',
                                      EFI_IMAGE_DIRECTORY_ENTRY_COPYRIGHT: 'CopyRight',
                                      EFI_IMAGE_DIRECTORY_ENTRY_GLOBALPTR: 'Global Pointer',
                                      EFI_IMAGE_DIRECTORY_ENTRY_TLS: 'Tls',
                                      EFI_IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG: 'Load Config'} 
                                      
EFI_IMAGE_SCN_TYPE_NO_PAD             = 0x00000008  # Reserved.
EFI_IMAGE_SCN_CNT_CODE                = 0x00000020
EFI_IMAGE_SCN_CNT_INITIALIZED_DATA    = 0x00000040
EFI_IMAGE_SCN_CNT_UNINITIALIZED_DATA  = 0x00000080

EFI_IMAGE_SCN_LNK_OTHER               = 0x00000100  # Reserved.
EFI_IMAGE_SCN_LNK_INFO                = 0x00000200  # Section contains comments or some other type of information.
EFI_IMAGE_SCN_LNK_REMOVE              = 0x00000800  # Section contents will not become part of image.
EFI_IMAGE_SCN_LNK_COMDAT              = 0x00001000

EFI_IMAGE_SCN_ALIGN_1BYTES            = 0x00100000
EFI_IMAGE_SCN_ALIGN_2BYTES            = 0x00200000
EFI_IMAGE_SCN_ALIGN_4BYTES            = 0x00300000
EFI_IMAGE_SCN_ALIGN_8BYTES            = 0x00400000
EFI_IMAGE_SCN_ALIGN_16BYTES           = 0x00500000
EFI_IMAGE_SCN_ALIGN_32BYTES           = 0x00600000
EFI_IMAGE_SCN_ALIGN_64BYTES           = 0x00700000

EFI_IMAGE_SCN_MEM_DISCARDABLE         = 0x02000000
EFI_IMAGE_SCN_MEM_NOT_CACHED          = 0x04000000
EFI_IMAGE_SCN_MEM_NOT_PAGED           = 0x08000000
EFI_IMAGE_SCN_MEM_SHARED              = 0x10000000
EFI_IMAGE_SCN_MEM_EXECUTE             = 0x20000000
EFI_IMAGE_SCN_MEM_READ                = 0x40000000
EFI_IMAGE_SCN_MEM_WRITE               = 0x80000000

_section_Characteristics_bit_mapping = {EFI_IMAGE_SCN_TYPE_NO_PAD: 'Reserved',
                                        EFI_IMAGE_SCN_CNT_CODE: 'Code Section',
                                        EFI_IMAGE_SCN_CNT_INITIALIZED_DATA: 'Initialized data section',
                                        EFI_IMAGE_SCN_CNT_UNINITIALIZED_DATA: 'Uninitialized data section',
                                        EFI_IMAGE_SCN_LNK_INFO: 'Section contains comments or some other type of information',
                                        EFI_IMAGE_SCN_LNK_REMOVE: 'Section contents will not become part of image',
                                        EFI_IMAGE_SCN_LNK_COMDAT: 'Comdat',
                                        EFI_IMAGE_SCN_ALIGN_1BYTES: 'section align 1 byte',
                                        EFI_IMAGE_SCN_ALIGN_2BYTES: 'section align 2 bytes',
                                        EFI_IMAGE_SCN_ALIGN_4BYTES: 'section align 4 bytes',
                                        EFI_IMAGE_SCN_ALIGN_8BYTES: 'section align 8 bytes',
                                        EFI_IMAGE_SCN_ALIGN_16BYTES: 'section align 16 bytes',
                                        EFI_IMAGE_SCN_ALIGN_32BYTES: 'section align 32 bytes',
                                        EFI_IMAGE_SCN_ALIGN_64BYTES: 'section align 64 bytes',
                                        EFI_IMAGE_SCN_MEM_DISCARDABLE: 'memory discardable',
                                        EFI_IMAGE_SCN_MEM_NOT_CACHED: 'Section cannot be cached',
                                        EFI_IMAGE_SCN_MEM_NOT_PAGED: 'Section is not pageable',
                                        EFI_IMAGE_SCN_MEM_SHARED: 'Section is shared',
                                        EFI_IMAGE_SCN_MEM_EXECUTE: 'Executable section',
                                        EFI_IMAGE_SCN_MEM_READ: 'Readable section',
                                        EFI_IMAGE_SCN_MEM_WRITE: 'Writable section'}

IMAGE_SUBSYSTEM_UNKNOWN = 0
IMAGE_SUBSYSTEM_NATIVE = 1
IMAGE_SUBSYSTEM_WINDOWS_GUI = 2
IMAGE_SUBSYSTEM_WINDOWS_CUI = 3
IMAGE_SUBSYSTEM_WINDOWS_CE_GUI = 4
IMAGE_SUBSYSTEM_OS2_CUI = 5
IMAGE_SUBSYSTEM_POSIX_CUI = 7
IMAGE_SUBSYSTEM_RESERVED8 = 8              
IMAGE_SUBSYSTEM_EFI_APPLICATION         = 10
IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER = 11
IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER      = 12
IMAGE_SUBSYSTEM_EFI_EFI_ROM             = 13              

_image_subsystem_mapping = {IMAGE_SUBSYSTEM_UNKNOWN: 'IMAGE_SUBSYSTEM_UNKNOWN',
                            IMAGE_SUBSYSTEM_NATIVE: 'IMAGE_SUBSYSTEM_NATIVE',
                            IMAGE_SUBSYSTEM_WINDOWS_GUI: 'IMAGE_SUBSYSTEM_WINDOWS_GUI',
                            IMAGE_SUBSYSTEM_WINDOWS_CUI: 'IMAGE_SUBSYSTEM_WINDOWS_CUI',
                            IMAGE_SUBSYSTEM_WINDOWS_CE_GUI: 'IMAGE_SUBSYSTEM_WINDOWS_CE_GUI',
                            IMAGE_SUBSYSTEM_OS2_CUI: 'IMAGE_SUBSYSTEM_OS2_CUI',
                            IMAGE_SUBSYSTEM_POSIX_CUI: 'IMAGE_SUBSYSTEM_POSIX_CUI',
                            IMAGE_SUBSYSTEM_RESERVED8: 'IMAGE_SUBSYSTEM_RESERVED8',
                            IMAGE_SUBSYSTEM_EFI_APPLICATION: 'IMAGE_SUBSYSTEM_EFI_APPLICATION',
                            IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER: 'IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER',
                            IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER: 'IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER',
                            IMAGE_SUBSYSTEM_EFI_EFI_ROM: 'IMAGE_SUBSYSTEM_EFI_EFI_ROM'}
                                                                                     
def GetLogger():
    return logging.getLogger('EFI Binary File')

class PEFile(object):
    """ This class describe PE image layout and provide read/write interface """
    
    def __init__(self, parent = None):
        self._parent         = None
        self._offset         = 0
        self._size           = 0
        self._optionalheader = None
        self._dosheader      = None
        self._imageheader    = None
        self._raw            = array.array('B')
        self._type           = None
        self._sectionheaders = []
        self._dirsraw        = {}
        self._debugentries   = []
        
    def Load(self, fd, size):
        self._offset = fd.tell()
        self._size   = size
        
        # Load Dos Header
        self._dosheader = DosHeader.Read(fd, self)
        
        # Check magic number in dos header
        if self._dosheader.GetMagicNumber() != IMAGE_DOS_SIGNATURE: #'MZ'
            GetLogger().warning("Invalid Image magic number: 0x%X!" % self._dosheader.GetMagicNumber())
            return
            
        # Check "PE" signature    
        fd.seek(self._offset + self._dosheader.GetPeHeaderOffset())
        signature = array.array('L')
        signature.fromfile(fd, 1)
        if signature.tolist()[0] != IMAGE_NT_SIGNATURE: #PE
            GetLogger().warning('Invalid PE signature: 0x%X' % signature.tolist()[0])
            return
            
        # Load image header
        self._imageheader = ImageHeader.Read(fd, self)
        optionalsize = self._imageheader.GetSizeOfOptionalHeader()
        if optionalsize > 0:
            #check magic of optional header
            tempindex = fd.tell()
            temparr   = array.array('H')
            temparr.fromfile(fd, 1)
            magic     = temparr[0]
            fd.seek(tempindex)
            
            if magic == IMAGE_ROM_OPTIONAL_HDR_MAGIC:
                print 'Rom image'
                self._type = 'IMAGE_ROM_OPTIONAL_HDR_MAGIC'
                return
            elif magic == IMAGE_NT_OPTIONAL_HDR32_MAGIC:
                self._optionalheader = ImageOptionalHeader32(optionalsize, self)
                self._optionalheader.Load(fd)
                self._type = 'IMAGE_NT_OPTIONAL_HDR32_MAGIC'
            elif magic == IMAGE_NT_OPTIONAL_HDR64_MAGIC:
                # Load optional image header
                self._optionalheader = ImageOptionalHeader64(optionalsize, self)
                self._optionalheader.Load(fd)
                self._type = 'IMAGE_NT_OPTIONAL_HDR64_MAGIC'
            else:
                GetLogger().error("Invalid magic number 0x%X!" % magic)
                fd.seek(self._offset)
                self._raw.fromfile(fd, size)                
                return
                
        # Read sections
        index = 0
        while (index < self._imageheader.GetNumberOfSections()):
            sectionheader = ImageSectionHeader.Read(fd, self)
            self._sectionheaders.append(sectionheader)
            index += 1
        
        fd.seek(self._offset)
        self._raw.fromfile(fd, size)
        
        # retrieve raw data for all valid directory entry
        dirs = self._optionalheader.GetDataDirectory()
        index = 0
        for entry, size in dirs:
            if size != 0: 
                for sec in self._sectionheaders:
                    if (entry >= sec.GetVirtualAddress()) and \
                       (entry < sec.GetVirtualAddress() + sec.GetPhysicalAddress()):
                        break
                addr = entry - sec.GetVirtualAddress() + sec.GetPointerToRawData()
                print 'addr = 0x%X' % addr
                fd.seek(addr)
                if index == 6:
                    count = 0
                    tempindex = fd.tell()
                    while count < size:
                        item = ImageDebugDirectory.Read(fd, self)
                        self._debugentries.append(item)
                        count += item.GetSize()
                    fd.seek(tempindex)
                arr = array.array('B')
                arr.fromfile(fd, size)
                self._dirsraw[index] = (addr, arr.tolist())
            index += 1     
        
    def GetDirectoryEntryContent(self, index):
        if index not in self._dirsraw.keys():
            return None
        return self._dirsraw[index]
        
    def GetSize(self):
        return self._size
        
    def GetDosHeader(self):
        return self._dosheader
    
    def GetImageHeader(self):
        return self._imageheader
        
    def GetImageOptionalHeader(self):
        return self._optionalheader
        
    def GetSectionHeaders(self):
        return self._sectionheaders
        
    def GetRawData(self):
        return self._raw.tolist()
        
    def GetDebugSection(self):
        return self._debugentries
        
    def Dump(self):
        import time
        print '=============================================================='
        print 'Machine            :  0x%X' % self._imageheader.GetMachine()
        print 'Number of sections :  0x%X' % self._imageheader.GetNumberOfSections()
        print 'TimeDateStamp      :  %s' % time.strftime( '%d/%m/%y %H:%M', time.localtime(self._imageheader.GetTimeDateStamp()))
        print 'Pointer To Symbols :  0x%X' % self._imageheader.GetPointerToSymbolTable()
        print 'Number of symbols  :  0x%X' % self._imageheader.GetNumberOfSymbols()
        print 'Size of optional   :  0x%X' % self._imageheader.GetSizeOfOptionalHeader()
        print 'Characteristics    :  0x%X' % self._imageheader.GetCharacteristics()
        if self._optionalheader != None:
            print 'Magic              :  0x%X' % self._optionalheader.GetMagic()
            print 'Linker Major Version: 0x%X' % self._optionalheader.GetMajorLinkerVersion()
            print 'Linker Minor Version: 0x%X' % self._optionalheader.GetMinorLinkerVersion()
            print 'Size of Code       :  0x%X' % self._optionalheader.GetSizeOfCode()
            print 'Size of Initialize :  0x%X' % self._optionalheader.GetSizeOfInitializedData()
            print 'Size of UnInitialize: 0x%X' % self._optionalheader.GetSizeOfUninitializedData()
            print 'Entry Point        :  0x%X' % self._optionalheader.GetAddressOfEntryPoint()
            print 'Base of Code       :  0x%X' % self._optionalheader.GetBaseOfCode()
            print 'Image Base         :  0x%X' % self._optionalheader.GetImageBase()
            print 'Section Alignment  :  0x%X' % self._optionalheader.GetSectionAlignment()
            print 'File Alignment     :  0x%X' % self._optionalheader.GetFileAlignment()
            print 'NumberOfRvaAndSizes:  0x%X' % self._optionalheader.GetNumberOfRvaAndSizes()
            count = 0
            for item in self._optionalheader.GetDataDirectory():
                print 'Data Entry[%d] Virtual Address = 0x%X, Size = 0x%X' % (count, item[0], item[1])
                count += 1 
            
class BinaryItem(object):
    def __init__(self, parent=None):
        self._size = 0
        self._arr  = array.array('B')
        self._parent = parent
        
    @classmethod
    def Read(cls, fd, parent=None):
        item = cls(parent)
        item.fromfile(fd)
        return item
    
    def Load(self, fd):
        self.fromfile(fd)
        
    def GetSize(self):
        """should be implemented by inherited class"""
        
    def fromfile(self, fd):
        self._arr.fromfile(fd, self.GetSize())
        
    def GetParent(self):
        return self._parent
                    
class DosHeader(BinaryItem):
    def GetSize(self):
        return 62
    
    def GetMagicNumber(self):
        list = self._arr.tolist()
        return list2int(list[0:2])
    
    def GetMagicString(self):
        list = self._arr.tolist()
        str = chr(list[0])
        str += chr(list[1])
        return str
        
    def GetPeHeaderOffset(self):
        list = self._arr.tolist()
        return list2int(list[60:62])
    
class ImageHeader(BinaryItem):
    def GetSize(self):
        return 20
                    
    def GetMachine(self):
        list = self._arr.tolist()
        return list2int(list[0:2])
    
    def GetMachineString(self):
        machine = self.GetMachine()
        if machine in _machine_mapping.keys():
            return _machine_mapping[machine]
            
        return "UNKNOWN_MACHINE"
        
    def GetNumberOfSections(self):
        list = self._arr.tolist()
        return list2int(list[2:4])
    
    def GetTimeDateStamp(self):
        list = self._arr.tolist()
        return list2int(list[4:8])
    
    def GetPointerToSymbolTable(self):
        list = self._arr.tolist()
        return list2int(list[8:12])
    
    def GetNumberOfSymbols(self):
        list = self._arr.tolist()
        return list2int(list[12:16])
    
    def GetSizeOfOptionalHeader(self):
        list = self._arr.tolist()
        return list2int(list[16:18])
    
    def GetCharacteristics(self):
        list = self._arr.tolist()
        return list2int(list[18:20])
    
    def GetGetCharacteristicsSrtings(self):
        char = self.GetCharacteristics()
        list = []
        if char & EFI_IMAGE_FILE_RELOCS_STRIPPED > 0:
            list.append('EFI_IMAGE_FILE_RELOCS_STRIPPED: No relocation information')
        if char & EFI_IMAGE_FILE_EXECUTABLE_IMAGE > 0:
            list.append('EFI_IMAGE_FILE_EXECUTABLE_IMAGE: Executable')
        if char & EFI_IMAGE_FILE_LINE_NUMS_STRIPPED > 0:
            list.append('EFI_IMAGE_FILE_LINE_NUMS_STRIPPED: No line number information')
        if char & EFI_IMAGE_FILE_LOCAL_SYMS_STRIPPED > 0:
            list.append('EFI_IMAGE_FILE_LOCAL_SYMS_STRIPPED: No local symbol information')
        if char & EFI_IMAGE_FILE_BYTES_REVERSED_LO > 0:
            list.append('EFI_IMAGE_FILE_BYTES_REVERSED_LO: Bytes of machine is reversed')
        if char & EFI_IMAGE_FILE_32BIT_MACHINE > 0:
            list.append('EFI_IMAGE_FILE_32BIT_MACHINE: 32-bit machine')
        if char & EFI_IMAGE_FILE_DEBUG_STRIPPED > 0:
            list.append('EFI_IMAGE_FILE_DEBUG_STRIPPED: No debug information')
        if char & EFI_IMAGE_FILE_SYSTEM > 0:
            list.append('EFI_IMAGE_FILE_SYSTEM: System File')
        if char & EFI_IMAGE_FILE_DLL> 0:
            list.append('EFI_IMAGE_FILE_DLL: DLL')
        if char & EFI_IMAGE_FILE_BYTES_REVERSED_HI > 0:
            list.append('EFI_IMAGE_FILE_BYTES_REVERSED_HI: Bytes of machine is reversed')
            
        if len(list) == 0:
            list.append('Unknown Characteristics')
            
        return list

class ImageOptionalHeader32(BinaryItem):
    def __init__(self, size, parent=None):
        BinaryItem.__init__(self, parent)
        self._size = size

    def GetSize(self):
        return self._size
    
    def GetMagic(self):
        list = self._arr.tolist()
        return list2int(list[0:2])
    
    def GetMajorLinkerVersion(self):
        list = self._arr.tolist()
        return int(list[2])
    
    def GetMinorLinkerVersion(self):
        list = self._arr.tolist()
        return int(list[3])
    
    def GetSizeOfCode(self):
        list = self._arr.tolist()
        return list2int(list[4:8])
        
    def GetSizeOfInitializedData(self):
        list = self._arr.tolist()
        return list2int(list[8:12])

    def GetSizeOfUninitializedData(self):
        list = self._arr.tolist()
        return list2int(list[12:16])

    def GetAddressOfEntryPoint(self):
        list = self._arr.tolist()
        return list2int(list[16:20])
    
    def GetBaseOfCode(self):
        list = self._arr.tolist()
        return list2int(list[20:24])    
        
    def GetBaseOfData(self):
        list = self._arr.tolist()
        return list2int(list[24:28])    
        
    def GetImageBase(self):
        list = self._arr.tolist()
        return list2int(list[28:32])    

    def GetSectionAlignment(self):
        list = self._arr.tolist()
        return list2int(list[32:36])    
            
    def GetFileAlignment(self):
        list = self._arr.tolist()
        return list2int(list[36:40])
        
    def GetMajorOperatingSystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[40:42])
        
    def GetMinorOperatingSystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[42:44])        
                
    def GetMajorImageVersion(self):
        list = self._arr.tolist()
        return list2int(list[44:46])        
        
    def GetMinorImageVersion(self):
        list = self._arr.tolist()
        return list2int(list[46:48])        
        
    def GetMajorSubsystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[48:50])        
        
    def GetMinorSubsystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[50:52])        
        
    def GetWin32VersionValue(self):
        list = self._arr.tolist()
        return list2int(list[52:56])        
    
    def GetSizeOfImage(self):
        list = self._arr.tolist()
        return list2int(list[56:60])        
            
    def GetSizeOfHeaders(self):
        list = self._arr.tolist()
        return list2int(list[60:64])        
        
    def GetCheckSum(self):
        list = self._arr.tolist()
        return list2int(list[64:68])        
        
    def GetSubsystem(self):
        list = self._arr.tolist()
        return list2int(list[68:70])        
        
    def GetSubsystemString(self):
        value = self.GetSubsystem()
        if value not in _image_subsystem_mapping.keys():
            return 'Unknown'
        return _image_subsystem_mapping[value]
        
    def GetDllCharacteristics(self):
        list = self._arr.tolist()
        return list2int(list[70:72])
    
    def GetSizeOfStackReserve(self):
        list = self._arr.tolist()
        return list2int(list[72:76])
        
    def GetSizeOfStackCommit(self):
        list = self._arr.tolist()
        return list2int(list[76:80])
        
    def GetSizeOfHeapReserve(self):
        list = self._arr.tolist()
        return list2int(list[80:84])
        
    def GetSizeOfHeapCommit(self):
        list = self._arr.tolist()
        return list2int(list[84:88])
        
    def GetLoaderFlags(self):
        list = self._arr.tolist()
        return list2int(list[88:92])
        
    def GetNumberOfRvaAndSizes(self):
        list = self._arr.tolist()
        return list2int(list[92:96])
        
    def GetDataDirectory(self):
        index  = 96
        list   = self._arr.tolist()
        dirs   = []
        while (index + 8 <= self.GetSize()):
            virtualaddr = list2int(list[index:index+4])
            size        = list2int(list[index+4:index+8])
            dirs.append((virtualaddr, size))
            index += 8
        
        return dirs
        
    def GetDataDirectoryTypeString(self, index):
        if index not in _data_directory_entry_type_mapping.keys():
            return None
        
        return _data_directory_entry_type_mapping[index]
        
class ImageOptionalHeader64(BinaryItem):
    def __init__(self, size, parent=None):
        BinaryItem.__init__(self, parent)
        self._size = size

    def GetSize(self):
        return self._size
    
    def GetMagic(self):
        list = self._arr.tolist()
        return list2int(list[0:2])
    
    def GetMajorLinkerVersion(self):
        list = self._arr.tolist()
        return int(list[2])
    
    def GetMinorLinkerVersion(self):
        list = self._arr.tolist()
        return int(list[3])
    
    def GetSizeOfCode(self):
        list = self._arr.tolist()
        return list2int(list[4:8])
        
    def GetSizeOfInitializedData(self):
        list = self._arr.tolist()
        return list2int(list[8:12])

    def GetSizeOfUninitializedData(self):
        list = self._arr.tolist()
        return list2int(list[12:16])

    def GetAddressOfEntryPoint(self):
        list = self._arr.tolist()
        return list2int(list[16:20])
    
    def GetBaseOfCode(self):
        list = self._arr.tolist()
        return list2int(list[20:24])    
        
    def GetImageBase(self):
        list = self._arr.tolist()
        return list2int(list[24:32])    
        
    def GetSectionAlignment(self):
        list = self._arr.tolist()
        return list2int(list[32:36])   
    
    def GetFileAlignment(self): 
        list = self._arr.tolist()
        return list2int(list[36:40])   
        
    def GetMajorOperatingSystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[40:42])   

    def GetMinorOperatingSystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[42:44])   
        
    def GetMajorImageVersion(self):
        list = self._arr.tolist()
        return list2int(list[44:46])   
        
    def GetMinorImageVersion(self):
        list = self._arr.tolist()
        return list2int(list[46:48])   
        
    def GetMajorSubsystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[48:50])   
        
    def GetMinorSubsystemVersion(self):
        list = self._arr.tolist()
        return list2int(list[50:52])   
        
    def GetWin32VersionValue(self):
        list = self._arr.tolist()
        return list2int(list[52:56])   
        
    def GetSizeOfImage(self):
        list = self._arr.tolist()
        return list2int(list[56:60])   
        
    def GetSizeOfHeaders(self):
        list = self._arr.tolist()
        return list2int(list[60:64])   
        
    def GetCheckSum(self):
        list = self._arr.tolist()
        return list2int(list[64:68])   
        
    def GetSubsystem(self):
        list = self._arr.tolist()
        return list2int(list[68:70])   
        
    def GetSubsystemString(self):
        value = self.GetSubsystem()
        if value not in _image_subsystem_mapping.keys():
            return 'Unknown'
        return _image_subsystem_mapping[value]
                
    def GetDllCharacteristics(self):
        list = self._arr.tolist()
        return list2int(list[70:72])   
        
    def GetSizeOfStackReserve(self):
        list = self._arr.tolist()
        return list2int(list[72:80])   
        
    def GetSizeOfStackCommit(self):
        list = self._arr.tolist()
        return list2int(list[80:88])   
        
    def GetSizeOfHeapReserve(self):
        list = self._arr.tolist()
        return list2int(list[88:96])   
        
    def GetSizeOfHeapCommit(self):
        list = self._arr.tolist()
        return list2int(list[96:104])   
        
    def GetLoaderFlags(self):
        list = self._arr.tolist()
        return list2int(list[104:108])   
            
    def GetNumberOfRvaAndSizes(self):
        list = self._arr.tolist()
        return list2int(list[108:112])           
    
    def GetDataDirectory(self):
        index  = 112
        list   = self._arr.tolist()
        dirs   = []
        while (index + 8 <= self.GetSize()):
            virtualaddr = list2int(list[index:index+4])
            size        = list2int(list[index+4:index+8])
            dirs.append((virtualaddr, size))
            index += 8
            
        return dirs
        
    def GetDataDirectoryTypeString(self, index):
        if index not in _data_directory_entry_type_mapping.keys():
            return None
        
        return _data_directory_entry_type_mapping[index]
class ImageSectionHeader(BinaryItem):
    def __init__(self, parent=None):
        BinaryItem.__init__(self, parent)
        self._content = array.array('B')
        
    def GetSize(self):
        return 40
        
    def GetShortName(self):
        list = self._arr.tolist()
        name = ''
        for index in range(0, 8):
            if list[index] == 0: break
            name += chr(list[index])
        return name
        
    def GetPhysicalAddress(self):
        list = self._arr.tolist()
        return list2int(list[8:12])
        
    def GetVirtualAddress(self):
        list = self._arr.tolist()
        return list2int(list[12:16])

    def GetSizeOfRawData(self):
        list = self._arr.tolist()
        return list2int(list[16:20])
        
    def GetPointerToRawData(self):
        list = self._arr.tolist()
        return list2int(list[20:24])
        
    def GetPointerToRelocations(self):
        list = self._arr.tolist()
        return list2int(list[24:28])
    
    def GetPointerToLinenumbers(self):
        list = self._arr.tolist()
        return list2int(list[28:32])
        
    def GetNumberOfRelocations(self):
        list = self._arr.tolist()
        return list2int(list[32:34])

    def GetNumberOfLinenumbers(self):
        list = self._arr.tolist()
        return list2int(list[34:36])
        
    def GetCharacteristics(self):
        list = self._arr.tolist()
        return list2int(list[36:40])
        
    def GetCharacteristicStrings(self):
        value = self.GetCharacteristics()
        ret = []
        for key in _section_Characteristics_bit_mapping.keys():
            if value & key > 0:
                ret.append(_section_Characteristics_bit_mapping[key])
                
        return ret
        
    def fromfile(self, fd):
        BinaryItem.fromfile(self, fd)
        oldoffset = fd.tell()
        size = self.GetSizeOfRawData()
        if size == 0: return
        fd.seek(self.GetPointerToRawData())
        self._content.fromfile(fd, size)
        fd.seek(oldoffset)   
                
    def GetRawData(self):
        return self._content.tolist()
        
    def Dump(self):
        print 'Section name        : ', self.GetShortName()
        print 'Pointer to Raw data : 0x%X' % self.GetPointerToRawData()
        print 'Physical Address    : 0x%X' % self.GetPhysicalAddress()
        print 'Virtual Address     : 0x%X' % self.GetVirtualAddress()
        print 'Size of Raw data    : 0x%X' % self.GetSizeOfRawData()
        print 'Pointer to Relocate : 0x%X' % self.GetPointerToRelocations()
        print 'Pointer to linenum  : 0x%X' % self.GetPointerToLinenumbers()
        print 'Number of Lines     : 0x%X' % self.GetNumberOfLinenumbers()
        print 'Number of Relocate  : 0x%X' % self.GetNumberOfRelocations()
        
class ImageDebugDirectory(BinaryItem):
    def __init__(self, parent=None):
        BinaryItem.__init__(self, parent)
        self._content = array.array('B')
            
    def GetSize(self):
        return 28
    
    def GetCharacteristics(self):
        list = self._arr.tolist()
        return list2int(list[0:4])
        
    def GetTimeDateStamp(self):
        list = self._arr.tolist()
        return list2int(list[4:8])

    def GetMajorVersion(self):
        list = self._arr.tolist()
        return list2int(list[8:10])
        
    def GetMinorVersion(self):
        list = self._arr.tolist()
        return list2int(list[8:12])
        
    def GetType(self):
        list = self._arr.tolist()
        return list2int(list[12:16])
    
    def GetSizeOfData(self):
        list = self._arr.tolist()
        return list2int(list[16:20])
        
    def GetAddressOfRawData(self):
        list = self._arr.tolist()
        return list2int(list[20:24])
        
    def GetPointerToRawData(self):
        list = self._arr.tolist()
        return list2int(list[24:28])
        
    def fromfile(self, fd):
        BinaryItem.fromfile(self, fd)
        oldoffset = fd.tell()
        size = self.GetSizeOfData()
        if size == 0: return
        if size > self.GetParent().GetSize():
            GetLogger().warning('Invalid debug directory entry size: 0x%X' % size)
            return
        fd.seek(self.GetPointerToRawData())
        self._content.fromfile(fd, size)
        fd.seek(oldoffset)
                
    def GetRawData(self):
        return self._content.tolist()
        
def list2guid(list):
    val1 = list2int(list[0:4])
    val2 = list2int(list[4:6])
    val3 = list2int(list[6:8])
    val4 = 0
    for item in list[8:16]:
        val4 = (val4 << 8) | int(item)
        
    val  = val1 << 12 * 8 | val2 << 10 * 8 | val3 << 8 * 8 | val4
    guid = uuid.UUID(int=val)
    return guid
        
def list2int(list):
    val = 0
    for index in range(len(list) - 1, -1, -1):
        val = (val << 8) | int(list[index])
    return val
    
def align(value, alignment):
    return (value + ((alignment - value) & (alignment - 1)))
    
gInvalidGuid = uuid.UUID(int=0xffffffffffffffffffffffffffffffff)    
def isValidGuid(guid):
    if guid == gInvalidGuid:
        return False
    return True    