/*
- Verificar caminho critico
- Verificar a otimização para K
*/

module carry_skip_adder #(
    parameter N = 16,
    parameter X = 4
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A, B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout
);

    localparam NUM_BLOCKS = (N + X - 1) / X;
    wire [NUM_BLOCKS:0] carry;
    assign carry[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < NUM_BLOCKS; i = i + 1) begin : CSA_BLOCK
            localparam START = i * X;
            localparam END   = (START + X > N) ? N : (START + X);
            localparam SIZE  = END - START;

            wire [SIZE-1:0] A_blk = A[END-1:START];
            wire [SIZE-1:0] B_blk = B[END-1:START];
            wire [SIZE-1:0] S_blk;
            wire Cout_blk;
            wire prop_blk;

            // RCA do bloco
            rca #(.N(SIZE)) rca_blk (
                .A(A_blk),
                .B(B_blk),
                .Cin(carry[i]),
                .S(S_blk),
                .Cout(Cout_blk)
            );

            // Propagação do bloco: todos os bits precisam propagar
            assign prop_blk = & (A_blk ^ B_blk);

            // Carry skip: se propaga, pega carry de entrada; senão, pega Cout do bloco
            assign carry[i+1] = prop_blk ? carry[i] : Cout_blk;

            assign S[END-1:START] = S_blk;
        end
    endgenerate

    assign Cout = carry[NUM_BLOCKS];

endmodule
