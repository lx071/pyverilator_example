# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
# Simple tests for an adder module

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge, RisingEdge

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
        for i in range(5):
            print(Fore.LIGHTGREEN_EX + 'time: {} Initiator: transport'.format(env.now) + Fore.RESET)
            # 调用相连 socket 的方法 transport，传入 payload、delay
            self.socket.transport(payload, delay)
            print(Fore.LIGHTGREEN_EX + 'time: {} Initiator: transport finished'.format(env.now) + Fore.RESET)
            print(Fore.LIGHTYELLOW_EX + 'data: {}'.format(self.lst) + Fore.RESET)
            print()

            yield env.timeout(delay)


class Target(Module):
    def __init__(self, env, name, dut):
        super().__init__(env, name)
        self.socket = Socket()
        # 将方法 transport 注册到 socket 
        self.socket.register_transport(self.transport)
        self.dut = dut
        self.k = 1

    async def transport(self, payload, delay):
        # 拿到 Initiator 传来的 payload，包含 command、data_addr、len
        cmd = payload['command']
        if cmd == 1:
            rand = random.randrange(0, payload['len'])
            payload['data_addr'][rand] = random.randint(20, 40)
        print(Fore.LIGHTRED_EX + 'Target get data' + Fore.RESET)
        self.dut.A_s.value = self.k % 200
        self.dut.B_s.value = self.k % 200
        self.k = self.k + 1
        await RisingEdge(self.dut.clk_i)


# 顶层模块，包含 initiator 和 target 模块，传入 env；将两边的 socket 进行连接
class Top(Module):
    def __init__(self, env, name, dut):
        super().__init__(env, name)
        self.initiator = Initiator(env, "initiator")
        self.target = Target(env, "target", dut)
        self.initiator.socket.bind(self.target.socket)


async def generate_clock(dut):
    """Generate clock pulses."""
    dut.clk_i.value = 0
    # for cycle in range(100):
    while True:
        dut.clk_i.value = 0
        await Timer(5, units="ns")
        dut.clk_i.value = 1
        await Timer(5, units="ns")


async def generate_rst(dut):
    dut.reset_i.value = 1
    for cycle in range(10):
        await RisingEdge(dut.clk_i)
    dut.reset_i.value = 0


@cocotb.test()
async def adder_basic_test(dut):
    """Test for 5 + 10"""
    await cocotb.start(generate_clock(dut))  # run the clock "in the background"
    await cocotb.start(generate_rst(dut))  # run the clock "in the background"

    await FallingEdge(dut.reset_i)

    t = Top(env, 'top', dut)

    # 仿真运行 env 中的 process
    env.run()
    

if __name__ == '__main__':
    t = Top(env, 'top')

    # 仿真运行 env 中的 process
    env.run()
