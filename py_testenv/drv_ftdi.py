#########################FTDI I2C driver python3#####################
#   yfzhao
#   20250224
#   add FTDI i2c port switch
#   rebuild FTDI driver @python3
#   NOTE, higher speed of i2c xmit limite by FTDI_usb buffer size;
#   4KB buffer too small to put all IO ctrl data into it!!
#
#   20250804 yfzhao, build python3 fdit driver to python package
#
#########################FTDI I2C driver python3#####################
import datetime
import ctypes
from ctypes.util import find_library
import time
from pathlib import Path

# 加载ftd2xx.dll
ftd2xx = ctypes.windll.ftd2xx

# 加载libMPSSE.dll, x64 PC
#libmpsse = ctypes.CDLL("../libMPSSE.dll")
#libmpsse = ctypes.CDLL("./libMPSSE.dll")      #if use vscode
#libmpsse = ctypes.windll.libMPSSE

# 修改DLL加载逻辑（替换原来的CDLL调用）
dll_path = Path(__file__).parent / "libMPSSE.dll"
libmpsse = ctypes.CDLL(str(dll_path))


########Var deine#######
FT_OK = 0
FT_OPEN_BY_SERIAL_NUMBER = 1

AddLen10Bit = ctypes.c_bool(False)  # 使用 7 位地址

FT_W = ctypes.c_bool(False)  # 写操作
FT_R = ctypes.c_bool(True)  # read

# 传输选项：
# 在传输开始时生成START信号
I2C_TRANSFER_OPTIONS_START_BIT = 0x01
# 在传输结束时生成STOP信号
I2C_TRANSFER_OPTIONS_STOP_BIT = 0x02
# 如果从设备返回NACK，则立即停止传输
I2C_TRANSFER_OPTIONS_BREAK_ON_NACK = 0x04
# 启用快速传输模式（按字节传输）
#######copy from ftdi_i2c.c
# This function generates the START, ADDRESS, DATA(write) & STOP
#   phases in the I2C bus without having delays between these phases
I2C_TRANSFER_OPTIONS_FAST_TRANSFER_BYTES = 0x08
I2C_TRANSFER_OPTIONS_FAST_TRANSFER = 0x30

#use in i2c channel config
class ChannelConfig(ctypes.Structure):
    _fields_ = [
        ("ClockRate", ctypes.c_uint32),  # I2C时钟速率
        ("LatencyTimer", ctypes.c_uint8),  # 延迟计时器
        ("Options", ctypes.c_uint32)  # 配置选项
    ]

#use in FTDI find function
class FT_DEVICE_LIST_INFO_NODE(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
        ("ID", ctypes.c_ulong),
        ("LocId", ctypes.c_ulong),
        ("SerialNumber", ctypes.c_char * 16),
        ("Description", ctypes.c_char * 64),
        ("ftHandle", ctypes.c_void_p),
    ]

