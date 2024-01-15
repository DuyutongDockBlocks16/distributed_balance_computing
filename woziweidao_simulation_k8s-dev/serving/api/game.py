import os
import sys
import traceback

sys.path.append('../../')
# from task_celery import nm_with_kafka,cpu_use_task
from flask_restx import Namespace, Resource, reqparse, fields
import datetime
import threading
import time
import redis
import setup
from setup import FIELDS_TERMINATED, TAB_CHARACTER, FILENAME_SPLITTER
import mysql_operate
import logging
from celery.utils.log import get_task_logger

ns = Namespace('card', description='卡牌模拟战斗接口')
parser = reqparse.RequestParser()

ru = Namespace('rerun', description='重跑接口')
ru_parser = reqparse.RequestParser()

st = Namespace('stop', description='停止接口')
st_parser = reqparse.RequestParser()

dlt = Namespace('del', description='redis del')
dlt_parser = reqparse.RequestParser()

get = Namespace('get', description='redis get')
get_parser = reqparse.RequestParser()

llen = Namespace('llen', description='redis llen')
llen_parser = reqparse.RequestParser()

info_clients = Namespace('info_clients', description='info_clients')
info_clients_parser = reqparse.RequestParser()

r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)

logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # 日志的格式
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_rkey_progress(nm_version, proc_version):
    return '_'.join(str(i) for i in [nm_version, proc_version, 'progress'])


def getlines(thefilepath, line_num, batch_size):
    lines_list = list()
    for currline, line in enumerate(open(thefilepath, 'r'), start=line_num):
        f = open(thefilepath, 'r')
        if currline < line_num + batch_size:
            lines_list.append(str(line).strip())
        if currline == line_num + batch_size:
            return lines_list
    return lines_list


def getline(enum_file_list, line_num):
    return enum_file_list[line_num]


