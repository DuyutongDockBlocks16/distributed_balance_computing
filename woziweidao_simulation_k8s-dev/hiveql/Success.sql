create external table if not exists wzwd.wzwd_ods_game_Success_d (
    nm_version_p            STRING COMMENT '一次模拟的版本号。分区字段（冗余）',
    list_version            STRING COMMENT 'list文件推断的版本',
    proc_version            STRING COMMENT '一次模拟中，代表着第几次处理的版本号',
    bd_A_index_start            CHAR(10) COMMENT 'A阵容索引开始',
    bd_A_index_end            CHAR(10) COMMENT 'A阵容索引结束',
    bd_B_index_start            CHAR(10) COMMENT 'B阵容索引开始',
    bd_B_index_end            CHAR(10) COMMENT 'B阵容索引结束',
    random_seed_start           INT COMMENT '随机种子开始',
    random_seed_end           INT COMMENT '随机种子结束',
    use_frame                 CHAR(50) COMMENT '对局总帧数',
    use_time                  DOUBLE COMMENT '对局模拟总用时'
)
    COMMENT '正常解析的对局日志'
    PARTITIONED BY (nm_version STRING)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE
    LOCATION '/staging/wzwd/nm/k8s/Success';

ALTER TABLE wzwd.wzwd_ods_game_Success_d add if not exists PARTITION(nm_version='${nm_version}')
    LOCATION '/staging/wzwd/nm/k8s/Success/${nm_version}';
