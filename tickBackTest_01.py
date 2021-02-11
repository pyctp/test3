# encoding:utf-8
from queue import Queue
import time
import json
from ctpapi import ApiStruct

from function import load_data_from_file, get_k_line_column, get_last_k_line, load_data_from_server, be_apart_from
from myfunction import HLV, HHV, LLV, MID, cross, CROSS
from myfunction import stringToDate
from tickToBar import tickToBar, q_bar
from Constant import LOGS_DIR

from vtObject import VtTickData

s = S = ApiStruct.D_Sell
b = B = ApiStruct.D_Buy
k = K = ApiStruct.OF_Open
p = P = ApiStruct.OF_Close
pj = PJ = ApiStruct.OF_CloseToday
pz = PZ = ApiStruct.OF_CloseYesterday


q_signals = Queue()
q_depth_market_data = Queue()

inst = 'rb1905'
granularity = 780
barinterval = inst + '_' + str(granularity)

bars = dict()

q_initdata = Queue()

def tickDataReplay():
    datafile = r"D:\qhreal\test\data\tick\rb1905tickcleaned.csv"
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
            tick.LastPrice = row[1]
            tick.Volume = row[6]

            q_depth_market_data.put(tick)

            if q_depth_market_data.qsize() > 10000:
                time.sleep(1)





def getPositionRatio(sigdetail):
    '''不下马策略，或者反手策略仓位比例计算'''
    # todo:确认传入的参数正确
    knum = len(sigdetail)
    signalall = sigdetail.count(True)
    if signalall > 0:

        avsigp = knum / signalall

        sigsum2 = sigdetail[(knum - avsigp):-2].count(True) * 2
        sigsum4 = sigsum2 * 2
        sigsum5 = sigsum4 if sigsum4 > 1 else 1
        sigsum5 = sigsum4 if sigdetail[-1] else 0
        posratio = min((sigsum5 + 1) * 10, 80)
        # 计算下单仓位数量
        # posratio = min(sigsum5 * 10, 80)
        return posratio
    else:
        return 0

# def initDataFromFile():
#     bars = load_data_from_file(instruments_id=inst, granularities='780', data_source_dir=data_path)
#     for bar in bars['rb1905_780']:
#         # print(bar)
#         q_initdata.put(bar)
#
#     bardatafile = data_path + barinterval + '.json'
#
#     return bardatafile
#
# barfile = initDataFromFile()



def initStrategy(q_initdata):
    bkprofits = []
    skprofits = []
    sigprofit_info = []
    posratio = []
    bkprofit = 0
    skprofit = 0

    initFund = 20000
    instMultifier = 10

    bars[barinterval] = list()

    while not q_initdata.empty():
        bar = q_initdata.get()
        bars[barinterval].append(bar)

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

        pp = getPositionRatio(buysigdetail)


        if buysigdetail[-1]:

            initFund += skprofit * pp * instMultifier
            bkprofits = []
            # signal = {'date_time': time.time(), 'signaltype': 'BK', 'signalprice': tick.LastPrice}
            # q_signals.put(signal)

            knum = len(H)
            signalall = buysigdetail.count(True)
            avsigp = knum / signalall
            sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
            sigsum3 = sigsum2 * 2

            pp = min((sigsum3 + 1), 8)

            # order_price = tick.LastPrice

            # td.PrepareOrder(tick.InstrumentID, b, k, pp, order_price)
            # log.info(log.printfNow() + u'下多单:' + str(pp) + ',orderprice:' + str(order_price))

            print('buy order issued.')

        if sellsigdetail[-1]:

            initFund += bkprofit * pp * instMultifier
            skprofits = []
            signal = {'date_time': time.time(), 'signaltype': 'SK', 'signalprice': tick.LastPrice}
            q_signals.put(signal)

            order_price = tick.LastPrice

            # TODO 暂时没有处理平昨仓和今仓,待处理... 应该有个完整的策略持仓管理模块

            td.PrepareOrder(tick.InstrumentID, s, p, pp, order_price)

            log.info(log.printfNow() + '平多单:' + str(pp) + ',orderprice:' + str(order_price))
            print('close order issued...')

            # spk
            sellcount = 0
            down_trading_flag = False

        knum = len(H)
        signalall = buysigdetail.count(True)

        if signalall>0:
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



