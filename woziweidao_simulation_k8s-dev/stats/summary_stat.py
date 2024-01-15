from kafka_producer import Kafka_Producer
from stats.base_stat import BaseStat
import lupa




# 所有事件类的统计（事件触发帧）
class SummaryStat(BaseStat):


    # summary_status 事件类帧数据
    # summary_classify 事件类型
    # summary_card_pos_key 聚合主体的key，例如sourceCardPos、targetCardPos
    def __init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, summary_status, summary_classify, summary_card_pos_key):
        # 初始化对局基本信息
        BaseStat.__init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time)
        # 初始化kafka producer（单例）
        self.kafka_producer = Kafka_Producer()
        self.summary_status = summary_status
        self.card_pos = self.summary_status[summary_card_pos_key]
        self.frame = self.summary_status['frame']
        self.card_key = self.generate_card_key()
        # 统计类型（damage，takeDamage等）
        self.summary_classify = summary_classify

    def analyze_jumppoint(self, summaryStatus_jumppoint_context, jumppoint_keys):
        jp_res = dict()
        # 分析每一个jumppoint字段
        for jumppoint_key in jumppoint_keys:
            jumppoint_val = self.summary_status[jumppoint_key]
            # 不存在跳变点
            if jumppoint_val == None or str(jumppoint_val).strip()=='' or str(jumppoint_val)=='0':
                continue
            # 如果第一次进入，创建card_key和jumppoint_key结构
            if self.card_key not in summaryStatus_jumppoint_context:
                summaryStatus_jumppoint_context[self.card_key] = dict()
            if jumppoint_key not in summaryStatus_jumppoint_context[self.card_key]:
                summaryStatus_jumppoint_context[self.card_key][jumppoint_key] = jumppoint_val
            # 非第一次进入，更新当前帧累加伤害
            else:
                summaryStatus_jumppoint_context[self.card_key][jumppoint_key] = summaryStatus_jumppoint_context[self.card_key][jumppoint_key]+jumppoint_val
            jp_res[jumppoint_key] = summaryStatus_jumppoint_context[self.card_key][jumppoint_key]
        # 发送跳变点数据
        if len(jp_res)!=0:
            pass
            self.kafka_producer.send(topic=self.get_topic_battle_hero_summary_jp(self.summary_classify), key=None,
                                     value=self.get_jp_info(jp_res, jumppoint_keys))
        # TODO 结束时应该再发一条带总条数的数据，因为跳变点的数据是没发提前知道总条数的，所以发这一条数据，可以在kudu里知道这场对局的跳变点数据是否加工完成

    def generate_card_key(self):
        battle_formation = self.left_id
        side = 1
        card_pos = int(self.card_pos)
        if (card_pos > 5):
            side = -1
            battle_formation = self.right_id
            card_pos = card_pos-5
        actor_id = f'100000{battle_formation[(card_pos-1)*2:(card_pos-1)*2+2]}'
        self.Side = side
        self.FightActorId = int(actor_id)
        return f'{side}_{actor_id}'


    def get_jp_info(self, jp_res, jumppoint_keys):
        jp_info = list()
        for jp_key in jumppoint_keys:
            if jp_key in jp_res.keys(): jp_info.append(jp_res[jp_key])
            else: jp_info.append(None)
        res_list = self.get_row_key_and_fixed_field(self.get_battle_row_key())
        res_list2 = [self.frame, self.Side, self.FightActorId]
        res_list2.extend(jp_info)
        return BaseStat.get_info(res_list, res_list2, f'{self.summary_classify}_JP')
