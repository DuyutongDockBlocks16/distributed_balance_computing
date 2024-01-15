from kafka_producer import Kafka_Producer
from stats.summary_stat import SummaryStat


class CastSkillStat(SummaryStat):

    # 注意顺序！决定了统计表中的字段顺序
    stats_last_keys = ()
    stats_accum_keys = ()
    stats_groupby_count_keys = ('skillId')

    def __init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, castSkill_status):
        # 初始化对局基本信息
        SummaryStat.__init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, castSkill_status, 'castSkill',
                             'sourceCardPos')
        # 初始化kafka producer（单例）
        self.kafka_producer = Kafka_Producer()
        self.castSkill_status = castSkill_status
        self.card_key = self.generate_card_key()