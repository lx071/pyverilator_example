import sys

from utils.harness_utils import sim
import time
import random

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

def alu_test():
    # 传入dut所在目录、顶层模块文件名
    s = sim('./hdl/', 'ALU.v')

    s.setValue("clk", 0)
    s.setValue("rst", 1)

    num = 0
    main_time = 0
    clk_value = 0
    reset_value = 1

    while True:

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

            s.setValue("io_input1", random.randrange(0, 20))
            s.setValue("io_input2", random.randrange(0, 20))
            s.setValue("io_function", 0)
            num = num + 1
            
        # 执行硬件设计逻辑，得到当前状态(各端口值)
        s.eval()
        # dump记录当前状态(各个端口值), 并锁定, time+=5
        s.sleep_cycles(5)
        main_time = main_time + 5

    s.deleteHandle()


if __name__ == '__main__':
    alu_test()
    pass

