import threading
import multiprocessing
import time
import json
import redis
from celery import Celery
import time

import setup
from kafka_producer import *
from fetchData import Fetch
from celery.utils.log import get_task_logger
from app_error import *
from kafka.errors import KafkaError
import sys
import logging

from stats import battle_data_classify
from stats.base_stat import BaseStat

logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # 日志的格式
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

app = Celery('cards')
app.config_from_object('celeryconfig')
# # app.control.time_limit('nm_with_kafka',soft=10, hard=120, reply=False)
fetch = Fetch()


cpu_cores = 32
concurrency = 1
max_thread = cpu_cores * concurrency


def worker_nm_with_kafka(nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start,
                         b_index_end,
                         random_seed_start, random_seed_end, log_time, analyze_jp,
                         analyze_stats):  # nm_version为模拟版本，proc_version为该次模拟的第几次数据处理
    # send_massage = b'{"battle_gra_id": "duyttest2022041101_1_30103_60--3520--_--4641--26_1", "proc_version": "1", "nm_version": "duyttest2022041101", "list_version": "30103", "logtime": "1649664128", "result": 2, "last_frame": 531, "last_time": "17.7", "execute_time": "0.26", "fightActor1": "10000060", "fightActor2": "", "fightActor3": "10000035", "fightActor4": "10000020", "fightActor5": "", "fightActor6": "", "fightActor7": "10000046", "fightActor8": "10000041", "fightActor9": "", "fightActor10": "10000026"}'
    #
    # print('kafka_producer.send')
    # kafka_producer.send(topic='HB0002_wzwd_nm_battlelog_Battle', key=None, value=send_massage)
    #
    # print('kafka_producer.flush()')
    # kafka_producer.flush()
    # print('program finished')
    kafka_producer = Kafka_Producer()
    base_stat = BaseStat(nm_version, proc_version, partition_str, a_index_start, b_index_start, random_seed_start,
                         log_time)
    res_list = base_stat.get_row_key_and_fixed_field(base_stat.get_pair_row_key())
    pair_list = [partition_str, proc_version, a_index_start, b_index_start, random_seed_start, random_seed_end]
    pair_info = BaseStat.get_info(res_list, pair_list, battle_data_classify.Pair)
    try:
        print(nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start,
              b_index_end, log_time,
              random_seed_start, random_seed_end)
        logger.info('nm_with_kafka start')
        fetch.nm_with_kafka(
            nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start, b_index_end,
            random_seed_start, random_seed_end, log_time, analyze_jp, analyze_stats
        )
        # flush 会将当前buffer里所有的msg立即发送，并block直到这些msg对应的requests的responses返回。flush之后，如果可以正常发送Success的msg，说明kafka持久化成功。
        logger.info('kafka_producer.flush()')
        kafka_producer.flush()
        logger.info(" kafka_producer.flush()")

        # 如果之前回调过err_callback，Success不会成功！
        kafka_producer.send_get(topic=base_stat.get_topic(battle_data_classify.Success), key=None, value=pair_info)
        # 发送Success msg也可能会失败，这局其实成功了，不过不影响，我们可以认为这局失败了。然后重跑。这种情况应该会极少
        return [nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start, b_index_end,
                random_seed_start, random_seed_end, 'Success']
    except BaseException as e:
        exc_type = battle_data_classify.Other_Error
        try:
            logger.info('异步任务失败', repr(e))

            if (isinstance(e, SDK_error)):
                exc_type = battle_data_classify.SDK_Error
            elif ((isinstance(e, AssertionError) and str(e) == 'RecordAccumulator is closed') or isinstance(e,
                                                                                                            KafkaError)):
                exc_type = battle_data_classify.Kafka_Error
            elif (isinstance(e, MemoryError)):
                exc_type = battle_data_classify.Memory_Error
            else:
                pass
            if exc_type != battle_data_classify.Kafka_Error:
                pass
                kafka_producer.send_get(topic=base_stat.get_topic(exc_type), key=None, value=pair_info)
        except BaseException as be:
            # 如果错误信息发送至kafka失败了，目前只能写日志
            logger.info(f'on_failure send Exception: {repr(be)}')
            logger.info(f'on_failure send battle_info: {pair_info}')
            
