from utils import *


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
        self.init2target = Socket()

        # 函数注册，用于从 alu 和 target 接收数据
        self.init2alu.register_transport(self.recv_from_alu)
        self.init2target.register_transport(self.recv_from_target)

        # 创建事件 event
        self.init_event = self.env.event()
        # self.alu_finish = self.env.event()
        self.target_finish = self.env.event()

        # 创建两个进程，用于向 alu 和 target 传输数据
        # process 函数：传入 ProcessGenerator，返回 Process(self, generator)
        self.trans2alu_thread = self.env.process(self.transport2alu())
        self.trans2target_thread = self.env.process(self.transport2target())

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
            # 等待 target 处理完毕
            yield self.target_finish
            # yield self.alu_finish
        payload = {
            'exit': True
        }
        self.init2alu.transport(payload, 1)

    # 向 target 传送数据，res
    def transport2target(self):

        # 等待 数据初始化
        yield self.init_event
        for i in range(len(self.res)):
            payload = {
                'data': self.res[i]
            }
            # 将 res 数据传送给 target
            self.init2target.transport(payload, 1)
            # 等待 target 处理完毕
            yield self.target_finish
        payload = {
            'exit': True
        }
        # 最后传给 target，'exit': True
        self.init2target.transport(payload, 1)

    def recv_from_alu(self, payload, delay):
        pass

    # 从 target 接收到 结束信息，触发 target_finish 事件
    def recv_from_target(self, payload, delay):
        if payload['finish']:
            self.target_finish.succeed()
            self.target_finish = self.env.event()


class Target(Module):

    def __init__(self, env, name):
        super().__init__(env, name)
        self.target2init = Socket()
        self.target2alu = Socket()
        self.target2alu.register_transport(self.recv_from_alu)
        self.target2init.register_transport(self.recv_from_init)

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


