import array
import comtypes
from comtypes.automation import VARIANT
from distorm import Decode, Decode16Bits, Decode32Bits, Decode64Bits
 
REG_TABLE = [
# General Registers             
u'eax', u'ebx', u'ecx', u'edx', u'esi', u'edi', u'esp', u'ebp',
# Instruction Pointer and Flags Register
u'eip', u'eflags',
# Control Register
u'cr0', u'cr2', u'cr3', u'cr4',
# System Address Registers
u'gdtbas', u'gdtlim', u'ldtr', u'ldtbas', u'ldtlim', u'ldtar', u'idtbas', u'idtlim',
u'tr', u'tssbas', u'tsslim', u'tssar',
# Segment Registers
u'cs', u'csbas', u'cslim', u'csar', u'csas', u'ss', u'ssbas', u'sslim', 
u'ssar', u'ssas', u'ds', u'dsbas', u'dslim', u'dsar', u'dsas', u'es', u'esbas',
u'eslim', u'esar', u'esas', u'fs', u'fsbas', u'fslim', u'fsar', u'fsas', u'gs',
u'gsbas', u'gslim', u'gsar', u'gsas',
# mmx register
u'mm0', u'mm1', u'mm2', u'mm3', u'mm4', u'mm5', u'mm6', u'mm7',
# SSE  register
u'xmm0', u'xmm1', u'xmm2', u'xmm3', u'xmm4', u'xmm5', u'xmm6', u'xmm7',
# Debug Registers
u'dr0', u'dr1', u'dr2', u'dr3', u'dr6', u'dr7',
]

