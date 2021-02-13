# encoding:utf-8
# 将几个常数移到 awpConstant 中。 2019-01-09
# import six

from six.moves.queue import Queue

# try:
#     from queue import Queue
# except:
#     from Queue import Queue

import time
import json
# from ctpapi import MyMdApi, MyTradeApi, ApiStruct
# from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order, q_positions, q_server_info
from getaccount import getAccountinfo

from function import load_data_from_file, get_k_line_column, get_last_k_line, load_data_from_server, be_apart_from
from myfunction import HLV, HHV, LLV, MID, cross, CROSS, cross2, MA
from myfunction import stringToDate
from tickToBar_backplay import tickToBar, q_bar
from vtObject import VtTickData
from awpConstant import *

from tnlog import Logger

q_depth_market_data = Queue()

strategy_name = 'dingdangNo6'
q_signals = Queue()

inst = 'rb1905'
granularity = 780

serverport = 'http://192.168.1.15:8008'
# serverport = 'http://192.168.1.19:8008'

bars = dict()
allSignal = list()


def tickDataReplay():
    datafile = r"D:\qhreal\test\data\bar\rb\rb1905_780.json"

    with open(datafile) as f:
        for i, line in enumerate(f):

            # 忽略 csv 头
            if i == 0:
                continue

            # date_time, tlastPrice, tbidPrice1, taskPrice1, tvolume, topenInt ,t1,t2, t3,t4,t5,t6,t7= line.split(',')

            row = line.split(',')
            if row[1] == 'nan':
                continue

            date_time = row[0]

            dt = stringToDate(date_time.split(' ')[1].split('.')[0]).time()

            # dt = stringToDate(row[0].split(' ')[1]).time()

            ddate = row[0].split()[0]
            dtime = row[0].split()[1][0:12]
            # dtime = row[0].split()[1][0:9]
            tick = VtTickData()

            tick.InstrumentID = 'rb1905'
            tick.ActionDay = ddate
            tick.UpdateTime = dtime
            tick.LastPrice = float(row[1])
            tick.Volume = int(float(row[6]))

            q_depth_market_data.put(tick)

            if q_depth_market_data.qsize() > 10000:
                time.sleep(1)


def barDataReplay(barfile=r"./data/bar/rb/rb1905_300.json"):
    barfile = barfile

    with open(barfile, 'r') as f:
        for line in f:
            json_k_line = json.loads(line.strip())
            q_bar.put(json_k_line)


# data_path = r'./data/bar/rb/'
# barss = load_data_from_server(server_base=serverport, instruments_id=inst, granularity=granularity)
# bars = load_data_from_file(instruments_id=inst, granularities='780', data_source_dir=data_path)
barinterval = inst + '_' + str(granularity)
# bardatafile = data_path + barinterval + '.json'
#

bars[barinterval] = []

instlist = ['rb1905']

bkprofits = []
skprofits = []
sigprofit_info = []
posratio = []


def getPositionRatio(sigdetail):
    '''不下马策略，或者反手策略仓位比例计算'''
    # todo:确认传入的参数正确
    knum = len(sigdetail)
    signalall = sigdetail.count(True)
    if signalall > 0:

        avsigp = int(knum / signalall)

        sigsum2 = sigdetail[(knum - avsigp):-2].count(True) * 2
        sigsum4 = sigsum2 * 2
        sigsum5 = sigsum4 if sigsum4 > 1 else 1
        sigsum5 = sigsum4 if sigdetail[-1] else 0
        posratio = min((sigsum5 + 1) * 10, 80)

        # 计算下单仓位数量
        # posratio = min(sigsum5 * 10, 80)
        return posratio / 100.

    else:
        return 0


def today():
    '''return today'''
    from datetime import time, datetime
    today = datetime.now().strftime('%Y-%m-%d')
    return today


