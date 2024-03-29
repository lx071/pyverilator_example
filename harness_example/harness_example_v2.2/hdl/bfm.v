`timescale 1ns/1ps

module bfm(
input   clk_i,
input   reset_i,
output  reg [7:0] res_o
);

reg [7:0] A_s;
reg [7:0] B_s;

parameter TOTAL_WIDTH=256;

MyTopLevel inst_add(
    .io_A(A_s),
    .io_B(B_s),
    .io_X(res_o),
    .clk(clk_i),
    .reset(reset_i)
);

reg[3:0]    xmit_en;
reg[5:0]    num = 0;
reg[TOTAL_WIDTH-1:0]		dat_out_v;

export "DPI-C" function send_bit_vec;
import "DPI-C" function void recv (input int data);

always @(posedge clk_i or posedge reset_i) begin
    if(reset_i) begin
        A_s = 8'h0;
        B_s = 8'h0;
    end else begin
        if(xmit_en) begin
            A_s = dat_out_v[7:0];
            B_s = dat_out_v[7:0];
            dat_out_v = (dat_out_v >> 8);
            num = num + 1;
            recv(6);
        end
        if(num >= 32) begin
            num = 0;
            xmit_en = xmit_en - 1;
        end
    end
end

function void send_bit_vec(bit[255:0] data);
begin
    xmit_en = xmit_en + 1;
    dat_out_v = data[TOTAL_WIDTH-1:0];
end
endfunction


endmodule