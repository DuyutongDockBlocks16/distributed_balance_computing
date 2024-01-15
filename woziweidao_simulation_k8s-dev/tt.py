import sys
import time

from stats.battle_stat import BattleStat

if __name__ == '__main__':
    left_id = sys.argv[1]
    right_id = sys.argv[2]
    random_seed = int(sys.argv[3])
    battle_stat = BattleStat('wyb1.0.0',1,10101,left_id,right_id,random_seed,'2234651492')
    starttime = time.time()
    battle_stat.analyze(True,True)
    endtime = time.time()
    print(f'use_time: {endtime-starttime}')