# initStrategy(q_initdata)


bkprofits = []
skprofits = []
sigprofit_info = []

tickfile = r"D:\qhreal\test\data\tick\rb1905tickcleaned.csv"

# tickDataReplay(r"D:\qhreal\test\data\tick\rb1905tickcleaned.csv")
bars['rb1905_780'] = []

tradingsignals = list()

def dingdangNo6():

    while True:

        if not q_depth_market_data.empty():

            tick = q_depth_market_data.get()
            q_depth_market_data.task_done()

            tickToBar(tick, granularity)

            # dayopen = tick.OpenPrice
            # dayhigh = tick.HighestPrice
            # daylow = tick.LowestPrice
            # dayavp = int(tick.AveragePrice / 10)
            # BB = (tick.LastPrice - daylow) / (dayhigh - daylow) if dayhigh != daylow else 0.5
            # siglast = min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail))

            # quote_info = "合约：{0},当前价格:{price},时间:{ttime},日内振幅：{1},价格位置：{2} 做多信号：{3},做空信号：{4}"
            # print quote_info.format(tick.InstrumentID,dayhigh - daylow,BB, buysigdetail.count(True),sellsigdetail.count(True), price=tick.LastPrice, ttime = tick.UpdateTime)
            # quote_info1 = "合约：{instid},日内振幅：{zhenfu},价格位置：{BB:.3f} 做多信号：{buynum},做空信号：{sellnum},信号距离:{siglast}"
            #
            # info= {'instid': tick.InstrumentID,
            # 'zhenfu' : dayhigh - daylow,
            # 'buynum' : buysigdetail.count(True),
            # 'sellnum' : sellsigdetail.count(True),
            # 'BB':BB,
            # 'siglast': siglast}
            # print quote_info1.format(**info)

            # knum = len(H)
            # signalall = buysigdetail.count(True)
            #
            # avsigp = knum / signalall
            #
            # sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
            # sigsum4 = sigsum2 * 2
            # sigsum5 = sigsum4 if sellsigdetail[-1] or buysigdetail[-1] else 0
            #
            # pp = min((sigsum5 + 1), 8)

            # buysigprice = C[len(C) - be_apart_from(buysigdetail)]
            # sellsigprice = C[len(C) - be_apart_from(sellsigdetail)]
            #
            # sellsigprice1 = C[-1] if sellsigdetail[-1] else 0   # 另外一种方法。
            #
            # lastsig = 'SK' if be_apart_from(buysigdetail) > be_apart_from(sellsigdetail) else 'BK'
            #
            # if lastsig == 'BK':
            #
            #     bkprofit = tick.LastPrice - buysigprice
            #     bkprofits.append(bkprofit)
            #
            #     bkpmax = max(bkprofits) if bkprofits else 0
            #     bkpmin = min(bkprofits) if bkprofits else 0
            #
            #     print u'当前信号:', lastsig, u'信号价:', buysigprice, tick.LastPrice, u'盈利价差:', bkprofit, u'最大:', bkpmax, u'最小', bkpmin, u'持续周期:', be_apart_from(buysigdetail)
            #     sigprofit_info.append([lastsig, bkpmax, bkpmin])
            #     print('buy signal:', avsigp, buysigdetail[(knum - avsigp):], pp)
            # elif lastsig == 'SK':
            #     skprofit = sellsigprice - tick.LastPrice
            #     skprofits.append(skprofit)
            #
            #     skpmax = max(skprofits) if skprofits else 0
            #     skpmin = min(skprofits) if skprofits else 0

                # print u'当前信号:', lastsig, u'信号价：', sellsigprice, sellsigprice1, tick.LastPrice, u'盈利价差:', skprofit, u'最大:', skpmax, u'最小', skpmin, u'持续周期:',be_apart_from(sellsigdetail)
                # sigprofit_info.append([lastsig, max(skprofits), min(skprofits)])
                # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):], pp)


            # print tick.InstrumentID, dayhigh - daylow, BB, buysigdetail.count(True), sellsigdetail.count(True), min(
            #     be_apart_from(buysigdetail), be_apart_from(sellsigdetail))

            if not q_signals.empty():
                lastsig = q_signals.get()
                print(lastsig)

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
            # signalall = buysigdetail.count(True)
            #
            # avsigp = knum / signalall
            #
            # # print(buysigdetail.count(True))
            # # print(sellsigdetail.count(True))
            # print dingdangline[(knum - avsigp):]
            # print C[(knum - avsigp):]
            # print('buy signal:', avsigp, buysigdetail[(knum - avsigp):])
            # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):])

        if not q_bar.empty():

            bar = q_bar.get()
            bars[barinterval].append(bar)

            # with open(bardatafile, 'a') as f:
            #     f.writelines(json.dumps(bar, ensure_ascii=False) + '\n')

            # print len(bars[barinterval])


            # bar_s = dict()
            # barss = load_data_from_server(server_base=serverport, instruments_id=inst, granularity=granularity)
            # barinterval = inst + '_' + str(granularity)
            # bar_s[barinterval] = barss
            # print len(bar_s[barinterval])

            # lastk = get_last_k_line(bars, 'rb1905', 780)
            # print lastk

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

            # knum = len(H)
            # signalall = buysigdetail.count(True)


            # if signalall >0:
            #     avsigp = knum / signalall
            #
                # print(buysigdetail.count(True))
                # print(sellsigdetail.count(True))

                # print('buy signal:', avsigp, buysigdetail[(knum - avsigp):])
                # print('sell signal:', avsigp, sellsigdetail[(knum - avsigp):])

                # print min(be_apart_from(buysigdetail), be_apart_from(sellsigdetail))
                # print be_apart_from(sellsigdetail)

                # sigsum2 = buysigdetail[(knum - avsigp):-2].count(True) + sellsigdetail[(knum - avsigp):-2].count(True)
                # sigsum4 = sigsum2 * 2
                # sigsum5 = sigsum4 if sellsigdetail[-1] or buysigdetail[-1] else 0
                # pp = min((sigsum5 + 1), 8)
                # # print 'pp:', pp

            if sellsigdetail[-1]:
                skprofits = []

                pp = getPositionRatio(sellsigdetail)
                sigdt = ' '.join([str(tick.ActionDay), str(tick.UpdateTime)])
                signal = {'date_time': sigdt, 'signaltype': 'SK', 'signalprice': tick.LastPrice, 'pos':pp}
                q_signals.put(signal)
                order_price = tick.LastPrice
                # td.PrepareOrder(tick.InstrumentID, s, k, pp, order_price)

                # spk
                sellcount = 0
                down_trading_flag = False
                # if not down_trading_flag and tick.LastPrice < get_last_k_line(bars,'rb1905',780)['low']:
                #     down_trading_flag = True
                #     sellcount +=1
                #     sk(pp) #
                #
                # pass
            elif buysigdetail[-1]:
                bkprofits = []

                pp = getPositionRatio(buysigdetail)
                sigdt = ' '.join([str(tick.ActionDay), str(tick.UpdateTime)])
                signal = {'date_time': sigdt, 'signaltype': 'BK', 'signalprice': tick.LastPrice, 'pos':pp}
                q_signals.put(signal)
                order_price = tick.LastPrice

                # td.PrepareOrder(tick.InstrumentID, b, k, pp, order_price)


                # bpk
                pass
            #
            # else:
            #     if not q_signals.empty():
            #         lastsig = q_signals.get()  # 是否最后一个信号，如何判断。
            #         print(lastsig)
def main():
    import threading

    play = threading.Thread(target=tickDataReplay)
    play.start()

    dingdang = threading.Thread(target=dingdangNo6())
    dingdang.start()


if __name__== '__main__':
    main()
