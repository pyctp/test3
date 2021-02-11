#-*- coding=utf-8 -*-
"This is the main demo file"
from ctp.futures import ApiStruct, MdApi, TraderApi
# import ctpapi
# from ctpgateway import ApiStruct, MdApi, TraderApi
import time
from copy import deepcopy
import traceback

ticks=[]


class MyMdApi(MdApi):
    def __init__(self, instruments,
                 *args,**kwargs):
        self.requestid=0
        self.instruments = instruments
        self.broker_id ='*'
        self.investor_id = '*'
        self.passwd = '*'

    def OnRspError(self, info, RequestId, IsLast):
        print(" Error")
        self.isErrorRspInfo(info)

    def isErrorRspInfo(self, info):
        if info.ErrorID !=0:
            print("ErrorID=", info.ErrorID, ", ErrorMsg=", info.ErrorMsg)
        return info.ErrorID !=0

    def OnFrontDisConnected(self, reason):
        print("onFrontDisConnected:", reason)

    def OnHeartBeatWarning(self, time):
        print("onHeartBeatWarning", time)

    def OnFrontConnected(self):
        print("OnFrontConnected:")
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ApiStruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)

        self.requestid+=1
        r=self.ReqUserLogin(req, self.requestid)

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        print("OnRspUserLogin", is_last, info)
        if is_last and not self.isErrorRspInfo(info):
            print("get today's trading day:", repr(self.GetTradingDay()))
            self.subscribe_market_data(self.instruments)

    def subscribe_market_data(self, instruments):
        self.SubscribeMarketData(instruments)

    def OnRspSubMarketData(self, spec_instrument, info, requestid, islast):
        print("OnRspSubMarketData", spec_instrument)

    #def OnRspUnSubMarketData(self, spec_instrument, info, requestid, islast):
    #    print "OnRspUnSubMarketData"

    def OnRtnDepthMarketData(self, depth_market_data):
        print(depth_market_data)
        # print 'orig time',depth_market_data.UpdateTime
        dd = deepcopy(depth_market_data)
        # if dd.Volume>0: ticks.append(dd)
        # lastprices.append(dd.LastPrice)
        # print depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec,depth_market_data.InstrumentID

inst = ['rb1810','hc1810','j1901']
lastprices = []
def mytest(cfgfile = '086038sim24.ac'):

	from colorama import init, Fore, Back, Style

	from tapy import cross, crossdown


	init()



	try:

		user = MyMdApi(instruments=inst)
		user.Create("data")
		user.RegisterFront(ADDR_MD)
		user.Init()

	except:
		print('sth wrong.')

	while True:
		time.sleep(1)

if __name__=="__main__":
	import sys
	print(sys.argv)
	if len(sys.argv)>1:
		# break
		cfgfile = sys.argv[1]
		print(cfgfile)
		mytest(cfgfile)
	else:
		mytest()
