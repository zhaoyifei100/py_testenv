import json

from xml_parser import XMLParser

class AutoPyScript:
    def __init__(self, xml_file_path: str):
        """
        初始化类，从XML里build json data。
        :param xml_file_path: XML文件路径
        """
        
        #get data from XML use XMLParser
        self.parser = XMLParser(xml_file_path)
        self.parser.xml_to_json()
        self.data = self.parser.json_data

        self.unique_data = self._remove_page_level_duplicates()
        self.page_name_dict = self._create_page_name_dict()



    def _clean_field_name(self, field_name):
        """
        清理field_name，去掉[n:m]部分。
        例如：将 'tseq_err_cnt[15:0]' 转换为 'tseq_err_cnt'
        """
        if not field_name:
            return field_name
        return field_name.split('[')[0]

    def _create_page_name_dict(self):
        """
        从unique_data生成一个只包含PAGE name和field_name的字典。
        field_name会去掉[n:m]部分。
        """
        page_name_dict = {}
        for key, registers in self.unique_data.items():
            page_name_dict[key] = [
                self._clean_field_name(reg.get("field_name"))
                for reg in registers 
                if reg.get("field_name")
            ]
        return page_name_dict

    def _remove_page_level_duplicates(self):
        """
        在每个PAGE下去除重复的field_name。
        :return: 去重后的JSON数据
        """
        unique_data = {}
        for key, registers in self.data.items():
            seen_fields = set()
            unique_registers = []
            for register in registers:
                field_name = self._clean_field_name(register.get("field_name"))
                if field_name and field_name not in seen_fields:
                    unique_registers.append(register)
                    seen_fields.add(field_name)
            unique_data[key] = unique_registers
        return unique_data

    def print_field_names(self):
        """
        遍历JSON数据并打印field_name。
        """
        for key, registers in self.data.items():
            for register in registers:
                field_name = register.get("field_name")
                if field_name:
                    clean_name = self._clean_field_name(field_name)
                    print(f"{key}: {clean_name}")

    def print_page_level_unique_field_names(self):
        """
        打印每个PAGE下不重复的field_name。
        """
        for key, registers in self.unique_data.items():
            for register in registers:
                field_name = register.get("field_name")
                if field_name:
                    clean_name = self._clean_field_name(field_name)
                    print(f"{key}: {clean_name}")

    def _convert_to_valid_class_name(self, name: str) -> str:
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


# 使用示例
if __name__ == "__main__":
    xml_file = "d:/GS_Projects/gs_svn/gsu1001/eval/aves/gsu1001/GSU1K1_R3.xml"
    autopy = AutoPyScript(xml_file)
    #getter.print_page_level_unique_field_names()
    #print(getter.page_name_dict)

    output_file = "auto_class.py"
    autopy.generate_register_class_file(output_file)