class DrvFTDI:
    def __init__(
        self,
        i2c_port=0,  #FTDI default i2c port
        chip_addr=0x58,
        ):
        self.aves_write = False                             # define if write to AVES script
        self.i2c_port = i2c_port                            #FTDI i2c port sel 0/1
        self.chip_addr=ctypes.c_uint32(chip_addr)           #
        self.handle = ctypes.c_void_p()                     #pointer to USB device?
        self.device_list = FT_DEVICE_LIST_INFO_NODE * 10    #rsv for more usb FTDI ctrl
        self.devices = self.device_list()                   #
        self.num_devices = ctypes.c_ulong()                 #num of usb FTDI
        self.bytes_written = ctypes.c_ulong()               #assume usb stable, not check

        #connect FTDI when class initial
        self.open_ftdi()        #get FTDI handle id
        self.config_ftdi_i2c()      #initial FTDI i2c
        self.ftdi_i2c_checkconn()       #check i2c connect use slow mode


        #write to aves
        '''Build AVES script path'''
        aves_path="./to_aves/"
        now = datetime.datetime.now()
        StyleTime = now.strftime("%Y_%m_%d_%H_%M_%S")
        self.write_to = aves_path + "aves_" + StyleTime + ".txt"

    def get_aves_str(self, addr1, addr2, value):
        #b0
        device_addr_print="{:02x}".format(0xb0)

        addr1_print = "{:02x}".format(addr1)
        addr2_print = "{:02x}".format(addr2)

        value_print = "{:02x}".format(value)

        #B0 0101 FF
        print_str=f"{device_addr_print} {addr1_print}{addr2_print} {value_print};\n"

        return print_str

    def print_str_to_aves(self, print_str):
        if(self.aves_write):
            with open(self.write_to, "a") as file:
                file.write(print_str)
        return

    def dac_to_hot_temp_code(self,num_in):
        if num_in == 0:
            num_out = 0x00
        elif num_in == 1:
            num_out = 0x01
        elif num_in == 2:
            num_out = 0x03
        elif num_in == 3:
            num_out = 0x07
        elif num_in == 4:
            num_out = 0x0F
        elif num_in == 5:
            num_out = 0x1F
        elif num_in == 6:
            num_out = 0x3F
        elif num_in == 7:
            num_out = 0x7F
        elif num_in == 8:
            num_out = 0xFF
        return num_out

    def close_ftdi(self):
        try:
            status = ftd2xx.FT_Close(self.handle)
        except:
            print(f"fail close FTDI, status:{status}")
        return

    def open_ftdi(self):
        # 获取设备列表
        status = FT_OK
        status |= ftd2xx.FT_CreateDeviceInfoList(ctypes.byref(self.num_devices))
        status |= ftd2xx.FT_GetDeviceInfoList(self.devices, ctypes.byref(self.num_devices))

        # 打印所有设备信息
        print_info = False
        if print_info:
            for i in range(self.num_devices.value):
                device = self.devices[i]
                print(f"Device {i}:")
                print(f"  Flags: {device.Flags}")
                print(f"  Type: {device.Type}")
                print(f"  ID: {device.ID}")
                print(f"  LocId: {device.LocId}")
                print(f"  SerialNumber: {device.SerialNumber}")
                print(f"  Description: {device.Description}")
                print(f"  ftHandle: {device.ftHandle}")

        # 打开设备
        # OpenEX HERE can define which to be opened
        status |= ftd2xx.FT_OpenEx(
            self.devices[self.i2c_port].SerialNumber,
            FT_OPEN_BY_SERIAL_NUMBER,
            ctypes.byref(self.handle)
            )

        # reset device
        status |= ftd2xx.FT_ResetDevice(self.handle)

        if status != FT_OK:
            raise Exception(f"FAIL open ftdi, FTstatus={status}")
        else:
            print(f"FTDI connect done, handle = {self.handle}")
            return

    def config_ftdi_i2c(self):
        #yfzhao
        #this funtion use FTDI top channel config function @libMPSSE.dll

        # 定义选项标志
        I2C_DISABLE_3PHASE_CLOCKING = 0x00000001
        I2C_ENABLE_DRIVE_ONLY_ZERO = 0x00000002
        I2C_ENABLE_PULLUPS = 0x00000004
        I2C_DISABLE_SCHMITT_TRIGGER = 0x00000008
        I2C_ENABLE_FAST_TRANSFER = 0x00000010
        I2C_ENABLE_HIGH_SPEED = 0x00000020
        I2C_ENABLE_STRETCH_CLOCK = 0x00000040
        I2C_DISABLE_ACK_POLLING = 0x00000080
        I2C_ENABLE_STRICT_ADDRESS_CHECK = 0x00000100
        I2C_ENABLE_DEBUG_MODE = 0x00000200

        # 配置ChannelConfig
        config = ChannelConfig()
        config.ClockRate = 400000  # 400 kHz, normal fast mode
        #config.ClockRate = 1000000  # 1MHz, fast+
        #config.LatencyTimer = 16  # 16 ms
        config.LatencyTimer = 1  # 1 ms

        #config.Options = 0  # 默认选项
        #yfzhao, 3phase clock good for i2c stable
        config.Options = I2C_ENABLE_FAST_TRANSFER | I2C_ENABLE_HIGH_SPEED

        # 调用I2C_InitChannel
        status = libmpsse.I2C_InitChannel(self.handle, ctypes.byref(config))
        if status != FT_OK:
            raise RuntimeError(f"FAIL I2C config: {status}")
        time.sleep(0.5)
        return


    def ftdi_i2c_checkconn(self):
        #use low speed read as i2c connect check

        #for gscoolink chip i2c
        #addr1 8bit
        #addr2 8bit

        #check connect option
        check_options = I2C_TRANSFER_OPTIONS_START_BIT | I2C_TRANSFER_OPTIONS_STOP_BIT |I2C_TRANSFER_OPTIONS_BREAK_ON_NACK

        # nouse addr, write 0x00, 0x00 then stop
        command = [0x00, 0x00]
        # loop 调用I2C_DeviceWrite函数
        for i in range(20):
            status = libmpsse.I2C_DeviceWrite(
                self.handle,  # FT_HANDLE handle
                self.chip_addr,  # uint32 deviceAddress
                ctypes.c_uint32(2),  # uint32 sizeToTransfer
                (ctypes.c_uint8 * 2)(*command),  # uint8 *buffer
                ctypes.byref(self.bytes_written),  # uint32 *sizeTransferred
                ctypes.c_uint32(check_options)  # uint32 options
            )
            if status == FT_OK:
                print(f"I2C connection check PASS")
                return

        #if 20 times status all not == FT_OK
        raise RuntimeError(f"I2C FAIL!! check I2C connection!!")
        return





    def ftdi_i2c_writeReg(self, addr1, addr2, data_8b):

        #for gscoolink chip i2c
        #addr1 8bit
        #addr2 8bit
        #data_8b 8bit

        #yfzhao
        #high performance i2c usage
        #use cpp dll file, donot use python control GPIO

        #direct use ftdi_i2c.c, see libmpsse
        #https://www.ftdichip.cn/Support/SoftwareExamples/MPSSE/LibMPSSE-I2C.htm

        #options = I2C_TRANSFER_OPTIONS_START_BIT | I2C_TRANSFER_OPTIONS_STOP_BIT | I2C_TRANSFER_OPTIONS_BREAK_ON_NACK

        # NOTE, if enable FAST_transfer, break on noack can not work
        options = I2C_TRANSFER_OPTIONS_START_BIT | I2C_TRANSFER_OPTIONS_STOP_BIT | \
                  I2C_TRANSFER_OPTIONS_FAST_TRANSFER_BYTES | I2C_TRANSFER_OPTIONS_FAST_TRANSFER


        # 将addr1, addr2, data打包成要写入的数据
        command = [addr1, addr2, data_8b]
        #write_data = (ctypes.c_uint8 * 3)(addr1, addr2, data_8b)

        #yfzhao note c++ use in python
        #在Python中，可以通过ctypes库创建固定大小的数组来模拟C/C++中的数组指针

        # 调用I2C_DeviceWrite函数
        status = libmpsse.I2C_DeviceWrite(
            self.handle,  # FT_HANDLE handle
            self.chip_addr,  # uint32 deviceAddress
            ctypes.c_uint32(3),  # uint32 sizeToTransfer
            (ctypes.c_uint8 * 3)(*command),  # uint8 *buffer
            ctypes.byref(self.bytes_written),  # uint32 *sizeTransferred
            ctypes.c_uint32(options)  # uint32 options
        )
        if status != FT_OK:
            raise RuntimeError(f"FAIL I2C write: {status}")


        ###add write to aves function###
        aves_str = self.get_aves_str(addr1, addr2, data_8b)
        self.print_str_to_aves(aves_str)

        return

    def ftdi_i2c_readReg(self, addr1, addr2):
        #标准的I2C读操作流程：
        #1生成START信号，开始I2C传输。
        #2发送设备地址，并设置写模式（R / W位为0）。
        #3发送要读取的寄存器地址。
        #4生成重复START信号（Repeated START）。
        #5重新发送设备地址，并设置读模式（R / W位为1）。
        #6从设备读取数据。
        #7生成STOP信号，结束I2C传输。

        #for gscoolink chip i2c
        #addr1 8bit
        #addr2 8bit

        #write option, donot stop, wait Repeated START
        w_options = I2C_TRANSFER_OPTIONS_START_BIT | \
                    I2C_TRANSFER_OPTIONS_FAST_TRANSFER_BYTES | I2C_TRANSFER_OPTIONS_FAST_TRANSFER

        # 将addr1, addr2打包成要写入的数据
        command = [addr1, addr2]
        # 调用I2C_DeviceWrite函数
        status = libmpsse.I2C_DeviceWrite(
            self.handle,  # FT_HANDLE handle
            self.chip_addr,  # uint32 deviceAddress
            ctypes.c_uint32(2),  # uint32 sizeToTransfer
            (ctypes.c_uint8 * 2)(*command),  # uint8 *buffer
            ctypes.byref(self.bytes_written),  # uint32 *sizeTransferred
            ctypes.c_uint32(w_options)  # uint32 options
        )
        if status != FT_OK:
            raise RuntimeError(f"FAIL I2C write page_addr: {status}")

        #read option, as normal
        r_options = I2C_TRANSFER_OPTIONS_START_BIT | I2C_TRANSFER_OPTIONS_STOP_BIT | \
                    I2C_TRANSFER_OPTIONS_FAST_TRANSFER_BYTES | I2C_TRANSFER_OPTIONS_FAST_TRANSFER

        rb_buffer = (ctypes.c_uint8 * 1)()

        status = libmpsse.I2C_DeviceRead(
            self.handle,  # handle
            self.chip_addr,  # deviceAddress
            ctypes.c_uint32(1),  # sizeToTransfer
            rb_buffer,  # uint8 *buffer
            ctypes.byref(self.bytes_written),  # uint32 *sizeTransferred
            ctypes.c_uint32(r_options)  # options
        )
        if status != FT_OK:
            raise RuntimeError(f"FAIL I2C read data: {status}")

        rb_data = list(rb_buffer)[0]

        return rb_data

    def ftdi_i2c_writeBits(self, addr1, addr2, lsb, bits, old_invalue):
        #bits -> temp_code bits
        bits_temp=self.dac_to_hot_temp_code(bits)

        #first read old value
        old_value=self.ftdi_i2c_readReg(addr1, addr2)
        #print("-------"+hex(old_value))
        #gen value mask 0

        #move up <<
        winvalue = old_invalue << lsb
        bits_pos = bits_temp << lsb
        #python bit not need & 0xFF
        mask0 = ~bits_pos & 0xFF

        #clear part of old value
        clear_value = mask0 & old_value

        #get new value by bit_or
        new_value = clear_value | winvalue

        #write back
        self.ftdi_i2c_writeReg(addr1, addr2, new_value)
        return

    def ftdi_i2c_readBits(self, addr1, addr2, lsb, bits):
        #bits -> temp_code bits
        bits_temp=self.dac_to_hot_temp_code(bits)
        bits_pos = bits_temp << lsb
        #first read old value
        old_value=self.ftdi_i2c_readReg(addr1, addr2)
        #python bit not need & 0xFF
        mask0 = bits_pos & 0xFF
        #clear part of old value
        clear_value = mask0 & old_value

        new_value = clear_value >> lsb
        return new_value

    def ftdi_i2c_readRegs(self, addr1, addr2, num):
        read_list=[]
        for i in range(num):
            addr_loop = addr2 + i
            read_value = self.ftdi_i2c_readReg(addr1, addr_loop)
            read_list.append(read_value)
        return read_list


    #Write all i2c in page addr_page
    def ftdi_i2c_write_page(self, addr_page, data_list):

        #write from 0x00->0xFF
        #data len must be 256

        len_data = len(data_list)

        if len_data != 256:
            print(f"WARNING write page i2c, len data={len_data} should eq 256!")


        options = I2C_TRANSFER_OPTIONS_START_BIT | I2C_TRANSFER_OPTIONS_STOP_BIT | \
                  I2C_TRANSFER_OPTIONS_FAST_TRANSFER_BYTES | I2C_TRANSFER_OPTIONS_FAST_TRANSFER


        #write addr from 0x00
        command = [addr_page, 0x00]
        command.extend(data_list)

        c_command = (ctypes.c_uint8 * len(command))(*command)

        # 调用I2C_DeviceWrite函数
        status = libmpsse.I2C_DeviceWrite(
            self.handle,  # FT_HANDLE handle
            self.chip_addr,  # uint32 deviceAddress
            ctypes.c_uint32(len(command)),  # uint32 sizeToTransfer
            c_command,  # uint8 *buffer
            ctypes.byref(self.bytes_written),  # uint32 *sizeTransferred
            ctypes.c_uint32(options)  # uint32 options
        )

        if status != FT_OK:
            raise RuntimeError(f"ERROR write page i2c: {status}")

        return


if __name__ == "__main__":
    i2c = DrvFTDI(i2c_port=0)


    i2c.ftdi_i2c_writeReg(0x26, 0x00, 0x03)
    i2c.ftdi_i2c_writeReg(0x26, 0x01, 0x04)
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x00)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x01)))
    data_list = [0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02]
    i2c.ftdi_i2c_write_page(0x26, data_list)
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x00)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x01)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x02)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x03)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x04)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x05)))
    print(hex(i2c.ftdi_i2c_readReg(0x26, 0x06)))

    i2c.close_ftdi()