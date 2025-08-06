from setuptools import setup, find_packages

setup(
    name="py_testenv",       # 包名（pip install时用）
    version="0.0.1",         # 版本号
    packages=find_packages(), # 自动发现包
    package_data={
        "py_testenv": ["libMPSSE.dll"],  # DLL放在py_testenv目录下
    },
    install_requires=[
        "openpyxl",          # Excel导出依赖
    ],
    author="yfzhao",
    description="Python3 i2c eval env via ftdi4232, AVES/寄存器脚本自动生成",
    url="https://github.com/zhaoyifei100/py_testenv", # 可选
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)