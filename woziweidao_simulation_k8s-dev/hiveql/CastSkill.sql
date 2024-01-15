create external table if not exists wzwd.wzwd_ods_game_CastSkill_d (
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
    skillId               STRING COMMENT '技能ID',
    isBaseAttack          STRING COMMENT '是否为普攻',
    isManual              STRING COMMENT '是否为手动释放',
    sourceActorType int comment '发起的角色类型',
    targetActorType int comment '目标的角色类型'
)
    COMMENT '技能发动日志'
    PARTITIONED BY (nm_version STRING)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE
    LOCATION '/staging/wzwd/nm/k8s/CastSkill';

ALTER TABLE wzwd.wzwd_ods_game_CastSkill_d add if not exists PARTITION(nm_version='${nm_version}')
    LOCATION '/staging/wzwd/nm/k8s/CastSkill/${nm_version}';
