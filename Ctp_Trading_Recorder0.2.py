#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 交易记录程序, v 0.1
# 改进日志文件，日志文件名称包含期货公司代码，交易账号，交易日信息 2018-09-11


import sys
import time
import json

import threading
from time import sleep
from datetime import datetime
import multiprocessing
from LogEngine import LogEngine

from ctpapi import MyMdApi, MyTradeApi, ApiStruct
from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order, q_positions, q_server_info

from copy import deepcopy
from data_sewing_machine import sewing_data_to_file_and_depositary, incept_config, load_data_from_file
# , llv, hhv, crossup, crossdown
from data_sewing_machine import init_k_line_pump, get_k_line_column, DEPOSITARY_OF_KLINE, q_macs, get_last_k_line
from trading_period import TradingPeriod, EXCHANGE_TRADING_PERIOD

# from myfunction import LLV, HHV
from tnlog import Logger

from Constant import LOGS_DIR

from myfunction import HHV, LLV, cross, MID, HLV

import queue

from getaccount import getAccountinfo


# today = datetime.now().strftime('%Y-%m-%d')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('simnow24_ctp.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('zrhx_ctp.json')
BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('CTP_tgjy_thm.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo(r'./conf/dfqhthm_ctp.json')
lastErrorID = 10
strategy_inst =''

orderList = list()

class traderRecorder(MyTradeApi):
    def traderRecord(self):
        pass


def getPos(tradespi, inst=strategy_inst):
    if tradespi is None or inst is None:
        return 0
    tradespi.qryPosition(InstrumentID=inst)

    all_buyorder = 0
    all_sellorder = 0

    while not q_positions.empty():
        pos = q_positions.get()

        if pos.PosiDirection == '2':  # 多头
            if pos.PositionDate == '1':  # 日内开平仓情况
                print('今天多单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission)
                all_buyorder += pos.Position
                # print 'today buy order: ', pos.YdPosition+pos.Position
                # print pos.YdPosition
                # print pos.Position
            elif pos.PositionDate == '2':  # history order
                print()
                '历史多单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission
                all_buyorder += pos.Position
                # print 'history buy order: ', pos.YdPosition + pos.Position
                print()
                pos.YdPosition
                print()
                pos.Position

        if pos.PosiDirection == '3':  # 空头持仓

            if pos.PositionDate == '1':  # 今日仓位
                print()
                '今天空单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission
                all_sellorder += pos.Position
                # print pos.YdPosition
                # print pos.Position
            elif pos.PositionDate == '2':  # history order
                print('历史空单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission)
                # print 'history sell order: ', pos.YdPosition + pos.Position
                all_sellorder += pos.Position
                # print pos.YdPosition
                # print pos.Position
    print(strategy_inst, '多单合计：', all_buyorder)
    print(strategy_inst, '空单合计：', all_sellorder)
    return (all_buyorder, all_sellorder)

def tradingRecorder(account):
    #accont 为ctp账号文件
    try:
        BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo(account)
    except:
        print('account file error of not existing... quit!')
        return

    global lastErrorID
    today = datetime.now().strftime("%Y-%m-%d")
    logfilename = BROKER_ID + '_' + INVESTOR_ID + '_交易日志' + str(today) + '.log'
    # log = Logger(logfilename=logfilename)
    # config = incept_config()
    # load_data_from_file()
    # init_k_line_pump()
    #
    # workdays = TradingPeriod.get_workdays(begin=config['begin'], end=config['end'])
    # workdays_exchange_trading_period_by_ts = \
    #     TradingPeriod.get_workdays_exchange_trading_period(
    #         _workdays=workdays, exchange_trading_period=EXCHANGE_TRADING_PERIOD)
    #
    # if workdays_exchange_trading_period_by_ts.has_key(today):
    #     trading_period_by_ts = workdays_exchange_trading_period_by_ts[today]
    # else:
    #     print('Not trading day, return to system.')
    #     return

    # T['TE_RESUME'] = 'int'  # 流重传方式
    # TERT_RESTART = 0  # 从本交易日开始重传
    # TERT_RESUME = 1  # 从上次收到的续传
    # TERT_QUICK = 2  # 只传送登录后的流内容

    # 登录行情服务器
    # md = MyMdApi(instruments=inst, broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
    # md.Create(INVESTOR_ID + "data")
    # md.RegisterFront(ADDR_MD)
    # md.Init()
    print(('-'*50))

    td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
    td.RegisterFront(ADDR_TD)
    td.SubscribePublicTopic(0)
    td.SubscribePrivateTopic(0)

    td.Init()

    # dt = td.getTradingday()

    # 初始化日志文件
    with open(logfilename, 'w') as f:
        print('initializing log file.')

    # td. Release()
    # td.ReqUserlogout()

    # tt = getPos(td,strategy_inst)
    # print tt

    while True:
        # td.fetch_investor_position_detail('SM905')
        if not q_server_info.empty():
            info = q_server_info.get()
            # print info.ErrorID
            lastErrorID = info.ErrorID
            print('the last ErrorID is: ', lastErrorID, INVESTOR_ID, BROKER_ID)
        if lastErrorID != 0:
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
            sleep(60)

        if not q_rtn_order.empty():
            rtn_order = q_rtn_order.get()
            print(rtn_order.OrderRef, rtn_order, '\n')

            print(rtn_order.InstrumentID, rtn_order.Direction, rtn_order.CombOffsetFlag, rtn_order.LimitPrice, rtn_order.VolumeTotalOriginal,rtn_order.OrderSubmitStatus, rtn_order.VolumeTraded,rtn_order.VolumeTotal, rtn_order.InsertTime, end=' ')
            orderList.append(rtn_order), '\n'
            if len(orderList) > 0:
                with open(logfilename, 'a') as f:
                    for ord in orderList[:]:
                        f.writelines(str(ord) + '\n')
                        orderList.remove(ord)
                        # f.writelines(json.dumps(ord, ensure_ascii=False) + '\n')



        if not q_rtn_trade.empty():
            rtn_trade = q_rtn_trade.get()
            print(rtn_trade)

        

        # print datetime.now(), 'the last ErrorID is: ', lastErrorID
        #
        # td.qryPosition(InstrumentID=strategy_inst)
        #
        # all_buyorder = 0
        # all_sellorder =0
        #
        # while not q_positions.empty():
        #     pos = q_positions.get()
        #     print pos
        #     if pos.PosiDirection=='2': #多头
        #         if pos.PositionDate =='1': #日内开平仓情况
        #             print '今天多单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission
        #             all_buyorder += pos.Position
        #             # print 'today buy order: ', pos.YdPosition+pos.Position
        #             # print pos.YdPosition
        #             # print pos.Position
        #         elif pos.PositionDate =='2': # history order
        #             print '历史多单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission
        #             all_buyorder += pos.Position
        #             # print 'history buy order: ', pos.YdPosition + pos.Position
        #             print pos.YdPosition
        #             print pos.Position
        #
        #     if pos.PosiDirection == '3': # 空头持仓
        #
        #         if pos.PositionDate =='1': # 今日仓位
        #             print '今天空单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：',pos.Commission
        #             all_sellorder += pos.Position
        #             # print pos.YdPosition
        #             # print pos.Position
        #         elif pos.PositionDate =='2': # history order
        #             print '历史空单情况：', '当前持仓：', pos.Position, '今天开仓数量: ', pos.OpenVolume, '今日平仓数量: ', pos.CloseVolume, '平仓盈利: ', pos.CloseProfit, '平仓手续费：', pos.Commission
        #             # print 'history sell order: ', pos.YdPosition + pos.Position
        #             all_sellorder += pos.Position
        #             # print pos.YdPosition
        #             # print pos.Position
        # print strategy_inst, '多单合计：', all_buyorder
        # print strategy_inst, '空单合计：', all_sellorder
        # time.sleep(12)

        # td.Init()

def runParentProcess():
    """父进程运行函数"""
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()

    le.info('启动CTA策略守护父进程')

    DAY_START = time(8, 58)  # 日盘启动和停止时间
    DAY_END = time(15, 3)

    NIGHT_START = time(20, 55)  # 夜盘启动和停止时间
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
    workdays = TradingPeriod.get_workdays(begin='2018-1-1', end='2019-12-31')

    workdays_exchange_trading_period_by_ts = \
        TradingPeriod.get_workdays_exchange_trading_period(
            _workdays=workdays, exchange_trading_period=EXCHANGE_TRADING_PERIOD)

    #
    # t = threading.Thread(target=macs_process)
    # t.setDaemon(False)
    # t.start()
    from time import sleep


    while True:

        today = datetime.now().strftime("%Y-%m-%d")
        logfilename = BROKER_ID + '_' + INVESTOR_ID + '_交易日志' + str(today) + '.log'
        currentTime = datetime.now().time()

        if today in workdays:  # 交易日 (写一个判断是否交易日的函数,isTradingDay()缺省参数为当日，可以传入特定日期)

            # if ((currentTime >= DAY_START and currentTime <= DAY_END) or  (currentTime >= NIGHT_START) or (currentTime <= NIGHT_END)):  # 交易时间
            #     recording = True
            # accountfile = r'./conf/htqh_ctp.json'
            # accountfile = r'./conf/dfqh_ctp_zjy.json'
            accountfile = r'./conf/dfqhthm.json'
            account1 = r'./conf/htqh_ctp.json'
            tradingRecorder(accountfile)
            tradingRecorder(account1)

            # else:
            #     print(u'not trading time, sleeping for 60 seconds.')
            #     sleep(60)
            #     pass

        else:
            nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(nowtime + '，非交易日，休息中。。。。。')
            sleep(300)
