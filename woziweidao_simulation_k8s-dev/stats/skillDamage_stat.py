from stats.damageId_skillId_mapper import damageId_skillId_mapper_dict
from kafka_producer import Kafka_Producer
from stats.summary_stat import SummaryStat


class SkillDamageStat(SummaryStat):

    # 注意顺序！决定了统计表中的字段顺序
    stats_groupby_accum_keys = {'damageId':('damage')}
    stats_groupby_count_keys = ('damageId')

    def __init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, damage_status):
        # 初始化对局基本信息
        SummaryStat.__init__(self, nm_version, list_version, proc_version, left_id, right_id, random_seed, log_time, damage_status, 'skill_damage', \
                                                                                                               'sourceCardPos')
        # 初始化kafka producer（单例）
        self.kafka_producer = Kafka_Producer()
        self.damageId = damage_status['damageId']
        damage_status['skillId'] = damageId_skillId_mapper_dict[str(self.damageId)]['skillId']
        self.damage_status = damage_status
        self.card_key = self.generate_card_key()