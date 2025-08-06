'''
yfzhao MOVE to python3

This file is used to convert AVES script to
1.python script
2.C header file
3.C source file

USAGE:
    see if __main__ at the end of this file

this class auto include "get_aves_def.py" file
    def.py include i2c driver base on FTDI or Raspberry Pi

You will get 4functions of i2c r/w:
    readReg, writeReg, readBits, writeBits

In the upper-level class, we generally inherit the aves_script class
    that is:
        from xxxxxx_scripts import aves_script
        class phy_func(aves_script):
            def __init__(self,i2c_port=1):
                self.i2c_port = i2c_port
                super().__init__(i2c_port, 0x58)

!!In this way, we can realize that two i2c ports share a set of scripts!!
There is a little trouble if you want to call the function in the upper class to use super().
that is:
    super().func_01_01_Chip_Power_Up()
or:
    super().writeReg(0x58, 0x00, 0x01)

    
'''

#import json
import os
#import sys
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .xml_parser import XMLParser

class GetAVES:
    def __init__(self,
                 xml_file_path="GSU1K1_R3.xml",
                 aves_script_name="gsu1001_2024_mpw_scripts.txt",
                 py_out_local_dir="",       #if need to change outdir
                 py_out_name="",            #if need to change out name
                 addr_conv=False,           #if need to change address name
                 ):
        self.xml_file_path = xml_file_path
        self.aves_script_name=aves_script_name
        self.addr_conv=addr_conv

        self.py_out_local_dir=py_out_local_dir

        self.base_name = os.path.splitext(os.path.basename(self.xml_file_path))[0]
        if py_out_name == "":
            self.py_out_name = self.base_name + "_scripts.py"
        else:
            self.py_out_name=py_out_name

        #use XMLParser to read the XML file and get device address dictionary
        self.parser = XMLParser(xml_file_path)
        self.dev_addr_dict = self.parser.parse_to_dict()

        print(f"aves path={self.aves_script_name}")


    def replace_func_name(self,func_name):
        func_name_new = list(func_name)
        for i_func_name in range(len(func_name_new)):
            if ((func_name_new[i_func_name] >= 'a' and func_name_new[i_func_name] <= 'z') \
                    or (func_name_new[i_func_name] >= 'A' and func_name_new[i_func_name] <= 'Z') \
                    or (func_name_new[i_func_name] >= '0' and func_name_new[i_func_name] <= '9')):
                func_name_new[i_func_name] = func_name_new[i_func_name]
            elif (func_name[i_func_name] == "."):
                func_name_new[i_func_name] = "p"
            else:
                func_name_new[i_func_name] = "_"
        func_name_new = "".join(func_name_new)
        return func_name_new

    def write_aves_script(self):

        aves_file_path=self.aves_script_name
        output_file_path=self.py_out_local_dir+self.py_out_name

        f=open(aves_file_path,encoding="utf-8")
        fo=open(output_file_path,'w')

        #first import reg define
        #build reg define file
        self.parser.get_regdefing_py()
        reg_define_name = self.base_name + "_reg_def"
        fo.write(f"from {reg_define_name} import *\n")

        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        get_aves_def_path = os.path.join(pkg_dir, "get_aves_def.py")

        # 250224, yfzhao use NEW FTDI driver
        with open(get_aves_def_path, encoding="utf-8") as header_file:
            for line in header_file:
                fo.write(line)
        #----Write Header End----


        func_write_en = 0
        line_num = 1
        all_content=f.readlines()
        func_index=0

        for line_tmp in all_content:
            line=line_tmp.strip()
            #ERROR, yf
            #print "Line "+str(line_num)+" : " + line
            line_num=line_num+1
            line_length=len(line)

            if line_length==0:
                #print("Blank Line!")
                continue
            else:
                # Find start ":" and end ":"
                if(line[0]==":" and line[-1]==":"):
                    # Replace "-" and " "
                    func_name_new=line.strip(":").strip(" ")
                    #print func_name_new
                    #print func_name_new[0:2]
                    func_index=int(func_name_new[0:2])
                    func_name_new = self.replace_func_name(func_name_new)
                    func_name_new = "func_"+func_name_new
                    #print "func_name_new: "+func_name_new
                    if(True):
                        fo.write("    def "+func_name_new+"(self):\n")
                        '''yfzhao MOVE to python3'''
                        #fo.write("    print \"Cfg "+func_name_new+"...\"\n")
                        fo.write("        print(\"Cfg "+func_name_new+"...\")\n")
                    func_write_en = 1
                    continue


                # Not translate 06/07/20
                if(func_write_en==1):
                    # Find "include"
                    if(line[0]=="i"):
                        # sub function call
                        call_func_name_new=line.strip().split('"')[-2]
                        call_func_name_new=self.replace_func_name(call_func_name_new)
                        #print "call_func_name_new:  "+call_func_name_new
                        fo.write("        self.func_"+call_func_name_new+"()\n")
                        #print("func_"+call_func_name_new+"()\n")

                    # Find End
                    elif(line=="End" or line=="end"):
                        func_write_en=0
                        fo.write("\n")

                    # Find configures
                    elif(line[0]!=";"):
                        if(';' in line):
                            split_line  = line.split(";")
                            cfg_txt     = split_line[0].strip().split(" ")
                            comments    = split_line[1].strip()
                        else:
                            cfg_txt     = line.strip().split(" ")
                            comments    = ""

                        cfg_16bit_addr = cfg_txt[1].strip()
                        cfg_dev_addr= cfg_16bit_addr[0:2]
                        if self.addr_conv:
                            cfg_dev_addr_para=self.dev_addr_dict[cfg_dev_addr.upper()]
                        cfg_sub_addr= cfg_16bit_addr[2:]
                        cfg_content = cfg_txt[2].strip()
                        if self.addr_conv:
                            fo.write("        self.writeReg("+cfg_dev_addr_para+",0x"+cfg_sub_addr+",0x"+cfg_content+") #"+comments)
                        else:
                            fo.write("        self.writeReg(0x"+cfg_dev_addr+",0x"+cfg_sub_addr+",0x"+cfg_content+") #"+comments)
                        fo.write("\n")
        f.close()
        fo.close()

        #print(f"Convert::from, {aves_file_path}")
        print(f"Convert::to  , {output_file_path}")

        return

    def write_c_header(self):
        #aves_txt_dir    = self.eval_dir
        #aves_file_path=aves_txt_dir+self.aves_script_name

        aves_file_path=self.aves_script_name
        #output_file_path=self.py_out_local_dir+self.py_out_name

        #c header name
        output_file_path = self.py_out_name.split(".")[0]+".h"

        f=open(aves_file_path,encoding="utf-8")
        fo=open(output_file_path,'w')

        #wtjiang use this file
        #not common use ,del 
        #fo.write(f"#include \"def_gsu1001_es3.h\"\n")     


        func_write_en = 0
        line_num = 1
        all_content=f.readlines()
        func_index=0

        for line_tmp in all_content:
            line=line_tmp.strip()
            #ERROR, yf
            #print "Line "+str(line_num)+" : " + line
            line_num=line_num+1
            line_length=len(line)

            if line_length==0:
                #print("Blank Line!")
                continue
            else:
                # Find start ":" and end ":"
                if(line[0]==":" and line[-1]==":"):
                    # Replace "-" and " "
                    func_name_new=line.strip(":").strip(" ")
                    func_index=int(func_name_new[0:2])
                    func_name_new = self.replace_func_name(func_name_new)
                    func_name_new = "func_"+func_name_new
                    #print "func_name_new: "+func_name_new
                    fo.write("void "+func_name_new+"();\n")
                    func_write_en = 1
                    continue
        f.close()
        fo.close()

        #print(f"Convert::from, {aves_file_path}")
        print(f"Convert::to  , {output_file_path}")

        return

    def write_c_file(self):
        #aves_txt_dir    = self.eval_dir
        #aves_file_path=aves_txt_dir+self.aves_script_name

        aves_file_path=self.aves_script_name
        #c header name
        output_file_path = self.py_out_name.split(".")[0]+".c"

        f=open(aves_file_path,encoding="utf-8")
        fo=open(output_file_path,'w')

        #fo.write(f"#include \"gsu1001_scripts.h\"\n")  #common use
        h_file_path = self.py_out_name.split(".")[0]+".h"
        fo.write(f"#include \"{h_file_path}\"\n")  #common use

        func_write_en = 0
        line_num = 1
        all_content=f.readlines()
        func_index=0

        for line_tmp in all_content:
            line=line_tmp.strip()
            #ERROR, yf
            #print "Line "+str(line_num)+" : " + line
            line_num=line_num+1
            line_length=len(line)

            if line_length==0:
                #print("Blank Line!")
                continue
            else:
                # Find start ":" and end ":"
                if(line[0]==":" and line[-1]==":"):
                    # Replace "-" and " "
                    func_name_new=line.strip(":").strip(" ")
                    #print func_name_new
                    #print func_name_new[0:2]
                    func_index=int(func_name_new[0:2])
                    func_name_new = self.replace_func_name(func_name_new)
                    func_name_new = "func_"+func_name_new
                    #print "func_name_new: "+func_name_new
                    fo.write("void "+func_name_new+"(){\n")
                    func_write_en = 1
                    continue


                # Not translate 06/07/20
                if(func_write_en==1):
                    # Find "include"
                    if(line[0]=="i"):
                        # sub function call
                        call_func_name_new=line.strip().split('"')[-2]
                        call_func_name_new=self.replace_func_name(call_func_name_new)
                        #print "call_func_name_new:  "+call_func_name_new
                        #fo.write("        self.func_"+call_func_name_new+"()\n")
                        fo.write("    func_" + call_func_name_new + "();\n")
                        #print("func_"+call_func_name_new+"()\n")

                    # Find End
                    elif(line=="End" or line=="end"):
                        func_write_en=0
                        fo.write("}\n")
                        fo.write("\n")

                    # Find configures
                    elif(line[0]!=";"):
                        if(';' in line):
                            split_line  = line.split(";")
                            cfg_txt     = split_line[0].strip().split(" ")
                            comments    = split_line[1].strip()
                        else:
                            cfg_txt     = line.strip().split(" ")
                            comments    = ""

                        cfg_16bit_addr = cfg_txt[1].strip()
                        cfg_dev_addr= cfg_16bit_addr[0:2]

                        cfg_sub_addr= cfg_16bit_addr[2:]
                        cfg_content = cfg_txt[2].strip()

                        fo.write("    writeReg(0x"+cfg_dev_addr+",0x"+cfg_sub_addr+",0x"+cfg_content+"); //"+comments)
                        fo.write("\n")
        f.close()
        fo.close()

        #print(f"Convert::from, {aves_file_path}")
        print(f"Convert::to  , {output_file_path}")

        return



if __name__ == "__main__":


    aves_script_name = "D:/GS_Projects/gs_svn/gsu1001/eval/aves/shared_scripts/gsu1001_2024_mpw_scripts.txt"
    xml_file = "D:/GS_Projects/gs_svn/gsu1001/eval/aves/gsu1001/GSU1K1_R3.xml"


    cov=GetAVES(
        xml_file_path=xml_file,
        aves_script_name=aves_script_name,
    )
    cov.write_aves_script()
    cov.write_c_header()
    cov.write_c_file()
