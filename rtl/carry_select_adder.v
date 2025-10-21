module carry_select_adder #(
    parameter N = 16,  // largura total
    parameter K = 4    // tamanho do bloco
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A, B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout
);

    localparam NUM_BLOCKS = (N + K - 1) / K;
    wire [NUM_BLOCKS:0] carry;
    assign carry[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < NUM_BLOCKS; i = i + 1) begin : CS_BLOCK
            localparam START = i * K;
            localparam END   = (START + K > N) ? N : (START + K);
            localparam SIZE  = END - START;

            wire [SIZE-1:0] A_blk = A[END-1:START];
            wire [SIZE-1:0] B_blk = B[END-1:START];
            wire [SIZE-1:0] S0_blk, S1_blk;
            wire Cout0_blk, Cout1_blk;

            if (i == 0) begin
                // Primeiro bloco: RCA normal
                rca #(.N(SIZE)) rca_blk (
                    .A(A_blk),
                    .B(B_blk),
                    .Cin(carry[i]),
                    .S(S0_blk),
                    .Cout(Cout0_blk)
                );
                assign S[END-1:START] = S0_blk;
                assign carry[i+1] = Cout0_blk;
            end else begin
                // Bloco subsequente: RCA duplo
                rca #(.N(SIZE)) rca0 (
                    .A(A_blk),
                    .B(B_blk),
                    .Cin(1'b0),
                    .S(S0_blk),
                    .Cout(Cout0_blk)
                );

                rca #(.N(SIZE)) rca1 (
                    .A(A_blk),
                    .B(B_blk),
                    .Cin(1'b1),
                    .S(S1_blk),
                    .Cout(Cout1_blk)
                );

                // Seleção da soma correta via MUX
                assign S[END-1:START] = carry[i] ? S1_blk : S0_blk;
                assign carry[i+1]    = carry[i] ? Cout1_blk : Cout0_blk;
            end
        end
    endgenerate

    assign Cout = carry[NUM_BLOCKS];

endmodule
