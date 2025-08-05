from setuptools import setup, find_packages

setup(
    name="py_testenv",       # 包名（pip install时用）
    version="0.0.1",              # 版本号
    packages=find_packages(),      # 自动发现包
    package_data={
        "py_ftdi": ["libMPSSE.dll"],  # 包含DLL文件
    },
    install_requires=[],          # 依赖项（如需要可添加）
    author="yfzhao",
    description="Python3 icer i2c eval env via ftdi4232",
)