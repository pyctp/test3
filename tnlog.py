#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import inspect

'''
import inspect
def test():
    a = inspect.stack()[1]
    print a

得到一个元组，如：
(<frame object at 0x8604aa4>, 'test.py', 10, 'function_one', ['\t\tprint get_current_function_name()\n'], 0)

a = inspect.stack()[1]
该行代码所在函数（被调函数）栈幀是0，根据调用的顺序，这个调用链条上的函数栈幀偏移值递增1
a -> b -> c （a调用b,b调用c）c中通过inspect获得栈幀集合，对于c来说
函数b的栈幀是inspect.stack()[1],函数a的栈幀是inspect.stack()[2]



那么这个元组的分别是：(调用者的栈对象，调用者的文件名，调用行数，调用者函数名，调用代码，0)
最后的0未知其含义
'''


class Logger(object):
    def printfNow(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def __init__(self, logfilename='tnlog-info.log'):
        self.__logger = logging.getLogger()
        self.logfilename = logfilename
        path = os.path.abspath(self.logfilename)
        handler = logging.FileHandler(path)
        self.__logger.addHandler(handler)
        self.__logger.setLevel(logging.NOTSET)

    def getLogMessage(self, level, message):
        # message = "[%s] %s " %(self.printfNow(),message)

        frame, filename, lineNo, functionName, code, unknowField = inspect.stack()[2]
        '''日志格式：[时间] [类型] [记录代码] 信息'''
        return "[%s] [%s] [%s - %s - %s] %s" % (self.printfNow(), level, filename, lineNo, functionName, message)

    def info(self, message):
        message = self.getLogMessage("info", message)
        self.__logger.info(message)

    def error(self, message):
        message = self.getLogMessage("error", message)
        self.__logger.error(message)

    def warning(self, message):
        message = self.getLogMessage("warning", message)
        self.__logger.warning(message)

    def debug(self, message):
        message = self.getLogMessage("debug", message)
        self.__logger.debug(message)

    def critical(self, message):
        message = self.getLogMessage("critical", message)
        self.__logger.critical(message)


# logger = consoleLog()

if __name__ == "__main__":
    logger = Logger()
    logger.info("hello")