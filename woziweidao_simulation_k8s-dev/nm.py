import sys
import tools

if __name__ == '__main__':
    a_index_start=int(sys.argv[1])
    a_index_end=int(sys.argv[2])
    b_index_start=int(sys.argv[3])
    b_index_end=int(sys.argv[4])
    random_seed_start=int(sys.argv[5])
    random_seed_end=int(sys.argv[6])
    num=int(sys.argv[7])
    res_size = 0
    for a_index in range(a_index_start, a_index_end+1):
        for b_index in range(b_index_start, b_index_end+1):
            for random_seed in range(random_seed_start, random_seed_end+1):
                res = tools.data_transform(1,1,a_index,b_index,random_seed)