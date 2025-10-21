// ==============================================
// Carry Select Adder com blocos de tamanho variável
// (2, 4, 6, 8, ...) até cobrir N bits
// ==============================================
module CSelA_op #(
    parameter N = 64  // largura total
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A, B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout
);

    // ====================================
    // Função para calcular número de blocos
    // tal que soma(2 + 4 + 6 + ... + 2k) >= N
    // ====================================
    function integer num_blocks;
        input integer n;
        integer sum, k;
        begin
            sum = 0;
            k   = 0;
            while (sum < n) begin
                k   = k + 1;
                sum = sum + 2*k;
            end
            num_blocks = k;
        end
    endfunction

    localparam NUM_BLOCKS = num_blocks(N);

    // ====================================
    // Função para calcular posição inicial de cada bloco
    // START(i) = soma dos tamanhos anteriores = 2*(1 + 2 + ... + i) = i*(i+1)
    // ====================================
    function integer block_start;
        input integer idx;
        integer j, sum;
        begin
            sum = 0;
            for (j = 0; j < idx; j = j + 1)
                sum = sum + 2 * (j + 1);
            block_start = sum;
        end
    endfunction

    // ====================================
    // Rede de propagação de carry
    // ====================================
    wire [NUM_BLOCKS:0] carry;
    assign carry[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < NUM_BLOCKS; i = i + 1) begin : CS_BLOCK
            // ====================================
            // Cálculo seguro dos limites do bloco
            // ====================================
            localparam integer START = block_start(i);
            localparam integer SIZE  = 2 * (i + 1);
            localparam integer END   = (START + SIZE > N) ? N : (START + SIZE);
            localparam integer ACTUAL_SIZE = (END > START) ? (END - START) : 0;

            if (START < N && ACTUAL_SIZE > 0) begin : VALID
                // ====================================
                // Particiona os vetores A e B
                // ====================================
                wire [ACTUAL_SIZE-1:0] A_blk = A[END-1:START];
                wire [ACTUAL_SIZE-1:0] B_blk = B[END-1:START];
                wire [ACTUAL_SIZE-1:0] S0_blk, S1_blk;
                wire Cout0_blk, Cout1_blk;

                if (i == 0) begin
                    // ====================================
                    // Primeiro bloco → RCA simples
                    // ====================================
                    rca #(.N(ACTUAL_SIZE)) rca_first (
                        .A(A_blk),
                        .B(B_blk),
                        .Cin(carry[i]),
                        .S(S0_blk),
                        .Cout(Cout0_blk)
                    );
                    assign S[END-1:START] = S0_blk;
                    assign carry[i+1] = Cout0_blk;

                    initial $display("Bloco %0d -> bits [%0d:%0d], SIZE=%0d (RCA simples)",
                                     i, END-1, START, ACTUAL_SIZE);
                end 
                else begin
                    // ====================================
                    // Blocos subsequentes → Carry Select
                    // ====================================
                    rca #(.N(ACTUAL_SIZE)) rca0 (
                        .A(A_blk),
                        .B(B_blk),
                        .Cin(1'b0),
                        .S(S0_blk),
                        .Cout(Cout0_blk)
                    );

                    rca #(.N(ACTUAL_SIZE)) rca1 (
                        .A(A_blk),
                        .B(B_blk),
                        .Cin(1'b1),
                        .S(S1_blk),
                        .Cout(Cout1_blk)
                    );

                    assign S[END-1:START] = carry[i] ? S1_blk : S0_blk;
                    assign carry[i+1]    = carry[i] ? Cout1_blk : Cout0_blk;

                    initial $display("Bloco %0d -> bits [%0d:%0d], SIZE=%0d (Carry Select)",
                                     i, END-1, START, ACTUAL_SIZE);
                end
            end
        end
    endgenerate

    assign Cout = carry[NUM_BLOCKS];

endmodule
