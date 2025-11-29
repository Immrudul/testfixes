`default_nettype none
`timescale 1ns / 1ps

module tb();

    // Dump waves
    initial begin
        $dumpfile("tb.fst");
        $dumpvars(0, tb);
        #1;
    end

    // TT signals
    reg clk;
    reg rst_n;
    reg ena;

    reg  [7:0] ui_in;
    reg  [7:0] uio_in;

    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
`endif

    // Instantiate ONLY the top-level module
    tt_um_example dut (
`ifdef GL_TEST
        .VPWR(VPWR),
        .VGND(VGND),
`endif
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n)
    );

    // Clock (tiny tapeout default is slow, but simulation can be faster)
    always #5 clk = ~clk;

    initial begin
        // init
        clk = 0;
        rst_n = 0;
        ena = 1;
        ui_in = 0;
        uio_in = 0;

        // Come out of reset
        #40;
        rst_n = 1;

        // ---------- Stimulus examples ----------
        // Speed control (ui_in[3:0])
        #100 ui_in[3:0] = 4'd3;

        // Direction (ui_in[4])
        #200 ui_in[4] = 1;

        // Let animation run
        #20000;

        $finish;
    end

endmodule
