module half_adder (
	input wire CLOCK_50,
    input  wire A,
    input  wire B,
    output wire S,
    output wire Co
);

    assign S  = A ^ B;   // soma
    assign Co = A & B;   // carry

endmodule
