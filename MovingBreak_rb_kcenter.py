#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 搬砖机器人 dingdang_fariy, v 0.1
# 改进日志文件，日志文件名称包含期货公司代码，交易账号，交易日信息 2018-09-11


import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

import threading
from time import sleep
from datetime import time, datetime
import multiprocessing
from LogEngine import LogEngine

from ctpapi import MyMdApi, MyTradeApi, ApiStruct
from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order, q_positions, q_server_info

from copy import deepcopy


from function import load_data_from_file_v2, get_k_line_column, get_last_k_line, load_data_from_server, be_apart_from

from trading_period import TradingPeriod, EXCHANGE_TRADING_PERIOD


from tickToBar import tickToBar, q_bar

# from myfunction import LLV, HHV
from tnlog import Logger

from Constant import LOGS_DIR

from myfunction import HHV, LLV, cross, MID, HLV

from emailNotify import mailsender

import queue

from getaccount import getAccountinfo

BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('conf\simnowstd_ctp.json')

inst = 'rb1905'
granularity = 180


bars = dict()
data_path = r'./data/bar/rb/'
# barss = load_data_from_server(server_base=serverport, instruments_id=inst, granularity=granularity)
bars = load_data_from_file_v2(instruments_id=inst, granularities='180', data_source_dir=data_path)
barinterval = inst + '_' + str(granularity)
bardatafile = data_path + barinterval + '.json'




strategy_paras = {'inst': 'rb1905', 'interval': 300, 'bkvol': 2, 'skvol': 2, 'grid': 8, 'single_vol': 1}

period = 180
strategy_inst = strategy_paras['inst']

strategy_period = 180

single_volume = 1
buy_limit = 3
sell_limit = 3

grid = 10
step = 3

today = datetime.now().strftime('%Y-%m-%d')

# receivers = ['vnctp@qq.com', 'tianhm2012@foxmail.com', 'smartmanp@qq.com', '2509055963@qq.com', 'zjy1301@qq.com','3053269797@qq.com']
receivers = ['vnctp@qq.com', 'tianhm2012@foxmail.com', 'smartmanp@qq.com', 'zjy1301@qq.com']

