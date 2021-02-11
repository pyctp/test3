#encoding:utf-8
# 跟单程序 0.2 增加撤单功能

from queue import Queue
from ctpapi import MyMdApi, MyTradeApi, ApiStruct
from ctpapi import ApiStruct as UType

from ctpapi import q_depth_market_data, q_rtn_trade, q_rtn_order, q_positions, q_server_info

import time
import os

import yaml


with open(r'..\qhrealaccount.yaml') as f:
    accountqh = yaml.load(f)

with open('conf\\accounts_simstd.yml') as f:
    accounts_simstd = yaml.load(f)

with open('conf\\accounts_sim724.yml') as f:
    accounts724 = yaml.load(f)

s = S = ApiStruct.D_Sell
b = B = ApiStruct.D_Buy
k = K = ApiStruct.OF_Open
p = P = ApiStruct.OF_Close
pj = PJ = ApiStruct.OF_CloseToday
pz = PZ = ApiStruct.OF_CloseYesterday

# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('simnow24_ctp.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo(r'.\conf\simnowstd_ctp.json')
BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo('CTP_tgjy_thm.json')
# BROKER_ID, INVESTOR_ID, PASSWORD, ADDR_MD, ADDR_TD = getAccountinfo(r'..\conf\\dfqhthm.json')


def to_ctp_direction(direction):
    # print(direction)
    return UType.D_Buy if direction == 'BUY' else UType.D_Sell

def from_ctp_direction(ctp_direction):
    return '买' if ctp_direction == UType.D_Buy else '卖'   # UType.D_Sell

def to_ctp_offsetflag(offsetflag):
    # print(direction)T['OffsetFlag'] = 'char' #开平标志
    # OF_Open = '0' #开仓
    # OF_Close = '1' #平仓
    # OF_ForceClose = '2' #强平
    # OF_CloseToday = '3' #平今
    # OF_CloseYesterday = '4' #平昨
    # OF_ForceOff = '5' #强减
    # OF_LocalForceClose = '6' #本地强平
    if offsetflag == 'OPEN':
        ret = UType.OF_Open
    elif offsetflag == 'CLOSE':
        ret = UType.OF_Close
    elif offsetflag == 'CloseYesterday':
        ret = UType.OF_CloseYesterday
    elif offsetflag == 'CloseToday':
        ret = UType.OF_CloseToday

    return ret


def from_ctp_offsetflag(ctp_offsetflag):

    if ctp_offsetflag == UType.OF_Open:
        ret = '开'
    elif ctp_offsetflag == UType.OF_Close:
        ret = '平'
    elif ctp_offsetflag == UType.OF_CloseToday:
        ret = '平今'
    elif ctp_offsetflag == UType.OF_CloseYesterday:
        ret = '平昨'
    return ret



def xopen(tdapi, instrument_id, direction, volume, price):
    # print("spidelegate,xopen",instrument_id,volume,price,self)
    ref_id = self.inc_request_id()
    req = UStruct.InputOrder(
        InstrumentID=instrument_id,
        Direction=self.to_ctp_direction(direction),
        OrderRef=str(ref_id),
        LimitPrice=price,  # 有个疑问，double类型如何保证舍入舍出，在服务器端取整?
        VolumeTotalOriginal=volume,
        OrderPriceType=UType.OPT_LimitPrice,
        ContingentCondition=UType.CC_Immediately,

        BrokerID=self._broker,
        InvestorID=self._investor,
        CombOffsetFlag=UType.OF_Open,  # 开仓 5位字符, 但是只用到第0位
        CombHedgeFlag=UType.HF_Speculation,  # 投机 5位字符, 但是只用到第0位

        VolumeCondition=UType.VC_AV,
        MinVolume=1,  # 这个作用有点不确定, 有的文档设成0了
        ForceCloseReason=UType.FCC_NotForceClose,
        IsAutoSuspend=1,
        UserForceClose=0,
        TimeCondition=UType.TC_GFD,
    )
    ret = self.ReqOrderInsert(req, ref_id)
    return ret


