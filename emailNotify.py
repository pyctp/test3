#encoding:utf-8

#发邮件的库
import smtplib
#邮件文本
from email.mime.text import MIMEText


def mailsender(info, receivers):
    if info is None or receivers is None:
        return 0

    receiverslist = receivers
    message = info

    #SMTP 服务器
    SMTPServer = 'smtp.qq.com'

    #发邮件的地址

    Sender = 'smartmanp@qq.com'

    passwd = 'oyjyxiqgbsfmbjhf'

    #发送的内容
    # message = '交易信号：东旭光电: 15分钟周期 买入 价格 5.80'

    #转换成邮件文本
    msg = MIMEText(message)

    #title or subject

    msg['Subject'] = '模拟交易下单通知！！！ '

    #receiver
    msg['From']=Sender

    mailServer = smtplib.SMTP(SMTPServer, 25)

    mailServer.login(Sender, passwd)

    mailServer.sendmail(Sender,receiverslist , msg.as_string())

    mailServer.quit()