def makeMd():

    md = MyMdApi(instruments=['rb1905'], broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
    md.Create(INVESTOR_ID + "data")
    md.RegisterFront(ADDR_MD)
    md.Init()
    return md


def makeTd():
    td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
    td.RegisterFront(ADDR_TD)
    td.SubscribePublicTopic(1)
    td.SubscribePrivateTopic(1)
    td.Init()

    return td


def MovingBreak():
    lastErrorID = 0

    logfilename = BROKER_ID + '_' + INVESTOR_ID + '_交易日志' + str(today) + '.log'
    log = Logger(logfilename=logfilename)

    pc_grid = grid

    s = S = ApiStruct.D_Sell
    b = B = ApiStruct.D_Buy
    k = K = ApiStruct.OF_Open
    p = P = ApiStruct.OF_Close
    pj = PJ = ApiStruct.OF_CloseToday
    pz = PZ = ApiStruct.OF_CloseYesterday

    # T['TE_RESUME'] = 'int'  # 流重传方式
    # TERT_RESTART = 0  # 从本交易日开始重传
    # TERT_RESUME = 1  # 从上次收到的续传
    # TERT_QUICK = 2  # 只传送登录后的流内容

    # 登录行情服务器
    md = MyMdApi(instruments=['rb1905'], broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
    md.Create(INVESTOR_ID + "data")
    md.RegisterFront(ADDR_MD)
    md.Init()

    td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
    td.RegisterFront(ADDR_TD)
    td.SubscribePublicTopic(2)
    td.SubscribePrivateTopic(2)

    td.Init()

    last_time = None

    buy_order = 0
    sell_order = 0
    bp_total = 0
    sp_total = 0

    bk_limit = 1
    sk_limit = 1

    up_trader_flag = False
    down_trader_flag = False
    buy_rec = list()
    sell_rec = list()

    while True:

        if not q_server_info.empty():
            info = q_server_info.get()
            # print info.ErrorID
            lastErrorID = info.ErrorID
            print('the last ErrorID is: ', lastErrorID)
        if lastErrorID != 0:
            # print 'release the api...'
            # td.Release()
            print(datetime.now(), 'reconnect the trading server.')
            del td
            sleep(60)
            td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
            td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
            td.RegisterFront(ADDR_TD)
            td.SubscribePublicTopic(2)
            td.SubscribePrivateTopic(2)
            # td.ReqUserLogout()
            td.Init()
            sleep(60)




        if not q_depth_market_data.empty():
            tick = q_depth_market_data.get()

            tickToBar(tick,granularity=180)


            D_open = tick.OpenPrice

            lastk = get_last_k_line(bars, inst, granularity)
            last_k_line = get_last_k_line(bars, inst, granularity)
            print((lastk, datetime.now()))

            O = get_k_line_column(bars, inst, granularity, ohlc='open')
            H = get_k_line_column(bars, inst, granularity, ohlc='high')
            L = get_k_line_column(bars, inst, granularity, ohlc='low')
            C = get_k_line_column(bars, inst, granularity, ohlc='close')
            # print(H[-3:],L[-3:], type(H[-1]))

            kcenter = (O[-1]+H[-1]+L[-1]+C[-1])/4


            # HL = HLV(H, L)
            # MHL = max(HL)
            # MminHL = min(HL)
            # AVHL = sum(HL) / len(HL)
            # vgrid = int(AVHL * 0.8)
            # calculate the uppper and lower band
            HV = HHV(H, 23)
            LV = LLV(L, 23)
            # #middle line
            Mid = MID(HV, LV)

            # 根据叮当值调整仓位控制参数

            # bk_limit = 3 if C[-1] > Mid[-1] else 0
            bk_limit = 10
            # sk_limit = 3 if C[-1] < Mid[-1] else 0
            sk_limit = 10
            # print tick.InstrumentID, strategy_inst
            if lastk is not None and tick.InstrumentID == strategy_inst:

                if last_time != last_k_line['date_time']:
                    last_time = last_k_line['date_time']
                    up_trader_flag = False
                    down_trader_flag = False

                dingdang = 'Buy!' if tick.LastPrice > Mid[-1] else 'Sell'
                bkvol = buy_order - sp_total if buy_order - sp_total > 0 else 0
                skvol = sell_order - bp_total if sell_order - bp_total > 0 else 0
                # bkvol = get_day_bkvol(td, strategy_inst)
                # skvol = get_day_skvol(td, strategy_inst)

                # outformat = "当前时间:{tick.UpdateTime}, High:{last_k_line['high']}"
                # print(outformat)
                print('当前时间: ', tick.UpdateTime, 'HIGH:', last_k_line['high'], '    ', 'LOW:', last_k_line[
                    'low'], '当前价: ', tick.LastPrice, '叮当值:', Mid[
                    -1], dingdang, 'buy_limit:', bk_limit, 'sell_limit:', sk_limit)
                print('buy_order: ', buy_order, 'sell_order: ', sell_order, BROKER_ID, INVESTOR_ID, tick.InstrumentID, 'sp_total: ', sp_total, 'bp_total: ', bp_total, '日多:', bkvol, '日空:', skvol)

                if not up_trader_flag and tick.LastPrice > kcenter + 1 and bkvol < bk_limit:
                    # 下多单
                    print(bkvol, bk_limit)
                    up_trader_flag = True
                    order_price = tick.LastPrice
                    buy_rec.append([datetime.now(), order_price])
                    # if sell_order > 0:
                    #     td.PrepareOrder(tick.InstrumentID, B, PJ, sell_order, order_price)
                        # sell_order -= sell_order

                    td.PrepareOrder(tick.InstrumentID, b, k, single_volume, order_price)
                    log.info(log.printfNow() + '下空单:' + str(single_volume) + ',orderprice:' + str(
                        order_price) + 'skvol:' + str(skvol) + 'sk_limit:' + str(sk_limit))

                    # td.PrepareOrder(tick.InstrumentID, s, pz, single_volume, tick.LastPrice)

                    info = 'buy: ' + tick.InstrumentID +' '+ str(order_price)

                    mailsender(info, receivers)

                    print('下多单', tick.InstrumentID, INVESTOR_ID, str(single_volume) + ',orderprice:' + str(
                        order_price) + 'skvol:' + str(skvol) + 'sk_limit:' + str(sk_limit))

                    print('lastHigh:', last_k_line['high'], 'lastLow: ', last_k_line[
                        'low'], 'lastPrice: ', tick.LastPrice)

                if not down_trader_flag and tick.LastPrice < kcenter - 1 and skvol < sk_limit:
                    # 下空单
                    down_trader_flag = True
                    order_price = tick.LastPrice

                    # if buy_order > 0:
                    #     td.PrepareOrder(tick.InstrumentID, S, PJ, buy_order, tick.LastPrice - pc_grid)

                        # buy_order -= buy_order

                    td.PrepareOrder(tick.InstrumentID, s, k, single_volume, order_price)
                    log.info(log.printfNow() + '下空单:' + str(single_volume) + ',orderprice:' + str(
                        order_price) + 'skvol:' + str(skvol) + 'sk_limit:' + str(sk_limit))
                    # td.PrepareOrder(tick.InstrumentID, b, pz, single_volume, tick.LastPrice)

                    info = 'sell: ' + tick.InstrumentID + ' ' + str(order_price)
                    # mailsender(info, receivers)

                    print('下空单', tick.InstrumentID, INVESTOR_ID, ', orderprice:' + str(order_price) + ', skvol:' + str(
                        skvol) + ', sk_limit:' + str(sk_limit))
                    print('lastHigh:', last_k_line['high'], 'lastLow: ', last_k_line[
                        'low'], 'lastPrice: ', tick.LastPrice)

        if not q_bar.empty():
            bartmp = q_bar.get()
            bars[barinterval].append(bartmp)

        if not q_rtn_order.empty():
            rtn_order = q_rtn_order.get()
            print(rtn_order)
            print('下单成功，请注意。。。')

        if not q_rtn_trade.empty():
            rtn_td = q_rtn_trade.get()
            print('下单成交', rtn_td)

            '''
            Trade(BrokerID='0127', InvestorID='200277', InstrumentID='ni1811', OrderRef='69169', UserID='200277',
                  ExchangeID='SHFE', TradeID='      652868', Direction='0', OrderSysID='     2413585',
                  ParticipantID='0011', ClientID='01789993', TradingRole='\x00', ExchangeInstID='ni1811',
                  OffsetFlag='0', HedgeFlag='1', Price=112560.0, Volume=1, TradeDate='20180727',
                  TradeTime='23:52:48', TradeType='\x00', PriceSource='\x00', TraderID='0011c6c',
                  OrderLocalID='         684', ClearingPartID='0011', BusinessUnit='', SequenceNo=1536,
                  TradingDay='20180730', SettlementID=1, BrokerOrderSeq=2310, TradeSource='0')
            '''
            # k
            if rtn_td.Direction == B:  # 方向 多
                if rtn_td.OffsetFlag == K and rtn_td.InstrumentID == strategy_inst:  # 多单开仓成交，下平仓指令， 开盘价+30

                    buy_order += rtn_td.Volume
                    order_price = rtn_td.Price + grid

                    td.PrepareOrder(rtn_td.InstrumentID, s, pj, rtn_td.Volume, order_price)

                    info = tick.InstrumentID + '多单建仓成交，平仓单挂单。。。' + str(order_price)
                    print(info)
                    # mailsender(info, receivers)

                elif rtn_td.OffsetFlag in [P, PJ, PZ] and rtn_td.InstrumentID == strategy_inst:  # 平仓，
                    print(rtn_td)
                    bp_total += rtn_td.Volume
                    skvol -= rtn_td.Volume
                    info = '平仓单成交。。。'
                    print(info)
                    # mailsender(info,receivers)



            elif rtn_td.Direction == S:  # 方向：空
                if rtn_td.OffsetFlag == K and rtn_td.InstrumentID == strategy_inst:  # 开仓
                    # 空单建仓成交
                    sell_order += rtn_td.Volume
                    order_price = rtn_td.Price - grid
                    td.PrepareOrder(rtn_td.InstrumentID, b, pj, rtn_td.Volume, order_price)
                    info = '空单建仓成交，平仓单挂单。。。'
                    print(info)
                    # mailsender(info, receivers)

                elif rtn_td.OffsetFlag in [P, PJ, PZ] and rtn_td.InstrumentID == strategy_inst:

                    sp_total += rtn_td.Volume
                    bkvol -= rtn_td.Volume
                    info = '平仓单成交' + str(rtn_td.TradeTime)+ rtn_td.InstrumentID
                    print(info)

                    # mailsender(info, receivers)

            print(rtn_td.TradeTime, rtn_td.InstrumentID)

        # time.sleep(0.2)
        # if rtn_td:
        #     if rtn_td.Direction == B and rtn_td.OffsetFlag == K:
        #         price = rtn_td.Price + 10
        #         volume = rtn_td.Volume
        #         td.PrepareOrder(tick.InstrumentID, s, p, volume, price)
        #         print u'平多指令发出。',price
        #     if rtn_td.Direction == S and rtn_td.OffsetFlag == K:
        #         price = rtn_td.Price - 10
        #         volume = rtn_td.Volume
        #         td.PrepareOrder(tick.InstrumentID, b, p, volume, price)
        #         print u'平空指令发出',price
        # except Queue.Empty as e:
        #     print u'数据队列为空。',e


def get_day_bkvol(tdapi, instrumentID):
    tdapi.qryPosition(instrumentID)
    while not q_positions.empty():
        posi = q_positions.get(timeout=1)
        # print posi
        if posi.InstrumentID == instrumentID and posi.PosiDirection == '2' and posi.PositionDate == '1':
            return int(posi.Position)


def get_day_skvol(tdapi, instrumentID):
    tdapi.qryPosition(instrumentID)
    while not q_positions.empty():
        posi = q_positions.get(timeout=1)
        # print posi
        if posi.InstrumentID == instrumentID and posi.PosiDirection == '3' and posi.PositionDate == '1':
            return int(posi.Position)


def runParentProcess():
    """父进程运行函数"""
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()

    le.info('启动CTA策略守护父进程')

    DAY_START = time(8, 58)  # 日盘启动和停止时间
    DAY_END = time(15, 3)

    NIGHT_START = time(20, 58)  # 夜盘启动和停止时间
    NIGHT_END = time(2, 45)

    p = None  # 子进程句柄

    while True:
        # 获取当前日期和时间
        today = datetime.now().strftime("%Y-%m-%d")
        currentTime = datetime.now().time()
        recording = False

        # today = '2018-08-27'

        # 判断是否是交易日
        if today in workdays:

            # 判断当前处于的时间段
            if ((currentTime >= DAY_START and currentTime <= DAY_END) or
                    (currentTime >= NIGHT_START) or
                    (currentTime <= NIGHT_END)):
                recording = True

            # 记录时间则需要启动子进程
            if recording and p is None:
                le.info('启动子进程')
                p = multiprocessing.Process(target=Strategy_dingdang_fairy_std)
                p.start()
                le.info('子进程启动成功')

            # 非记录时间则退出子进程
            if not recording and p is not None:
                le.info('关闭子进程')
                p.terminate()
                p.join()
                p = None
                le.info('子进程关闭成功')

                print(BROKER_ID, INVESTOR_ID, currentTime, 'not trading time, resting...')
                sleep(30)

        else:
            print(today, currentTime, 'Not trading day, resting......')
            sleep(300)


if __name__ == "__main__":
    #
    # t = threading.Thread(target=macs_process)
    # t.setDaemon(False)
    # t.start()
    from time import sleep


    # workdays = TradingPeriod.get_workdays(begin=config['begin'], end=config['end'])
    # workdays_exchange_trading_period_by_ts = \
    #     TradingPeriod.get_workdays_exchange_trading_period(
    #         _workdays=workdays, exchange_trading_period=EXCHANGE_TRADING_PERIOD)

    MovingBreak()
    #     while True:

    # today = datetime.now().strftime("%Y-%m-%d")

    # if today in workdays:
    #     runParentProcess()
    #     # Strategy_dingdang_fairy_std()
    # nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # print  nowtime + u'，非交易日，休息中。。。。。'
    # sleep(60)
    # runParentProcess()





