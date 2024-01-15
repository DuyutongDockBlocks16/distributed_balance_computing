import lupa
from stats import json_keys
import json
import stats.battle_data_classify as battle_data_classify

# 1. 初始化对局的最基本属性，例如nm_version，proc_version
# 2. 通用的类sql聚合函数
# 3. 获取所有topic名称的逻辑
# 4. 所有row_key的生成逻辑
# 5. lua和python数据类型转换的逻辑
# 6. 数据输出的格式转换
class BaseStat:

    FIELDS_TERMINATED = '\001'
    ROW_KEY_TERMINATED = '_'
    # FIELDS_TERMINATED = '|'
    COLLECTION_ITEMS_TERMINATED = ','
    TAB_CHARACTER = '\t'
    FILENAME_SPLITTER = ';'
    CHA_ENCODING = 'utf-8'

    def __init__(self, nm_version, proc_version, list_version, left_id, right_id, random_seed, log_time):
        self.nm_version = nm_version
        self.proc_version = proc_version
        self.list_version = list_version
        self.left_id = left_id
        self.right_id = right_id
        self.random_seed = random_seed
        self.log_time = log_time

    # 按照对局统计粒度的各种聚合函数（模拟sql功能）
    # last_keys：格式为tuple，tuple里的元素为需要统计last逻辑的key，ex：('HP', 'Frame','State')
    # accum_keys：格式为dict，ex：{'damage':{'damage':'gt_0','isHit':'eq_True'}}，
        # 外层dict的key为需要accum的key，
        # 内层dict为数据筛选的where条件，key为要筛选的key，value为key需要满足的条件，如果不需要where条件筛选，就传None
        # value目前有两种格式：gt_/eq_，分别表示大于和等于，大于会将后面的值转换成int来比较，eq会将后面的值转换成string来比较，其他的逻辑可以自行添加
    # groupby_accum_keys：格式为dict，ex：{'skillId':{'damage':{'damage':'gt_0','isHit':'eq_True'}}}，
        # 外层dict的key为需要分组的key，
        # 内存dict与accum_keys的结构一致
    # groupby_count_keys：格式为dict，ex：{'skillId':{'1':{'damage':'gt_0','isHit':'eq_True'}}，
        # 外层dict的key为需要分组的key，
        # 内层dict与accum_keys的结构一致，只不过key不需要额外指定，可以写常量1
    # max_keys：格式为tuple，tuple里的元素为需要统计max逻辑的key，ex：('MaxHP',)
    # TODO 方法还不是很通用，有需求再统一添加
    def analyze_stats(self, context, card_key, data, last_keys=None, accum_keys=None, groupby_accum_keys=None, groupby_count_keys=None, max_keys=None):
        if card_key not in context:
            context[card_key] = dict()
        # 计算max逻辑
        if max_keys != None:
            for max_key in max_keys:
                cur_val = data[max_key]
                if f'max_{max_key}' not in context[card_key]:
                    context[card_key][f'max_{max_key}'] = cur_val
                else:
                    pre_max_val = context[card_key][f'max_{max_key}']
                    if pre_max_val==None or pre_max_val=='' or (float(cur_val) > float(pre_max_val)):
                        context[card_key][f'max_{max_key}'] = cur_val
                    else:
                        pass

        # 计算最后一帧逻辑
        if last_keys != None:
            for last_key in last_keys:
                # 取结束时最后一帧数据
                last_val = data[last_key]
                context[card_key][f'last_{last_key}'] = last_val
        # 计算累加逻辑
        if accum_keys != None:
            for accum_key in dict(accum_keys).keys():
                where_clause = accum_keys[accum_key]
                if where_clause != None:
                    res = self.satisfy_where_clause(where_clause, data)
                    if not res: continue
                accum_val = data[accum_key]
                if (f'accum_{accum_key}' not in context[card_key]):
                    context[card_key][f'accum_{accum_key}'] = accum_val
                else:
                    context[card_key][f'accum_{accum_key}'] = context[card_key][f'accum_{accum_key}'] + accum_val
        # 计算groupby_accum逻辑
        if groupby_accum_keys != None:
            for group_accum_key_item in dict(groupby_accum_keys).items():
                # skillId
                group_accum_key = group_accum_key_item[0]
                # skillId_val
                group_accum_val = str(data[group_accum_key])
                # damage
                accum_keys = group_accum_key_item[1]
                for accum_key in dict(accum_keys).keys():
                    where_clause = accum_keys[accum_key]
                    if where_clause != None:
                        res = self.satisfy_where_clause(where_clause, data)
                        if not res: continue
                    accum_val = data[accum_key]
                    if (f'groupby_{group_accum_key}_accum_{accum_key}' not in context[card_key]):
                        context[card_key][f'groupby_{group_accum_key}_accum_{accum_key}'] = {group_accum_val: accum_val}
                    elif (group_accum_val not in context[card_key][f'groupby_{group_accum_key}_accum_{accum_key}']):
                        context[card_key][f'groupby_{group_accum_key}_accum_{accum_key}'][group_accum_val] = accum_val
                    else:
                        context[card_key][f'groupby_{group_accum_key}_accum_{accum_key}'][group_accum_val] = \
                            context[card_key][f'groupby_{group_accum_key}_accum_{accum_key}'][group_accum_val] + accum_val
        # 计算groupby_count逻辑
        if groupby_count_keys != None:
            for group_count_key in dict(groupby_count_keys).keys():
                group_count_val = str(data[group_count_key])
                where_clause = groupby_count_keys[group_count_key]['1']
                if where_clause != None:
                    res = self.satisfy_where_clause(where_clause, data)
                    if not res: continue
                if (f'groupby_{group_count_key}_count' not in context[card_key]):
                    context[card_key][f'groupby_{group_count_key}_count'] = {group_count_val: 1}
                elif (group_count_val not in context[card_key][f'groupby_{group_count_key}_count']):
                    context[card_key][f'groupby_{group_count_key}_count'][group_count_val] = 1
                else:
                    context[card_key][f'groupby_{group_count_key}_count'][group_count_val] = \
                        context[card_key][f'groupby_{group_count_key}_count'][group_count_val] + 1

    # ------------ topic 加工逻辑
    # ------ 还有4个记录模拟状态的topic（Success，Other_Error，Memory_Error，SDK_Error）

    # 作为基本方法
    # 作为ODS数据，有5个topic（Damage，TakeDamage，CastSkill，Heal，EnergyRecovery）
    @staticmethod
    def get_topic(summary_type):
        return f'HB0002_wzwd_nm_battlelog_{summary_type}'

    @staticmethod
    def get_topic_battle_hero_status_jp():
        return BaseStat.get_topic(f'{battle_data_classify.FrameStatue}_JP')

    # 有4个跳变点的topic（Damage，TakeDamage，Heal，EnergyRecovery）
    @staticmethod
    def get_topic_battle_hero_summary_jp(summary_type):
        return BaseStat.get_topic(f'{summary_type}_JP')

    # 聚合指标的两个topic
    @staticmethod
    def get_topic_battle():
        return BaseStat.get_topic(battle_data_classify.Battle)

    @staticmethod
    def get_topic_battle_hero():
        return BaseStat.get_topic(battle_data_classify.BattleHero)

    # ------------ row key 设计
    # nm 粒度
    def get_nm_row_key(self):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version])
    # proc 粒度
    def get_proc_row_key(self):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version,self.proc_version])

    def get_list_row_key(self):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version,self.proc_version,self.list_version])

    def get_pair_row_key(self):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version,self.proc_version,self.list_version,self.left_id,self.right_id])

    def get_battle_row_key(self):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version,self.proc_version,self.list_version,self.left_id,self.right_id,
                                                                self.random_seed])

    def get_hero_row_key(self,actor_id,side):
        return BaseStat.ROW_KEY_TERMINATED.join(str(i) for i in [self.nm_version,self.proc_version,self.list_version,self.left_id,self.right_id,
                                                                self.random_seed,actor_id,side])

    def get_row_key_and_fixed_field(self, row_key):
        return [row_key, self.proc_version, self.nm_version, self.list_version, self.log_time]

    # ------------ 通过pair和pos获得英雄的actor_id
    def get_actor_id(self, pos):
        battle = self.left_id
        p = pos
        if (pos > 5):
            p = pos -5
            battle = self.right_id
        actor_short_id = battle[(p-1)*2:(p-1)*2+2]
        if actor_short_id!='--': return int(f'100000{actor_short_id}')
        return None

    # 实现了gt和eq的功能，需要其他的逻辑自行添加
    def satisfy_where_clause(self, where_clause, data):
        wc_dict = dict(where_clause)
        for key in wc_dict.keys():
            val = data[key]
            if val==None:
                return False
            judge_con = wc_dict[key]
            judge = str(judge_con).split('_')[0]
            judge_val = str(judge_con).split('_')[1]
            if (judge=='gt'):
                if val > int(judge_val):
                    pass
                else: return False
            if (judge=='eq'):
                if str(val) == str(judge_val):
                    pass
                else: return False
        return True

    # ------------ 数据清洗

    # lua 不同类型的值的转换逻辑
    @staticmethod
    def frame_val_transform(val):
        if lupa.lua_type(val) == 'table':
            res_list = list()
            key_list = list(val.keys())
            # 如果是dict，按照key排序。避免因为item顺序的问题而导致对值的判断不相等
            key_list.sort()
            for key in key_list:
                value = val[key];
                res_list.append(f'{key}:{value}')
            return BaseStat.COLLECTION_ITEMS_TERMINATED.join(res_list)
        elif lupa.lua_type(val) == 'boolean':
            return 'true' if bool(val) else 'false'
        else:
            return str(val)

    # 需要保证msg里的值顺序和json_type的键顺序一致！需求变更的时候，需要同步修改
    # 值要保证数据类型能够正常转换，值有几种可能：int型，string型，bool型（'True'或'False'），空值是'None'
    @classmethod
    def trans_json(cls, msg, json_type):
        res_dict = dict()
        json_keys_list = json_keys.res[json_type]
        value_list = str(msg).split(BaseStat.FIELDS_TERMINATED)
        for i in range(0, len(json_keys_list)):
            json_key = json_keys_list[i]
            key = str(json_key).split(':')[0]
            val_type = str(json_key).split(':')[1]
            val = value_list[i]
            res_dict[key] = BaseStat.trans_val(val, val_type)
        return json.JSONEncoder().encode(res_dict).encode(BaseStat.CHA_ENCODING)

    @classmethod
    def trans_val(cls, val, val_type):
        v = str(val).strip()
        v_type = str(val_type)

        if 'int' in v_type:
            if 'None' in v:
                return 0
            return int(v)
        # 布尔值的处理，要求值为True或False的字符串
        elif 'bool' in v_type:
            if 'None' in v:
                return 'false'
            return 'true' if bool(v) else 'false'
        elif 'string' in v_type:
            if 'None' in v:
                return ''
            if 'True' in v or 'true' in v:
                return 'true'
            if 'False' in v or 'False' in v:
                return 'false'
            return v
        elif 'float' in v_type:
            if 'None' in v:
                return 0.00
            return float(v)
        else:
            return v

    @classmethod
    def get_info(cls, fixed_field_list, info_list, info_classify):
        fixed_field_list.extend(info_list)
        return BaseStat.trans_json(BaseStat.FIELDS_TERMINATED.join(str(i) for i in fixed_field_list), info_classify)

    @classmethod
    def merge_section(cls, original_list):
        tuple_list = list(original_list)
        tuple_list.sort(key=lambda k: k[0])
        min = 0;
        max = 0;
        result_dict = dict()
        dict_index = 0;
        for tuple in tuple_list:
            start = tuple[0]
            end = tuple[1]
            if start <= max:
                if end > max:
                    max = end
            else:
                min = start
                max = end
                dict_index += 1
            result_dict[dict_index] = (min, max)
        return list(result_dict.values())