# 使用 simpy 模拟 SystemC TLM
# colorama 是一个python专门用来在控制台、命令行输出彩色文字的模块，可以跨平台使用
# Fore 是针对字体颜色，Back 是针对字体背景颜色，Style 是针对字体格式

import simpy
from colorama import Fore, Back, Style
import random
env = simpy.Environment()

# Python 生成器函数 => Processes => 建模
# 所有 Processes 都存在于一个 environment 中, 它们通过事件（events）与环境和彼此进行交互

class Socket:
    def __init__(self):
        self.data = None
        self.other_socket = None
        self.func = None

    # 将该 socket 与其他 socket 进行连接
    def bind(self, other):
        # 如果两个 socket 还未进行连接
        if (self.other_socket is None and other.other_socket is None):
            self.other_socket = other
            other.other_socket = self
        else:
            print("bind error")
    
    # 将 函数 注册到该 socket 中
    def register_transport(self, func):
        self.func = func

    # 调用 相连接的 socket 的函数
    def transport(self, payload, delay):
        if self.other_socket.func is not None:
            self.other_socket.func(payload, delay)

class Module:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        pass
    def __register(self, func):
        pass

class Initiator(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.socket = Socket()
        self.lst = [i for i in range(15)]
        # 将进程 main_thread 添加到 env 中
        self.thread_proc = env.process(self.main_thread(env))

    def main_thread(self, env):
        # 产生 payload，包含 command、data_addr、len
        payload = {
            'command': random.randint(0, 1),
            'data_addr': self.lst,
            'len': len(self.lst)
        }
        delay = 1
        # 每隔 1 秒 向 Target 发送一次 payload
        while True:
            print(Fore.LIGHTGREEN_EX + 'time: {} Initiator: transport'.format(env.now) + Fore.RESET)
            # 调用相连 socket 的方法 transport，传入 payload、delay
            self.socket.transport(payload, delay)
            print(Fore.LIGHTGREEN_EX + 'time: {} Initiator: transport finished'.format(env.now) + Fore.RESET)
            print(Fore.LIGHTYELLOW_EX + 'data: {}'.format(self.lst) + Fore.RESET)
            print()

            yield env.timeout(delay)


class Target(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.socket = Socket()
        # 将方法 transport 注册到 socket 
        self.socket.register_transport(self.transport)

    def transport(self, payload, delay):
        # 拿到 Initiator 传来的 payload，包含 command、data_addr、len
        cmd = payload['command']
        if cmd == 1:
            rand = random.randrange(0, payload['len'])
            payload['data_addr'][rand] = random.randint(20, 40)
        print(Fore.LIGHTRED_EX + 'Target get data' + Fore.RESET)


# 顶层模块，包含 initiator 和 target 模块，传入 env；将两边的 socket 进行连接
class Top(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.initiator = Initiator(env, "initiator")
        self.target = Target(env, "target")
        self.initiator.socket.bind(self.target.socket)

if __name__ == '__main__':
    t = Top(env, 'top')

    # 仿真运行 env 中的 process
    env.run(until=10)
