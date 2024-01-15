from setup import Card
import lupa
from kafka_producer import *
from app_error import *

card = Card()
DEFAULT = ''

# TODO 测试静态方法
LIBS = "./Fight.lua"
f = open(LIBS)
# \n 是将代码加入行分割，这样使用 lua.execute() 来运行代码
code_str = '\n'.join(f.readlines())
f.close()

k_producer = Kafka_Producer()

def sdk_nm(a_index, b_index, random_seed):
    # lua 每一套阵容的战斗都要执行 lua 环境的初始化
    lua = lupa.LuaRuntime()
    g = lua.globals()
    lua.execute(code_str)
    print('indexa, indexb, random_seed', a_index, b_index, random_seed)
    lua_table = g.fight(a_index, b_index, random_seed)
    return lua_table

def data_transform(nm_version, partition_str, proc_version, a_index, b_index, random_seed):

    lua_table = sdk_nm(a_index, b_index, random_seed)
    if lua_table==-1:
        raise SDK_error('sdk 内部可捕获异常！')

    else:
        # 捕获 lua table 的错误
        # TODO 测试lua_table是否是dict类型，这样就不用每次都转成dict。测试完毕，lua_table就是Lua Table类型！
        lua_table_dict = dict(lua_table)
        time_stamp = lua_table_dict['last_time']
        result = lua_table_dict['result']
        use_frame = lua_table_dict['use_frame']

        for type_key in card.properties:
            # 解析不同数据类型
            for val in dict(lua_table_dict[type_key]).values():
                # 某个 frame 下的数据（状态）
                tem = dict(val)
                properties_val = list()
                for f_key in card.frame_properties[str(type_key)]:
                    # 弃用字符串规则：f_key:deprecated，如果字符串弃用，不解析内容，直接置为''
                    if ':' in f_key and f_key.split(':')[-1]=='deprecated':
                        properties_val.append(DEFAULT)
                    try:

                        properties_val.append(frame_val_transform(tem[f_key]))
                    # TODO 测试key不存在时是否会抛出异常，测试DEFAULT为''时，插入数据库时是否为Null
                    except KeyError:
                        properties_val.append(DEFAULT)

                frame_hiverow=get_data_info(nm_version, partition_str, proc_version, a_index, b_index, random_seed, result, time_stamp, properties_val)
                k_producer.send(topic=get_topic(type_key), key=None, value=frame_hiverow.encode('ascii'))

        return str(use_frame)


def frame_val_transform(val):
    if lupa.lua_type(val)=='table':
        res_list = list()
        for ele in dict(val).items():
            key = str(ele[0]);
            # print(f'key is {key}')
            value = str(ele[1]);
            # print(f'value is {value}')
            res_list.append(f'{key}:{value}')
        return BaseStat.COLLECTION_ITEMS_TERMINATED.join(res_list)
    elif lupa.lua_type(val)=='boolean':
        return str(1) if bool(val) else str(0)
    else:
        return str(val)

def get_topic(type):
    return f'HB0002_wzwd_nm_battlelog_{type}'

def get_error_info(args):
    return BaseStat.FIELDS_TERMINATED.join(str(i) for i in args)

def get_data_info(nm_version, partition_str, proc_version, a_index, b_index, random_seed, result, time_stamp,
                  properties_val):
    return BaseStat.FIELDS_TERMINATED.join([BaseStat.FIELDS_TERMINATED.join(str(i) for i in
                                                          [nm_version, partition_str, proc_version, a_index, b_index,
                                                           random_seed, result, time_stamp]),
                                   BaseStat.FIELDS_TERMINATED.join(properties_val)])