def xclose(tdapi, instrument_id, close_type, direction, volume, price):
    """
        上期所区分平昨和平今
            搞反的话就会被CTP直接拒绝. 如平昨来平当日仓,且无足够昨仓,就会报:综合交易平台：平昨仓位不足
    """
    ref_id = self.inc_request_id()
    close_flag = UType.OF_CloseToday if close_type == XCLOSE_TODAY else UType.OF_Close
    req = UStruct.InputOrder(
        InstrumentID=instrument_id,
        Direction=self.to_ctp_direction(direction),
        OrderRef=str(ref_id),
        LimitPrice=price,  # 有个疑问，double类型如何保证舍入舍出，在服务器端取整?
        VolumeTotalOriginal=volume,
        OrderPriceType=UType.OPT_LimitPrice,

        BrokerID=self._broker,
        InvestorID=self._investor,
        CombOffsetFlag=close_flag,
        CombHedgeFlag=UType.HF_Speculation,  # 投机 5位字符, 但是只用到第0位

        VolumeCondition=UType.VC_AV,
        MinVolume=1,  # 这个作用有点不确定, 有的文档设成0了
        ForceCloseReason=UType.FCC_NotForceClose,
        IsAutoSuspend=1,
        UserForceClose=0,
        TimeCondition=UType.TC_GFD,
    )
    ret = self.ReqOrderInsert(req, ref_id)
    return ret

def xcancel(tdapi, instrument_id, exchange_id, order_sys_id, front_id, session_id, order_ref):
    """
        当以RESTART方式订阅流时,会收到之前的委托/成交回报. 在委托回报中,有各委托单状态
            如果撤单的时候数据对不上号,就会有 撤单找不到相应报单 的错误
        撤单请求返回的OnRtnOrder是被撤单的这个pOrder的委托响应的状态更新,不会有单独的撤单OnRtnOrder
            该OnRtnOrder中, front_id,session_id等都对应到被撤的那个pOrder
            如果是重新登陆,那么发出撤单命令的这个session_id和OnRtnOrder响应中的session_id是不一样的
    """
    self.logger.info('SPI_XC:取消命令')
    ref_id = self.inc_request_id()
    # orderActionRef是一个可有可无的值,设置错了也无关紧要
    req = UStruct.InputOrderAction(
        InstrumentID=instrument_id,
        BrokerID=self._broker,
        InvestorID=self._investor,
        ActionFlag=UType.AF_Delete,
        OrderActionRef=ref_id,  # 这需要一个int,真TM矛盾, OrderRef是一个String
        # OrderActionRef = order_ref, #   这个ref无关紧要,根据文档,应当是ref_id
    )
    if exchange_id:  # 已设置,则采用Exchange_id+orderSysID方式. 这两种方式均可撤当日任意单
        req.ExchangeID = exchange_id
        req.OrderSysID = order_sys_id
    else:  # 采用frontID + sessionID + orderRef标识的方式. 这两种方式均可撤当日任意单
        # 这个分支的测试 必须在OnRtnOrder第一次Callback时才能触发. 需要在该回调中测试
        req.FrontID = front_id
        req.SessionID = session_id
        req.OrderRef = str(order_ref)
    ret = self.ReqOrderAction(req, self.inc_request_id())
    return ret


