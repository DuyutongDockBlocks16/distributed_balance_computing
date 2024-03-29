create external table if not exists wzwd.wzwd_ods_game_BattleHero_d_tmp (data string)
partitioned by (proc_version string, year string, month string, day string)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '|'  ESCAPED BY '\\'
STORED AS TEXTFILE location '/staging/wzwd/nm/k8s/BattleHero';

create table if not exists wzwd.wzwd_ods_game_BattleHero_d (
    battle_gra_id            STRING COMMENT 'row_key',
    nm_version            STRING COMMENT '一次模拟的版本号。分区字段（冗余）',
    list_version            STRING COMMENT 'list文件推断的版本',
    logtime            STRING COMMENT '模拟时间',
    side                INT COMMENT '阵营（1为左边，-1为右边）',
    fightActor_id             STRING COMMENT '卡牌id（不包含召唤物）',
    last_is_dead             STRING COMMENT '结束时是否存活',

    max_MaxHP             STRING COMMENT '本场最大MaxHP',
    last_HP             STRING COMMENT '结束时剩余HP',
    last_HP_rate             STRING COMMENT '结束时剩余HP比率',
    last_frame             INT COMMENT '结束时帧号',
    valid_fight_time             INT COMMENT '有效战斗时长',
    invalid_fight_time             INT COMMENT '无效战斗时长',
    accum_damage             STRING COMMENT '总输出',
    damage_persec             STRING COMMENT '每秒平均输出',
    valid_damage_persec             STRING COMMENT '有效每秒输出',
    accum_takeDamage             STRING COMMENT '总承伤',
    takeDamage_persec             STRING COMMENT '每秒平均承伤',
    valid_takeDamage_persec             STRING COMMENT '有效每秒承伤',
    accum_heal             STRING COMMENT '总治疗',
    heal_persec             STRING COMMENT '每秒平均治疗',
    valid_heal_persec             STRING COMMENT '有效每秒治疗',
    accum_energyRecovery             STRING COMMENT '总回能',
    energyRecovery_persec             STRING COMMENT '每秒平均回能',
    valid_energyRecovery_persec             STRING COMMENT '有效每秒回能',
    skill0_cast_count             INT COMMENT '0技能发动次数',
    skill0_accum_damage             STRING COMMENT '0技能造成总伤害',
    skill0_damage_cast_coount             INT COMMENT '0技能造成伤害次数',
    skill0_damage_persec             STRING COMMENT '0技能单位时间伤害',
    skill1_cast_count             INT COMMENT '1技能发动次数',
    skill1_accum_damage             STRING COMMENT '1技能造成总伤害',
    skill1_damage_cast_coount             INT COMMENT '1技能造成伤害次数',
    skill1_damage_persec             STRING COMMENT '1技能单位时间伤害',
    skill2_cast_count             INT COMMENT '2技能发动次数',
    skill2_accum_damage             STRING COMMENT '2技能造成总伤害',
    skill2_damage_cast_coount             INT COMMENT '2技能造成伤害次数',
    skill2_damage_persec             STRING COMMENT '2技能单位时间伤害',
    skill3_cast_count             INT COMMENT '3技能发动次数',
    skill3_accum_damage             STRING COMMENT '3技能造成总伤害',
    skill3_damage_cast_coount             INT COMMENT '3技能造成伤害次数',
    skill3_damage_persec             STRING COMMENT '3技能单位时间伤害',
    skill4_cast_count             INT COMMENT '4技能发动次数',
    skill4_accum_damage             STRING COMMENT '4技能造成总伤害',
    skill4_damage_cast_coount             INT COMMENT '4技能造成伤害次数',
    skill4_damage_persec             STRING COMMENT '4技能单位时间伤害',
    skill5_cast_count             INT COMMENT '5技能发动次数',
    skill5_accum_damage             STRING COMMENT '5技能造成总伤害',
    skill5_damage_cast_coount             INT COMMENT '5技能造成伤害次数',
    skill5_damage_persec             STRING COMMENT '5技能单位时间伤害',
    skill6_cast_count             INT COMMENT '6技能发动次数',
    skill6_accum_damage             STRING COMMENT '6技能造成总伤害',
    skill6_damage_cast_coount             INT COMMENT '6技能造成伤害次数',
    skill6_damage_persec             STRING COMMENT '6技能单位时间伤害',
    skill7_cast_count             INT COMMENT '7技能发动次数',
    skill7_accum_damage             STRING COMMENT '7技能造成总伤害',
    skill7_damage_cast_coount             INT COMMENT '7技能造成伤害次数',
    skill7_damage_persec             STRING COMMENT '7技能单位时间伤害',
    skill8_cast_count             INT COMMENT '8技能发动次数',
    skill8_accum_damage             STRING COMMENT '8技能造成总伤害',
    skill8_damage_cast_coount             INT COMMENT '8技能造成伤害次数',
    skill8_damage_persec             STRING COMMENT '8技能单位时间伤害',
    skill9_cast_count             INT COMMENT '9技能发动次数',
    skill9_accum_damage             STRING COMMENT '9技能造成总伤害',
    skill9_damage_cast_coount             INT COMMENT '9技能造成伤害次数',
    skill9_damage_persec             STRING COMMENT '9技能单位时间伤害',
    skill10_cast_count             INT COMMENT '10技能发动次数',
    skill10_accum_damage             STRING COMMENT '10技能造成总伤害',
    skill10_damage_cast_coount             INT COMMENT '10技能造成伤害次数',
    skill10_damage_persec             STRING COMMENT '10技能单位时间伤害'
)
    COMMENT '对局英雄统计日志'
    PARTITIONED BY (proc_version STRING, year string, month string, day string)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE;

