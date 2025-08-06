# this is change AVES script to Class
# Class for two board sweep
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#from reg_define import *
#reg define change to unique name base on proj



#add windows judgement#
#FTDI & raspberry Compatible#
import platform

def get_system():
    system = platform.system()
    machine = platform.machine()
    if system == "Windows":
        output = "win_x86"
    else:
        output = "linux"
    return output

#direct use PIP manage i2c driver
#no need to consider .dll issue
#yfzhao, 250805

class aves_script:
    def __init__(self,i2c_port=1,chip_addr=0x58,):
        self.i2c_port = i2c_port
        self.chip_addr = chip_addr
        self.system = get_system()
        if self.system == "linux":
            #from common.raspberry import raspberry
            from py_testenv.drv_pi import DrvPI
            self.raspberry_i2c = DrvPI(i2c_port=self.i2c_port)
        else:
            #from common.FTDI import FTDI
            from py_testenv.drv_ftdi import DrvFTDI
            self.ftdi_i2c = DrvFTDI(i2c_port=self.i2c_port)


    def readReg(self, addr1, addr2):
        if self.system == "linux":
            read_int = self.raspberry_i2c.readReg(addr1, addr2)
        else:
            read_int = self.ftdi_i2c.ftdi_i2c_readReg(addr1, addr2)
        return read_int

    def writeReg(self, addr1, addr2, value):
        if self.system == "linux":
            self.raspberry_i2c.writeReg(addr1, addr2, value)
        else:
            self.ftdi_i2c.ftdi_i2c_writeReg(addr1, addr2, value)

    def writeBits(self, addr1, addr2, lsb, bits, invalue):
        if self.system == "linux":
            self.raspberry_i2c.writeBits(addr1, addr2, lsb, bits, invalue)
        else:
            self.ftdi_i2c.ftdi_i2c_writeBits(addr1, addr2, lsb, bits, invalue)

    def readBits(self, addr1, addr2, lsb, bits):
        if self.system == "linux":
            output = self.raspberry_i2c.readBits(addr1, addr2, lsb, bits)
        else:
            output = self.ftdi_i2c.ftdi_i2c_readBits(addr1, addr2, lsb, bits)
        return output

    def readRegs(self, addr1, addr2, num):
        if self.system == "linux":
            output = self.raspberry_i2c.readRegs(addr1, addr2, num)
        else:
            output = self.ftdi_i2c.ftdi_i2c_readRegs(addr1, addr2, num)
        return output


#######rasp_conv_aves_defination end##########