def main():
    # account_base =r'conf'
    #
    # master2 = r'CTP_tgjy_thm.json'
    # master_user = getAccountinfo(master2)

    # master_user = accounts724['sim2']
    follow_user = accounts_simstd['sim1']

    fltd = MyTradeApi(broker_id=follow_user['broker_id'], investor_id=follow_user['investor_id'], passwd=follow_user['passwd'])
    fltd.Create( "fltd_trader")
    fltd.RegisterFront(follow_user['addr_td'])
    fltd.SubscribePublicTopic(1)
    fltd.SubscribePrivateTopic(1)
    fltd.Init()



    # mastertd = MyTradeApi(broker_id=master_user['broker_id'], investor_id=master_user['investor_id'], passwd=master_user['passwd'])
    mastertd = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
    mastertd.Create("master_trader")
    mastertd.RegisterFront(ADDR_TD)
    mastertd.SubscribePublicTopic(2)
    mastertd.SubscribePrivateTopic(2)
    mastertd.Init()



    master_order_list = []
    follow_order_list = []
    while True:
        time.sleep(0.2)
        if not mastertd.q_order.empty():
            order = mastertd.q_order.get()
            print(order)
            print(order.StatusMsg.decode('gbk'), order.OrderStatus)
            print((order.InsertTime, order.ActiveTime, order.UpdateTime, order.SuspendTime, order.CancelTime))
            if order.OrderStatus == '5':
                print('主账户撤单成功:', order.InvestorID, order.InstrumentID, order.OrderRef, from_ctp_direction(order.Direction), from_ctp_offsetflag(order.CombOffsetFlag), order.CombOffsetFlag, order.LimitPrice, order.VolumeTotalOriginal)
                print(order.ExchangeID, order.OrderSysID)

            if order.OrderStatus == '3':
                print('主账户下单成功:', order.InvestorID,order.InstrumentID, order.OrderRef, from_ctp_direction(order.Direction),from_ctp_offsetflag(order.CombOffsetFlag), order.CombOffsetFlag, order.LimitPrice, order.VolumeTotalOriginal)
                print(order.ExchangeID, order.OrderSysID)

                instid = order.InstrumentID
                Direction = order.Direction
                CombOffsetFlag = order.CombOffsetFlag
                order_price = int(order.LimitPrice)
                order_volume = order.VolumeTotal
                order_ref = order.OrderRef

                # 子账户下单 考虑子账户用主账户的orderRef, 需要修改ctpapi.
                fltd.PrepareOrder(instid, Direction, CombOffsetFlag, order_volume, order_price)

        if not fltd.q_order.empty():
            forder = fltd.q_order.get()
            print(forder)
            if forder.OrderStatus == '3':
                print('子账户下单成功', forder.InvestorID, forder.InstrumentID, forder.OrderRef, from_ctp_direction(forder.Direction), from_ctp_offsetflag(forder.CombOffsetFlag), forder.LimitPrice, forder.VolumeTotalOriginal)
                print(forder.ExchangeID, forder.OrderSysID)

            '''
            Order(BrokerID='4050', InvestorID='66881869', InstrumentID='SF905', OrderRef='185148', UserID='66881869',
                  OrderPriceType='2', Direction='1', CombOffsetFlag='0', CombHedgeFlag='1', LimitPrice=5748.0,
                  VolumeTotalOriginal=2, TimeCondition='3', GTDDate='', VolumeCondition='1', MinVolume=1,
                  ContingentCondition='1', StopPrice=0.0, ForceCloseReason='0', IsAutoSuspend=0,
                  BusinessUnit='00870060', RequestID=0, OrderLocalID='        1451', ExchangeID='CZCE',
                  ParticipantID='0087', ClientID='30967812', ExchangeInstID='SF905', TraderID='00870060', InstallID=1,
                  OrderSubmitStatus='3', NotifySequence=1, TradingDay='20190102', SettlementID=1,
                  OrderSysID='2019010201876130', OrderSource='0', OrderStatus='5', OrderType='0', VolumeTraded=0,
                  VolumeTotal=2, InsertDate='20190102', InsertTime='11:29:24', ActiveTime='00:00:00',
                  SuspendTime='00:00:00', UpdateTime='00:00:00', CancelTime='', ActiveTraderID='00870060',
                  ClearingPartID='', SequenceNo=4414, FrontID=3, SessionID=283576240, UserProductInfo='webstock',
                  StatusMsg='\xd2\xd1\xb3\xb7\xb5\xa5', UserForceClose=0, ActiveUserID='66881869', BrokerOrderSeq=44834,
                  RelativeOrderSysID='', ZCETotalTradedVolume=0, IsSwapOrder=0)

            '''






    # flowertd= MyTradeApi(follow_user)


if __name__ == '__main__':
    main()



    # if not mastertd.rtn_order.empty():
    #     pass

    # master onrtnorder
    # follower order

