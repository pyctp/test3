#encoding:utf-8

import cmath
import math
# from numba import jit
from datetime import datetime


def MA(elements=None, step=None):
    assert isinstance(elements, list)
    assert isinstance(step, int)

    import decimal

    numbers = list()
    ma_list = list()

    for ele in elements:
        numbers.append(decimal.Decimal(ele))

        if numbers.__len__() < step:
            avg = float('%0.2f' % (float(sum(numbers)) / numbers.__len__()))

        else:
            numbers = numbers[0 - step:]
            avg = float('%0.2f' % (float(sum(numbers)) / numbers.__len__()))

        ma_list.append(avg)

    return ma_list

def HHV(slist, n):
    """
    Highest value over a specified period
    """
    max_list = []
    i = 0
    while i < len(slist):
        if i + 1 < n:
            MAX = max(slist[0:i+1])
        else:
            start = i + 1 - n
            end = i + 1
            MAX = max(slist[start:end])
        max_list.append(MAX)
        i += 1
    return max_list

def MAXINDEX(df, n, price='Close'):
    """
    Index of highest value over a specified period
    """

def LLV(slist, n):
    """
    Lowest value over a specified period
    """
    min_list = []
    i = 0
    while i < len(slist):
        if i + 1 < n:
            MIN = min(slist[0:i+1])
        else:
            start = i + 1 - n
            end = i + 1
            MIN = min(slist[start:end])
        min_list.append(MIN)
        i += 1
    return min_list


def cross(alist,blist):

    if len(alist) != len(blist):
        return 0

    crosscount = 0
    crosslist = []

    if len(alist)>1:
        for i in range(len(alist)):
            if alist[i-1]<=blist[i-1] and alist[i]>blist[i]:
                crosscount+=1
                crosslist.append((i,alist[i]))

    return (crosscount,crosslist)


def cross2(alist,blist):

    if len(alist) != 2 or len(blist) != 2:
        return False

    if alist[0] < blist[0] and alist[1] > blist[1]:
    # if alist[0] <= blist[0] and alist[1] > blist[1]:
        return True
    else:
        return False


def cross(alist,blist):

    if len(alist) != len(blist):
        return 0

    crosscount = 0
    crosslist = []

    if len(alist)>1:
        for i in range(len(alist)):
            if alist[i-1]<=blist[i-1] and alist[i]>blist[i]:
                crosscount+=1
                crosslist.append((i,alist[i]))

    return (crosscount,crosslist)


def CROSS(series_a=None, series_b=None):

    assert isinstance(series_a, list)
    assert isinstance(series_b, list)
    assert series_a.__len__() == series_b.__len__()

    cross_series = list()

    for i, v in enumerate(series_a):
        if i > 0:
            if series_a[i] > series_b[i] and series_a[i - 1] <= series_b[i - 1]:
                cross_series.append(True)
                continue

        cross_series.append(None)

    return cross_series


def crossdown(alist,stdvalue):
    crosscount = 0
    crosslist = []

    if len(alist)>1:
        for i in range(len(alist)):
            if alist[i-1]>stdvalue and alist[i]<stdvalue:
                crosscount+=1
                crosslist.append((i,alist[i]))

    return crosslist


def MID(list1, list2):
    mid = []
    J = len(list1)
    for j in range(J):
        tmpmid = (list1[j] + list2[j]) / 2
        mid.append(tmpmid)
    return mid


def HLV(list1, list2):
    hlv = []
    J = len(list1)
    for j in range(J):
        tmphlv = abs(list1[j] - list2[j])
        hlv.append(tmphlv)
    return hlv


def calculate_grid(data=160, factor=0.8, priceTick=10):
    #计算止盈止损价格间隔
    b, c = divmod(data*factor, priceTick)
    d = data * factor - c
    return d




def stringToDate(string):
    #example '2013-07-22 09:44:15+00:00'
    dt = datetime.strptime(string, "%H:%M:%S")
    # print dt
    return dt


# 最大数
def Get_Max(list):
    return max(list)


# 最小数
def Get_Min(list):
    return min(list)


# 极差
def Get_Range(list):
    return max(list) - min(list)


# 中位数
def get_median(data):
    data = sorted(data)
    size = len(data)
    if size % 2 == 0:
        # 判断列表长度为偶数
        median = (data[size // 2] + data[size // 2 - 1]) / 2
    if size % 2 == 1:
        # 判断列表长度为奇数
        median = data[(size - 1) // 2]
    return median


# 众数(返回多个众数的平均值)
def Get_Most(list):
    most = []
    item_num = dict((item, list.count(item))
                    for item in list)
    for k, v in list(item_num.items()):
        if v == max(item_num.values()):
            most.append(k)
    return sum(most) / len(most)


# 获取平均数
def Get_Average(list):
    sum = 0
    for item in list:
        sum += item
    return sum / len(list)

if __name__=='__main__':
    a=[1,3,4,5,2,3,56,22,22,55,66,22,11]
    hva = HHV(a, 5)
    print(a)
    print(hva)
    print((LLV(a,5)))
    print(calculate_grid(350, 0.8, 0.2))
    print(MA(a,5))
    print(len(a), len(MA(a,6)))