class ALU(Module):

    def __init__(self, env, name):
        super().__init__(env, name)

        # 创建两个 socket，分别与 init、target进行连接
        self.alu2init = Socket()
        self.alu2target = Socket()

        # 函数注册，用于从 init 和 target 接收数据
        self.alu2init.register_transport(self.recv_from_init)
        self.alu2target.register_transport(self.recv_from_target)

        # mux多路选择进程，不断接收到数据，进行各种基本运算
        self.mux_thread = self.env.process(self.mux())
        self.trans2target_thread = self.env.process(self.transport2target())

        # 创建10个进程，用于10种基本运算
        self.op_add_thread = self.env.process(self.op_add())
        self.op_sll_thread = self.env.process(self.op_sll())
        self.op_xor_thread = self.env.process(self.op_xor())
        self.op_srl_thread = self.env.process(self.op_srl())
        self.op_or_thread = self.env.process(self.op_or())
        self.op_and_thread = self.env.process(self.op_and())
        self.op_sub_thread = self.env.process(self.op_sub())
        self.op_sra_thread = self.env.process(self.op_sra())
        self.op_slt_thread = self.env.process(self.op_slt())
        self.op_sltu_thread = self.env.process(self.op_sltu())

        # self.thread = self.env.process(self.probe())

        self.received = self.env.event()

        # 16个事件--对应16个操作符
        self.calculate = [self.env.event() for i in range(16)]
        self.transport = self.env.event()
        self.exit = self.env.event()

        self.input1 = None
        self.input2 = None
        self.op = None
        self.output = None
        self.res = [0] * 16

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

    def recv_from_target(self, payload, delay):
        pass

    # 加法，结果放入 res[0]
    def op_add(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[0] = (self.input1 + self.input2) & 0xffffffff
            self.calculate[0].succeed()
            yield self.env.timeout(1)
            self.calculate[0] = self.env.event()
    
    # 左移，结果放入 res[1]
    def op_sll(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[1] = (self.input1 << (self.input2 & (1 << ALUOp.SZ_OP) - 1)) & 0xffffffff
            self.calculate[1].succeed()
            yield self.env.timeout(1)
            self.calculate[1] = self.env.event()
    
    # 按位异或，结果放入 res[2]
    def op_xor(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[2] = self.input1 ^ self.input2
            self.calculate[2].succeed()
            yield self.env.timeout(1)
            self.calculate[2] = self.env.event()
    
    # 右移，结果放入 res[3]
    def op_srl(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[3] = (self.input1 >> (self.input2 & (1 << ALUOp.SZ_OP) - 1)) & 0xffffffff
            self.calculate[3].succeed()
            yield self.env.timeout(1)
            self.calculate[3] = self.env.event()
    
    # 按位或，结果放入 res[4]
    def op_or(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[4] = self.input1 | self.input2
            self.calculate[4].succeed()
            yield self.env.timeout(1)
            self.calculate[4] = self.env.event()
    
    # 按位与，结果放入 res[5]
    def op_and(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[5] = self.input1 & self.input2
            self.calculate[5].succeed()
            yield self.env.timeout(1)
            self.calculate[5] = self.env.event()
    
    # 减法，结果放入 res[6]
    def op_sub(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[6] = (self.input1 - self.input2) & 0xffffffff
            self.calculate[6].succeed()
            yield self.env.timeout(1)
            self.calculate[6] = self.env.event()
    
    # 算术右移，结果放入 res[7]
    def op_sra(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 if self.input1 < 2**31 else self.input1 - 2**32
            self.res[7] = (n >> (self.input2 & (1 << ALUOp.SZ_OP) - 1)) & 0xffffffff
            self.calculate[7].succeed()
            yield self.env.timeout(1)
            self.calculate[7] = self.env.event()
    
    # 小于比较，结果放入 res[8]
    def op_slt(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n1 = self.input1 if self.input1 < 2**31 else self.input1 - 2**32
            n2 = self.input2 if self.input2 < 2**31 else self.input2 - 2**32
            self.res[8] = n1 < n2
            self.calculate[8].succeed()
            yield self.env.timeout(1)
            self.calculate[8] = self.env.event()
    
    # 无符号小于比较，结果放入 res[9]
    def op_sltu(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            self.res[9] = self.input1 < self.input2
            self.calculate[9].succeed()
            yield self.env.timeout(1)
            self.calculate[9] = self.env.event()
    
    # 乘法，结果放入 res[10]
    def op_mul(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 * self.input2
            self.res[10] = (n >> 32) & 0xffffffff
            self.calculate[10].succeed()
            self.calculate[10] = self.env.event()
    
    # 乘法(有符号数扩展)，结果放入 res[11]
    def op_mulh(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 * self.input2
            self.res[11] = (n >> 32) & 0xffffffff
            self.calculate[11].succeed()
            self.calculate[11] = self.env.event()
    
    # 乘法(有、无符号数扩展)，结果放入 res[12]
    def op_mulhsu(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 * (self.input2 & 0xffffffff)
            self.res[12] = (n >> 32) & 0xffffffff
            self.calculate[12].succeed()
            self.calculate[12] = self.env.event()
    
    # 乘法(无符号数扩展)，结果放入 res[13]
    def op_mulhu(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = (self.input1 & 0xffffffff) * (self.input2 & 0xffffffff)
            self.res[13] = (n >> 32) & 0xffffffff
            self.calculate[13].succeed()
            self.calculate[13] = self.env.event()
    
    # 除法(有符号数扩展)，结果放入 res[14]
    def op_div(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 / self.input2
            self.res[14] = n & 0xffffffff
            self.calculate[14].succeed()
            self.calculate[14] = self.env.event()
    
    # 除法(无符号数扩展)，结果放入 res[15]
    def op_divu(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = (self.input1 & 0xffffffff) % (self.input2 & 0xffffffff)
            self.res[15] = n & 0xffffffff
            self.calculate[15].succeed()
            self.calculate[15] = self.env.event()
    
    # 取余
    def op_rem(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = self.input1 % self.input2
            return n & 0xffffffff
    
    # 取余(无符号数扩展)
    def op_remu(self):
        while True:
            yield self.received | self.exit
            if self.exit.triggered:
                break
            n = (self.input1 & 0xffffffff) % (self.input2 & 0xffffffff)
            return n & 0xffffffff

    def probe(self):
        pass
        # yield self.init
        # while True:
            # print("probe ???")
            # yield self.calculate[self.op]
            # print(self.calculate[self.op])
            # if self.calculate[self.op].triggered:
            #     print("yes")
            # if self.received.triggered:
            #     print("yes")

    # 进行多路选择；op=0~9:基本运算；触发 transport 事件
    def mux(self):
        while True:
            # print(self.op)
            # print(self.res)
            yield self.received | self.exit
            if self.exit.triggered:
                break
            # print(self.res)
            if self.op <= 9:
                yield self.calculate[self.op]
            # print(self.res)
            # print(self.op)
            self.output = 0 if self.op > 9 else self.res[self.op]
            self.transport.succeed()
            self.transport = self.env.event()

    # 将 output 传输给 target，执行 target 的 recv_from_alu 函数
    def transport2target(self):
        while True:
            yield self.transport | self.exit
            if self.exit.triggered:
                break
            payload = {
                'output': self.output
            }
            self.alu2target.transport(payload, 1)


class Top(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        # 创建实例 init、tar、alu，传入 env，将各自的 socket 进行连接
        self.init = Initiator(self.env, 'init')
        self.alu = ALU(self.env, 'alu')
        self.tar = Target(self.env, 'tar')
        self.init.init2alu.bind(self.alu.alu2init)
        self.init.init2target.bind(self.tar.target2init)
        self.alu.alu2target.bind(self.tar.target2alu)


def test_alu(in1, in2, op, res):
    # 创建一个 env 实例
    env = simpy.Environment()
    
    # 创建顶层模块 top，传入 env
    top = Top(env, 'top')

    # 启动初始化
    top.init.src_in(in1, in2, op, res)

    # 运行仿真
    env.run()


# in1 = [0x48368ba4,0x9528653a,0xe8012689,0x326e7a90,0x16f8939f,0xc691072d,0x7180d681,0xca576c3d,0xb37dcf14,0xb818dc23]
# in2 = [0x2c9051dd,0x575a3285,0x8db432cc,0x53317c01,0xaeeecc28,0x24311a06,0x513d07fd,0xbda1539,0xa40478f6,0xa303cef5]
# op = [0x3,0xf,0x0,0xa,0x9,0x8,0x6,0x3,0xe,0x3]
# res = [0x2,0x0,0x75b55955,0x0,0x1,0x1,0x2043ce84,0x65,0x0,0x5c0]
if __name__ == '__main__':
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
