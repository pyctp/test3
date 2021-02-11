#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import threading
from copy import deepcopy
from data_sewing_machine import sewing_data_to_file_and_depositary, incept_config, load_data_from_file
from data_sewing_machine import init_k_line_pump, get_k_line_column, DEPOSITARY_OF_KLINE, q_macs, get_last_k_line

from trading_period import TradingPeriod, EXCHANGE_TRADING_PERIOD
from myfunction import HHV, LLV, cross
from TraderDelegate import TraderDelegate

from Constant import LOGS_DIR

mutex = threading.Lock()
import Queue

if sys.platform == 'win32':
    from ctp_win32 import ApiStruct, MdApi, TraderApi

elif sys.platform == 'linux2':
    from ctp_linux64 import ApiStruct, MdApi, TraderApi


__author__ = 'James Iter'
__date__ = '2018/4/25'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


# strategy_para = [u'rb1810',780]
strategy_para = [u'AP901',180]
# inst = [u'AP810']
inst = [u'AP901']
# BROKER_ID = '9999'
# INVESTOR_ID = '116649'
# PASSWORD = 'ftp123'
# ADDR_MD = 'tcp://180.168.146.187:10010'
ADDR_MD = 'tcp://210.5.151.247:41213' #海通实盘
# ADDR_TD = 'tcp://180.168.146.187:10000'

q_depth_market_data = Queue.Queue()
q_rtn_trade = Queue.Queue()
q_rtn_order = Queue.Queue()

single_volume = 1
grid = 40

class MyMdApi(MdApi):
    def __init__(self, instruments, broker_id,
                 investor_id, password, *args, **kwargs):
        self.request_id = 0
        self.instruments = instruments
        self.broker_id = broker_id
        self.investor_id = investor_id
        self.password = password

    def OnRspError(self, info, request_id, is_last):
        print " Error: " + info

    @staticmethod
    def is_error_rsp_info(info):
        if info.ErrorID != 0:
            print "ErrorID=", info.ErrorID, ", ErrorMsg=", info.ErrorMsg
        return info.ErrorID != 0

    def OnHeartBeatWarning(self, _time):
        print "onHeartBeatWarning", _time

    def OnFrontConnected(self):
        print "OnFrontConnected:"
        self.user_login(self.broker_id, self.investor_id, self.password)

    def user_login(self, broker_id, investor_id, password):
        req = ApiStruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=password)

        self.request_id += 1
        ret = self.ReqUserLogin(req, self.request_id)

    def OnRspUserLogin(self, user_login, info, rid, is_last):
        print "OnRspUserLogin", is_last, info

        if is_last and not self.is_error_rsp_info(info):
            print "get today's trading day:", repr(self.GetTradingDay())
            self.subscribe_market_data(self.instruments)

    def subscribe_market_data(self, instruments):
        self.SubscribeMarketData(instruments)

    def OnRtnDepthMarketData(self, depth_market_data):
        tick = deepcopy(depth_market_data)
        # print tick
        q_depth_market_data.put(deepcopy(depth_market_data))

        # print u'行情数据发送：',tick.UpdateTime, tick.InstrumentID, tick.LastPrice

class MyTradeApi(TraderDelegate):

    def __init__(self, broker_id,
                 investor_id, passwd, *args,**kwargs):
        self.requestid=0
        # self.instruments = instruments
        self.broker_id =broker_id
        self.investor_id = investor_id
        self.passwd = passwd

    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        print repr(pOrder)
        self.logger.info(u'报单响应,Order=%s' % str(pOrder))
        # print pOrder
        if pOrder.OrderStatus == 'a':
            #CTP接受，但未发到交易所
            print u'CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID))
            # self.agent.rtn_order(pOrder)
        else:
            print u'交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID))
            #self.agent.rtn_order_exchange(pOrder)
            # self.agent.rtn_order(pOrder)

    def OnRtnTrade(self, pTrade):
        '''成交通知'''
        self.logger.info(u'TD:成交通知,BrokerID=%s,BrokerOrderSeq = %s,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' %(pTrade.BrokerID,pTrade.BrokerOrderSeq,pTrade.ExchangeID,pTrade.OrderSysID,pTrade.TraderID,pTrade.OrderLocalID))
        self.logger.info(u'TD:成交回报,Trade=%s' % repr(pTrade))
        pt = deepcopy(pTrade)
        print u'报单成交。'
        print pt.InstrumentID, pt.Direction,pt.OffsetFlag, pt.Price
        q_rtn_trade.put(pt)

        # self.agent.rtn_trade(pTrade)

    def sendOrder(traderSpi, order):
        global mutex
        mutex.acquire()
        # print order

        traderSpi.ReqOrderInsert(order, traderSpi.inc_request_id())
        # DatabaseController.insert_SendOrder(order)

        print("sendOrder = " + order.InstrumentID + " dir = " + order.Direction)
        # + " strategy = " + self.__module__)
        # time.sleep(1)
        mutex.release()

    def formatOrder(self, inst, direc, open_close, volume, price):
        orderp = ApiStruct.InputOrder(

            InstrumentID=inst,
            Direction=direc,  # ApiStruct.D_Buy or ApiStruct.D_Sell
            OrderRef=str(self.inc_request_id()),
            LimitPrice=price,
            VolumeTotalOriginal=volume,
            OrderPriceType=ApiStruct.OPT_LimitPrice,
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            UserID=self.investor_id,
            CombOffsetFlag=open_close,  # OF_Open, OF_Close, OF_CloseToday
            CombHedgeFlag=ApiStruct.HF_Speculation,
            VolumeCondition=ApiStruct.VC_AV,
            MinVolume=1,
            ForceCloseReason=ApiStruct.FCC_NotForceClose,
            IsAutoSuspend=1,
            UserForceClose=0,
            TimeCondition=ApiStruct.TC_GFD,
        )
        # print orderp
        return orderp

    def PrepareOrder(self, inst, direc, open_close, volume, price):
        order = self.formatOrder( inst, direc, open_close, volume, price)
        print u'send order:', inst, u'price: ', price, u'amount:', volume
        self.sendOrder(order)

