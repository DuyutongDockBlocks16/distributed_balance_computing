from kafka_producer import Kafka_Producer
from stats.base_stat import BaseStat
import stats.battle_data_classify as battle_data_classify




# 所有状态类的数据统计（全量帧）
# 对象以帧为数据粒度
class FrameStat(BaseStat):

    unable_fight_effectId = ('4', '6')

    def __init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, frame_status):
        # 初始化对局基本信息
        BaseStat.__init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time)
        # 初始化kafka producer（单例）
        self.kafka_producer = Kafka_Producer()
        self.frame_status = frame_status
        self.Frame = self.frame_status['Frame']
        self.Side = self.frame_status['Side']
        self.FightActorId = self.frame_status['FightActorId']
        self.card_key = f'{self.Side}_{self.FightActorId}'


    # 所有非跳变点字段默认值都是None
    def analyze_jumppoint(self, battleStatus_jumppoint_context, battleStatus_stats_context, jumppoint_keys, analyze_jp):
        jp_keys = jumppoint_keys
        if not analyze_jp:
            jp_keys=('BuffEffects',)
        # 当前帧的跳变点字段的值，只有发生跳变的字段才会记录
        jp_res = dict()
        cur_battleStatus_jumppoint_info = dict()
        # 分析每一个跳变点字段（存在必要的性能消耗）
        for jp_key in jp_keys:
            # 取当前这一帧的 key 所对应的数据（根据数据格式做相应的转换）
            jp_cur_val = self.frame_val_transform(self.frame_status[jp_key])
            # 将当前值存起来（无论是否有跳变点都将当前值存起来，如果存在跳变点则更新context）
            cur_battleStatus_jumppoint_info[jp_key] = jp_cur_val
            jp_pre_val = None
            # 尝试取jp_pre_val的值（没有则为None）
            if self.card_key in battleStatus_jumppoint_context:
                jp_pre_val = battleStatus_jumppoint_context[self.card_key][jp_key]
            # 如果是第一次，所有字段都需要作为结果发送
            if jp_pre_val == None:
                jp_res[jp_key] = jp_cur_val
            # 如果不是第一次，并且本次跟上次的值不同，说明出现了跳变点，用res记录本帧的跳变点的key和value
            elif jp_pre_val != jp_cur_val:
                # BuffEffects跳变点特殊处理
                # 原始的BuffEffects数据格式为：2300001:1,550002:1
                if jp_key == 'BuffEffects':
                    # 当前帧的buffeffect的状态id的集合
                    cur_effectId_set=set()
                    if jp_cur_val.strip()!='':
                        cur_effectId_set = set(
                            effect_key.split(':')[0] for effect_key in jp_cur_val.split(BaseStat.COLLECTION_ITEMS_TERMINATED))
                    # 上一帧的buffeffect的状态id的集合
                    pre_effectId_set=set()
                    if str(jp_pre_val).strip()!='':
                        pre_effectId_set = set(
                            effect_key.split(':')[0] for effect_key in jp_pre_val.split(BaseStat.COLLECTION_ITEMS_TERMINATED))
                    # 当前帧的集合差集上一帧的集合，能够差集出属于当前帧但不属于上一帧的状态id，也就是这个状态生成了
                    appr_effectId_set = cur_effectId_set.difference(pre_effectId_set)
                    # 上一帧的集合差集当前帧的集合，能够差集出属于上一帧但不属于当前帧的状态id，也就是这个状态消失了
                    disappr_effectId_set = pre_effectId_set.difference(cur_effectId_set)
                    # 如果存在跳变点
                    if len(appr_effectId_set)!=0 or len(disappr_effectId_set)!=0:
                        effect_res = self.generate_effect_res(appr_effectId_set, disappr_effectId_set, battleStatus_stats_context)
                        jp_res[jp_key] = effect_res
                # 如果不是BuffEffects，则存在跳变点，直接赋值
                else:
                    jp_res[jp_key] = jp_cur_val
            else:
                pass

        if len(jp_res) != 0:
            if analyze_jp: self.kafka_producer.send(topic=self.get_topic_battle_hero_status_jp(), key=None, value=self.get_jp_info(jp_res, jp_keys))
            # 更新context里的最新值
            battleStatus_jumppoint_context[self.card_key] = cur_battleStatus_jumppoint_info
        # TODO 结束时应该再发一条带总条数的数据，因为跳变点的数据是没发提前知道总条数的，所以发这一条数据，可以在kudu里知道这场对局的跳变点数据是否加工完成

    # 1.生成buff_effect的结果，格式：A:1,B:0，代表A状态生成，B状态消失
    # 2.记录每个card、每个无法战斗的effect_id的帧区间
    def generate_effect_res(self, appr_effectId_set, disappr_effectId_set, battleStatus_stats_context):
        res = list()
        for appr_effectId in appr_effectId_set:
            res.append(f'{appr_effectId}:1')
            if appr_effectId in FrameStat.unable_fight_effectId:
                if self.card_key not in battleStatus_stats_context:
                    battleStatus_stats_context[self.card_key] = {'invalid_fight_section': {appr_effectId: str(self.Frame)}}
                elif 'invalid_fight_section' not in battleStatus_stats_context[self.card_key]:
                    battleStatus_stats_context[self.card_key]['invalid_fight_section'] = {appr_effectId: str(self.Frame)}
                elif appr_effectId not in battleStatus_stats_context[self.card_key]['invalid_fight_section']:
                    battleStatus_stats_context[self.card_key]['invalid_fight_section'][appr_effectId] = str(self.Frame)
                else:
                    battleStatus_stats_context[self.card_key]['invalid_fight_section'][appr_effectId] = \
                    battleStatus_stats_context[self.card_key]['invalid_fight_section'][appr_effectId] + str(self.Frame)
        for disappr_effectId in disappr_effectId_set:
            res.append(f'{disappr_effectId}:0')
            if disappr_effectId in FrameStat.unable_fight_effectId:
                battleStatus_stats_context[self.card_key]['invalid_fight_section'][disappr_effectId] = \
                    battleStatus_stats_context[self.card_key]['invalid_fight_section'][disappr_effectId] + ':' + str(self.Frame) + ','
        return BaseStat.COLLECTION_ITEMS_TERMINATED.join(res)

    def get_jp_info(self, jp_res, jumppoint_keys):
        jp_info = list()
        for jp_key in jumppoint_keys:
            if jp_key in jp_res.keys(): jp_info.append(jp_res[jp_key])
            else: jp_info.append(None)
        res_list = self.get_row_key_and_fixed_field(self.get_battle_row_key())
        res_list2 = [self.Frame, self.Side, self.FightActorId]
        res_list.extend(res_list2)
        res_list.extend(jp_info)
        return BaseStat.trans_json(BaseStat.FIELDS_TERMINATED.join(str(i) for i in res_list), f'{battle_data_classify.FrameStatue}_JP')