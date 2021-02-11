# encoding:utf-8
# 将几个常数移到 awpConstant 中。 2019-01-09 v0.2
# todo: 单个账户，改进可以同时处理多个合约，单一策略， 单一周期 v0.3
# todo：单个账户，改进可以同时处理多个合约，多个策略， 单一周期 v0.4
# todo：多账户， 单合约，单周期 v0.5
# todo：多账户， 多合约，单周期 v0.6
# todo: 多账户， 多合约，多周期 v0.7



from queue import Queue
import time
import json
from ctpapi import MyMdApi, MyTradeApi, ApiStruct
from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order, q_positions, q_server_info
from getaccount import getAccountinfo

from function import load_data_from_file, get_k_line_column, get_last_k_line, load_data_from_server, be_apart_from
from myfunction import HLV, HHV, LLV, MID, cross, CROSS

from tickToBar import tickToBar, q_bar
from awpConstant import *

# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('simnow24_ctp.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo(r'.\conf\simnowstd_ctp.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('CTP_tgjy_thm.json')
BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('.\conf\dfqhthm_ctp.json')

q_signals = Queue()

granularity = 780

serverport = 'http://192.168.1.15:8008'
# serverport = 'http://192.168.1.19:8008'

bars = dict()
data_path = r'./data/bar/rb/'
# barss = load_data_from_server(server_base=serverport, instruments_id=inst, granularity=granularity)
bars = load_data_from_file(instruments_id=inst, granularities='780', data_source_dir=data_path)


barinterval = inst + '_' + str(granularity)
bardatafile = data_path + barinterval + '.json'

# bars[barinterval] = barss
# O30 = get_k_line_column(bars, inst, 300, ohlc='open')
O = get_k_line_column(bars, inst, granularity, ohlc='open')
H = get_k_line_column(bars, inst, granularity, ohlc='high')
L = get_k_line_column(bars, inst, granularity, ohlc='low')
C = get_k_line_column(bars, inst, granularity, ohlc='close')

lastk = get_last_k_line(bars, inst, granularity)
print(lastk)

uperband = HHV(H, 23)
lowerband = LLV(L, 23)
dingdangline = MID(uperband, lowerband)
signalList = cross(C, dingdangline)
buysigdetail = CROSS(C, dingdangline)
sellsigdetail = CROSS(dingdangline, C)

knum = len(H)
signalall = buysigdetail.count(True)

avsigp = knum / signalall
# print(buysigdetail.count(True))
# print(sellsigdetail.count(True))
# print len(O)
print(('buy signal:', avsigp, buysigdetail[(knum - avsigp):]))
print(('sell signal:', avsigp, sellsigdetail[(knum - avsigp):]))

# print be_apart_from(buysigdetail)
# print be_apart_from(sellsigdetail)

# 计算发出信号时刻，最近平均信号距离内的信号数量
sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
sigsum4 = sigsum2 * 2
sigsum5 = sigsum4 if sellsigdetail[-1] or buysigdetail[-1] else 0
# pp = min((sigsum5+1)*10, 80)
# 计算下单仓位数量
pp = min((sigsum5 + 1), 8)

instlist = ['rb1905', 'rb1910', 'rb2001']

