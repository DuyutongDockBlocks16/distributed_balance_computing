create external table if not exists wzwd.wzwd_ods_game_TakeDamage_d (
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
    targetCardPos         INT COMMENT '受击方卡牌位置',
    time                  DOUBLE COMMENT '战斗内时间',
    damage                DOUBLE COMMENT '实际造成伤害数值',
    damageType            INT COMMENT '伤害类型',
    damageStatus          INT COMMENT '特殊状态（被盾抵消，闪避，暴击）',
    isInterrupt           STRING COMMENT '是否打断',
    sourceActorType int comment '发起的角色类型',
    targetActorType int comment '目标的角色类型'
)
    COMMENT '受到伤害日志'
    PARTITIONED BY (nm_version STRING)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE
    LOCATION '/staging/wzwd/nm/k8s/TakeDamage';

ALTER TABLE wzwd.wzwd_ods_game_TakeDamage_d add if not exists PARTITION(nm_version='${nm_version}')
    LOCATION '/staging/wzwd/nm/k8s/TakeDamage/${nm_version}';