"""
寄存器类生成工具
从JSON配置文件生成PAGE和register类结构
"""

import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from py_auto_func.json_register_get import JSONRegisterGet

def convert_to_valid_class_name(name: str) -> str:
    """
    将寄存器名称转换为有效的Python类名
    处理以下情况：
    1. 移除特殊字符 ([]:)
    2. 处理以数字开头的类名（添加前缀reg_）
    
    :param name: 原始寄存器名称
    :return: 有效的Python类名
    """
    # 移除特殊字符
    valid_name = name.replace('[', '_').replace(']', '_').replace(':', '_')
    
    # 检查是否以数字开头
    if valid_name[0].isdigit():
        valid_name = f"reg_{valid_name}"
        
    return valid_name

def generate_register_class_file(json_file_path, output_file_path="register_classes.py"):
    """
    根据JSON配置文件生成寄存器类文件
    :param json_file_path: JSON配置文件路径
    :param output_file_path: 输出的Python文件路径
    """
    # 加载JSON文件
    printer = JSONRegisterGet(json_file_path)
    page_name_dict = printer.page_name_dict
    
    # 开始写入文件
    with open(output_file_path, "w", encoding="utf-8") as f:
        # 写入文件头
        f.write('"""\n自动生成的寄存器类文件\n根据JSON配置文件动态生成PAGE和register类\n"""\n\n')
        
        # 定义基类
        f.write("class RegisterAccessor:\n")
        f.write('    """\n    寄存器访问器主类\n    每个PAGE作为一级子类\n    每个寄存器作为二级子类\n    """\n')
        
        # 为每个PAGE生成类
        for page, registers in page_name_dict.items():
            f.write(f"    class {page}:\n")
            
            if not registers:
                f.write("    pass\n\n")
                continue
                
            # 为每个寄存器生成子类
            for register in registers:
                if not register:
                    continue
                    
                # 转换为有效的Python类名
                register_class_name = convert_to_valid_class_name(register)
                
                f.write(f"        class {register_class_name}:\n")
                f.write("            @staticmethod\n")
                f.write("            def r():\n")
                f.write("                pass\n\n")
                f.write("            @staticmethod\n")
                f.write("            def w(val):\n")
                f.write("                pass\n\n")
            
            f.write("\n")
    
    print(f"寄存器类文件已生成: {output_file_path}")

if __name__ == "__main__":
    json_file = "GSU1K1_R3_Register_Config.json"
    output_file = "RegisterAccessor.py"
    generate_register_class_file(json_file, output_file)