REG_NON_REAL = [
# mmx register
u'mm0', u'mm1', u'mm2', u'mm3', u'mm4', u'mm5', u'mm6', u'mm7',
# SSE  register
u'xmm0', u'xmm1', u'xmm2', u'xmm3', u'xmm4', u'xmm5', u'xmm6', u'xmm7',
# Debug Registers
u'dr0', u'dr1', u'dr2', u'dr3', u'dr6', u'dr7',
]
class ITPApiCOM:
    """
    ITP API COM class manage all interface provide by COM 'ApiItpProgID.1' 
    """
    API_PROGID          = "ApiItpProgID.1"
    CONFIG_PROGID       = "ItpConfig.ItpConfig.1"
    BREAKPOINT_PROGID   = "ItpBreakpoint.ItpBreakpoint.1"
    
    def __init__(self):
        self._itpApiObj    = None
        self._itpConfigObj = None
        self._oldmode      = None
        self._itpBreakPointObj = None
        
    def ConnectITP(self):
        """
        Connect ITP COM
        """
        if not self.IsNeedReconnect():
            return True
        
        try:
            self._itpApiObj = comtypes.client.CreateObject(self.API_PROGID)
        except:
            return False
        
        try:
            self._itpConfigObj = comtypes.client.CreateObject(self.CONFIG_PROGID)
        except:
            return False
       
        try:
            self._itpBreakPointObj = comtypes.client.CreateObject(self.BREAKPOINT_PROGID)
        except:
            return False
        
        return True

    def IsITPReady(self):
        ret = False
        if self._itpApiObj == None:
            return False
        try:
            ret = self._itpApiObj.IsItpReady()
        except:
            self._itpApiObj    = None
            self._itpConfigObj = None
            return False
        return ret

    def IsNeedReconnect(self):
        if self._itpApiObj == None:
            return True
        return False

    def GetTargetPowerStatus(self, c_uiDID=0):
        """
         Get target power status.
        
         @param c_uiDID      Target processor device ID
        """        
        if not self.IsITPReady():
            return None      
        return self._itpApiObj.get_Status(c_uiDID, u'power')  
    
    def GetTargetProcessorStatus(self, c_uiDID=0):
        """
         Get target processor status.
        
         @param c_uiDID      Target processor device ID
        """     
        if not self.IsITPReady():
            return None
     
        return self._itpApiObj.get_Status(c_uiDID, u'processor')  
    
    def GetTargetResetStatus(self, c_uiDID=0): 
        """
         Get target reset status.
        
         @param c_uiDID      Target processor device ID
        """     
        if not self.IsITPReady():
            return None      
        return self._itpApiObj.get_Status(c_uiDID, u'reset')
                        
    def Go(self, c_uiDID=0, c_uiOption=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_uiOption  Action applies to all processor. 1 mean all target.
        """
        if not self.IsITPReady():
            return
        ret = self._itpApiObj.Go(c_uiDID, c_uiOption)
        
    def Reset(self, bsType="target"):
        """
        Type of reset to perform. Currently, only "target" is supported.
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Reset(bsType)
        
    def Halt(self, c_uiDID=0, c_uiOption=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_uiOption  If it is 1 then the action applies to all processor
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Halt(c_uiDID, c_uiOption)
        
    def StepInto(self, c_uiDID=0, c_ulCount=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_ulCount   Specifies number of times to perform step
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Step(c_uiDID, u'into', c_ulCount)       
        
    def StepOver(self, c_uiDID=0, c_ulCount=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_ulCount   Specifies number of times to perform step
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Step(c_uiDID, u'over', c_ulCount)
        
    def StepOut(self, c_uiDID=0, c_ulCount=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_ulCount   Specifies number of times to perform step
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Step(c_uiDID, u'out', c_ulCount) 
        
    def StepBranch(self, c_uiDID=0, c_ulCount=1):
        """
        @param c_uiDID     Target processor device identifier
        @param c_ulCount   Specifies number of times to perform step
        """
        if not self.IsITPReady():
            return
        self._itpApiObj.Step(c_uiDID, u'branch', c_ulCount)                        
        
    def GetAllRegisterValue(self, c_uiDID=0):
        """
        @param c_uiDID     Target processor device identifier
        """        
        dict = {}
        if not self.IsITPReady():
            return None
        #value = self._itpApiObj.get_Memory(0, 32, 200, 0xffff0000, u'IA32_PHY_PTR', 0, 0)
        #print value
        for reg in REG_TABLE:
            dict[reg] = self.GetRegisterValue(c_uiDID, reg)
            
        return dict
    
    def GetRegisterValue(self, c_uiDID, regname):
        cr0_value_arr = self._itpApiObj.get_Register(c_uiDID, 'cr0')
        cr0_value = ConvertByteArrayToInt(cr0_value_arr)
        if cr0_value[0] & 0x01 == 0:     
            if regname in REG_NON_REAL:
                return 0, 0
        value = self._itpApiObj.get_Register(c_uiDID, regname)
        return ConvertByteArrayToInt(value)
    
    def PutRegisterValue(self, c_uiDID, regname, value, length):
        ba = ConvertToByteArray(value, length)
        try:
            self._itpApiObj.put_Register(c_uiDID, regname, ba)
        except:
            return False
        return True
            
    def DoesSupportBreakPointType(self, name):
        if self._itpBreakPointObj == None:
            return False
        #for item in self._bpCapa:
        #    if name.lower() == item[0].lower():
        #        return True
        #return False
        return True
    
    def PutHardwareBreakPointer(self, index, addr, active=1, c_uiDID=0, privmask=0, slot=0,  
                                breaktype=u'Hardware', behavior=u'Execution', addrtype=u'IA32_PHY_PTR', dtsel=0, segsel=0, addrmask=0xffffffff):
        if self._itpBreakPointObj == None:
            return None
        
        if not self.DoesSupportBreakPointType('Hardware execution breakpoint'):
            return False
        
        #arr = [[VARIANT(0), VARIANT(1), ConvertToByteArray(addr, 8), VARIANT(1)]]
        
        arr = array.array('b')
        arr.fromlist([0L])
        bps = self._itpBreakPointObj.ReadBp(arr)
        print bps
        t = VARIANT()
        t.vt = comtypes.automation.VT_EMPTY
        t2 = VARIANT()
        t2.vt = comtypes.automation.VT_INT
        print self._itpBreakPointObj.QueryBpTypes(arr, 0x00000000L)
        self._itpBreakPointObj.WriteBp(bps)
        #arr = [0, 4, [segsel, ConvertToByteArray1(addr, 8), 0], 1]
        #try:
        #    arr = [[0, [5, 0], [segsel, addr, 0], 1]]
        #    self._itpBreakPointObj.WriteBp(arr)
        #except comtypes.COMError, hresult:
        #    print hresult
        #    return
        """
        self._itpApiObj.put_BreakPoint(c_uiDID, 
                                       breaktype, 
                                       index, 
                                       privmask, 
                                       slot, 
                                       True, 
                                       behavior, 
                                       ConvertToByteArray(addr, 8), 
                                       addrtype,
                                       ConvertToByteArray(dtsel, 2), 
                                       ConvertToByteArray(segsel, 2),
                                       0)
        """
        
    def IsRealMode(self, c_uiDID=0):
        cr0_value = self.GetRegisterValue(c_uiDID, 'cr0')
        if cr0_value[0] & 0x01 == 0:
            return True
        return False

    def QueryBpCapabilities(self, c_uiDID=0):
        return self._itpBreakPointObj.QueryBpCapabilities(0)
     
    def GetMemory(self, addr, c_uiDID=0, width=1, count=128, addrType='IA32_PHY_PTR', dtSel=0, segSel=0):
        num = count
        if self.IsRealMode(c_uiDID):
            if (addr + count) > 0xfffff:
                num = 0xfffff - addr
            self._oldmode = 'real'
        else:
            if self._oldmode == 'real':
                self._oldmode = 'protect'
                return None
        return self._itpApiObj.get_Memory(c_uiDID, width, num, 
                                          ConvertToByteArray(addr, 8), 
                                          addrType, 
                                          ConvertToByteArray(dtSel, 2), 
                                          ConvertToByteArray(segSel, 2))
  
    def GetNumberOfDevices(self):
        return self._itpApiObj.get_ControlVariable(0, 'num_devices')
    
    def GetLastError(self):
        return self._itpConfigObj.get_LastError()
    
    def PutMessage(self, text):
        self._itpApiObj.put_Message(text)
        
    def GetDiasm(self, c_uiDID=0):
        eip, length = self.GetRegisterValue(c_uiDID, 'eip')
        cr0_value = self.GetRegisterValue(c_uiDID, 'cr0')
        if cr0_value[0] & 0x01 == 0:
            # real mode
            cs_value = self.GetRegisterValue(c_uiDID, 'cs')
            eip += cs_value[0] << 4

        import array
        arr = array.array('B')
        bytes = self.GetMemory(eip, addrType='IA32_PHY_PTR', count=0x40)
        if bytes == None:
            return None
        
        for byte in bytes:
            arr.append(byte)

        return Decode(eip, arr, Decode16Bits)
        
def ConvertToByteArray(value, size):
    """
    Convert value to COM's VARIANT byte array
    """
    list = []
    temp = value
    for index in range(size):
        list.append(temp & 0xff)
        temp = temp >> 8
    arr = array.array('B')
    arr.fromlist(list)
    return VARIANT(arr)

def ConvertToByteArray1(value, size):
    """
    Convert value to COM's VARIANT byte array
    """
    list = []
    temp = value
    for index in range(size):
        list.append(temp & 0xff)
        temp = temp >> 8
    arr = array.array('B')
    arr.fromlist(list)
    return arr

def ConvertByteArrayToInt(list):
    length = len(list)
    value  = 0
    for index in range(length):
        value += list[index] << (8 * index)
    return value, length