cfgfile = 'meythm.ac'

def run():

    strategy_parameters = [['AP901',180],['rb1810',780]]
    strategy_inst = ['rb1810']
    # strategy_parameters[1][0]
    strategy_period = strategy_parameters[1][1]

    import shelve
    acinfo = shelve.open(cfgfile)
    # BROKER_ID = acinfo['BROKER_ID']
    BROKER_ID = '7030'
    INVESTOR_ID = acinfo['INVESTOR_ID']
    PASSWORD = acinfo['PASSWORD']
    # ADDR_MD = acinfo['ADDR_MD']
    ADDR_MD = 'tcp://210.5.151.247:41213'  # 海通实盘
    ADDR_TD = acinfo['ADDR_TRADE']
    acinfo.close()

    s = S = ApiStruct.D_Sell
    b = B = ApiStruct.D_Buy
    k = K = ApiStruct.OF_Open
    p = P = ApiStruct.OF_Close
    # T['TE_RESUME'] = 'int'  # 流重传方式
    # TERT_RESTART = 0  # 从本交易日开始重传
    # TERT_RESUME = 1  # 从上次收到的续传
    # TERT_QUICK = 2  # 只传送登录后的流内容


    # 登录行情服务器
    user = MyMdApi(instruments=strategy_inst, broker_id=BROKER_ID, investor_id=INVESTOR_ID, password=PASSWORD)
    user.Create("data")
    user.RegisterFront(ADDR_MD)
    user.Init()
    print u'行情服务器登录成功'

    td = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    td.Create(LOGS_DIR + INVESTOR_ID + "_trader")
    td.RegisterFront(ADDR_TD)
    td.SubscribePublicTopic(1)
    td.SubscribePrivateTopic(1)

    td.Init()
    print BROKER_ID, INVESTOR_ID, u'交易服务器登录成功。'

    last_time = None
    up_trader_flag = False
    down_trader_flag = False

    while True:
        if not q_depth_market_data.empty():
            payload = q_depth_market_data.get()

            tick = deepcopy(payload)
            sewing_data_to_file_and_depositary(depth_market_data=payload)

            last_k_line = get_last_k_line(instrument_id='rb1810', interval=strategy_period)

            # print last_k_line['low'], last_k_line['high'], payload.LastPrice


            if last_k_line is not None:

                # get the h,l c,serieses.
                stra_inst = 'rb1810'
                H = get_k_line_column(stra_inst, strategy_period, ohlc='high')
                L = get_k_line_column(stra_inst, strategy_period, ohlc='low')
                C = get_k_line_column(stra_inst, strategy_period, ohlc='close')

                # calculate the uppper and lower band
                HV = HHV(H, 23)
                LV = LLV(L, 23)

                # middle line
                Mid = list(map(lambda x: (x[0] + x[1]) / 2, zip(HV, LV)))

                num, detail = cross(C, Mid)
                # print 'High:', High[-20:]
                # print 'Low:', Low[-20:]
                #
                # print 'HHV: ', HV[-20:]
                # print 'LLV: ', LV[-20:]

                print 'MID: ', Mid[-20:]
                print 'Close: ', C[-20:]
                print 'cross num: ', num
                print 'cross detail: ', detail

                if last_time != last_k_line['date_time']:
                    last_time = last_k_line['date_time']
                    up_trader_flag = False
                    down_trader_flag = False

                if not up_trader_flag and payload.LastPrice > last_k_line['high'] and C[-1]>Mid[-1]:
                    # 下多单
                    up_trader_flag = True

                    td.PrepareOrder(tick.InstrumentID, b, k, single_volume, tick.LastPrice)

                    td.PrepareOrder(tick.InstrumentID, S, P, single_volume, tick.LastPrice + grid)

                    print
                    print u'下多单'

                    print last_k_line
                    print payload.LastPrice

                if not down_trader_flag and payload.LastPrice < last_k_line['low'] and C[-1] <= Mid[-1]:
                    # 下空单
                    down_trader_flag = True

                    td.PrepareOrder(tick.InstrumentID, s, k, single_volume, tick.LastPrice)

                    td.PrepareOrder(tick.InstrumentID, B, P, single_volume, tick.LastPrice - grid)

                    print
                    print u'下空单'
                    print last_k_line
                    print payload.LastPrice

            if not q_rtn_trade.empty():
                rtn_td = q_rtn_trade.get()
                print rtn_td.TradeTime


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
            payload = q_macs.get(timeout=1)
            # print payload

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

    run()


