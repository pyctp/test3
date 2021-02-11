#encoding:utf-8
#bar data file transfer: from tianqin to awp

import json

infile = 'rb1905_60.csv'
outfile = 'rb1905_60.json'
klines = list()

with open(infile) as f:
    for i, line in enumerate(f):

        # 忽略 csv 头
        if i == 0:
            continue
        #读取数据行，赋值给变量
        date_time, topen, thigh, tlow, tclose = line.split(',')
        #print date_time, topen, thigh, tlow, tclose
        #转换为字典格式
        k_line = {'open': float(topen), 'high': float(thigh), 'low': float(tlow), 'close': float(tclose),'date_time': date_time}

        #append到k线列表中
        klines.append(k_line)

        # 查看格式是否正确
        # print date_time, topen, thigh, tlow, tclose
        # print len(klines)

with open(outfile,'a') as f:
    for kline in klines:
        f.writelines(json.dumps(kline, ensure_ascii=False) + '\n')
    f.close()


    '''
    天勤格式：
    datetime,last_price,bid_price1,ask_price1,volume,open_interest
    2018-05-15 18:35:32,nan,nan,nan,0,0
    2018-05-15 20:59:00,3420.0,3400.0,3420.0,4,4
    2018-05-15 21:00:00,3420.0,3402.0,3425.0,10,10
    2018-05-15 21:00:01,3425.0,3420.0,3425.0,12,12
    2018-05-15 21:00:01,3425.0,3422.0,3425.0,12,12
    2018-05-15 21:00:04,3425.0,3422.0,3425.0,14,14

    tb格式：
    时间,最新价,申卖价,申买价,现手,持仓量
    2018/11/05 11:08:20.000,4032,4033,4032,50,2677056
    2018/11/05 11:08:20.500,4033,4033,4032,52,2677038
    2018/11/05 11:08:21.000,4032,4032,4031,210,2677046
    2018/11/05 11:08:21.500,4033,4033,4032,626,2677614
    2018/11/05 11:08:22.000,4033,4033,4032,2,2677614

    '''
