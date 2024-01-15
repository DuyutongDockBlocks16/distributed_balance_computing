import lupa

from app_error import SDK_error
from kafka_producer import Kafka_Producer
from stats.base_stat import BaseStat
from stats.castSkill_stat import CastSkillStat
from stats.frame_stat import FrameStat
from stats.skillDamage_stat import SkillDamageStat
from stats.summary_stat import SummaryStat
import time
import stats.battle_data_classify as battle_data_classify

LIBS = "./Fight.lua"
f = open(LIBS)
code_str = '\n'.join(f.readlines())
f.close()


# v1.0.0版本采用数据预加工的方式（纯逻辑加工，而不是使用sql，目的在于执行效率高），
# 优点在于kafka生产的数据量少，后续存储资源占用少，数据后续加工步骤少，看到数据的速度快，
# 问题在于人工成本大，需求变更需要修改逻辑，通用性差，数仓规范性差

# 整个数据聚合逻辑的入口
# 对象以“局”为数据粒度



class BattleStat(BaseStat):

    def __init__(self, nm_version, proc_version, list_version, left_id, right_id, random_seed, log_time):

        # 初始化对局基本信息
        BaseStat.__init__(self, nm_version, proc_version, list_version, left_id, right_id, random_seed, log_time)
        # 初始化kafka producer（单例）
        self.kafka_producer = Kafka_Producer()
        # 生成对局数据
        self.lua_table = self.sdk_nm(left_id, right_id, random_seed)
        if self.lua_table == -1:
            raise SDK_error('sdk 内部可捕获异常！')
        # 生成对局结算信息
        self.result = self.lua_table['result']
        self.last_frame = self.lua_table['last_frame']
        self.last_time = self.lua_table['last_time']
        self.execute_time = self.lua_table['execute_time']
        self.isFightTimeOver = self.lua_table['isFightTimeOver']
        # 生成对局英雄集合
        self.generate_fightActor()

        # 战斗状态跳变点上下文
        self.battleStatus_jumppoint_context = dict()
        # 战斗状态统计上下文
        self.battleStatus_stats_context = dict()

        # ------- damage/takeDamage/Heal/EnergyRecovery统计逻辑和内存中的数据结构都是一样的
        # damage 跳变点上下文
        self.damageStatus_jumppoint_context = dict()
        # damage统计上下文
        self.damageStatus_stats_context = dict()
        # takeDamage 跳变点上下文
        self.takeDamageStatus_jumppoint_context = dict()
        # takeDamage统计上下文
        self.takeDamageStatus_stats_context = dict()
        # Heal 跳变点上下文
        self.healStatus_jumppoint_context = dict()
        # Heal统计上下文
        self.healStatus_stats_context = dict()
        # EnergyRecovery 跳变点上下文
        self.energyRecoveryStatus_jumppoint_context = dict()
        # EnergyRecovery统计上下文
        self.energyRecoveryStatus_stats_context = dict()
        # --------

        # castSkill统计上下文
        self.castSkillStatus_stats_context = dict()

        # 对局所有card_keys(Side_FightActorId)
        self.card_keys = set()

    def sdk_nm(self, a_index, b_index, random_seed):
        # lua 每一套阵容的战斗都要执行 lua 环境的初始化
        lua = lupa.LuaRuntime()
        g = lua.globals()
        lua.execute(code_str)
        print('indexa, indexb, random_seed', a_index, b_index, random_seed)
        lua_table = g.fight(a_index, b_index, random_seed)
        return lua_table

    # 数据聚合具体的入口
    def analyze(self, analyze_jp=False, analyze_stats=False):
        if self.lua_table == -1:
            raise SDK_error('sdk 内部可捕获异常！')
        if not analyze_jp and not analyze_stats:
            return
        # 分析战斗状态相关指标（数据来源frame_status表）
        self.analyze_battleStatus(analyze_jp, analyze_stats)
        # 分析战斗事件相关指标（数据来源Damage、Heal表等）
        self.analyze_battleSummary(analyze_jp, analyze_stats)
        if analyze_stats:
            # 加工战斗时长、有效战斗时长、无效战斗时长
            self.generate_fight_time()
            # 加工其他衍生指标
            self.generate_derivative_metric()
            # 发送所有统计指标
            self.send_all_stats_context()

    # 生成跳变点数据及时发送
    # 生成对局统计数据
    def analyze_battleStatus(self, analyze_jp, analyze_stats):
        for frame_status in self.lua_table['AllFrameTable'].values():
            # 生成对局的card_key集合
            self.card_keys.add(f'{frame_status["Side"]}_{frame_status["FightActorId"]}')
            frame_stat = FrameStat(self.nm_version, self.list_version, self.proc_version, self.left_id, self.right_id,
                                   self.random_seed, self.log_time, frame_status)
            # 召唤物不参与统计
            if frame_stat.FightActorId not in self.fightActor_dict.values():continue
            # 分析跳变点指标（变化帧粒度）
            # self.kafka_producer.send(topic=self.get_topic(battle_data_classify.FrameStatue), key=None,
            #                          value=self.get_frame_info(battle_data_classify.FrameStatue, frame_status, ('Frame', 'Side', 'FightActorId', 'HP',
            #                                                                                                     'MP', 'AD', 'MaxHP',
            #                                                                                                     'HPRegeneration',
            #                               'MPRegeneration', 'Hast', 'ADReduction',
            #                               'APReduction', 'TakeHealRate', 'Shield',
            #                               'Crit', 'Aspd', 'Buffs', 'BuffEffects', 'State')))
            # analyze_jp开关的原因：统计指标：有效战斗时长，依赖BuffEffects的跳变点结果
            frame_stat.analyze_jumppoint(self.battleStatus_jumppoint_context, self.battleStatus_stats_context,
                                         ('HP', 'MP', 'AD', 'MaxHP', 'HPRegeneration',
                                          'MPRegeneration', 'Hast', 'ADReduction',
                                          'APReduction', 'TakeHealRate', 'Shield',
                                          'Crit', 'Aspd', 'Buffs', 'BuffEffects'),
                                         analyze_jp)
            if not analyze_stats: continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.battleStatus_stats_context, frame_stat.card_key, frame_stat.frame_status, ('HP', 'Frame','State'), None,None,None,
                               ('MaxHP',))

    # 生成跳变点数据及时发送
    # 生成对局统计数据
    def analyze_battleSummary(self, analyze_jp, analyze_stats):
        # 处理Damage数据
        for damage_status in self.lua_table[battle_data_classify.Damage].values():

            damage_stat = SummaryStat(self.nm_version, self.list_version, self.proc_version, self.left_id, self.right_id,
                                   self.random_seed, self.log_time, damage_status, battle_data_classify.Damage, 'sourceCardPos')
            # 召唤物不参与统计
            if damage_stat.FightActorId not in self.fightActor_dict.values(): continue
            # 分析跳变点指标（变化帧粒度）
            if analyze_jp:
                self.kafka_producer.send(topic=self.get_topic(battle_data_classify.Damage), key=None,
                                         value=self.get_frame_info(battle_data_classify.Damage, damage_status, ('frame', 'damageId',
                                                                                   'sourceCardPos',
                                                                                   'targetCardPos', 'damage',
                                                                                   'isHit', 'isCrit', 'isKilled', 'targetActorType', 'sourceActorType')))
                damage_stat.analyze_jumppoint(self.damageStatus_jumppoint_context, ('damage',))
            if not analyze_stats: continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.damageStatus_stats_context, damage_stat.card_key, damage_stat.summary_status, ('damage',), {'damage':{'damage':'gt_0',
             'isHit':'eq_True'}})

            skill_damage_stat = SkillDamageStat(self.nm_version, self.list_version, self.proc_version, self.left_id, self.right_id, self.random_seed,
                                                self.log_time, damage_status)
            # 分析技能伤害统计指标（英雄粒度）
            self.analyze_stats(self.damageStatus_stats_context, skill_damage_stat.card_key,skill_damage_stat.damage_status, None, None,
                               {'skillId':{'damage':{'damage':'gt_0','isHit':'eq_True'}}}, {'skillId':{'1':{'damage':'gt_0','isHit':'eq_True'}}})


        # 处理TakeDamage数据
        for takeDamage_status in self.lua_table[battle_data_classify.TakeDamage].values():

            takeDamage_stat = SummaryStat(self.nm_version, self.list_version, self.proc_version, self.left_id,self.right_id,
                                      self.random_seed, self.log_time, takeDamage_status, battle_data_classify.TakeDamage, 'targetCardPos')
            # 召唤物不参与统计
            if takeDamage_stat.FightActorId not in self.fightActor_dict.values(): continue
            # 分析跳变点指标（变化帧粒度）
            if analyze_jp:
                self.kafka_producer.send(topic=self.get_topic(battle_data_classify.TakeDamage), key=None,
                                         value=self.get_frame_info(battle_data_classify.TakeDamage, takeDamage_status, ('frame',
                                                                                   'sourceCardPos','targetCardPos','damage',)))
                takeDamage_stat.analyze_jumppoint(self.takeDamageStatus_jumppoint_context, ('damage',))
            if not analyze_stats: continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.takeDamageStatus_stats_context, takeDamage_stat.card_key, takeDamage_stat.summary_status, ('damage',), {'damage':None})

        # 处理Heal数据
        for heal_status in self.lua_table[battle_data_classify.Heal].values():

            heal_stat = SummaryStat(self.nm_version, self.list_version, self.proc_version, self.left_id,self.right_id,
                                          self.random_seed, self.log_time, heal_status, 'Heal', 'sourceCardPos')
            # 召唤物不参与统计
            if heal_stat.FightActorId not in self.fightActor_dict.values(): continue
            # 分析跳变点指标（变化帧粒度）
            if analyze_jp:
                self.kafka_producer.send(topic=self.get_topic(battle_data_classify.Heal), key=None,
                                         value=self.get_frame_info(battle_data_classify.Heal, heal_status, ('frame', 'skillId',
                                                                                 'sourceCardPos', 'targetCardPos', 'heal',)))
                heal_stat.analyze_jumppoint(self.healStatus_jumppoint_context, ('heal',))
            if not analyze_stats: continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.healStatus_stats_context, heal_stat.card_key, heal_stat.summary_status, ('heal',), {'heal':None})

        # 处理EnergyRecovery数据
        for energyRecovery_status in self.lua_table[battle_data_classify.EnergyRecovery].values():

            energyRecovery_stat = SummaryStat(self.nm_version, self.list_version, self.proc_version, self.left_id,self.right_id,
                                    self.random_seed, self.log_time, energyRecovery_status, 'EnergyRecovery', 'targetCardPos')
            # 召唤物不参与统计
            if energyRecovery_stat.FightActorId not in self.fightActor_dict.values(): continue
            # 分析跳变点指标（变化帧粒度）
            if analyze_jp:
                self.kafka_producer.send(topic=self.get_topic(battle_data_classify.EnergyRecovery), key=None,
                                         value=self.get_frame_info(battle_data_classify.EnergyRecovery, energyRecovery_status, ('frame',
                                                                                           'sourceCardPos', 'targetCardPos', 'energyRecovery',
                                                                                           'energyRecoveryType',)))
                energyRecovery_stat.analyze_jumppoint(self.energyRecoveryStatus_jumppoint_context, ('energyRecovery',))
            if not analyze_stats: continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.energyRecoveryStatus_stats_context, energyRecovery_stat.card_key, energyRecovery_stat.summary_status,
                               ('energyRecovery',), {'energyRecovery':None})

        # 处理castSkill数据
        for castSkill_status in self.lua_table[battle_data_classify.CastSkill].values():
            if analyze_jp:
                self.kafka_producer.send(topic=self.get_topic(battle_data_classify.CastSkill), key=None,
                                     value=self.get_frame_info(battle_data_classify.CastSkill, castSkill_status, ('frame', 'skillId', 'sourceCardPos',
                                                                                                                 'targetCardPos')))
            if not analyze_stats: continue
            castSkill_stat = CastSkillStat(self.nm_version, self.list_version, self.proc_version, self.left_id,
                                              self.right_id,
                                              self.random_seed, self.log_time, castSkill_status)
            # 召唤物不参与统计
            if castSkill_stat.FightActorId not in self.fightActor_dict.values(): continue
            # 分析统计指标（英雄粒度）
            self.analyze_stats(self.castSkillStatus_stats_context, castSkill_stat.card_key, castSkill_stat.castSkill_status, None, None, None,
                               {'skillId':{'1':None}})

    # 生成有效战斗时长、无效战斗时长的逻辑（根据buffeffect的处理逻辑存储的内存中间结果得到）
    def generate_fight_time(self):
        for card_key in self.card_keys:
            if card_key not in self.battleStatus_stats_context:
                continue
            elif 'invalid_fight_section' not in self.battleStatus_stats_context[card_key]:
                self.battleStatus_stats_context[card_key]['invalid_fight_time'] = 0
                self.battleStatus_stats_context[card_key]['valid_fight_time'] = self.battleStatus_stats_context[card_key]['last_Frame']
            else:
                card_key_ufs = self.battleStatus_stats_context[card_key]['invalid_fight_section']
                invalid_fight_time = 0
                time_section_list = list()
                for time_sections in dict(card_key_ufs).values():
                    for time_section in str(time_sections).split(','):
                        if time_section.strip()=='': continue
                        start_frame = time_section.split(':')[0]
                        end_frame = self.battleStatus_stats_context[card_key]['last_Frame'];
                        if ':' in time_section:
                            end_frame = time_section.split(':')[1]
                        time_section_list.append((int(start_frame), int(end_frame)))
                # 对invalid_fight_section进行区间合并（先排序，再遍历合并）
                time_section_res_list = BaseStat.merge_section(time_section_list)
                for time_section_res in list(time_section_res_list):
                    invalid_fight_time += time_section_res[1]-time_section_res[0]
                self.battleStatus_stats_context[card_key]['invalid_fight_time'] = invalid_fight_time
                self.battleStatus_stats_context[card_key]['valid_fight_time'] = self.battleStatus_stats_context[card_key]['last_Frame']-invalid_fight_time

    # 生成衍生指标
    def generate_derivative_metric(self):
        for card_key in self.card_keys:
            # 结束时是否存活
            self.generate_last_is_dead(card_key)
            # 结束时剩余 HP 比率
            self.generate_last_HP_rate(card_key)
            # 每秒平均输出
            self.generate_summary_persec(card_key, 'damage', self.damageStatus_stats_context)
            # 有效每秒输出
            self.generate_valid_summary_persec(card_key, 'damage', self.damageStatus_stats_context)
            # 每秒平均承伤
            self.generate_summary_persec(card_key, 'damage', self.takeDamageStatus_stats_context)
            # 有效每秒承伤
            self.generate_valid_summary_persec(card_key, 'damage', self.takeDamageStatus_stats_context)
            # 每秒平均治疗
            self.generate_summary_persec(card_key, 'heal', self.healStatus_stats_context)
            # 有效每秒治疗
            self.generate_valid_summary_persec(card_key, 'heal', self.healStatus_stats_context)
            # 每秒平均回能
            self.generate_summary_persec(card_key, 'energyRecovery', self.energyRecoveryStatus_stats_context)
            # 有效每秒回能
            self.generate_valid_summary_persec(card_key, 'energyRecovery', self.energyRecoveryStatus_stats_context)
            # 技能单位时间伤害
            self.generate_skill_damage_persec(card_key)


    def generate_last_is_dead(self, card_key):
        if card_key not in self.battleStatus_stats_context:
            pass
        elif 'last_State' not in self.battleStatus_stats_context[card_key]:
            pass
        else:
            if str(self.battleStatus_stats_context[card_key]['last_State']) == '4':
                self.battleStatus_stats_context[card_key]['last_is_dead'] = True
            else:
                self.battleStatus_stats_context[card_key]['last_is_dead'] = False

    def generate_last_HP_rate(self, card_key):
        if card_key not in self.battleStatus_stats_context:
            pass
        elif 'last_HP' not in self.battleStatus_stats_context[card_key] or 'max_MaxHP' not in self.battleStatus_stats_context[card_key]:
            pass
        else:
            last_HP = self.battleStatus_stats_context[card_key]['last_HP']
            max_MaxHP = self.battleStatus_stats_context[card_key]['max_MaxHP']
            self.battleStatus_stats_context[card_key]['last_HP_rate'] = format(last_HP/max_MaxHP, ".2f")

    def generate_summary_persec(self, card_key, summary_type, summaryStatus_stats_context):
        if card_key not in summaryStatus_stats_context:
            pass
        elif f'accum_{summary_type}' not in summaryStatus_stats_context[card_key]:
            pass
        else:
            accum_summary = int(summaryStatus_stats_context[card_key][f'accum_{summary_type}'])
            last_second = int(self.battleStatus_stats_context[card_key]['last_Frame'])//30
            summaryStatus_stats_context[card_key][f'{summary_type}_persec'] = format(accum_summary/last_second, '.2f')

    def generate_valid_summary_persec(self, card_key, summary_type, summaryStatus_stats_context):
        if card_key not in summaryStatus_stats_context:
            pass
        elif f'accum_{summary_type}' not in summaryStatus_stats_context[card_key]:
            pass
        else:
            accum_summary = int(summaryStatus_stats_context[card_key][f'accum_{summary_type}'])
            last_valid_second = int(self.battleStatus_stats_context[card_key]['valid_fight_time']) // 30
            summaryStatus_stats_context[card_key][f'valid_{summary_type}_persec'] = format(accum_summary / last_valid_second,'.2f')

    def generate_skill_damage_persec(self, card_key):
        if card_key not in self.damageStatus_stats_context:
            pass
        elif 'groupby_skillId_accum_damage' not in self.damageStatus_stats_context[card_key]:
            pass
        else:
            groupby_accum_skillId = dict(self.damageStatus_stats_context[card_key]['groupby_skillId_accum_damage'])
            self.damageStatus_stats_context[card_key]['groupby_skillId_skill_damage_persec']=dict()
            for skillId in groupby_accum_skillId.keys():
                accum_skill_damage = groupby_accum_skillId[skillId]
                last_second = int(self.battleStatus_stats_context[card_key]['last_Frame']) // 30
                self.damageStatus_stats_context[card_key]['groupby_skillId_skill_damage_persec'][skillId] = format(accum_skill_damage / last_second, '.2f')

    def send_all_stats_context(self):
        # battle 粒度
        self.kafka_producer.send(topic=self.get_topic_battle(), key=None, value=self.get_battle_info())
        # battle hero 粒度
        for card_key in self.fightActor_valid_dict.values():
            self.kafka_producer.send(topic=self.get_topic_battle_hero(), key=None, value=self.get_battle_hero_info(card_key))

    def generate_fightActor(self):
        actor_dict = dict()
        actor_valid_dict = dict()
        for i in range(1,11):
            pos = str(i)
            side = 1 if i <6 else -1
            actor_id = self.get_actor_id(i)
            actor_dict[pos] = actor_id
            if actor_id!=None: actor_valid_dict[pos] = f'{side}_{actor_id}'
        # key范围为（1,10）,value为fightActorId
        self.fightActor_dict = actor_dict
        self.fightActor_valid_dict = actor_valid_dict

    def get_battle_info(self):
        res_list = self.get_row_key_and_fixed_field(self.get_battle_row_key())
        battle_info = [self.result, self.last_frame, self.last_time, self.execute_time, self.frame_val_transform(self.isFightTimeOver), self.fightActor_dict['1'],
                       self.fightActor_dict['2'],
                    self.fightActor_dict['3'], self.fightActor_dict['4'],self.fightActor_dict['5'],self.fightActor_dict['6'],self.fightActor_dict['7'],
                    self.fightActor_dict['8'], self.fightActor_dict['9'], self.fightActor_dict['10']]
        return BaseStat.get_info(res_list, battle_info, battle_data_classify.Battle)

    def get_battle_hero_info(self, card_key):
        # 加工所属技能指标
        if card_key in self.castSkillStatus_stats_context and 'groupby_skillId_count' in self.castSkillStatus_stats_context[card_key]:
            for skillId in dict(self.castSkillStatus_stats_context[card_key]['groupby_skillId_count']).keys():
                self.castSkillStatus_stats_context[card_key][f'skillId_{skillId[-2:]}_count'] = self.castSkillStatus_stats_context[card_key][
                    'groupby_skillId_count'][skillId]
        if card_key in self.damageStatus_stats_context and 'groupby_skillId_count' in self.damageStatus_stats_context[card_key]:
            for skillId in dict(self.damageStatus_stats_context[card_key]['groupby_skillId_count']).keys():
                self.damageStatus_stats_context[card_key][f'skillId_{skillId[-2:]}_count'] = self.damageStatus_stats_context[card_key][
                    'groupby_skillId_count'][skillId]
        if card_key in self.damageStatus_stats_context and 'groupby_skillId_accum_damage' in self.damageStatus_stats_context[card_key]:
            for skillId in dict(self.damageStatus_stats_context[card_key]['groupby_skillId_accum_damage']).keys():
                self.damageStatus_stats_context[card_key][f'skillId_{skillId[-2:]}_accum_damage'] = self.damageStatus_stats_context[card_key][
                    'groupby_skillId_accum_damage'][skillId]
        if card_key in self.damageStatus_stats_context and 'groupby_skillId_skill_damage_persec' in self.damageStatus_stats_context[card_key]:
            for skillId in dict(self.damageStatus_stats_context[card_key]['groupby_skillId_skill_damage_persec']).keys():
                self.damageStatus_stats_context[card_key][f'skillId_{skillId[-2:]}_skill_damage_persec'] = self.damageStatus_stats_context[card_key][
                    'groupby_skillId_skill_damage_persec'][skillId]
        # 技能统计（涉及两个内存结构：castSkillStatus_stats_context 和 damageStatus_stats_context）
        skill_stats = list()
        for i in range(0,11):
            skill_type = str(i)
            if i < 9: skill_type = f'0{i}'
            if card_key in self.castSkillStatus_stats_context:
                skill_stats.append(self.castSkillStatus_stats_context[card_key][f'skillId_{skill_type}_count'] if f'skillId_{skill_type}_count' in \
                                                                                                                  self.castSkillStatus_stats_context[card_key] else None)  # 1技能发动次数
            else:
                skill_stats.append(None)
            if card_key in self.damageStatus_stats_context:
                skill_stats.append(self.damageStatus_stats_context[card_key][f'skillId_{skill_type}_accum_damage'] if f'skillId_{skill_type}_accum_damage' in \
                                                                                                                      self.damageStatus_stats_context[card_key] else None) # 1技能造成总伤害
                skill_stats.append(self.damageStatus_stats_context[card_key][f'skillId_{skill_type}_count'] if f'skillId_{skill_type}_count' in
                                                                                                               self.damageStatus_stats_context[card_key] else None)  # 1技能造成伤害次数
                skill_stats.append(self.damageStatus_stats_context[card_key][f'skillId_{skill_type}_skill_damage_persec']
                                   if f'skillId_{skill_type}_skill_damage_persec' in self.damageStatus_stats_context[card_key] else None) # 1技能单位时间伤害
            else:
                skill_stats.append(None)
                skill_stats.append(None)
                skill_stats.append(None)
        res_list = self.get_row_key_and_fixed_field(self.get_battle_row_key())
        # 最终的统计数据（与输出的excel表一一对应）
        battleHero_info = [
            # 英雄
            str(card_key).split('_')[0],  # side
            str(card_key).split('_')[1],  # actor_id
            # ---- 胜负表现
            self.battleStatus_stats_context[card_key]['last_is_dead'] if card_key in self.battleStatus_stats_context and 'last_is_dead' in
                                                                         self.battleStatus_stats_context[card_key] else None, # 结束时是否存活
            self.battleStatus_stats_context[card_key]['max_MaxHP'] if card_key in self.battleStatus_stats_context and 'max_MaxHP' in
                                                                      self.battleStatus_stats_context[card_key] else None, # 本场最大MaxHP
            self.battleStatus_stats_context[card_key]['last_HP'] if card_key in self.battleStatus_stats_context and 'last_HP' in
                                                                    self.battleStatus_stats_context[card_key] else None,  # 结束时剩余HP
            self.battleStatus_stats_context[card_key]['last_HP_rate'] if card_key in self.battleStatus_stats_context and 'last_HP_rate' in
                                                                         self.battleStatus_stats_context[card_key] else None,  # 结束时剩余HP比率
            # ---- 战斗表现
            self.battleStatus_stats_context[card_key]['last_Frame'] if card_key in self.battleStatus_stats_context and 'last_Frame' in
                                                                       self.battleStatus_stats_context[card_key] else None,  # 战斗时长
            self.battleStatus_stats_context[card_key]['valid_fight_time'] if card_key in self.battleStatus_stats_context and 'valid_fight_time' in
                                                                             self.battleStatus_stats_context[card_key] else None,  # 有效战斗时长
            self.battleStatus_stats_context[card_key]['invalid_fight_time'] if card_key in self.battleStatus_stats_context and 'invalid_fight_time' in
                                                                               self.battleStatus_stats_context[card_key] else None,  # 无效战斗时长
            self.damageStatus_stats_context[card_key]['accum_damage'] if card_key in self.damageStatus_stats_context and 'accum_damage' in
                                                                         self.damageStatus_stats_context[card_key] else None,  # 总输出
            self.damageStatus_stats_context[card_key]['damage_persec'] if card_key in self.damageStatus_stats_context and 'damage_persec' in
                                                                          self.damageStatus_stats_context[card_key] else None,  # 每秒平均输出
            self.damageStatus_stats_context[card_key]['valid_damage_persec'] if card_key in self.damageStatus_stats_context and 'valid_damage_persec' in
                                                                                self.damageStatus_stats_context[card_key] else None,  # 有效每秒输出
            self.takeDamageStatus_stats_context[card_key]['accum_damage'] if card_key in self.takeDamageStatus_stats_context and 'accum_damage' in
                                                                             self.takeDamageStatus_stats_context[card_key] else None,  # 总承伤
            self.takeDamageStatus_stats_context[card_key]['damage_persec'] if card_key in self.takeDamageStatus_stats_context and 'damage_persec' in
                                                                              self.takeDamageStatus_stats_context[card_key] else None,  # 每秒平均承伤
            self.takeDamageStatus_stats_context[card_key]['valid_damage_persec'] if card_key in self.takeDamageStatus_stats_context and 'valid_damage_persec' in
                                                                                    self.takeDamageStatus_stats_context[card_key] else None,  # 有效每秒承伤
            self.healStatus_stats_context[card_key]['accum_heal'] if card_key in self.healStatus_stats_context and 'accum_heal' in
                                                                     self.healStatus_stats_context[card_key] else None,  # 总治疗
            self.healStatus_stats_context[card_key]['heal_persec'] if card_key in self.healStatus_stats_context and 'heal_persec' in
                                                                      self.healStatus_stats_context[card_key] else None,  # 每秒平均治疗
            self.healStatus_stats_context[card_key]['valid_heal_persec'] if card_key in self.healStatus_stats_context and 'valid_heal_persec' in
                                                                            self.healStatus_stats_context[card_key] else None,  # 有效每秒治疗
            self.energyRecoveryStatus_stats_context[card_key]['accum_energyRecovery'] if card_key in self.energyRecoveryStatus_stats_context and 'accum_energyRecovery' in
                                                                                         self.energyRecoveryStatus_stats_context[card_key] else None,  # 总回能
            self.energyRecoveryStatus_stats_context[card_key]['energyRecovery_persec'] if card_key in self.energyRecoveryStatus_stats_context and 'energyRecovery_persec' in
                                                                                          self.energyRecoveryStatus_stats_context[card_key] else None,  # 每秒平均回能
            self.energyRecoveryStatus_stats_context[card_key]['valid_energyRecovery_persec'] if card_key in self.energyRecoveryStatus_stats_context and 'valid_energyRecovery_persec' in
                                                                                                self.energyRecoveryStatus_stats_context[card_key] else None,  # 有效每秒回能
        ]
        battleHero_info.extend(skill_stats)
        return BaseStat.get_info(res_list, battleHero_info, battle_data_classify.BattleHero)

    def get_frame_info(self, summary_classify, summary_status, param):
        res_info = list()
        for key in list(param):
            if key in summary_status:
                res_info.append(BaseStat.frame_val_transform(summary_status[key]))
            else:
                res_info.append(None)
        res_list = self.get_row_key_and_fixed_field(self.get_battle_row_key())
        return BaseStat.get_info(res_list, res_info, summary_classify)