ALTER TABLE wzwd.wzwd_ods_game_BattleHero_d_tmp add if not exists PARTITION(proc_version='${proc_version}', year='${year}', month='${month}', day='${day}')
    LOCATION '/staging/wzwd/nm/k8s/BattleHero/${proc_version}/${year}/${month}/${day}';


insert overwrite table wzwd.wzwd_ods_game_BattleHero_d PARTITION(proc_version='${proc_version}', year='${year}', month='${month}', day='${day}') select
    get_json_object(data,'$.battle_gra_id'),
    get_json_object(data,'$.nm_version'),
    get_json_object(data,'$.list_version'),
    get_json_object(data,'$.logtime'),
    cast(get_json_object(data,'$.side') as int),
    get_json_object(data,'$.fightActor_id'),
    get_json_object(data,'$.last_is_dead'),
    get_json_object(data,'$.max_MaxHP'),
    get_json_object(data,'$.last_HP'),
    get_json_object(data,'$.last_HP_rate'),
    cast(get_json_object(data,'$.last_frame') as int),
    cast(get_json_object(data,'$.valid_fight_time') as int),
    cast(get_json_object(data,'$.invalid_fight_time') as int),
    get_json_object(data,'$.accum_damage'),
    get_json_object(data,'$.damage_persec'),
    get_json_object(data,'$.valid_damage_persec'),
    get_json_object(data,'$.accum_takeDamage'),
    get_json_object(data,'$.takeDamage_persec'),
    get_json_object(data,'$.valid_takeDamage_persec'),
    get_json_object(data,'$.accum_heal'),
    get_json_object(data,'$.heal_persec'),
    get_json_object(data,'$.valid_heal_persec'),
    get_json_object(data,'$.accum_energyRecovery'),
    get_json_object(data,'$.energyRecovery_persec'),
    get_json_object(data,'$.valid_energyRecovery_persec'),
    cast(get_json_object(data,'$.skill0_cast_count') as int),
    get_json_object(data,'$.skill0_accum_damage'),
    cast(get_json_object(data,'$.skill0_damage_cast_coount') as int),
    get_json_object(data,'$.skill0_damage_persec'),
    cast(get_json_object(data,'$.skill1_cast_count') as int),
    get_json_object(data,'$.skill1_accum_damage'),
    cast(get_json_object(data,'$.skill1_damage_cast_coount') as int),
    get_json_object(data,'$.skill1_damage_persec'),
    cast(get_json_object(data,'$.skill2_cast_count') as int),
    get_json_object(data,'$.skill2_accum_damage'),
    cast(get_json_object(data,'$.skill2_damage_cast_coount') as int),
    get_json_object(data,'$.skill2_damage_persec'),
    cast(get_json_object(data,'$.skill3_cast_count') as int),
    get_json_object(data,'$.skill3_accum_damage'),
    cast(get_json_object(data,'$.skill3_damage_cast_coount') as int),
    get_json_object(data,'$.skill3_damage_persec'),
    cast(get_json_object(data,'$.skill4_cast_count') as int),
    get_json_object(data,'$.skill4_accum_damage'),
    cast(get_json_object(data,'$.skill4_damage_cast_coount') as int),
    get_json_object(data,'$.skill4_damage_persec'),
    cast(get_json_object(data,'$.skill5_cast_count') as int),
    get_json_object(data,'$.skill5_accum_damage'),
    cast(get_json_object(data,'$.skill5_damage_cast_coount') as int),
    get_json_object(data,'$.skill5_damage_persec'),
    cast(get_json_object(data,'$.skill6_cast_count') as int),
    get_json_object(data,'$.skill6_accum_damage'),
    cast(get_json_object(data,'$.skill6_damage_cast_coount') as int),
    get_json_object(data,'$.skill6_damage_persec'),
    cast(get_json_object(data,'$.skill7_cast_count') as int),
    get_json_object(data,'$.skill7_accum_damage'),
    cast(get_json_object(data,'$.skill7_damage_cast_coount') as int),
    get_json_object(data,'$.skill7_damage_persec'),
    cast(get_json_object(data,'$.skill8_cast_count') as int),
    get_json_object(data,'$.skill8_accum_damage'),
    cast(get_json_object(data,'$.skill8_damage_cast_coount') as int),
    get_json_object(data,'$.skill8_damage_persec'),
    cast(get_json_object(data,'$.skill9_cast_count') as int),
    get_json_object(data,'$.skill9_accum_damage'),
    cast(get_json_object(data,'$.skill9_damage_cast_coount') as int),
    get_json_object(data,'$.skill9_damage_persec'),
    cast(get_json_object(data,'$.skill10_cast_count') as int),
    get_json_object(data,'$.skill10_accum_damage'),
    cast(get_json_object(data,'$.skill10_damage_cast_coount') as int),
    get_json_object(data,'$.skill10_damage_persec')
from wzwd.wzwd_ods_game_BattleHero_d_tmp
where proc_version='${proc_version}' and year='${year}' AND month='${month}' AND day='${day}';