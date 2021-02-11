del rb*.*
d:\python37\python bardl.py -n rb1905 -g 60
d:\python37\python bardl.py -n rb1910 -g 60
d:\python37\python bardl.py -n rb2001 -g 60
py2 integrate_minute_k_line.py -s rb1905_60.json -i 13
py2 integrate_minute_k_line.py -s rb1910_60.json -i 13
py2 integrate_minute_k_line.py -s rb2001_60.json -i 13

d:\python37\python integrate_minute_k_line.py -s rb1905_60.json -i 3
d:\python37\python integrate_minute_k_line.py -s rb1905_60.json -i 5

d:\python37\python integrate_minute_k_line.py -s rb1910_60.json -i 3
d:\python37\python integrate_minute_k_line.py -s rb1910_60.json -i 5

d:\python37\python integrate_minute_k_line.py -s rb2001_60.json -i 3
d:\python37\python integrate_minute_k_line.py -s rb2001_60.json -i 5
