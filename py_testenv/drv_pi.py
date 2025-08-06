#########################PI I2C driver python3#####################
#   yfzhao
#   2024
#   raspberry pi i2c driver in python3
#   use i2ctransfer to access i2c bus
#
#########################PI I2C driver python3#####################


import datetime
import subprocess
import time


class DrvPI:
    def __init__(
        self,
        i2c_port=1,         #raspberry default i2c_1
        chip_addr=0x58,     #gs chip 0xB0->0x58
        ):
        self.aves_write=False        #define if write to AVES script
        self.i2c_port=i2c_port
        self.chip_addr=chip_addr

        '''Build AVES script path'''
        aves_path="./to_aves/"
        now = datetime.datetime.now()
        StyleTime = now.strftime("%Y_%m_%d_%H_%M_%S")
        self.write_to = aves_path + "aves_" + StyleTime + ".txt"

    def run_linux(self,cmd):
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, encoding='utf-8')
            return output.strip()
        except subprocess.CalledProcessError as error_run:
            error_message = f"Command '{cmd}' returned non-zero exit status {error_run.returncode}:\n{error_run.output}"
            print(error_message)
            return "error"

    def get_aves_str(self, addr1, addr2, value):
        #b0
        device_addr_print="{:02x}".format(self.chip_addr<<1)

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

    def writeReg(self, addr1, addr2, value):
        #address1->first 8bit address
        #address2->second 8bit address
        #value->value write to addr
        write_cmd=f"/usr/sbin/i2ctransfer -f -y {str(self.i2c_port)} " \
                  f"w3@{hex(self.chip_addr)} " \
                  f"{hex(addr1)} {hex(addr2)} " \
                  f"{hex(value)}"
        #Make sure write reg complete
        while 1:
            write_result = self.run_linux(write_cmd)
            if (write_result != "error"):
                break
            else:
                print("PI::writereg error, wait 1s, continue.")
                time.sleep(1)

        # add print to aves function
        aves_str = self.get_aves_str(addr1, addr2, value)
        self.print_str_to_aves(aves_str)
        return

    def readReg(self, addr1, addr2):
        #address1->first 8bit address
        #address2->second 8bit address
        read_cmd=f"/usr/sbin/i2ctransfer -f -y {str(self.i2c_port)} " \
                 f"w2@{hex(self.chip_addr)} " \
                 f"{hex(addr1)} {hex(addr2)} " \
                 f"r1"
        while 1:
            read_out=self.run_linux(read_cmd)
            if(read_out != "error"):
                break
            else:
                print("PI::readreg error, wait 1s, continue.")
                time.sleep(1)
        #hex str -> int
        read_int=int(read_out, 16)
        return read_int

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

    def writeBits(self, addr1, addr2, lsb, bits, old_invalue):

        #bits -> temp_code bits
        bits_temp=self.dac_to_hot_temp_code(bits)

        #first read old value
        old_value=self.readReg(addr1, addr2)
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
        self.writeReg(addr1, addr2, new_value)

        return

    def readBits(self, addr1, addr2, lsb, bits):
        #bits -> temp_code bits
        bits_temp=self.dac_to_hot_temp_code(bits)
        bits_pos = bits_temp << lsb
        #first read old value
        old_value=self.readReg(addr1, addr2)
        #python bit not need & 0xFF
        mask0 = bits_pos & 0xFF
        #clear part of old value
        clear_value = mask0 & old_value

        new_value = clear_value >> lsb
        return new_value

    def readRegs(self, addr1, addr2, num):
        read_list=[]
        for i in range(num):
            addr_loop = addr2 + i
            read_value = self.readReg(addr1, addr_loop)
            read_list.append(read_value)
        return read_list