def process_shell(nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start,
                         b_index_end,
                         random_seed_start, random_seed_end, log_time, analyze_jp,
                         analyze_stats):
    worker_nm_with_kafka_thread = threading.Thread(target=worker_nm_with_kafka, args=(
        nm_version, partition_str, proc_version, a_index_start, a_index_end, b_index_start,
        b_index_end,
        random_seed_start, random_seed_end, log_time, analyze_jp,
        analyze_stats
    ), name='worker_nm_with_kafka')
    worker_nm_with_kafka_thread.start()
    worker_nm_with_kafka_thread.join()


class MyThread(threading.Thread):
    """继承Thread类重写run方法创建新进程"""

    def __init__(self, func, args, name):
        """
        :param func: run方法中要调用的函数名
        :param args: func函数所需的参数
        """
        threading.Thread.__init__(self)

        self.func = func
        self.args = args
        self.name = name

    def run(self):
        self.func(self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6],
                  self.args[7], self.args[8], self.args[9], self.args[10], self.args[11])


class MyProcess(multiprocessing.Process):
    """继承Thread类重写run方法创建新进程"""

    def __init__(self, func, args, name):
        """
        :param func: run方法中要调用的函数名
        :param args: func函数所需的参数
        """
        multiprocessing.Process.__init__(self)

        self.func = func
        self.args = args
        self.name = name

    def run(self):
        self.func(self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6],
                  self.args[7], self.args[8], self.args[9], self.args[10], self.args[11])


if __name__ == '__main__':
    r = redis.Redis(host=setup.redis_host, port=setup.redis_port, decode_responses=True)
    first_time_flag = 0
    while True:
        if r.llen("celery") == 0:
            time.sleep(1)
            first_time_flag = 0
        elif r.llen("celery") > 0:
            if first_time_flag == 0:
                arg_list_num = list()
                # for i in range(multiprocessing.cpu_count() - 2):
                for i in range(1):
                    msg = r.rpop("celery")
                    if msg:
                        arg_list = list()
                        for arg in msg.split(","):
                            arg_list.append(arg)
                        arg_list_num.append(arg_list)
                thread_list = list()
                for t in arg_list_num:
                    m = MyProcess(worker_nm_with_kafka,
                                  (t[0], t[1], t[2], t[3], t[4], t[5], t[6], int(t[7]), int(t[8]), t[9], t[10], t[11]),
                                  "worker_nm_with_kafka")
                    thread_list.append(m)
                for m in thread_list:
                    m.start()

            first_time_flag = 1

            # for i in range(multiprocessing.cpu_count() - 2):
            for i in range(1):
                if thread_list[i].is_alive() is False:
                    thread_list.remove(thread_list[i])
                    msg = r.rpop("celery")
                    if msg:
                        arg_list = list()
                        for arg in msg.split(","):
                            arg_list.append(arg)
                        m = MyProcess(worker_nm_with_kafka,
                                      (arg_list[0], arg_list[1], arg_list[2], arg_list[3], arg_list[4], arg_list[5],
                                       arg_list[6], int(arg_list[7]), int(arg_list[8]), arg_list[9], arg_list[10],
                                       arg_list[11]),
                                      "worker_nm_with_kafka")
                        thread_list.append(m)
                        m.start()

            # while True:
            #     need_break_flag = 0
            #     process_num = 0
            #     for m in thread_list:
            #         if m.is_alive() is False:
            #             need_break_flag = 1
            #             process_num += 1
            #     if need_break_flag == 1:
            #         break

    # while True:
    #     if r.llen("celery") == 0:
    #         time.sleep(20)
    #     elif r.llen("celery") > 0:
    #         arg_list_num = list()
    #         for i in range(0, max_thread):
    #             msg = r.rpop("celery")
    #             # todo 以下为正常逻辑
    #             if msg:
    #                 arg_list = list()
    #                 for arg in msg.split(","):
    #                     arg_list.append(arg)
    #                 arg_list_num.append(arg_list)
    #             else:
    #                 break
    #
    #         # todo 以下为正常逻辑
    #         thread_list = list()
    #
    #         pool_sema = multiprocessing.BoundedSemaphore(max_thread)
    #         for t in arg_list_num:
    #             m = MyProcess(worker_nm_with_kafka,
    #                          (t[0], t[1], t[2], t[3], t[4], t[5], t[6], int(t[7]), int(t[8]), t[9], t[10], t[11]),
    #                          "worker_nm_with_kafka")
    #             thread_list.append(m)
    #
    #         for m in thread_list:
    #             m.start()
    #
    #         for m in thread_list:
    #             m.join()  # 子线程调用join()方法，使主线程等待子线程运行完毕之后才退出
