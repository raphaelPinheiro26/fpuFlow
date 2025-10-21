module iterative_adder #(
    parameter N = 16,   // largura total
    parameter X = 4     // tamanho do bloco base (ex: 4-bit RCA)
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A, B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout
);
    // Quantidade de blocos
    localparam NUM_BLOCKS = (N + X - 1) / X; // arredonda pra cima

    // Vetores internos de carry entre blocos
    wire [NUM_BLOCKS:0] carry;
    assign carry[0] = Cin;

    // ===============================
    // Geração dos blocos iterativos
    // ===============================
    genvar i;
    generate
        for (i = 0; i < NUM_BLOCKS; i = i + 1) begin : ITER_BLOCK

            // Calcula os índices para o bloco atual
            localparam  START = i * X;
            localparam  END   = (START + X > N) ? N : (START + X);
            localparam  SIZE  = END - START;

            // Fios intermediários
            wire [SIZE-1:0] A_blk = A[END-1:START];
            wire [SIZE-1:0] B_blk = B[END-1:START];
            wire [SIZE-1:0] S_blk;
            wire Cout_blk;

            // Instancia um RCA com o tamanho apropriado
            rca #(.N(SIZE)) rca_blk (
                .A(A_blk),
                .B(B_blk),
                .Cin(carry[i]),
                .S(S_blk),
                .Cout(Cout_blk)
            );

            // Liga as saídas no vetor final
            assign S[END-1:START] = S_blk;
            assign carry[i+1] = Cout_blk;
        end
    endgenerate

    assign Cout = carry[NUM_BLOCKS];

endmodule
