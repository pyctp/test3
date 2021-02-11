#encoding:utf-8

# 叮当6号完全版 0.1 2019-03-31

#行情功能提供
md = ctpMdApi()

#交易功能提供
td = ctpTdApi()

#交易合约，周期

trading_inst = 'rb1905'
trading_period = 780

#策略内容

class DingDangNo6:

    malength = 23

    def __init__(self,md, td, trading_inst, trading_period):
        self.md = md
        self.td = td
        self.inst = trading_inst
        self.period = trading_period

        self.trading_fee = getTradingFee(self.inst)
        self.priceTick = getPriceTick(self.inst)
        self.multifier = getMultifier(self.inst)



        self.initFund = 100000
        self.tradingdict= {}
        self.realFund = self.initFund
        self.realFundMa = ma(self.realFund, malength)
        self.bars = load_bars_from_file()
        # self.bars = load_bars_from_server()


    def onOrder(self):
        pass

    def onTrade(self):
        pass

    def onTick(self):
        pass

    def onBar(self):
        pass

    def sendOrder(self):
        pass

    def cancelOrder(self):
        pass

    def xopen(self):
        pass

    def xclose(self):
        pass

    def xcancel(self):
        pass

