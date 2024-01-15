import config


class Card():
  def __init__(self):
    self.properties = [
      'Damage',
      'Heal',
      'TakeDamage',
      'CastSkill',
      'EnergyRecovery',
      # 'AllFrameTable'
    ]
    self.frame_properties = {
      'TakeDamage': ["frame","sourceCardPos","targetCardPos","time","damage","damageType","damageStatus","isInterrupt","sourceActorType","targetActorType"],
      'EnergyRecovery': ["frame","sourceCardPos","energyRecoveryType","energyRecovery","skillId","targetCardPos","targetId","time","sourceActorType","targetActorType"],
      'Damage': ["frame","sourceCardPos","targetCardPos","time","damage","damageType","damageSource","damageStatus","buffReduce","damageId","isCrit","isHit","isKilled",
                 "linkReduce","shieldReduce","sourceId","targetId","sourceActorType","targetActorType"],
      'CastSkill': ["frame","sourceCardPos","targetCardPos","time","skillId","isBaseAttack","isManual","sourceActorType","targetActorType"],
      'Heal': ["frame","sourceCardPos","targetCardPos","time","heal","skillId","healType","sourceActorType","targetActorType"],
      'AllFrameTable': ["Frame", "AD", "ADMultiplier", "ADReduction", "AD_IMMUNE", "APMultiplier", "APReduction","AP_IMMUNE",
                        "AntiCrit", "AntiDamage", "Aspd", "Combat", "Crit", "CritDamage", "DamageAbsorbRate","DamageMultiplier",
                        "DamageReduction", "Def", "DefBreak", "Elements", "Flee", "HP", "HPRegeneration", "Hast","HealRate", "Hit",
                        "Insight", "LifeSteal", "MP", "MPReductionRate", "MPRegeneration", "MaxHP", "Mdef", "MdefBreak","PerfectDodge",
                        "S1Level", "S2Level", "SkillDamageEnhancement", "SkillDamageReduction", "SkinID", "Speed","TakeHealRate",
                        "TakeMPRate", "Toughness", "_display_script_name", "isCopyActor", "wuxing", "BuffEffects","Buffs",
                        "CardName:deprecated", "Direction", "FightActorId", "Pos1", "Pos2", "Side", "State", "ViperCount","ActorType", "Id", "Shield", "Pos"]
    }

# sql_address = 'mysql+pymysql://dev_ai_rwl:665B20AC3A8DA@192.168.250.80:4306/aidb?charset=utf8'

# # =================redis-aliyun=================
# redis_host = '10.119.113.149'
# redis_port = 6379

# # =================redis-local-test=================
# redis_host = '127.0.0.1'
# redis_port = 6379

# # =================昌平集群===================
# redis_host = '192.168.240.19'
# redis_port = 6379


# general
redis_host = config.CONFIG.redis_host
redis_port = config.CONFIG.redis_port
redis_db = config.CONFIG.redis_db

# task queue 的最大长度
# task_queue_max_length = 20

task_queue_max_length = 80000
# task queue 的最小长度，小于这个长度会delay task，每次delay 的 batch 数量 = max_length - min_length
# task_queue_min_length = 5
task_queue_min_length = 30000

# 检测task queue 长度的时间间隔，需要访问redis，查询llen，时间复杂度O(1)
task_queue_length_check_second = 1

FIELDS_TERMINATED = '\001'
COLLECTION_ITEMS_TERMINATED = '\002'
TAB_CHARACTER = '\t'
FILENAME_SPLITTER = ';'