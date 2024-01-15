from stats.battle_stat import BattleStat
import time

class Fetch():

    def nm_with_kafka(self, nm_version,partition_str, proc_version, a_index_start, a_index_end, b_index_start, b_index_end,
                      random_seed_start, random_seed_end,log_time,analyze_jp, analyze_stats):
        print("nm_with_kafka")
        for random_seed in range(random_seed_start, random_seed_end + 1):
            battle_stat = BattleStat(nm_version, proc_version, partition_str, a_index_start, b_index_start, random_seed, log_time)
            starttime = time.time()
            battle_stat.analyze(True if analyze_jp=='1' else False, True if analyze_stats=='1' else False)
            endtime = time.time()
            print(f'analyze_time: {endtime - starttime}')
