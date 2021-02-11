# encoding: UTF-8

import constants

# 将常量定义添加到vtConstant.py的局部字典中
d = locals()
for name in dir(constants):
    if '__' not in name:
        d[name] = constants.__getattribute__(name)
