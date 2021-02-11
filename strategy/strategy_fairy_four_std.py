#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import time
import threading

from ctpapi import MyMdApi, MyTradeApi, ApiStruct
from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order

from copy import deepcopy
from data_sewing_machine import sewing_data_to_file_and_depositary, incept_config, load_data_from_file, llv, hhv, crossup, crossdown
from data_sewing_machine import init_k_line_pump, get_k_line_column, DEPOSITARY_OF_KLINE, q_macs, get_last_k_line
from trading_period import TradingPeriod, EXCHANGE_TRADING_PERIOD

# from myfunction import LLV, HHV


from Constant import LOGS_DIR

from myfunction import HHV, LLV, cross




import Queue


# cfgfile = 'meythm.ac'
# import shelve
# acinfo = shelve.open(cfgfile)
# # BROKER_ID = acinfo['BROKER_ID']
# BROKER_ID = '7030'
# INVESTOR_ID = acinfo['INVESTOR_ID']
# PASSWORD = acinfo['PASSWORD']
# ADDR_MD = acinfo['ADDR_MD']
# ADDR_TD = acinfo['ADDR_TRADE']
# acinfo.close()

from getaccount import getAccountinfo

BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('ctp_zrhx.json')

period = 900
inst = [u'rb1901']
# inst = [u'AP901']

strategy_inst = inst[0]
strategy_period = 900

single_volume = 1
grid = 40
step = 3


def Strategy_fairy_std():

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
    md = MyMdApi(instruments=inst, broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
    md.Create(INVESTOR_ID+"data")
    md.RegisterFront(ADDR_MD)
    md.Init()

    td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
    td.RegisterFront(ADDR_TD)
    td.SubscribePublicTopic(1)
    td.SubscribePrivateTopic(1)

    td.Init()


    last_time = None

    buy_order = 0
    sell_order = 0
    up_trader_flag = False
    down_trader_flag = False

    while True:
        if not q_depth_market_data.empty():
            tick = q_depth_market_data.get()

            sewing_data_to_file_and_depositary(depth_market_data=tick)

            last_k_line = get_last_k_line(instrument_id=inst[0], interval= period)

            # print last_k_line['low'], last_k_line['high'], tick.LastPrice

            if last_k_line is not None and tick.InstrumentID == strategy_inst:

                if last_time != last_k_line['date_time']:
                    last_time = last_k_line['date_time']
                    up_trader_flag = False
                    down_trader_flag = False
                print u'当前时间: ',tick.UpdateTime,u'HIGH: ',last_k_line['high'],u'LOW: ', last_k_line['low'], u'当前价: ', tick.LastPrice
                print u'buy_order: ', buy_order, u'sell_order: ', sell_order, BROKER_ID, INVESTOR_ID, tick.InstrumentID

                if (not up_trader_flag and not last_k_line['low'] == last_k_line['high']) and tick.LastPrice > last_k_line['high']:
                    # 下多单
                    up_trader_flag = True

                    # if sell_order > 0:
                    #     td.PrepareOrder(tick.InstrumentID, B, P, sell_order, tick.LastPrice + pc_grid)
                    #     sell_order -= sell_order

                    td.PrepareOrder(tick.InstrumentID, b, k, single_volume, tick.LastPrice)
                    buy_order += single_volume
                    td.PrepareOrder(tick.InstrumentID, s, pj, single_volume, tick.LastPrice + 5)

                    pc_grid -= step
                    pc_grid = max(6,pc_grid)

                    print
                    print u'下多单', tick.InstrumentID, INVESTOR_ID

                    print u'lastHigh:', last_k_line['high'], u'lastLow: ',last_k_line['low'], 'lastPrice: ', tick.LastPrice

                if (not down_trader_flag and not last_k_line['low'] == last_k_line['high']) and tick.LastPrice < last_k_line['low']:
                    # 下空单
                    down_trader_flag = True

                    # if buy_order > 0:
                    #     td.PrepareOrder(tick.InstrumentID, S, P, buy_order, tick.LastPrice - pc_grid)
                    #
                    #     buy_order -= buy_order

                    td.PrepareOrder(tick.InstrumentID, s, k, single_volume, tick.LastPrice)
                    sell_order += single_volume

                    td.PrepareOrder(tick.InstrumentID, b, pj, single_volume, tick.LastPrice - 4)

                    pc_grid -= step
                    pc_grid = max(6, pc_grid)

                    print
                    print u'下空单', tick.InstrumentID, INVESTOR_ID
                    print u'lastHigh:', last_k_line['high'], u'lastLow: ', last_k_line['low'], 'lastPrice: ', tick.LastPrice


        if not q_rtn_trade.empty():
                rtn_td = q_rtn_trade.get()
                print rtn_td
                print rtn_td.TradeTime, rtn_td.InstrumentID

        time.sleep(0.2)
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


def macs_process():
    while True:
        try:
            tick = q_macs.get(timeout=1)
            # print tick

        except Queue.Empty as e:
            pass


if __name__ == "__main__":
    #
    # t = threading.Thread(target=macs_process)
    # t.setDaemon(False)
    # t.start()

    config = incept_config()
    load_data_from_file()
    init_k_line_pump()

    workdays = TradingPeriod.get_workdays(begin=config['begin'], end=config['end'])
    workdays_exchange_trading_period_by_ts = \
        TradingPeriod.get_workdays_exchange_trading_period(
            _workdays=workdays, exchange_trading_period=EXCHANGE_TRADING_PERIOD)

    Strategy_fairy_std()