md = MyMdApi(instruments=instlist, broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
md.Create(INVESTOR_ID + "data")
md.RegisterFront(ADDR_MD)
md.Init()


td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
td.RegisterFront(ADDR_TD)
td.SubscribePublicTopic(1)
td.SubscribePrivateTopic(1)

td.Init()

lastErrorID = 0

bkprofits = []
skprofits = []
sigprofit_info = []
posratio = []


def dingdangno6bksp(md,td,instid, instrumentid):
    while True:
        time.sleep(0.3)
        if not md.q_depth_market_data.empty():

            tick = q_depth_market_data.get()
            tickToBar(tick, granularity)

            dayopen = tick.OpenPrice
            dayhigh = tick.HighestPrice
            daylow = tick.LowestPrice
            dayavp = int(tick.AveragePrice / 10)
            BB = (tick.LastPrice - daylow) / (dayhigh - daylow) if dayhigh != daylow else 0.5
            siglast = min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail))

            quote_info = "合约：{0},当前价格:{price},时间:{ttime},日内振幅：{1},价格位置：{2} 做多信号：{3},做空信号：{4}"
            print(quote_info.format(tick.InstrumentID,dayhigh - daylow,BB, buysigdetail.count(True),sellsigdetail.count(True), price=tick.LastPrice, ttime = tick.UpdateTime))
            quote_info1 = "合约：{instid},日内振幅：{zhenfu},价格位置：{BB:.3f} 做多信号：{buynum},做空信号：{sellnum},信号距离:{siglast}"

            info= {'instid': tick.InstrumentID,
            'zhenfu' : dayhigh - daylow,
            'buynum' : buysigdetail.count(True),
            'sellnum' : sellsigdetail.count(True),
            'BB':BB,
            'siglast': siglast}
            print(quote_info1.format(**info))

            knum = len(H)
            signalall = buysigdetail.count(True)

            avsigp = knum / signalall

            # sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
            # sigsum4 = sigsum2 * 2
            # sigsum5 = sigsum4 if sellsigdetail[-1] or buysigdetail[-1] else 0
            #
            # pp = min((sigsum5 + 1), 8)

            buysigprice = C[len(C) - be_apart_from(buysigdetail)]
            sellsigprice = C[len(C) - be_apart_from(sellsigdetail)]

            sellsigprice1 = C[-1] if sellsigdetail[-1] else 0   # 另外一种方法。

            lastsig = 'SK' if be_apart_from(buysigdetail) > be_apart_from(sellsigdetail) else 'BK'

            # if buysigdetail[-1] or sellsigdetail[-1]:
            #     knum = len(H)
            #     signalall = buysigdetail.count(True)
            #     avsigp = knum / signalall
            #     sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
            #     sigsum3 = sigsum2 * 2
            #
            #     pp = min((sigsum3 + 1), 8)
            #     posratio.append(pp)

            if lastsig == 'BK':

                bkprofit = tick.LastPrice - buysigprice
                bkprofits.append(bkprofit)

                bkpmax = max(bkprofits) if bkprofits else 0
                bkpmin = min(bkprofits) if bkprofits else 0

                print(INVESTOR_ID, '当前信号:', lastsig, '信号价:', buysigprice, tick.LastPrice, '盈利价差:', bkprofit, '最大:', bkpmax, '最小', bkpmin, '持续周期:', be_apart_from(buysigdetail), '理论持仓', pp)
                sigprofit_info.append([lastsig, bkpmax, bkpmin])
                print(('buy signal:', avsigp, buysigdetail[(knum - avsigp):], pp))
            elif lastsig == 'SK':
                skprofit = sellsigprice - tick.LastPrice
                skprofits.append(skprofit)

                skpmax = max(skprofits) if skprofits else 0
                skpmin = min(skprofits) if skprofits else 0

                print('当前信号:', lastsig, '信号价：', sellsigprice, sellsigprice1, tick.LastPrice, '盈利价差:', skprofit, '最大:', skpmax, '最小', skpmin, '持续周期:',be_apart_from(sellsigdetail))
                sigprofit_info.append([lastsig, max(skprofits), min(skprofits)])
                print(('sell signal:', avsigp, sellsigdetail[(knum - avsigp):], pp))


            # print tick.InstrumentID, dayhigh - daylow, BB, buysigdetail.count(True), sellsigdetail.count(True), min(
            #     be_apart_from(buysigdetail), be_apart_from(sellsigdetail))

            if not q_signals.empty():
                lastsig = q_signals.get()
                print(lastsig)

            O = get_k_line_column(bars, inst, granularity, ohlc='open')
            H = get_k_line_column(bars, inst, granularity, ohlc='high')
            L = get_k_line_column(bars, inst, granularity, ohlc='low')
            C = get_k_line_column(bars, inst, granularity, ohlc='close')

            lastk = get_last_k_line(bars, 'rb1905', 780)
            print(lastk)

            uperband = HHV(H, 23)
            lowerband = LLV(L, 23)
            dingdangline = MID(uperband, lowerband)
            signalList = cross(C, dingdangline)
            buysigdetail = CROSS(C, dingdangline)
            sellsigdetail = CROSS(dingdangline, C)

            knum = len(H)
            signalall = buysigdetail.count(True)

            avsigp = knum / signalall

            # print(buysigdetail.count(True))
            # print(sellsigdetail.count(True))
            print('叮  当: ', dingdangline[(knum - avsigp):])
            print('收盘价: ', C[(knum - avsigp):])
            print(('buy signal:', avsigp, buysigdetail[(knum - avsigp):]))
            print(('sell signal:', avsigp, sellsigdetail[(knum - avsigp):]))

        if not q_bar.empty():

            bar = q_bar.get()
            bars[barinterval].append(bar)

            with open(bardatafile, 'a') as f:
                f.writelines(json.dumps(bar, ensure_ascii=False) + '\n')

            print(len(bars[barinterval]))


            # bar_s = dict()
            # barss = load_data_from_server(server_base=serverport, instruments_id=inst, granularity=granularity)
            # barinterval = inst + '_' + str(granularity)
            # bar_s[barinterval] = barss
            # print len(bar_s[barinterval])

            lastk = get_last_k_line(bars, 'rb1905', 780)
            print(lastk)

            # O30 = get_k_line_column(bars, inst, 300, ohlc='open')
            O = get_k_line_column(bars, inst, granularity, ohlc='open')
            H = get_k_line_column(bars, inst, granularity, ohlc='high')
            L = get_k_line_column(bars, inst, granularity, ohlc='low')
            C = get_k_line_column(bars, inst, granularity, ohlc='close')
            uperband = HHV(H, 23)
            lowerband = LLV(L, 23)
            dingdangline = MID(uperband, lowerband)
            signalList = cross(C, dingdangline)
            buysigdetail = CROSS(C, dingdangline)
            sellsigdetail = CROSS(dingdangline, C)

            knum = len(H)
            signalall = buysigdetail.count(True)

            avsigp = knum / signalall

            # print(buysigdetail.count(True))
            # print(sellsigdetail.count(True))

            print(('buy signal:', avsigp, buysigdetail[(knum - avsigp):]))
            print(('sell signal:', avsigp, sellsigdetail[(knum - avsigp):]))

            print(min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail)))
            # print be_apart_from(sellsigdetail)

            # if buysigdetail[-1] or sellsigdetail[-1]:  # 发出交易信号并确认，计算下单仓位
            #     knum = len(H)
            #     signalall = buysigdetail.count(True)
            #     avsigp = knum / signalall
            #     sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
            #     sigsum3 = sigsum2 * 2
            #
            #     pp = min((sigsum3 + 1), 8)
            #     posratio.append(pp)



            if buysigdetail[-1]:
                bkprofits = []
                signal = {'date_time': time.time(), 'signaltype': 'BK', 'signalprice': tick.LastPrice}
                q_signals.put(signal)

                knum = len(H)
                signalall = buysigdetail.count(True)
                avsigp = knum / signalall
                sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
                sigsum3 = sigsum2 * 2

                pp = min((sigsum3 + 1), 8)

                order_price = tick.LastPrice

                td.PrepareOrder(tick.InstrumentID, b, k, pp, order_price)



            if sellsigdetail[-1]:
                skprofits = []
                signal = {'date_time': time.time(), 'signaltype': 'SK', 'signalprice': tick.LastPrice}
                q_signals.put(signal)

                order_price = tick.LastPrice

                # TODO 暂时没有处理平昨仓和今仓,待处理... 应该有个完整的策略持仓管理模块
                if bkprofit > 0:
                    td.PrepareOrder(tick.InstrumentID, s, p, pp, order_price)

                # spk
                sellcount = 0
                down_trading_flag = False
                # if not down_trading_flag and tick.LastPrice < get_last_k_line(bars,'rb1905',780)['low']:
                #     down_trading_flag = True
                #     sellcount +=1
                #     sk(pp) #
                #
                # pass
            # else:
            #     if not q_signals.empty():
            #         lastsig = q_signals.get()  # 是否最后一个信号，如何判断。
            #         print(lastsig)


if __name__=='__main__':

    while True:
        if not td.q_server_info.empty():
            info = td.q_server_info.get()
            # print info.ErrorID
            lastErrorID = info.ErrorID
            print('the last ErrorID is: ', lastErrorID, td.investor_id, td.broker_id)
        if lastErrorID == 7 or lastErrorID == 8:
            # print 'release the api...'
            # td.Release()
            print('reconnect the trading server.')
            del td
            td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
            td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
            td.RegisterFront(ADDR_TD)
            td.SubscribePublicTopic(0)
            td.SubscribePrivateTopic(0)
            # td.ReqUserLogout()
            td.Init()
            time.sleep(60)
