# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
# Simple tests for an adder module

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge, RisingEdge

import random
from myhdl import *

def adder (
    clk,
    rst,
    io_input1,
    io_input2,
    io_function,
    io_stall,
    io_kill,
    io_output,
    io_req_stall
):
    io_a = Signal(modbv(0)[32:])
    io_b = Signal(modbv(0)[32:])

    @always_comb
    def _assignments():
        io_output.next = io_a + io_b
    
    @always(clk.posedge, rst.posedge)
    def rtl():
        if rst:
            io_a.next = 2
            io_b.next = 2
        elif io_function == 1:
            io_a.next = io_input1
            io_b.next = io_input2
        else:
            io_a.next = 1
            io_b.next = 1

    return _assignments, rtl


def convert_adder():
    """Convert inc block to Verilog or VHDL."""

    clk = Signal(False)
    rst = Signal(True)
    input1    = Signal(modbv(0)[32:])
    input2    = Signal(modbv(0)[32:])
    function  = Signal(modbv(0)[2:])
    stall     = Signal(False)
    kill      = Signal(False)
    output    = Signal(modbv(0)[32:])
    req_stall = Signal(False)
    

    toVerilog(adder, clk, rst, input1, input2, function, stall, kill, output, req_stall)

    
def _testbench():
    """
    Testbech for the module
    """
    clk = Signal(False)
    rst = Signal(True)
    input1    = Signal(modbv(0)[32:])
    input2    = Signal(modbv(0)[32:])
    function  = Signal(modbv(0)[2:])
    stall     = Signal(False)
    kill      = Signal(False)
    output    = Signal(modbv(0)[32:])
    req_stall = Signal(False)

    dut = adder(
        clk=clk,
        rst=rst,
        io_input1=input1,
        io_input2=input2,
        io_function=function,
        io_stall=stall,
        io_kill=kill,
        io_output=output,
        io_req_stall=req_stall
    )
            
    halfperiod = delay(5)

    @always(halfperiod)
    def clk_drive():
        clk.next = not clk

    @instance
    def stimulus():
        yield delay(5)
        rst.next = 0

        # Execute 1000 tests.
        for j in range(10):

            yield clk.posedge

            input1.next = random.randrange(0, 20)
            input2.next = random.randrange(0, 20)
            function.next = 1
            a = input1
            b = input2

            print("clk = ", clk, ", rst = ", rst, ", func = ", function)
            print("a = ", a, ", b = ", b, ", output = ", output)

        raise StopSimulation

    return dut, clk_drive, stimulus


if __name__ == '__main__':
    sim = Simulation(_testbench())
    sim.run()


@cocotb.test()
async def adder_basic_test(dut):

    sim = Simulation(_testbench())
    sim.run()

    