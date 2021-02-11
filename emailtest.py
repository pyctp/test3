#encoding:utf-8

from emailNotify import mailsender
import time
info = 'just another test. pls ignore it. thank you.'+ time.ctime()
# receivers = ['vnctp@qq.com','tianhm2012@foxmail.com','smartmanp@qq.com','2509055963@qq.com','zjy1301@qq.com']
receivers = ['vnctp@qq.com','tianhm2012@foxmail.com','smartmanp@qq.com','zjy1301@qq.com']

mailsender(info, receivers)
