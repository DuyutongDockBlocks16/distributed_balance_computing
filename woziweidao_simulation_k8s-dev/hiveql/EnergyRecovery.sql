create external table if not exists wzwd.wzwd_ods_game_EnergyRecovery_d (
    nm_version_p            STRING COMMENT '一次模拟的版本号。分区字段（冗余）',
    list_version            STRING COMMENT 'list文件推断的版本',
    proc_version            STRING COMMENT '一次模拟中，代表着第几次处理的版本号',
    bd_A_index            CHAR(10) COMMENT 'A阵容索引',
    bd_B_index            CHAR(10) COMMENT 'B阵容索引',
    random_seed           INT COMMENT '随机种子',
    result                INT COMMENT '战斗结果',
    last_time             DOUBLE COMMENT '战斗持续时长',
    frame                 INT COMMENT '帧号',
    sourceCardPos         INT COMMENT '攻击方卡牌位置',
    energyRecoveryType    INT COMMENT '回能类型（普攻攻击回能、技能攻击回能、击杀回能、受击回能、buff回能、放技能能量清零）',
    energyRecovery        DOUBLE COMMENT '实际回能数值（加减都要记）',
    skillId             STRING,
    targetCardPos           INT,
    targetId                INT,
    time                DOUBLE,
    sourceActorType int comment '发起的角色类型',
    targetActorType int comment '目标的角色类型'
)
    COMMENT '回能日志'
    PARTITIONED BY (nm_version STRING)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE
    LOCATION '/staging/wzwd/nm/k8s/EnergyRecovery';

ALTER TABLE wzwd.wzwd_ods_game_EnergyRecovery_d add if not exists PARTITION(nm_version='${nm_version}')
    LOCATION '/staging/wzwd/nm/k8s/EnergyRecovery/${nm_version}';