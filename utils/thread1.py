# encoding: utf-8
# Python queue队列，实现并发，在网站多线程推荐最后也一个例子,比这货简单，但是不够规范


__author__ = 'yeayee.com'  # 由本站增加注释，可随意Fork、Copy

from queue import Queue  # Queue在3.x中改成了queue
import random
import threading
import time


class Producer(threading.Thread):
    """
    Producer thread 制作线程
    """
    def __init__(self, t_name, queue):  # 传入线程名、实例化队列
        threading.Thread.__init__(self, name=t_name)  # t_name即是threadName
        self.data = queue

    """
    run方法 和start方法:
    它们都是从Thread继承而来的，run()方法将在线程开启后执行，
    可以把相关的逻辑写到run方法中（通常把run方法称为活动[Activity]）；
    start()方法用于启动线程。
    """

    def run(self):
        with open('rb1910_0.csv') as f:
            for i, line in enumerate(f):

                # for i in range(5):  # 生成0-4五条队列
                print("%s: %s is producing %d to the queue!" % (time.ctime(), self.getName(), i))  # 当前时间t生成编号d并加入队列
                print(line)
                self.data.put(line)  # 写入队列编号
                time.sleep(random.randrange(10) / 5)  # 随机休息一会
                print("%s: %s producing finished!" % (time.ctime(), self.getName))  # 编号d队列完成制作


class Consumer(threading.Thread):
    """
    Consumer thread 消费线程，感觉来源于COOKBOOK
    """
    def __init__(self, t_name, queue):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue

    def run(self):
        for i in range(5):
            val = self.data.get()
            print("%s: %s is consuming. %d in the queue is consumed!" % (time.ctime(), self.getName(), val))  # 编号d队列已经被消费
            time.sleep(random.randrange(10))
        print("%s: %s consuming finished!" % (time.ctime(), self.getName()))  # 编号d队列完成消费


def main():
    """
    Main thread 主线程
    """
    queue = Queue()  # 队列实例化
    producer = Producer('Pro.', queue)  # 调用对象，并传如参数线程名、实例化队列
    consumer = Consumer('Con.', queue)  # 同上，在制造的同时进行消费
    producer.start()  # 开始制造
    consumer.start()  # 开始消费
    """
    join（）的作用是，在子线程完成运行之前，这个子线程的父线程将一直被阻塞。
　　join()方法的位置是在for循环外的，也就是说必须等待for循环里的两个进程都结束后，才去执行主进程。
    """
    producer.join()
    consumer.join()
    print('All threads terminate!')


if __name__ == '__main__':
    main()


"""运行结果：

Thu Feb  4 11:05:48 2016: Pro. is producing 0 to the queue!
Thu Feb  4 11:05:48 2016: Pro. is producing 1 to the queue!
Thu Feb  4 11:05:48 2016: Con. is consuming. 0 in the queue is consumed!
Thu Feb  4 11:05:49 2016: Pro. is producing 2 to the queue!
Thu Feb  4 11:05:50 2016: Pro. is producing 3 to the queue!
Thu Feb  4 11:05:51 2016: Pro. is producing 4 to the queue!
Thu Feb  4 11:05:52 2016: Con. is consuming. 1 in the queue is consumed!
Thu Feb  4 11:05:53 2016: <bound method Producer.getName of <Producer(Pro., started 6864)>> producing finished!
Thu Feb  4 11:06:00 2016: Con. is consuming. 2 in the queue is consumed!
Thu Feb  4 11:06:06 2016: Con. is consuming. 3 in the queue is consumed!
Thu Feb  4 11:06:06 2016: Con. is consuming. 4 in the queue is consumed!
Thu Feb  4 11:06:12 2016: Con. consuming finished!
All threads terminate!

"""