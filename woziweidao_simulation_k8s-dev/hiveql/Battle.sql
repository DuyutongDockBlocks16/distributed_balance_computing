create external table if not exists wzwd.wzwd_ods_game_Battle_d_tmp (data string)
partitioned by (proc_version string, year string, month string, day string)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '|'  ESCAPED BY '\\'
STORED AS TEXTFILE location '/staging/wzwd/nm/k8s_v2/Battle';

create table if not exists wzwd.wzwd_ods_game_Battle_d (
    battle_gra_id            STRING COMMENT 'row_key',
    nm_version            STRING COMMENT '一次模拟的版本号。分区字段（冗余）',
    list_version            STRING COMMENT 'list文件推断的版本',
    logtime            STRING COMMENT '模拟时间',
    result                INT COMMENT '战斗结果',
    last_time             STRING COMMENT '战斗持续时长',
    last_frame             INT COMMENT '战斗持续帧数',
    execute_time             STRING COMMENT '模拟执行时长',
    fightActor1             STRING COMMENT '位置1的卡牌id',
    fightActor2             STRING COMMENT '位置2的卡牌id',
    fightActor3             STRING COMMENT '位置3的卡牌id',
    fightActor4             STRING COMMENT '位置4的卡牌id',
    fightActor5             STRING COMMENT '位置5的卡牌id',
    fightActor6             STRING COMMENT '位置6的卡牌id',
    fightActor7             STRING COMMENT '位置7的卡牌id',
    fightActor8             STRING COMMENT '位置8的卡牌id',
    fightActor9             STRING COMMENT '位置9的卡牌id',
    fightActor10             STRING COMMENT '位置10的卡牌id'
)
    COMMENT '对局统计日志'
    PARTITIONED BY (proc_version STRING, year string, month string, day string)
    ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '\001'
        COLLECTION ITEMS TERMINATED BY '\002'
        MAP KEYS TERMINATED BY '\003'
    STORED AS TEXTFILE;

ALTER TABLE wzwd.wzwd_ods_game_Battle_d_tmp add if not exists PARTITION(proc_version='${proc_version}', year='${year}', month='${month}', day='${day}')
    LOCATION '/staging/wzwd/nm/k8s_v2/Battle/${proc_version}/${year}/${month}/${day}';


insert overwrite table wzwd.wzwd_ods_game_Battle_d PARTITION(proc_version='${proc_version}', year='${year}', month='${month}', day='${day}') select
    get_json_object(data,'$.battle_gra_id'),
    get_json_object(data,'$.nm_version'),
    get_json_object(data,'$.list_version'),
    get_json_object(data,'$.logtime'),
    cast(get_json_object(data,'$.result') as int),
    get_json_object(data,'$.last_time'),
    cast(get_json_object(data,'$.last_frame') as int),
    get_json_object(data,'$.execute_time'),
    get_json_object(data,'$.fightActor1'),
    get_json_object(data,'$.fightActor2'),
    get_json_object(data,'$.fightActor3'),
    get_json_object(data,'$.fightActor4'),
    get_json_object(data,'$.fightActor5'),
    get_json_object(data,'$.fightActor6'),
    get_json_object(data,'$.fightActor7'),
    get_json_object(data,'$.fightActor8'),
    get_json_object(data,'$.fightActor9'),
    get_json_object(data,'$.fightActor10')
from wzwd.wzwd_ods_game_Battle_d_tmp
where proc_version='${proc_version}' and year='${year}' AND month='${month}' AND day='${day}';