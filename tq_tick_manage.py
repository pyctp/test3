#encoding:utf-8
#!/usr/bin/pypy
infile = 'rb1905.csv'
outfile = 'rb1905n.csv'

outf = open(outfile,'w')

with open(infile) as f:

    for i, line in enumerate(f):

        # 忽略 csv 头
        if i == 0:
            continue
        # 读取数据行，赋值给变量
        row = line.split(',')

        ddate=row[0].split()[0]
        dtime=row[0].split()[1][0:12]
        newrow=''.join([ddate,' ',dtime,',',row[1],',',row[2],',',row[3],',',row[4],',',row[5],',',row[6],',',row[7],',',row[8],',',row[9],',',row[10]])

        outf.writelines(newrow)

        # print date_time, topen, thigh, tlow, tclose
