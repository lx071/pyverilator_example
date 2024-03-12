from utils.tlm_utils import *
from utils.harness_utils import sim
import time
import random
import os

class ALUOp:
    """
    List of ALU opcodes.
    简单算术运算：
        加法(ADD)、减法(SUB)、小于比较(SLT)、无符号小于比较(SLTU)

    逻辑运算：
        按位或非(NOR)，按位与(AND)，按位或(OR)，按位异或(XOR)，左移(SLL)、右移(SRL)、算术右移(SRA)

    """
    SZ_IN      = 32
    SZ_OP      = 5

    # 10种基本运算
    OP_ADD     = 0
    OP_SLL     = 1
    OP_XOR     = 2
    OP_SRL     = 3
    OP_OR      = 4
    OP_AND     = 5
    OP_SUB     = 6
    OP_SRA     = 7
    OP_SLT     = 8
    OP_SLTU    = 9

    # 乘法、除法
    OP_MUL     = 10
    OP_MULH    = 11
    OP_MULHSU  = 12
    OP_MULHU   = 13
    OP_DIV     = 14
    OP_DIVU    = 15

    # 取余
    OP_REM     = 16
    OP_REMU    = 17


class Initiator(Module):

    def __init__(self, env, name):
        super().__init__(env, name)
        
        # 创建两个 socket，分别与 alu、target进行连接
        self.init2alu = Socket()

        # 函数注册，用于从 alu 和 target 接收数据
        self.init2alu.register_transport(self.recv_from_alu)

        # 创建事件 event
        self.init_event = self.env.event()
        self.alu_finish = self.env.event()

        # 创建进程，用于向 alu 传输数据
        # process 函数：传入 ProcessGenerator，返回 Process(self, generator)
        self.trans2alu_thread = self.env.process(self.transport2alu())

        self.in1 = []
        self.in2 = []
        self.op = []
        self.res = []

    # 数据初始化；触发 init_event 事件
    def src_in(self, in1, in2, op_, res_):
        self.in1 = in1
        self.in2 = in2
        self.op = op_
        self.res = res_
        self.init_event.succeed()

    # 从 'src.txt' 读取激励数据
    def file_read(self):
        with open('src.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().split(' ')
                # print(line)
                self.in1.append(int(line[0], 16))
                self.in2.append(int(line[1], 16))
                self.op.append(int(line[2], 16))
                # line = line[:-1]
                # print(in1, in2, op)
                # print(line.strip().split(' '))
                # break
    
    # 向 alu 传送数据，in1、in2、op
    def transport2alu(self):

        # 等待 数据初始化
        yield self.init_event

        for i in range(len(self.op)):
            payload = {
                'in1': self.in1[i],
                'in2': self.in2[i],
                'op': self.op[i],
            }
            # 取出一组数据，发送给 alu
            self.init2alu.transport(payload, 1)

            # 等待 alu 处理完毕
            yield self.alu_finish

        payload = {
            'exit': True
        }
        self.init2alu.transport(payload, 1)


    # 从 alu 接收到 结束信息，触发 alu_finish 事件
    def recv_from_alu(self, payload, delay):
        if payload['finish']:
            self.alu_finish.succeed()
            self.alu_finish = self.env.event()

class Checker(Module):

    def __init__(self, env, name):
        super().__init__(env, name)
        self.check2init = Socket()
        self.check2alu = Socket()
        self.check2init.register_transport(self.recv_from_init)
        self.check2alu.register_transport(self.recv_from_alu)

        self.very_thread = self.env.process(self.verification())
        self.trans2init_thread = self.env.process(self.transport2init())

        self.msg_from_init = self.env.event()
        self.msg_from_alu = self.env.event()
        self.finish = self.env.event()
        self.exit = self.env.event()

        self.res_init = None
        self.res_alu = None

    # 对 alu 功能进行验证
    def verification(self):
        while True:
            yield (self.msg_from_init & self.msg_from_alu) | self.exit
            if self.exit.triggered:
                print("finish time: {}".format(self.env.now))
                break
            # print("time: {} init: {} alu: {}".format(self.env.now, self.res_init, self.res_alu))
            assert self.res_init == self.res_alu
            yield self.env.timeout(1)
            self.finish.succeed()
            self.finish = self.env.event()

    # 从 init 接收数据，由 init2target.transport(payload, 1) 调用
    def recv_from_init(self, payload, delay):
        if 'exit' in payload.keys():
            self.exit.succeed()
            return

        self.res_init = payload['data']

        self.msg_from_init.succeed()
        self.msg_from_init = self.env.event()

    # 从 alu 接收数据，由 alu2target.transport(payload, 1) 调用
    def recv_from_alu(self, payload, delay):
        self.res_alu = payload['output']

        self.msg_from_alu.succeed()
        self.msg_from_alu = self.env.event()
        pass

    # 向 init 发送结束信息
    def transport2init(self):
        while True:
            yield self.finish
            payload = {
                'finish': True
            }
            self.target2init.transport(payload, 1)


"""
    input clk;
    input rst;
    input [31:0] io_input1;
    input [31:0] io_input2;
    input [4:0] io_function;
    input io_stall;
    input io_kill;
    output [31:0] io_output;
    reg [31:0] io_output;
    output io_req_stall;
    wire io_req_stall;
"""
class ALU(Module):

    def __init__(self, env, name):
        super().__init__(env, name)

        # 创建 socket，与 init 进行连接
        self.alu2init = Socket()
        
        # 函数注册，用于从 init 接收数据
        self.alu2init.register_transport(self.recv_from_init)

        self.received = self.env.event()

        self.dut_thread = self.env.process(self.dut())
        self.trans2init_thread = self.env.process(self.transport2init())
        
        self.finish = self.env.event()
        self.exit = self.env.event()

        self.input1 = None
        self.input2 = None
        self.op = None
        self.output = None
        self.res = [0] * 16

    # 向 init 发送结束信息
    def transport2init(self):
        while True:
            yield self.finish
            payload = {
                'finish': True
            }
            self.alu2init.transport(payload, 1)

    # 从 init 接收数据，由 init2alu.transport(payload, 1) 调用
    def recv_from_init(self, payload, delay):
        if 'exit' in payload.keys():
            self.exit.succeed()
            return
        self.input1 = payload['in1']
        self.input2 = payload['in2']
        self.op = payload['op']
        # print(self.input1, self.input2, self.op)

        # 数据接收完毕
        self.received.succeed()
        # yield self.env.timeout(1)
        self.received = self.env.event()

    def src_in(self):
        pass

    def dut(self):
        pid = os.getpid()
        print("pid: ", pid)
        sim_folder = 'simulation' + str(pid)
        # 传入dut所在目录、顶层模块文件名
        s = sim('./hdl/', 'ALU.v', sim_folder)

        s.setValue("clk", 0)
        s.setValue("rst", 1)

        num = 0
        main_time = 0
        clk_value = 0
        reset_value = 1

        while True:
            # print("time:", main_time)
            if num >= 100:
                break
            
            s.setValue("clk", not clk_value)
            clk_value = not clk_value
            
            if main_time == 20:
                s.setValue("rst", 0)
                reset_value = 0
            
            if reset_value == 1:
                # reset
                pass

            if reset_value == 0 and clk_value:
                
                yield self.received | self.exit
                if self.exit.triggered:
                    break
                
                s.setValue("io_input1", self.input1)
                s.setValue("io_input2", self.input2)
                s.setValue("io_function", 0)
                num = num + 1

                # 执行硬件设计逻辑，得到当前状态(各端口值)
                s.eval()
                # dump记录当前状态(各个端口值), 并锁定, time+=5
                s.sleep_cycles(5)

                self.finish.succeed()
                self.finish = self.env.event()  
            
            else:
                # 执行硬件设计逻辑，得到当前状态(各端口值)
                s.eval()
                # dump记录当前状态(各个端口值), 并锁定, time+=5
                s.sleep_cycles(5)
            
            main_time = main_time + 5

        s.deleteHandle()
        

        
class Top(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        # 创建实例 init、alu，传入 env，将各自的 socket 进行连接
        self.init = Initiator(self.env, 'init')
        self.alu = ALU(self.env, 'alu')

        self.init.init2alu.bind(self.alu.alu2init)


def test_alu(in1, in2, op, res):
    # 创建一个 env 实例
    env = simpy.Environment()
    
    # 创建顶层模块 top，传入 env
    top = Top(env, 'top')

    # 启动初始化
    top.init.src_in(in1, in2, op, res)

    # 运行仿真
    env.run()


def basic_test():
    in1 = [random.randrange(0, 20) for i in range(20)]
    in2 = [random.randrange(0, 20) for i in range(20)]
    op = [0 for i in range(20)]
    res = [0 for i in range(20)]
    test_alu(in1, in2, op, res)
    pass


# in1 = [0x48368ba4,0x9528653a,0xe8012689,0x326e7a90,0x16f8939f,0xc691072d,0x7180d681,0xca576c3d,0xb37dcf14,0xb818dc23]
# in2 = [0x2c9051dd,0x575a3285,0x8db432cc,0x53317c01,0xaeeecc28,0x24311a06,0x513d07fd,0xbda1539,0xa40478f6,0xa303cef5]
# op = [0x3,0xf,0x0,0xa,0x9,0x8,0x6,0x3,0xe,0x3]
# res = [0x2,0x0,0x75b55955,0x0,0x1,0x1,0x2043ce84,0x65,0x0,0x5c0]
def multi_test():

    import time
    start = time.time()

    in1 = []
    in2 = []
    op = []
    res = []

    with open('src.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().split(' ')
            # print(line)
            in1.append(int(line[0], 16))
            in2.append(int(line[1], 16))
            op.append(int(line[2], 16))
    with open('dst.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().split(' ')
            # print(line)
            res.append(int(line[0], 16))

    read_data = time.time() - start

    batch = 4

    step = len(res) // batch
    l = len(res)

    # 激励数据分为 4组，多进程处理
    input1 = [in1[i:i+step] for i in range(0, l, step)]
    input2 = [in2[i:i+step] for i in range(0, l, step)]
    op_ = [op[i:i+step] for i in range(0, l, step)]
    res_ = [res[i:i+step] for i in range(0, l, step)]

    multi = 1
    for i in range(len(op_)):
        input1[i] = input1[i] * multi
        input2[i] = input2[i] * multi
        op_[i] = op_[i] * multi
        res_[i] = res_[i] * multi

    from multiprocessing import Process
    from threading import Thread

    start = time.time()

    lst = []
    interp = [None] * batch
    for x in range(batch):
        i = x % batch
        # test_alu(input1[i], input2[i], op_[i], res_[i])
        p = Process(target=test_alu, args=(input1[i], input2[i], op_[i], res_[i]))
        lst.append(p)
        p.start()
    for p in lst:
        p.join()


    end = time.time()

    print("read_data: {}\n processing: {}".format(read_data, end - start))


if __name__ == '__main__':
    # basic_test()
    multi_test()