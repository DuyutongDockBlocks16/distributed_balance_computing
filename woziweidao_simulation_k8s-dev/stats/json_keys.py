import stats.battle_data_classify as battle_data_classify
import stats.battle_data_type as battle_data_type
# 规范化定义的json数据格式和类型
# 也就是生产到kafka里的数据格式和类型
res = {
    # battle_data_classify.FrameStatue : (
    #     f'battle_gra_id:{battle_data_type.string}',
    #     f'proc_version:{battle_data_type.string}',
    #     f'nm_version:{battle_data_type.string}',
    #     f'list_version:{battle_data_type.string}',
    #     f'logtime:{battle_data_type.string}',
    #     f'frame:{battle_data_type.int32}',
    #     f'side:{battle_data_type.int32}',
    #     f'fightActor_id:{battle_data_type.string}',
    #     f'HP:{battle_data_type.string}',
    #     f'MP:{battle_data_type.string}',
    #     f'AD:{battle_data_type.string}',
    #     f'maxHP:{battle_data_type.string}',
    #     f'HP_regeneration:{battle_data_type.string}',
    #     f'MP_regeneration:{battle_data_type.string}',
    #     f'hast:{battle_data_type.string}',
    #     f'AD_reduction:{battle_data_type.string}',
    #     f'AP_reduction:{battle_data_type.string}',
    #     f'takeHeal_rate:{battle_data_type.string}',
    #     f'shield:{battle_data_type.string}',
    #     f'crit:{battle_data_type.string}',
    #     f'aspd:{battle_data_type.string}',
    #     f'buffs:{battle_data_type.string}',
    #     f'buff_effects:{battle_data_type.string}',
    #     f'State:{battle_data_type.string}',
    # ),
    battle_data_classify.CastSkill : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'skill_id:{battle_data_type.string}',
        f'source_card_pos:{battle_data_type.int32}',
        f'target_card_pos:{battle_data_type.int32}',
    ),
    battle_data_classify.Damage : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'damage_id:{battle_data_type.string}',
        f'source_card_pos:{battle_data_type.int32}',
        f'target_card_pos:{battle_data_type.int32}',
        f'damage:{battle_data_type.string}',
        f'is_hit:{battle_data_type.string}',
        f'is_crit:{battle_data_type.string}',
        f'is_killed:{battle_data_type.string}',
        f'targetActorType:{battle_data_type.int32}',
        f'sourceActorType:{battle_data_type.int32}',
    ),
    battle_data_classify.TakeDamage : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'source_card_pos:{battle_data_type.int32}',
        f'target_card_pos:{battle_data_type.int32}',
        f'takeDamage:{battle_data_type.string}',
    ),
    battle_data_classify.Heal : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'skill_id:{battle_data_type.string}',
        f'source_card_pos:{battle_data_type.int32}',
        f'target_card_pos:{battle_data_type.int32}',
        f'heal:{battle_data_type.string}',
    ),
    battle_data_classify.EnergyRecovery : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'source_card_pos:{battle_data_type.int32}',
        f'target_card_pos:{battle_data_type.int32}',
        f'energy_recovery:{battle_data_type.string}',
        f'energy_recovery_type:{battle_data_type.int32}',
    ),
    f'{battle_data_classify.Damage}_JP' : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'accum_damage:{battle_data_type.string}',
    ),
    f'{battle_data_classify.TakeDamage}_JP' : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'accum_takeDamage:{battle_data_type.string}',
    ),
    f'{battle_data_classify.Heal}_JP' : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'accum_heal:{battle_data_type.string}',
    ),
    f'{battle_data_classify.EnergyRecovery}_JP' : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'accum_energyRecovery:{battle_data_type.string}',
    ),
    f'{battle_data_classify.FrameStatue}_JP' : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'frame:{battle_data_type.int32}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'HP:{battle_data_type.string}',
        f'MP:{battle_data_type.string}',
        f'AD:{battle_data_type.string}',
        f'maxHP:{battle_data_type.string}',
        f'HP_regeneration:{battle_data_type.string}',
        f'MP_regeneration:{battle_data_type.string}',
        f'hast:{battle_data_type.string}',
        f'AD_reduction:{battle_data_type.string}',
        f'AP_reduction:{battle_data_type.string}',
        f'takeHeal_rate:{battle_data_type.string}',
        f'shield:{battle_data_type.string}',
        f'crit:{battle_data_type.string}',
        f'aspd:{battle_data_type.string}',
        f'buffs:{battle_data_type.string}',
        f'buff_effects:{battle_data_type.string}',
    ),
    battle_data_classify.Battle : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'result:{battle_data_type.int32}',
        f'last_frame:{battle_data_type.int32}',
        f'last_time:{battle_data_type.string}',
        f'execute_time:{battle_data_type.string}',
        f'isFightTimeOver:{battle_data_type.string}',
        f'fightActor1:{battle_data_type.string}',
        f'fightActor2:{battle_data_type.string}',
        f'fightActor3:{battle_data_type.string}',
        f'fightActor4:{battle_data_type.string}',
        f'fightActor5:{battle_data_type.string}',
        f'fightActor6:{battle_data_type.string}',
        f'fightActor7:{battle_data_type.string}',
        f'fightActor8:{battle_data_type.string}',
        f'fightActor9:{battle_data_type.string}',
        f'fightActor10:{battle_data_type.string}',
    ),
    battle_data_classify.BattleHero : (
        f'battle_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'side:{battle_data_type.int32}',
        f'fightActor_id:{battle_data_type.string}',
        f'last_is_dead:{battle_data_type.string}',
        f'max_MaxHP:{battle_data_type.string}',
        f'last_HP:{battle_data_type.string}',
        f'last_HP_rate:{battle_data_type.string}',
        f'last_frame:{battle_data_type.int32}',
        f'valid_fight_time:{battle_data_type.int32}',
        f'invalid_fight_time:{battle_data_type.int32}',
        f'accum_damage:{battle_data_type.string}',
        f'damage_persec:{battle_data_type.string}',
        f'valid_damage_persec:{battle_data_type.string}',
        f'accum_takeDamage:{battle_data_type.string}',
        f'takeDamage_persec:{battle_data_type.string}',
        f'valid_takeDamage_persec:{battle_data_type.string}',
        f'accum_heal:{battle_data_type.string}',
        f'heal_persec:{battle_data_type.string}',
        f'valid_heal_persec:{battle_data_type.string}',
        f'accum_energyRecovery:{battle_data_type.string}',
        f'energyRecovery_persec:{battle_data_type.string}',
        f'valid_energyRecovery_persec:{battle_data_type.string}',
        f'skill0_cast_count:{battle_data_type.int32}',f'skill0_accum_damage:{battle_data_type.string}',f'skill0_damage_cast_coount:{battle_data_type.int32}',f'skill0_damage_persec:{battle_data_type.string}',
        f'skill1_cast_count:{battle_data_type.int32}',f'skill1_accum_damage:{battle_data_type.string}',f'skill1_damage_cast_coount:{battle_data_type.int32}',f'skill1_damage_persec:{battle_data_type.string}',
        f'skill2_cast_count:{battle_data_type.int32}',f'skill2_accum_damage:{battle_data_type.string}',f'skill2_damage_cast_coount:{battle_data_type.int32}',f'skill2_damage_persec:{battle_data_type.string}',
        f'skill3_cast_count:{battle_data_type.int32}',f'skill3_accum_damage:{battle_data_type.string}',f'skill3_damage_cast_coount:{battle_data_type.int32}',f'skill3_damage_persec:{battle_data_type.string}',
        f'skill4_cast_count:{battle_data_type.int32}',f'skill4_accum_damage:{battle_data_type.string}',f'skill4_damage_cast_coount:{battle_data_type.int32}',f'skill4_damage_persec:{battle_data_type.string}',
        f'skill5_cast_count:{battle_data_type.int32}',f'skill5_accum_damage:{battle_data_type.string}',f'skill5_damage_cast_coount:{battle_data_type.int32}',f'skill5_damage_persec:{battle_data_type.string}',
        f'skill6_cast_count:{battle_data_type.int32}',f'skill6_accum_damage:{battle_data_type.string}',f'skill6_damage_cast_coount:{battle_data_type.int32}',f'skill6_damage_persec:{battle_data_type.string}',
        f'skill7_cast_count:{battle_data_type.int32}',f'skill7_accum_damage:{battle_data_type.string}',f'skill7_damage_cast_coount:{battle_data_type.int32}',f'skill7_damage_persec:{battle_data_type.string}',
        f'skill8_cast_count:{battle_data_type.int32}',f'skill8_accum_damage:{battle_data_type.string}',f'skill8_damage_cast_coount:{battle_data_type.int32}',f'skill8_damage_persec:{battle_data_type.string}',
        f'skill9_cast_count:{battle_data_type.int32}',f'skill9_accum_damage:{battle_data_type.string}',f'skill9_damage_cast_coount:{battle_data_type.int32}',f'skill9_damage_persec:{battle_data_type.string}',
        f'skill10_cast_count:{battle_data_type.int32}',f'skill10_accum_damage:{battle_data_type.string}',f'skill10_damage_cast_coount:{battle_data_type.int32}',f'skill10_damage_persec:{battle_data_type.string}',
    ),
    battle_data_classify.Pair : (
        f'pair_gra_id:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'nm_version:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'logtime:{battle_data_type.string}',
        f'list_version:{battle_data_type.string}',
        f'proc_version:{battle_data_type.string}',
        f'left_id:{battle_data_type.string}',
        f'right_id:{battle_data_type.string}',
        f'randomSeed_start:{battle_data_type.int32}',
        f'randomSeed_end:{battle_data_type.int32}',
    ),
}