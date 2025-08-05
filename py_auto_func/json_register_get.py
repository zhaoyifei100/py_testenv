import json

class JSONRegisterGet:
    def __init__(self, json_file_path):
        """
        初始化类，加载JSON文件。
        :param json_file_path: JSON文件路径
        """
        self.json_file_path = json_file_path
        self.data = self._load_json()
        self.unique_data = self._remove_page_level_duplicates()
        self.page_name_dict = self._create_page_name_dict()

    def _load_json(self):
        """
        加载JSON文件内容。
        :return: JSON数据
        """
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

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

# 使用示例
if __name__ == "__main__":
    json_file = "GSU1K1_R3_Register_Config.json"
    getter = JSONRegisterGet(json_file)
    # getter.print_page_level_unique_field_names()
    print(getter.page_name_dict)
