import sys
import lupa

# TODO 测试静态方法
LIBS = "./Fight.lua"
f = open(LIBS)
# \n 是将代码加入行分割，这样使用 lua.execute() 来运行代码
code_str = '\n'.join(f.readlines())
f.close()

def sdk_nm(a_index, b_index, random_seed):
    # lua 每一套阵容的战斗都要执行 lua 环境的初始化
    lua = lupa.LuaRuntime()
    g = lua.globals()
    lua.execute(code_str)
    print('indexa, indexb, random_seed', a_index, b_index, random_seed)
    lua_table = g.fight(a_index, b_index, random_seed)
    return lua_table

if __name__ == '__main__':
    a_index = sys.argv[1]
    b_index = sys.argv[2]
    random_seed = int(sys.argv[3])
    sdk_nm(a_index, b_index, random_seed)
