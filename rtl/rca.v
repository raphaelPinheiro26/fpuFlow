module rca #(
    parameter N = 8   // número de bits
)(
	input  wire CLOCK_50,   // clock físico da FPGA
    input  wire [N-1:0] A, B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout
);
    wire [N:0] carry;   // sinais internos de carry
    assign carry[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : RCA
            full_adder fa (
                .A(A[i]),
                .B(B[i]),
                .Cin(carry[i]),
                .S(S[i]),
                .Cout(carry[i+1])
            );
        end
    endgenerate

    assign Cout = carry[N]; // carry final
endmodule