def dingdangNo6():
    st = time.time()

    lastsig = ''
    initFund = 500000
    fundNow = initFund
    fundTemp = fundNow
    pp = 0
    fundList = list()

    initFundReal = 500000
    fundNowReal = initFundReal
    fundTempReal = fundNowReal
    sigAllReal = list()
    PPReal = 0
    fundListReal = list()
    skprofitReal = 0
    bkprofitReal = 0

    profitlist = []
    losslist = []





    Signals = list()


    skprofit = 0
    bkprofit = 0

    bkloss = 0
    skloss = 0

    feeRatio = 0.0065
    instMultifier = 10
    signalslist = list()

    while True:

        if not q_depth_market_data.empty():
            tick = q_depth_market_data.get()

            tickToBar(tick, granularity)

            # dayopen = tick.OpenPrice
            # dayhigh = tick.HighestPrice
            # daylow = tick.LowestPrice
            # dayavp = int(tick.AveragePrice / 10)
            # BB = (tick.LastPrice - daylow) / (dayhigh - daylow) if dayhigh != daylow else 0.5
            # siglast = min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail))

            # quote_info = "合约：{0},当前价格:{price},时间:{ttime},日内振幅：{1},价格位置：{2} 做多信号：{3},做空信号：{4}"
            # # print quote_info.format(tick.InstrumentID,dayhigh - daylow,BB, buysigdetail.count(True),sellsigdetail.count(True), price=tick.LastPrice, ttime = tick.UpdateTime)
            # quote_info1 = "合约：{instid},日内振幅：{zhenfu},价格位置：{BB:.3f} 做多信号：{buynum},做空信号：{sellnum},信号距离:{siglast}"

            # info= {'instid': tick.InstrumentID,
            # 'zhenfu' : dayhigh - daylow,
            # 'buynum' : buysigdetail.count(True),
            # 'sellnum' : sellsigdetail.count(True),
            # 'BB':BB,
            # 'siglast': siglast}
            # # print quote_info1.format(**info)

            # knum = len(H)
            # signalall = buysigdetail.count(True)
            # avsigp = knum / signalall
            # buysigprice = C[len(C) - be_apart_from(buysigdetail)]
            # sellsigprice = C[len(C) - be_apart_from(sellsigdetail)]
            # sellsigprice1 = C[-1] if sellsigdetail[-1] else 0   # 另外一种方法。
            #
            # lastsig = 'SK' if be_apart_from(buysigdetail) > be_apart_from(sellsigdetail) else 'BK'

        if not q_signals.empty():
            lastsigdict = q_signals.get()
            allSignal.append(lastsigdict)

            print(lastsigdict)

            # O = get_k_line_column(bars, inst, granularity, ohlc='open')
            # H = get_k_line_column(bars, inst, granularity, ohlc='high')
            # L = get_k_line_column(bars, inst, granularity, ohlc='low')
            # C = get_k_line_column(bars, inst, granularity, ohlc='close')
            #
            # lastk = get_last_k_line(bars, 'rb1905', 780)
            # print lastk
            #
            # uperband = HHV(H, 23)
            # lowerband = LLV(L, 23)
            # dingdangline = MID(uperband, lowerband)
            # signalList = cross(C, dingdangline)
            # buysigdetail = CROSS(C, dingdangline)
            # sellsigdetail = CROSS(dingdangline, C)
            #
            # knum = len(H)
            #
            # signalall = buysigdetail.count(True)
            #
            # avsigp = knum / signalall if signalall > 0 else knum
            #
            # # print(buysigdetail.count(True))
            # # print(sellsigdetail.count(True))
            # print u'叮  当: ', dingdangline[(knum - avsigp):]
            # print u'收盘价: ', C[(knum - avsigp):]
            # # print('buy signal:', avsigp, buysigdetail[(knum - avsigp):])
            # # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):])

        if not q_bar.empty():

            bar = q_bar.get()
            bars[barinterval].append(bar)

            # with open(bardatafile, 'a') as f:
            #     f.writelines(json.dumps(bar, ensure_ascii=False) + '\n')

            # print len(bars[barinterval])
            ed = time.time()
            lastk = get_last_k_line(bars, inst, granularity)
            print(lastk, len(bars[barinterval]), ed-st)

            O = get_k_line_column(bars, inst, granularity, ohlc='open')
            H = get_k_line_column(bars, inst, granularity, ohlc='high')
            L = get_k_line_column(bars, inst, granularity, ohlc='low')
            C = get_k_line_column(bars, inst, granularity, ohlc='close')
            dt = lastk['date_time']


            HH = H[-50:]
            LL = L[-50:]
            CC = C[-50:]
            
            uperband = HHV(HH, 23)
            lowerband = LLV(LL, 23)
            dingdangline = MID(uperband, lowerband)

            if cross2(C[-2:], dingdangline[-2:]):
                signalslist.append('bk')
            elif cross2(dingdangline[-2:], C[-2:], ):
                signalslist.append('sk')
            else:
                signalslist.append(None)

            signalList = cross(CC, dingdangline)
            buysigdetail = CROSS(CC, dingdangline)
            sellsigdetail = CROSS(dingdangline, CC)

            knum = len(H)

            signalall = signalslist.count('bk') + signalslist.count('sk') + signalslist.count('bp') + signalslist.count(
                'sp')

            # signalall1 = buysigdetail.count(True) + sellsigdetail.count(True)
            #
            # avsigp = knum / signalall if signalall > 0 else knum

            # print('buysig all:',buysigdetail.count(True))
            # print('sellsig all:', sellsigdetail.count(True))

            # print('buy signal:', avsigp, buysigdetail[(knum - avsigp):])
            # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):])

            # print min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail))
            # print be_apart_from(sellsigdetail)
            # pp= getPositionRatio(buysigdetail)

            if buysigdetail[-1]:
                fundTemp += skprofit * pp * instMultifier - (pp * instMultifier * C[-1] * 1.11 / 10000) * 2
                fundratio = getPositionRatio(sellsigdetail)
                fundToUse = fundratio * fundTemp
                unitPrice = C[-1]*10*0.15

                pp = int(fundToUse/unitPrice)
                if skprofit >0:
                    profitlist.append(skprofit)
                else:
                    losslist.append(skprofit)
                bkprofits = []

                signal = {'date_time': dt, 'signaltype': 'BK', 'signalprice': C[-1], 'pos': pp}
                q_signals.put(signal)

                Signals.append(signal)


                # with open('allsignal.json', 'a') as f:
                #     f.writelines(json.dumps(signal, ensure_ascii=False) + '\n')

                order_price = C[-1]

                # td.PrepareOrder(tick.InstrumentID, b, k, pp, order_price)
                # log.info(log.printfNow() + u'下多单:' + str(pp) + ',orderprice:'+str(order_price))

                print('buy order issued.')
                lastsig = 'BK'
                buysigprice = C[-1]
                print('buysigprice', buysigprice)

            if sellsigdetail[-1]:
                fundTemp += bkprofit * pp * instMultifier - (pp * instMultifier * C[-1] * 1.11 / 10000) * 2
                fundratio = getPositionRatio(buysigdetail)
                fundToUse = fundTemp * fundratio
                unitPrice = C[-1] * 10 * 0.15

                pp = int(fundToUse / unitPrice)
                if bkprofit >0:
                    profitlist.append(bkprofit)
                else:
                    losslist.append(bkprofit)


                skprofits = []

                signal = {'date_time': dt, 'signaltype': 'SK', 'signalprice': C[-1], 'pos': pp}
                q_signals.put(signal)

                Signals.append(signal)

                # with open('allsignal.json', 'a') as f:
                #     f.writelines(json.dumps(signal, ensure_ascii=False) + '\n')

                # order_price = tick.LastPrice
                #
                # # TODO 暂时没有处理平昨仓和今仓,待处理... 应该有个完整的策略持仓管理模块
                #
                # td.PrepareOrder(tick.InstrumentID, s, p, pp, order_price)
                #
                # log.info(log.printfNow() + u'平多单:' + str(pp) + ',orderprice:'+str(order_price))
                # print('close order issued...')

                lastsig = 'SK'
                sellsigprice = C[-1]

                print('sellsigprice', sellsigprice)

            if lastsig == 'BK':
                # print tick.LastPrice, buysigprice

                bkprofit = C[-1] - buysigprice
                print('多单盈利价差', bkprofit)

                bkprofits.append(bkprofit)

                bkpmax = max(bkprofits) if bkprofits else 0
                bkpmin = min(bkprofits) if bkprofits else 0

                print('当前信号:', lastsig, '信号价:', buysigprice, '当前价: ', C[
                    -1], '仓位', pp, '盈利价差:', bkprofit, '最大:', bkpmax, '最小', bkpmin, '持续周期:', be_apart_from(
                    buysigdetail), '理论持仓', pp)
                sigprofit_info.append([lastsig, bkpmax, bkpmin])
                # print('buy signal:', avsigp, buysigdetail[(knum - avsigp):], pp)

                if len(bkprofits) >= 2:
                    fundNow = fundTemp + (bkprofits[-1]-bkprofits[-2]) * pp * instMultifier

            elif lastsig == 'SK':
                skprofit = sellsigprice - C[-1]
                skprofits.append(skprofit)

                skpmax = max(skprofits) if skprofits else 0
                skpmin = min(skprofits) if skprofits else 0

                # print u'当前信号:', lastsig, u'信号价：', sellsigprice, u'当前价: ', C[
                #     -1], u'盈利价差:', skprofit, u'最大:', skpmax, u'最小', skpmin, u'持续周期:', be_apart_from(sellsigdetail)

                print('当前信号:', lastsig, '信号价:', sellsigprice, '当前价: ', C[
                    -1], '仓位', pp, '盈利价差:', skprofit, '最大:', skpmax, '最小', skpmin, '持续周期:', be_apart_from(
                    buysigdetail), '理论持仓', pp)

                sigprofit_info.append([lastsig, max(skprofits), min(skprofits)])
                # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):], pp)
                if len(skprofits) >= 2:
                    fundNow = fundTemp + (skprofits[-1]-skprofits[-2]) * pp * instMultifier

            fundList.append(fundNow)
            fundListMa = MA(fundList, 23)

            getinlist = CROSS(fundList, fundListMa)
            getoutlist = CROSS(fundListMa, fundList)
            # print getinlist.count(True)

            if getinlist[-1]:
                sigReal = {'date_time':dt, 'signaltype':signal['signaltype'], 'signalprice': C[-1], 'pos':signal['pos']}
                # if len(sigAllReal)>1 and sigAllReal[-1]['signaltype']==sigReal['signalprice']:
                #     continue
                # else:

                sigAllReal.append(sigReal)

            elif getoutlist[-1]:
                sigReal = {'date_time': dt, 'signaltype': signal['signaltype'], 'signalprice': C[-1],
                           'pos': signal['pos']}
                # if len(sigAllReal)>1 and sigAllReal[-1]['signaltype']==sigReal['signalprice']:
                #     continue
                # else:

                sigAllReal.append(sigReal)
                sigNow = sigAllReal[-1]
                sigNow1 = sigReal

                if sigNow['signaltype'] == 'BK':
                    profitReal = C[-1] - sigNow['signalprice']

                if sigNow['signaltype'] == 'SK':
                    profitReal = sigNow['signalprice'] - C[-1]


                fundTempReal += profitReal * sigNow['pos'] * instMultifier - (pp * instMultifier * C[-1] * 1.11 / 10000) * 2




            print(max(fundList), min(fundList))

            print('初始权益：', initFund, '策略当前权益: ', fundNow, '账号1权益', fundTempReal)
            # time.sleep(1)

            # print tick.InstrumentID, dayhigh - daylow, BB, buysigdetail.count(True), sellsigdetail.count(True), min(
            #     be_apart_from(buysigdetail), be_apart_from(sellsigdetail))


def main():
    import threading

    play = threading.Thread(target=barDataReplay)
    play.start()

    dingdang = threading.Thread(target=dingdangNo6())
    dingdang.start()


if __name__ == '__main__':
    main()
