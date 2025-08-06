"""
py_testenv 包初始化文件
------------------------
本包用于寄存器脚本自动生成、AVES脚本转换、I2C驱动等。

包含主要模块：
- xml_parser
- get_aves
- auto_py_script
- drv_ftdi
- drv_pi
- get_aves_def

用法示例：
    import py_testenv.xml_parser
    import py_testenv.get_aves
    import py_testenv.auto_py_script
"""

# 可选：导入常用类
# from .xml_parser import XMLParser
# from .get_aves import GetAVES
from .auto_py_script import AutoPyScript
