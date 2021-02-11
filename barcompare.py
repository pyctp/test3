#encoding:utf-8
#比较同一合约，同一时间周期的k线数据是否一致。（简单判断数量是否一致， 并找出缺少的部分。现在是tb和tq的数据）
infile1 = 'rb1905_900tb.csv'
infile2 = 'rb1905_900.csv'

klines1=list()
klines2=list()
k1=tuple()
k2=tuple()
with open(infile1) as f1:
    for i, line in enumerate(f1):

        # 忽略 csv 头
        if i == 0:
            continue
        k1=line.split(',')
        k1=k1[:-2]
        klines1.append(k1)

with open(infile2) as f2:
    for i, line in enumerate(f2):

        # 忽略 csv 头
        if i == 0:
            continue
        k2=line.strip().split(',')
        # k2=k1[:-2]
        klines2.append(k2)
dts1=list()
dts2=list()

if len(klines1)!=len(klines2):
    for k in klines1:
        kk=k[0].replace('/','-')

        # print kk
        dts1.append(kk)

    for k in klines2:
        kk=k[0]
        dts2.append(kk)
        # a=input('wait...')

print(len(dts1), len(dts2))
for s in dts1:
    if s not in dts2:
        print(s)

print('testing')



