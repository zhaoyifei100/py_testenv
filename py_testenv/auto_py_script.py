
"""
auto_py_script.py
--------------------------------------
自动化寄存器类生成工具。

功能：
1. 解析XML寄存器配置，自动生成寄存器结构的JSON数据。
2. 支持去重、清理、分组寄存器字段。
3. 可自动生成Python寄存器访问类文件，便于后续脚本开发。

依赖：json, xml_parser

用法示例：
    from auto_py_script import AutoPyScript
    autopy = AutoPyScript('your.xml')
    autopy.generate_register_class_file('auto_class.py')

作者：yfzhao

--------------------------------------
"""

import json
import os
import shutil

from .xml_parser import XMLParser
from .get_aves import GetAVES

class AutoPyScript:

    def __init__(self,
                 xml_file_path: str,
                 aves_script_name: str,
                 class_instance_name: str = "super()"):
        """
        初始化类，从XML里build json data。
        :param xml_file_path: XML文件路径
        """
        self.aves_script_name = aves_script_name
        self.class_instance_name = class_instance_name

        #get data from XML use XMLParser
        self.parser = XMLParser(xml_file_path)
        self.parser.xml_to_json()
        self.data = self.parser.json_data

        self.unique_data = self._remove_page_level_duplicates()
        self.page_name_dict = self._create_page_name_dict()
        self.page_reg_map = self._create_page_reg_map()

        # init GetAVES instance
        self.get_aves = GetAVES(
            xml_file_path=xml_file_path,
            aves_script_name=aves_script_name,
        )

    def aves_buildall(self):
        """
        一键生成Python脚本、C头文件、C源文件。
        用法：self.buildall()
        """
        self.get_aves.write_aves_script()
        self.get_aves.write_c_header()
        self.get_aves.write_c_file()
        print("GetAVES All files generated.")

    def _create_page_reg_map(self):
        """
        构建两级哈希表：PAGE -> register_name -> [寄存器信息字典]，支持O(1)查找。
        """
        page_reg_map = {}
        for page, registers in self.data.items():
            if page not in page_reg_map:
                page_reg_map[page] = {}
            for reg in registers:
                reg_name = reg.get("register_name")
                if reg_name:
                    if reg_name not in page_reg_map[page]:
                        page_reg_map[page][reg_name] = []
                    page_reg_map[page][reg_name].append(reg.copy())
        return page_reg_map

    def _create_page_name_dict(self):
        """
        从unique_data生成一个只包含PAGE name和register_name的字典。
        """
        page_name_dict = {}
        for key, registers in self.unique_data.items():
            page_name_dict[key] = [
                reg.get("register_name")
                for reg in registers 
                if reg.get("register_name")
            ]
        return page_name_dict

    def _remove_page_level_duplicates(self):
        """
        在每个PAGE下去除重复的register_name
        :return: 去重后的JSON数据
        """
        unique_data = {}
        for key, registers in self.data.items():
            seen_fields = set()
            unique_registers = []
            for register in registers:
                field_name = register.get("register_name")
                if field_name and field_name not in seen_fields:
                    unique_registers.append(register)
                    seen_fields.add(field_name)
            unique_data[key] = unique_registers
        return unique_data

    def _convert_to_valid_class_name(self, name: str) -> str:
        """
        将寄存器名称转换为有效的Python类名
        处理以下情况：
        1. 移除特殊字符 (:)
        2. 处理以数字开头的类名（添加前缀reg_）
        
        :param name: 原始寄存器名称
        :return: 有效的Python类名
        """
        # 移除特殊字符
        #valid_name = name.replace('[', '_').replace(']', '_').replace(':', '_')
        valid_name = name.replace(':', '_')
        
        # 检查是否以数字开头
        if valid_name[0].isdigit():
            valid_name = f"reg_{valid_name}"
            
        return valid_name

    def generate_register_class_file(self, output_file_path="register_classes.py"):
        """
        根据JSON配置文件生成寄存器类文件
        :param json_file_path: JSON配置文件路径
        :param output_file_path: 输出的Python文件路径
        """

        #self.page_name_dict initial in __init__
        
        # 开始写入文件
        with open(output_file_path, "w", encoding="utf-8") as f:
            # 写入文件头
            f.write('"""\n自动生成的寄存器类文件\n根据JSON配置文件动态生成PAGE和register类\n"""\n\n')
            
            # 定义基类
            f.write("class AutoClass:\n")
            f.write('    """\n    寄存器访问器主类\n    每个PAGE作为一级子类\n    每个寄存器作为二级子类\n    """\n')
            
            # 为每个PAGE生成类
            for page, registers in self.page_name_dict.items():
                f.write(f"    class {page}:\n")
                
                if not registers:
                    f.write("    pass\n\n")
                    continue
                    
                # 为每个寄存器生成子类
                for register in registers:
                    if not register:
                        continue
                        
                    # 转换为有效的Python类名
                    register_class_name = self._convert_to_valid_class_name(register)
                    
                    f.write(f"        class {register_class_name}:\n")
                    f.write("            @staticmethod\n")
                    f.write("            def r():\n")
                    f.write("                pass\n\n")
                    f.write("            @staticmethod\n")
                    f.write("            def w(val):\n")
                    f.write("                pass\n\n")
                
                f.write("\n")
        
        print(f"寄存器类文件已生成: {output_file_path}")

    def _get_register_info(self, page: str, reg_name: str) -> list:
        """
        根据输入的page和reg_name，O(1)查找寄存器信息。
        :param page: PAGE名称
        :param reg_name: 要查询的寄存器名称
        :return: 包含该寄存器所有信息的字典（如有多个，返回列表）
        """
        page_dict = self.page_reg_map.get(page)
        if not page_dict:
            return None
        result = page_dict.get(reg_name)
        if not result:
            return None
        #result is dict list
        return result

    def _get_addr12(self, addr_str) -> list:
        addr_int = int(addr_str, 16)
        addr1 = (addr_int >> 8) & 0xFF
        addr2 = addr_int & 0xFF
        # 返回十六进制字符串
        return [f"0x{addr1:02X}", f"0x{addr2:02X}"]
    
    def _get_rshift_str(self, byte_shift: str) -> str:
        shift = int(byte_shift)
        if shift == 0:
            return ""
        elif shift < 0:
            return f"<<{-shift}"
        else:
            return f">>{shift}"

    def _get_read_cmd(self, reg_info) -> str:
        addr_str = reg_info.get("byte_address")
        [addr1, addr2] = self._get_addr12(addr_str)
        #lsb = int(reg_info.get("byte_shift")) % 8
        #bits = reg_info.get("effective_bits")

        byte_mask = reg_info.get("byte_mask")
        if byte_mask == "0xFF":
            byte_mask_str = ""
        else:
            byte_mask_str = f"&{byte_mask}"

        shift_str = self._get_rshift_str(reg_info.get("byte_shift"))

        cmd = f"( {self.class_instance_name}.readReg({addr1},{addr2}){byte_mask_str} ) {shift_str}"
        return cmd
        

    def _get_read_list(self, page: str, reg_name: str) -> list:
        return_list = []
        #get reg info
        reg_info_list = self._get_register_info(page, reg_name)
        reg_len = len(reg_info_list)
        if reg_len == 0:
            return_list.append(f"# {reg_name} get read function fail")
            return return_list
        elif reg_len == 1:
            #only one reg info
            reg_info = reg_info_list[0]
            full_cmd = f"rb_{reg_name}"+f" = {self._get_read_cmd(reg_info)}"
            return_list.append(full_cmd)
        else:
            #multiple reg info, need to read all
            #set rb to 0
            return_list.append(f"rb_{reg_name} = 0")
            for reg_info in reg_info_list:
                full_cmd = f"rb_{reg_name}"+f" |= {self._get_read_cmd(reg_info)}"
                return_list.append(full_cmd)
        return return_list

    def _mask_to_lsb_bits(self, mask: str) -> list:
        """
        将I2C掩码转换为LSB位置和位数
        
        参数:
            mask (str): 掩码值，是十六进制字符串(如"0xF0")
        
        返回:
            tuple: (lsb, bits) - LSB位置和位数
            
        示例:
            >>> mask_to_lsb_bits("0xF0")
            (4, 4)
            >>> mask_to_lsb_bits(0b11000000)
            (6, 2)
        """
        mask = int(mask, 16)
        
        # 确保mask是整数
        mask = int(mask)
        
        if mask == 0:
            return (0, 0)
        
        # 计算LSB位置（第一个置1的位的位置）
        lsb = (mask & -mask).bit_length() - 1
        
        # 计算连续1的位数
        shifted = mask >> lsb
        bits = 0
        while (shifted & 1):
            bits += 1
            shifted >>= 1
        
        return [lsb, bits]
    
    def _get_w_val(self, shift: str, mask: str, w_str: str) -> int:
        # 处理字符串形式的input
        if w_str.startswith(('0x', '0X')):
            w_num = int(w_str, 16)
        else:
            w_num = int(w_str)

        shift_num = int(shift)
        mask_num = int(mask, 16)
        if shift_num == 0:
            out_val = w_num & mask_num
        elif shift_num < 0:
            out_val = (w_num >> -shift_num) & mask_num
        else:
            out_val = ((w_num << shift_num) & mask_num ) >> shift_num
        return out_val


    def _get_write_cmd(self, reg_info, value_var) -> str:
        addr_str = reg_info.get("byte_address")
        mask_str = reg_info.get("byte_mask")
        shift_str = reg_info.get("byte_shift")
        #value_str = str(value_var)

        [addr1, addr2] = self._get_addr12(addr_str)
        [lsb, bits] = self._mask_to_lsb_bits(mask_str)
        write_val_num = self._get_w_val(shift_str, mask_str, value_var)

        cmd = f"{self.class_instance_name}.writeBits({addr1},{addr2},{lsb},{bits},{write_val_num})"
        return cmd

    def _get_write_list(self, page: str, reg_name: str, value_var: str) -> list:
        #list add comment, format: #w PAGE:regname->value
        value_str = str(value_var)
        return_list = []
        reg_info_list = self._get_register_info(page, reg_name)
        reg_len = len(reg_info_list)
        if reg_len == 0:
            return_list.append(f"# {reg_name} get write function fail")
            return return_list
        elif reg_len == 1:
            reg_info = reg_info_list[0]
            full_cmd = self._get_write_cmd(reg_info, value_str)
            return_list.append(f"#w {page}:{reg_name}->{value_str}")
            return_list.append(full_cmd)
        else:
            return_list.append(f"#w {page}:{reg_name}->{value_str}")
            for reg_info in reg_info_list:
                full_cmd = self._get_write_cmd(reg_info, value_str)
                return_list.append(full_cmd)
        return return_list
    
    def _backup_file_before_write(self, file_path: str):
        if os.path.isfile(file_path):
            backup_path = file_path + ".bak"
            shutil.copyfile(file_path, backup_path)
            print(f"Backup created: {backup_path}")
        else:
            print(f"No existing file to backup: {file_path}")
    
    def _revert_file_from_backup(self, file_path: str):
        backup_path = file_path + ".bak"
        if os.path.isfile(backup_path):
            shutil.copyfile(backup_path, file_path)
            print(f"File reverted from backup: {file_path}")
        else:
            print(f"No backup file found to revert: {backup_path}")

    def auto_register_replace(self, file_path: str):
        """
        自动生成寄存器操作脚本，replace指定文件。
        :param file_path: 输出的Python脚本文件路径
        """
        import re
        # 备份原文件
        self._backup_file_before_write(file_path)
        # 读取原文件内容
        with open(file_path, "r", encoding="utf-8") as fr:
            lines = fr.readlines()
        new_lines = []
        # Regex 匹配 AutoClass.<PAGE>.<reg>.<op>()
        pattern = re.compile(r"AutoClass\.(?P<page>\w+)\.(?P<reg>\w+)\.(?P<op>r|w)\(\s*(?P<args>[^)]*)\)")
        for line in lines:
            m = pattern.search(line)
            if m:
                page = m.group('page')
                reg = m.group('reg')
                op = m.group('op')
                args = m.group('args').strip()
                indent = re.match(r'\s*', line).group(0)

                if op == 'r':
                    cmds = self._get_read_list(page, reg)
                    print(f"[READ] {page}.{reg}")
                else:
                    value_var = args
                    cmds = self._get_write_list(page, reg, value_var)
                    print(f"[WRITE] {page}.{reg} <=", value_var)
                for cmd in cmds:
                    new_lines.append(f"{indent}{cmd}\n")
            else:
                new_lines.append(line)
        # 写回文件
        with open(file_path, "w", encoding="utf-8") as fw:
            fw.writelines(new_lines)
        return
