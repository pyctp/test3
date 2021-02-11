# coding: utf-8
# !/usr/bin/env python
import numpy as np
import pandas as pd
import os



def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n + 1]
    up = (seed[seed >= 0].sum()) / n + 0.000001
    down = (-seed[seed < 0].sum()) / n + 0.000001
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100. / (1. + rs)

    for i in range(n, len(prices)):
        delta = deltas[i - 1]  # cause the diff is 1 shorter

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (n - 1) + upval) / n
        down = (down * (n - 1) + downval) / n

        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def relative_strength(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n + 1]
    up = (seed[seed >= 0].sum()) / n + 0.000001
    down = (-seed[seed < 0].sum()) / n + 0.000001
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100. / (1. + rs)

    for i in range(n, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
            up = (up * (n - 1) + upval) / n
            down = (down * (n - 1) + downval) / n
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def rsi2(price, n=14):
    ''' rsi indicator '''
    gain = (price - price.shift(1)).fillna(0)  # calculate price gain with previous day, first row nan is filled with 0

    def rsiCalc(p):
        # subfunction for calculating rsi for one lookback period
        avgGain = p[p > 0].sum() / n
        avgLoss = -p[p < 0].sum() / n
        rs = avgGain / avgLoss
        return 100 - 100 / (1 + rs)

    # run for all periods with rolling_apply
    return pd.rolling_apply(gain, n, rsiCalc)


def kline(infile, period):
    # df = pd.read_csv(infile, skiprows=[0], encoding='GBK')
    df = pd.read_csv(infile)
    # names=['Symbol', 'Date_Time', 'Price','Volume']
    abf = df.iloc[:, [0, 1]]
    # abf.columns = ['Symbol', 'Date_Time', 'Price', 'Volume']
    abf.columns = ['Date_Time', 'Price']
    # abf = abf[abf['Volume'] > 0]
    abf.set_index(['Date_Time'], inplace=True)
    abf.index = pd.to_datetime(abf.index)
    bars = abf.Price.resample(period).ohlc()
    # Volumes = abf.Volume.resample(period).sum()
    # ohlcv = pd.concat([bars, Volumes], axis=1)
    ohlcv = bars.dropna()
    # ohlcv['Symbol'] = abf['Symbol'][1]
    return ohlcv


def batch_gen_kline(period, outfile):
    basedir = "F:\\share\\if\\"
    prefix = "IF1101"
    # rng = pd.date_range('20180102', freq='D', periods=30).strftime('%Y%m%d')
    rng = pd.date_range('20110104', freq='D', periods=30).strftime('%Y%m%d')
    no = 0
    for row in np.nditer(rng):
        filename = basedir + str(row) + "\\" + prefix + str(row) + ".csv"
        if (os.path.isfile(filename)):
            print(filename)
            data = kline(filename, period, outfile)
            no = no + 1
            if (no == 1):
                data.to_csv(outfile, mode='a', index_label='Date_Time')  # header=False,
            else:
                data.to_csv(outfile, mode='a', header=False, index_label='Date_Time')

        else:
            print((" %s is  not  exisits skip it!" % filename))



period = '1T'
bar = kline('.\data\\rb\\rb1901tick.csv','5T')
bar.to_csv('rb1901_300.csv')
outfile = 'ZC805_201801_' + period + 'K.csv'

batch_gen_kline(period, outfile)

period = '5T'
outfile = 'ZC805_201801_' + period + 'K.csv'
batch_gen_kline(period, outfile)

period = '10T'
outfile = 'ZC805_201801_' + period + 'K.csv'
batch_gen_kline(period, outfile)

period = '15T'
outfile = 'ZC805_201801_' + period + 'K.csv'
batch_gen_kline(period, outfile)
# rsi= rsiFunc(ohlcv['close'],6)
# rsi= rsi2(ohlcv['close'],6)
# ohlcv['rsi'] = pd.Series(rsi, index=ohlcv.index)

'''
---------------------
作者：DreamNotOver
来源：CSDN
原文：https: // blog.csdn.net / lwhsyit / article / details / 79819838
版权声明：本文为博主原创文章，转载请附上博文链接！
'''