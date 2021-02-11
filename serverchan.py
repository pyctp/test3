# encoding:utf-8
import requests
api = "https://sc.ftqq.com/SCU46429Tf30e7ae9d7379a36e2caa81c020a328f5c8a6de9cc3b4.send"
title = "准备开盘了。"
content = """
还没有起床吗？
"""
data = { "text":title, "desp":content }
req = requests.post(api,data = data)


def push(self, result):
    title = "TPYBoardv202提示您:注意天气变化保持健康心情"
    content = 'text=' + title + '&' + 'desp=' + result
    url = "https://sc.ftqq.com/SCU9545T6a65dcc064b04f78364fc3e6df6593c45951abe4d7219.send?%s" % content
    r = urequests.get(url)
    r.close()

def pushmsg():
    # coding=utf-8
    import requests

    key = "SCU46429Tf30e7ae9d7379a36e2caa81c020a328f5c8a6de9cc3b4"  # your-key
    url = "https://sc.ftqq.com/%s.send" % (key)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}

    payload = {'text': 'Server酱提醒', 'desp': 'Python用Server酱推送微信模板消息'}
    requests.post(url, params=payload, headers=headers)