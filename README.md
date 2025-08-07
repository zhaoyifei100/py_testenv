# py_testenv

寄存器自动化脚本与AVES脚本转换工具包

## 目录结构

```
py_testenv/
├── __init__.py
├── auto_py_script.py      # 自动化寄存器类生成与脚本批量替换
├── get_aves.py           # AVES脚本转Python/C脚本
├── get_aves_def.py       # I2C底层驱动适配
├── drv_ftdi.py           # FTDI I2C驱动
├── drv_pi.py             # 树莓派I2C驱动
├── xml_parser.py         # XML寄存器解析
├── ...
```

## 主要类与功能

### 1. AutoPyScript
- **功能**：
  - 解析XML寄存器配置，自动生成寄存器结构的JSON数据。
  - 支持去重、清理、分组寄存器字段。
  - 可自动生成Python寄存器访问类文件。
  - 支持批量替换Python脚本中的寄存器操作（AutoClass标记行自动生成真实读写代码）。
- **典型用法**：
```python
from py_testenv import AutoPyScript

auto = AutoPyScript(xml_file_path="your.xml", aves_script_name="your_aves.txt")
# 生成寄存器类文件
auto.generate_register_class_file("auto_class.py")
# 批量替换脚本中的AutoClass寄存器操作
auto.auto_register_build("your_script.py")
```

### 2. GetAVES
- **功能**：
  - 将AVES脚本转换为Python脚本、C头文件、C源文件。
  - 支持寄存器定义自动生成。
- **典型用法**：
```python
from py_testenv import GetAVES

aves = GetAVES(xml_file_path="your.xml", aves_script_name="your_aves.txt")
aves.buildall()  # 一键生成所有脚本
```

## 典型工作流

-STEP1 AVES脚本批量转换：
  1. 用GetAVES一键生成Python/C脚本。

-STEP2 解析XML，生成寄存器类和批量脚本：
  1. 用AutoPyScript生成寄存器类文件。
  2. 用auto_register_build批量替换脚本中的AutoClass寄存器操作。


## 贡献与反馈

如有问题或建议，欢迎提交issue或PR。

---