@ns.route("/fight")
class Card(Resource):
    req_fight_model = ns.model(
        # todo 20220516 可以再评估一下是否需要增加新的字段
        name="req_fight_model", model={
            "FileNames": fields.String(required=True, description="文件名或多个文件名（用;隔开）",
                                       example='pair_list001.list;pair_list002.list;pair_list003.list'),
            "RandStart": fields.Integer(required=True, description="随机种子起始值", example=1),
            "RandEnd": fields.Integer(required=True, description="随机种子结束值", example=1),
            "NMVersion": fields.String(required=True, description="模拟版本号", example='0.0.1'),
            "ProcVersion": fields.String(required=True, description="一次模拟的处理版本号", example='1'),
            "analyze_jp": fields.String(required=True, description="是否分析跳变点数据，True为1，False为0", example='0'),
            "analyze_stats": fields.String(required=True, description="是否分析统计数据，True为1，False为0", example='1'),
        }
    )

    def new_thread_to_delay_tasks_from_file(self, nm_version, proc_version, mode, filenames, random_seed_start,
                                            random_seed_end, log_time, analyze_jp, analyze_stats):

        global r

        # todo 20220516这个函数关门给enum模式用的，可以不要了
        def append_battlelist(count, team_a_positive, team_b_positive):
            battle_list = list()
            for i in range(team_a_positive, count + 1):
                for j in range(i, count + 1):
                    if len(battle_list) == total_batch:
                        team_a_positive = i
                        team_b_positive = j

                        return battle_list, int(team_a_positive), int(team_b_positive)
                    elif (i - 1) * (2 * count - i + 2) / 2 + j - i >= (team_a_positive - 1) * (
                            2 * count - team_a_positive + 2) / 2 + team_b_positive - team_a_positive:
                        battle_list.append(tuple((
                            enum_file_list[i - 1][0],
                            enum_file_list[j - 1][0],
                            enum_file_list[i - 1][1]
                        ))
                        )
                        if i == count and j == count:
                            return battle_list, int(team_a_positive), int(team_b_positive)

        combine_file_path = "combinefile"
        os.remove(combine_file_path)
        print('finish dealing with combinefile')

        file_name_list = str(filenames).split(FILENAME_SPLITTER)

        # todo 20220516 这里的逻辑是为了把文件中包含的分区数字串写入到combine_file中。
        #  举例：文件名为：pair_list30101.list，这里要把30101取出来并在combinefile中增加一列
        for file_name in file_name_list:
            partition_str = file_name[file_name.find("_list") + 5:file_name.find(".list")]
            f = open(combine_file_path, 'a+')
            for currline, line in enumerate(open(f'gamefile/{file_name}', 'r')):
                if len(str(line)) > 9:
                    f.write(str(line).strip() + TAB_CHARACTER + partition_str + '\n')
            f.close()

        execute_file = open(combine_file_path, "r")
        count = 0
        total_count = 0

        # todo 20220516这里把if里面的逻辑拿出来，功能是统计共计多少任务，在日志中会用
        if mode == "pair":
            while (execute_file.readline() != ''):
                total_count += 1
        # todo 20220516 elif这里的判断逻辑不需要了
        elif mode == "enum":
            while (execute_file.readline() != ''):
                count += 1
            total_count = int((1 + count) * count / 2)
        execute_file.close()

        # todo 20220516 就只有一种mode，所以不需要打印了
        print('the mode is:')
        print(mode)

        # todo 20220516 这个if中的逻辑都不需要了
        if mode == "enum":
            enum_file_list = list()
            for currline, line in enumerate(open(combine_file_path, "r")):
                enum_file_list.append(
                    tuple((
                        str(line).strip().split(TAB_CHARACTER)[0],
                        str(line).strip().split(TAB_CHARACTER)[1]
                    ))
                )

        delayed_count = 0
        task_queue_min_length = setup.task_queue_min_length
        task_queue_batch_length = setup.task_queue_max_length - setup.task_queue_min_length
        task_queue_max_length = setup.task_queue_max_length

        if mode == "pair":
            print('mode is pair, start delay')
            execute_file = open(combine_file_path, "r")
            # 如果redis上有该模拟的进度信息，则读取任务进度
            if (r.exists(get_rkey_progress(nm_version, proc_version))):
                # TODO 文件seek测试
                delayed_count = int(r.get(get_rkey_progress(nm_version, proc_version)))
                pair_file_list = list()
                for currline, line in enumerate(open(combine_file_path, "r"),start=delayed_count):
                    pair_file_list.append(
                        tuple((
                            str(line).strip().split(TAB_CHARACTER)[0],
                            str(line).strip().split(TAB_CHARACTER)[1],
                            str(line).strip().split(TAB_CHARACTER)[2],
                        ))
                    )
            else:
                pair_file_list = list()
                for currline, line in enumerate(open(combine_file_path, "r")):
                    pair_file_list.append(
                        tuple((
                            str(line).strip().split(TAB_CHARACTER)[0],
                            str(line).strip().split(TAB_CHARACTER)[1],
                            str(line).strip().split(TAB_CHARACTER)[2],
                        ))
                    )
            while (delayed_count < total_count):
                try:
                    r.ping()
                except Exception as e:
                    logger.info('redis连接失败,正在尝试重连')
                    r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port,
                                    decode_responses=True)
                    r.ping()

                r_llen = r.llen('celery')
                is_stop = r.get(nm_version + ':' + proc_version)



                if (r_llen < task_queue_min_length):
                    logger.info(
                        f'---- start delay task! queue_len: {r_llen} < queue_min_length: {task_queue_min_length}, time: {datetime.datetime.now()}')
                    delayed_batch = 0
                    total_batch = task_queue_max_length if delayed_count == 0 else task_queue_batch_length
                    # 当前delay批次有两个结束条件，要么达到批次数量，要么达到最大对局数量
                    r.incr(get_rkey_progress(nm_version, proc_version), amount=total_batch)
                    pool = redis.ConnectionPool(host=setup.redis_host, port=setup.redis_port)
                    client = redis.StrictRedis(connection_pool=pool)
                    p = client.pipeline()
                    while (delayed_count < total_count and delayed_batch < total_batch):
                        # todo 断点续传
                        para_list = pair_file_list[delayed_count]

                        # todo 20220516 增加对局id的字符串，需要在的文档中补充一下字符串实例
                        p.lpush("celery",
                                nm_version + "," + str(para_list[2]) + "," + proc_version + "," + str(
                                    para_list[0]) + "," + str(
                                    para_list[0]) + "," + str(
                                    para_list[1]) + "," + str(
                                    para_list[1]) + "," + str(random_seed_start) + "," + str(
                                    random_seed_end) + "," + log_time + "," + analyze_jp + "," + analyze_stats
                                )

                        delayed_batch = delayed_batch + 1
                        delayed_count = delayed_count + 1
                        # todo 把delay_count写在文件里面
                        # r.incr(get_rkey_progress(nm_version, proc_version))
                    p.execute()
                    logger.info(f'---- delay {delayed_batch} tasks, total: {delayed_count}, count: {total_count}')
                else:
                    time.sleep(setup.task_queue_length_check_second)
                    # logger.info(f'---- wait 3s')
                if (is_stop == '1'):
                    r.delete('celery')
                    r.set(nm_version + ':' + proc_version, '0')
                    logger.info(f'---- 任务被用户停止，清空任务队列！----，nm_version: {nm_version}，proc_version: {proc_version}')
                    os.remove(combine_file_path)
                    return
            logger.info(f'---- finish delay task, time: {datetime.datetime.now()}')

            execute_file.close()

        def find_position(previous_delayed_count):
            find_count = 0
            for i in (1, count + 1):
                for j in (i, count + 1):
                    if find_count == previous_delayed_count + 1:
                        return i, j
                    find_count += 1

        # todo 20220516 这个if中的逻辑都不需要了
        if mode == "enum":
            print('mode is enum, start delay')
            team_a_positive = 1
            team_b_positive = 1
            # 如果redis上有该模拟的进度信息，则读取任务进度
            if (r.exists(get_rkey_progress(nm_version, proc_version))):
                # TODO 文件seek测试
                delayed_count = int(r.get(get_rkey_progress(nm_version, proc_version)))
                find_position(delayed_count)
            while (delayed_count < total_count):
                try:

                    r.ping()
                except Exception as e:
                    logger.info('redis连接失败,正在尝试重连')
                    r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port,
                                    decode_responses=True)
                    r.ping()

                r_llen = r.llen('celery')
                is_stop = r.get(nm_version + ':' + proc_version)
                if (r_llen < task_queue_min_length):
                    delayed_batch = 0
                    total_batch = task_queue_max_length if delayed_count == 0 else task_queue_batch_length
                    # todo 断点续传
                    battle_list, team_a_positive, team_b_positive = append_battlelist(count,
                                                                                      team_a_positive,
                                                                                      team_b_positive)

                    logger.info(
                        f'---- start delay task! queue_len: {r_llen} < queue_min_length: {task_queue_min_length}, time: {datetime.datetime.now()}')
                    # 当前delay批次有两个结束条件，要么达到批次数量，要么达到最大对局数量
                    r.incr(get_rkey_progress(nm_version, proc_version), amount=total_batch)
                    pool = redis.ConnectionPool(host=setup.redis_host, port=setup.redis_port)
                    client = redis.StrictRedis(connection_pool=pool)
                    p = client.pipeline()
                    while (delayed_count < total_count and delayed_batch < total_batch):
                        # nm_with_kafka.delay(
                        #     nm_version, str(battle_list[delayed_batch][2]), proc_version,
                        #     str(battle_list[delayed_batch][0]), str(battle_list[delayed_batch][0]),
                        #     str(battle_list[delayed_batch][1]), str(battle_list[delayed_batch][1]),
                        #     random_seed_start, random_seed_end
                        #                     ).forget()
                        # nm_with_kafka.delay(
                        #     nm_version, "30102", proc_version,
                        #     "32--1631--", "32--1631--",
                        #     "32--1631--", "32--1631--",
                        #     random_seed_start, random_seed_end
                        #                     ).forget()
                        p.lpush("celery",
                                nm_version+","+str(battle_list[delayed_batch][2])+","+proc_version+","+str(battle_list[delayed_batch][0])+","+str(battle_list[delayed_batch][0])+","+str(battle_list[delayed_batch][1])+","+str(battle_list[delayed_batch][1])+","+str(random_seed_start)+","+str(random_seed_end)+","+log_time+","+analyze_jp+","+analyze_stats)
                        # todo 把 str(battle_list[delayed_batch][0]) 和 str(battle_list[delayed_batch][1]) 写在文件里面
                        delayed_batch = delayed_batch + 1
                        delayed_count = delayed_count + 1
                    p.execute()
                    logger.info(f'---- delay {delayed_batch} tasks, total: {delayed_count}, count: {total_count}')
                else:
                    time.sleep(setup.task_queue_length_check_second)
                    # logger.info(f'---- wait 3s')
                if (is_stop == '1'):
                    r.delete('celery')
                    r.set(nm_version + ':' + proc_version, '0')
                    logger.info(f'---- 任务被用户停止，清空任务队列！----，nm_version: {nm_version}，proc_version: {proc_version}')
                    os.remove(combine_file_path)
                    return
            logger.info(f'---- finish delay task, time: {datetime.datetime.now()}')

        try:
            # TODO 删除的逻辑有点问题
            r.delete(get_rkey_progress(nm_version, proc_version))
        except Exception as e:
            print(e)

    @ns.doc(parser)
    @ns.expect(req_fight_model)
    def post(self):
        try:
            print('program began')
            data = ns.payload
            # todo  sql语句和建表语句也得改一下
            submit_sql = \
                "INSERT INTO fight_simlulation_data( file_names , rand_start , rand_end , nm_version ,proc_version ) " \
                "VALUES('{}', '{}' , '{}', '{}' ,'{}' )". \
                    format(data['FileNames'], data['RandStart'], data['RandEnd'],
                           data['NMVersion'], data['ProcVersion'])
            print('submit_sql')
            print(submit_sql)

            mysql_operate.db.execute_db(submit_sql)
            print('finish mysql execute')

            mode = str()
            if str(data['FileNames']).find("enum") != -1:
                mode = "enum"
            elif str(data['FileNames']).find("pair") != -1:
                mode = "pair"

            # for i in range(0,500000):
            #     nm_with_kafka.delay(
            #         "0.0.1", "0.0.1", "1",
            #         "2438545504", "2438545504",
            #         "2438545504", "2438545504",
            #         1, 5
            #     ).forget()
            # TODO 如果master挂掉了，需要从数据库中读取logtime，确保每次模拟用的是同一个logtime
            logtime = str(int(time.time()))
            kafka_proc_thread = threading.Thread(target=self.new_thread_to_delay_tasks_from_file,
                                                 args=(data['NMVersion'], data['ProcVersion'], mode, data['FileNames'],
                                                       data['RandStart'], data['RandEnd'], logtime, data['analyze_jp'], data['analyze_stats']),
                                                 name='kafka_proc_thread')
            kafka_proc_thread.start()
            print('kafka_proc_thread has started')
            return {'msg': "success", "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@ru.route("/fight")
class Rerun(Resource):
    rerun_model = ru.model(
        name="rerun_model", model={
            "Mode": fields.String(required=True, description="重跑类型",
                                  example='pair'),
            "Filename": fields.String(required=True, description="重跑数据的文件名", example='test.txt'),
            "RandStart": fields.Integer(required=True, description="随机种子起始值", example=1),
            "RandEnd": fields.Integer(required=True, description="随机种子结束值", example=1),
            "NMVersion": fields.String(required=True, description="模拟版本号", example='0.0.1'),
            "ProcVersion": fields.String(required=True, description="一次模拟的处理版本号", example='1'),
            "analyze_jp": fields.String(required=True, description="是否分析跳变点数据，True为1，False为0", example='0'),
            "analyze_stats": fields.String(required=True, description="是否分析统计数据，True为1，False为0", example='1'),
        }
    )

    def new_thread_to_rerun_tasks_from_file(self, filename, random_seed_start,
                                            random_seed_end, nm_version, proc_version, log_time, analyze_jp, analyze_stats):

        global r
        rerun_file = open("/data/wzwd_celery_k8s/error_filter/error_file/"+filename, "r")
        total_count = 0
        while (rerun_file.readline() != ''):
            total_count += 1
        rerun_file.close()

        delayed_count = 0
        task_queue_min_length = setup.task_queue_min_length
        task_queue_batch_length = setup.task_queue_max_length - setup.task_queue_min_length
        task_queue_max_length = setup.task_queue_max_length

        # 如果redis上有该模拟的进度信息，则读取任务进度
        if (r.exists(get_rkey_progress(nm_version, proc_version))):
            # TODO 文件seek测试
            delayed_count = r.get(get_rkey_progress(nm_version, proc_version))
            rerun_file.seek()

        while (delayed_count < total_count):
            rerun_file = open("/data/wzwd_celery_k8s/error_filter/error_file/"+filename, "r")
            try:

                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()

            r_llen = r.llen('celery')
            is_stop = r.get(nm_version + ':' + proc_version)

            if (r_llen < task_queue_min_length):
                logger.info(
                    f'---- start delay task! queue_len: {r_llen} < queue_min_length: {task_queue_min_length}, time: {datetime.datetime.now()}')
                delayed_batch = 0
                total_batch = task_queue_max_length if delayed_count == 0 else task_queue_batch_length
                # 当前delay批次有两个结束条件，要么达到批次数量，要么达到最大对局数量
                r.incr(get_rkey_progress(nm_version, proc_version), amount=total_batch)
                pool = redis.ConnectionPool(host=setup.redis_host, port=setup.redis_port)
                client = redis.StrictRedis(connection_pool=pool)
                p = client.pipeline()
                while (delayed_count < total_count and delayed_batch < total_batch):
                    line = rerun_file.readline()
                    para_list = line.strip().split(TAB_CHARACTER)
                    p.lpush("celery",
                            ",".join(list((
                                nm_version, str(para_list[2]), proc_version,
                                str(para_list[0]), str(para_list[0]),
                                str(para_list[1]), str(para_list[1]),
                                str(random_seed_start), str(random_seed_end), log_time, analyze_jp, analyze_stats
                            )))
                            )
                    delayed_batch = delayed_batch + 1
                    delayed_count = delayed_count + 1
                p.execute()
                logger.info(f'---- delay {delayed_batch} tasks, total: {delayed_count}, count: {total_count}')
            else:
                time.sleep(setup.task_queue_length_check_second)
            if (is_stop == '1'):
                r.delete('celery')
                r.set(nm_version + ':' + proc_version, '0')
                logger.info(f'---- 任务被用户停止，清空任务队列！----，nm_version: {nm_version}，proc_version: {proc_version}')
                return
                # print(f'---- wait 3s')
        logger.info(f'---- finish delay task, time: {datetime.datetime.now()}')
        rerun_file.close()
        r.delete(get_rkey_progress(nm_version, proc_version))
        # os.remove(filename)

    @ru.doc(ru_parser)
    @ru.expect(rerun_model)
    def post(self):

        try:
            rerun_data = ru.payload

            submit_sql = "INSERT INTO rerun_data(mode, file_name, rand_start , rand_end , nm_version ,proc_version) " \
                         "VALUES('{}', '{}', '{}', '{}', '{}', '{}')".format(rerun_data['Mode'], rerun_data['Filename'],
                                                                             rerun_data['RandStart'],
                                                                             rerun_data['RandEnd'],
                                                                             rerun_data['NMVersion'],
                                                                             rerun_data['ProcVersion'])

            mysql_operate.db.execute_db(submit_sql)
            logtime = str(int(time.time()))

            kafka_rerun_proc_thread = threading.Thread(target=self.new_thread_to_rerun_tasks_from_file, args=(
                rerun_data['Filename'], rerun_data['RandStart'], rerun_data['RandEnd'],
                rerun_data['NMVersion'], rerun_data['ProcVersion'], logtime, rerun_data['analyze_jp'], rerun_data['analyze_stats']
            ), name='kafka_rerun_proc_thread')
            kafka_rerun_proc_thread.start()
            return {'msg': "success", "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@st.route("/fight")
class stop(Resource):
    stop_model = st.model(
        name="stop_model", model={
            "NMVersion": fields.String(required=True, description="模拟版本号", example='0.0.1'),
            "ProcVersion": fields.String(required=True, description="一次模拟的处理版本号", example='1'),
        }
    )

    @st.doc(st_parser)
    @st.expect(stop_model)
    def post(self):

        try:
            stop_data = st.payload
            global r
            try:

                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()
            r.set(stop_data['NMVersion'] + ':' + stop_data['ProcVersion'], 1)
            return {'msg': "success", "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@dlt.route("/fight")
class delete_key(Resource):
    dlt_model = dlt.model(
        name="dlt_model", model={
            "key": fields.String(required=True, description="redis 要删除的key", example='celery'),
        }
    )

    @dlt.doc(dlt_parser)
    @dlt.expect(dlt_model)
    def post(self):

        try:
            global r
            try:
                dlt_data = dlt.payload
                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()
            r.delete(dlt_data['key'])
            return {'msg': "success", "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@get.route("/fight")
class get_key(Resource):
    get_model = get.model(
        name="get_model", model={
            "key": fields.String(required=True, description="redis 要获得的key", example='celery'),
        }
    )

    @get.doc(get_parser)
    @get.expect(get_model)
    def post(self):

        try:
            global r
            try:
                get_data = get.payload
                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()
            val = r.get(get_data['key'])
            return {'msg': "success", 'value': val, "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@llen.route("/fight")
class llen_key(Resource):
    llen_model = llen.model(
        name="llen_model", model={
            "key": fields.String(required=True, description="redis 要获得 llen 的key", example='celery'),
        }
    )

    @llen.doc(llen_parser)
    @llen.expect(llen_model)
    def post(self):

        try:
            global r
            try:
                llen_data = llen.payload
                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()
            val = r.llen(llen_data['key'])
            return {'msg': "success", 'llen': val, "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))


@info_clients.route("/fight")
class info_clients_num(Resource):

    @info_clients.doc(info_clients_parser)
    @info_clients.expect()
    def post(self):

        try:
            global r
            try:
                r.ping()
            except Exception as e:
                logger.info('redis连接失败,正在尝试重连')
                r = redis.Redis(host=setup.redis_host, db=setup.redis_db, port=setup.redis_port, decode_responses=True)
                r.ping()

            val = r.execute_command("info clients")
            return {'msg': "success", 'info_clients': val, "code": 200}
        except Exception as e:
            traceback.print_exc()
            ns.abort(400, str(e))
