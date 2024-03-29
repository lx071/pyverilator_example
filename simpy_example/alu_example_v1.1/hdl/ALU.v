// File: ALU.v
// Generated by MyHDL 0.11.45
// Date: Wed Mar  6 11:12:13 2024


`timescale 1ns/10ps

module ALU (
    clk,
    rst,
    io_input1,
    io_input2,
    io_function,
    io_stall,
    io_kill,
    io_output,
    io_req_stall
);
// Defines an Arithmetic-Logic Unit (ALU)
// 
// :param clk: System clock
// :param rst: System reset
// :param IO:  An IO bundle (Function, Input1, Input2, Output)

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

wire [31:0] mult_h;
wire [31:0] mult_l;
wire mult_ss;
wire mult_su;
wire mult_uu;
wire [31:0] quotient;
wire [31:0] remainder;
wire [31:0] multIO_input1;
wire [31:0] multIO_input2;
wire [2:0] multIO_cmd;
wire multIO_enable;
wire multIO_active;
wire multIO_stall;
wire multIO_kill;
wire [63:0] multIO_output;
wire [31:0] divIO_dividend;
wire [31:0] divIO_divisor;
wire divIO_divs;
reg divIO_active;
wire divIO_divu;
wire [31:0] divIO_quotient;
wire [31:0] divIO_remainder;
wire divIO_ready;
wire multIO_ready;
reg div_active;
reg [4:0] div_cycle;
reg [31:0] div_denominator;
reg div_neg_remainder;
reg div_neg_result;
wire [32:0] div_partial_sub;
reg [31:0] div_residual;
reg [31:0] div_result;
reg [32:0] mult_A;
reg [32:0] mult_B;
wire [32:0] mult_a_sign_ext;
reg [0:0] mult_active0;
reg [0:0] mult_active1;
reg [0:0] mult_active2;
reg [0:0] mult_active3;
wire [32:0] mult_b_sign_ext;
wire [47:0] mult_partial_sum;
reg [31:0] mult_result_hh_0;
reg [31:0] mult_result_hh_1;
reg [31:0] mult_result_hl_0;
reg [31:0] mult_result_lh_0;
reg [31:0] mult_result_ll_0;
reg [31:0] mult_result_ll_1;
reg [32:0] mult_result_mid_1;
reg [63:0] mult_result_mult;
wire [0:0] mult_sign_a;
wire [0:0] mult_sign_b;
reg [0:0] mult_sign_result0;
reg [0:0] mult_sign_result1;
reg [0:0] mult_sign_result2;
reg [0:0] mult_sign_result3;



always @(quotient, mult_l, io_input2, remainder, mult_h, io_input1, io_function) begin: ALU_RTL
    case (io_function)
        'h0: begin
            io_output = (io_input1 + io_input2);
        end
        'h1: begin
            io_output = (io_input1 << io_input2[5-1:0]);
        end
        'h2: begin
            io_output = (io_input1 ^ io_input2);
        end
        'h3: begin
            io_output = (io_input1 >>> io_input2[5-1:0]);
        end
        'h4: begin
            io_output = (io_input1 | io_input2);
        end
        'h5: begin
            io_output = (io_input1 & io_input2);
        end
        'h6: begin
            io_output = (io_input1 - io_input2);
        end
        'h7: begin
            io_output = $signed($signed(io_input1) >>> io_input2[5-1:0]);
        end
        'h8: begin
            io_output = {31'h0, ($signed(io_input1) < $signed(io_input2))};
        end
        'h9: begin
            io_output = {31'h0, (io_input1 < io_input2)};
        end
        'ha: begin
            io_output = mult_l;
        end
        'hb: begin
            io_output = mult_h;
        end
        'hc: begin
            io_output = mult_h;
        end
        'hd: begin
            io_output = mult_h;
        end
        'he: begin
            io_output = quotient;
        end
        'hf: begin
            io_output = quotient;
        end
        'h10: begin
            io_output = remainder;
        end
        'h11: begin
            io_output = remainder;
        end
        default: begin
            io_output = 0;
        end
    endcase
end



assign mult_sign_a = (multIO_cmd[0] || multIO_cmd[2]) ? multIO_input1[31] : 1'h0;
assign mult_sign_b = multIO_cmd[0] ? multIO_input2[31] : 1'h0;
assign mult_partial_sum = ({15'h0, mult_result_mid_1} + {mult_result_hh_1[32-1:0], mult_result_ll_1[32-1:16]});
assign multIO_output = mult_sign_result3 ? (-mult_result_mult) : mult_result_mult;
assign multIO_ready = mult_active3;
assign multIO_active = (((mult_active0 | mult_active1) | mult_active2) | mult_active3);



assign mult_a_sign_ext = {mult_sign_a, multIO_input1};
assign mult_b_sign_ext = {mult_sign_b, multIO_input2};


always @(posedge clk) begin: ALU_MULT_PIPELINE
    if ((rst || multIO_kill)) begin
        mult_A <= 33'h0;
        mult_B <= 33'h0;
        mult_active0 <= 1'h0;
        mult_active1 <= 1'h0;
        mult_active2 <= 1'h0;
        mult_active3 <= 1'h0;
        mult_result_hh_0 <= 31'h0;
        mult_result_hh_1 <= 31'h0;
        mult_result_hl_0 <= 31'h0;
        mult_result_lh_0 <= 31'h0;
        mult_result_ll_0 <= 31'h0;
        mult_result_ll_1 <= 31'h0;
        mult_result_mid_1 <= 31'h0;
        mult_result_mult <= 64'h0;
        mult_sign_result0 <= 1'h0;
        mult_sign_result1 <= 1'h0;
        mult_sign_result2 <= 1'h0;
        mult_sign_result3 <= 1'h0;
    end
    else if ((!multIO_stall)) begin
        mult_A <= mult_sign_a ? (-mult_a_sign_ext) : mult_a_sign_ext;
        mult_B <= mult_sign_b ? (-mult_b_sign_ext) : mult_b_sign_ext;
        mult_sign_result0 <= (mult_sign_a ^ mult_sign_b);
        mult_active0 <= multIO_enable;
        mult_result_ll_0 <= (mult_A[16-1:0] * mult_B[16-1:0]);
        mult_result_lh_0 <= (mult_A[16-1:0] * mult_B[33-1:16]);
        mult_result_hl_0 <= (mult_A[33-1:16] * mult_B[16-1:0]);
        mult_result_hh_0 <= (mult_A[32-1:16] * mult_B[32-1:16]);
        mult_sign_result1 <= mult_sign_result0;
        mult_active1 <= mult_active0;
        mult_result_ll_1 <= mult_result_ll_0;
        mult_result_hh_1 <= mult_result_hh_0;
        mult_result_mid_1 <= (mult_result_lh_0 + mult_result_hl_0);
        mult_sign_result2 <= mult_sign_result1;
        mult_active2 <= mult_active1;
        mult_result_mult <= {mult_partial_sum, mult_result_ll_1[16-1:0]};
        mult_sign_result3 <= mult_sign_result2;
        mult_active3 <= mult_active2;
    end
end



assign divIO_quotient = (div_neg_result == 0) ? div_result : (-div_result);
assign divIO_remainder = (div_neg_remainder == 0) ? div_residual : (-div_residual);
assign divIO_ready = (divIO_active && (!div_active));
assign div_partial_sub = ({div_residual[31-1:0], div_result[31]} - div_denominator);


always @(posedge clk) begin: ALU_DIV__ACTIVE
    if (rst) begin
        divIO_active <= 1'b0;
    end
    else begin
        if (divIO_active) begin
            divIO_active <= (!div_active) ? 1'b0 : 1'b1;
        end
        else begin
            divIO_active <= (divIO_divs || divIO_divu) ? 1'b1 : 1'b0;
        end
    end
end


always @(posedge clk) begin: ALU_DIV_RTL
    if (rst) begin
        div_active <= 0;
        div_cycle <= 0;
        div_denominator <= 0;
        div_neg_result <= 0;
        div_neg_remainder <= 0;
        div_residual <= 0;
        div_result <= 0;
    end
    else begin
        if (divIO_divs) begin
            div_cycle <= 31;
            div_result <= (divIO_dividend[31] == 0) ? divIO_dividend : (-divIO_dividend);
            div_denominator <= (divIO_divisor[31] == 0) ? divIO_divisor : (-divIO_divisor);
            div_residual <= 0;
            div_neg_result <= (divIO_dividend[31] ^ divIO_divisor[31]);
            div_neg_remainder <= divIO_dividend[31];
            div_active <= 1;
        end
        else if (divIO_divu) begin
            div_cycle <= 31;
            div_result <= divIO_dividend;
            div_denominator <= divIO_divisor;
            div_residual <= 0;
            div_neg_result <= 0;
            div_neg_remainder <= 0;
            div_active <= 1;
        end
        else if (div_active) begin
            if ((div_partial_sub[32] == 0)) begin
                div_residual <= div_partial_sub[32-1:0];
                div_result <= {div_result[31-1:0], 1'h1};
            end
            else begin
                div_residual <= {div_residual[31-1:0], div_result[31]};
                div_result <= {div_result[31-1:0], 1'h0};
            end
            if ((div_cycle == 0)) begin
                div_active <= 0;
            end
            div_cycle <= (div_cycle - 5'h1);
        end
    end
end



assign multIO_input1 = io_input1;
assign multIO_input2 = io_input2;
assign multIO_cmd = mult_ss ? 3'h1 : mult_su ? 3'h4 : mult_uu ? 3'h2 : 3'h0;
assign multIO_enable = ((mult_ss || mult_su || mult_uu) && (!multIO_active));
assign multIO_stall = (io_stall != io_req_stall);
assign multIO_kill = io_kill;
assign mult_l = multIO_output[32-1:0];
assign mult_h = multIO_output[64-1:32];
assign divIO_dividend = io_input1;
assign divIO_divisor = io_input2;
assign divIO_divs = (((io_function == 14) || (io_function == 16)) && (!divIO_active));
assign divIO_divu = (((io_function == 15) || (io_function == 17)) && (!divIO_active));
assign quotient = divIO_quotient;
assign remainder = divIO_remainder;



assign mult_ss = ((io_function == 10) || (io_function == 11));
assign mult_su = (io_function == 12);
assign mult_uu = (io_function == 13);



assign io_req_stall = ((divIO_divs || divIO_divu || (divIO_active != divIO_ready)) || (multIO_enable || (multIO_active != multIO_ready)));

endmodule
