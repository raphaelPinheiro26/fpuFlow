// ======================================================
// Carry Increment Adder (Genérico)
// ======================================================
// Autor: Raphael Lopes Pinheiro
// Descrição: Implementa um somador carry-increment genérico
// com blocos de tamanho K, compatível com Verilog Quartus.
// ======================================================

module carry_increment_adder #(
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
        for (i = 0; i < NUM_BLOCKS; i = i + 1) begin : CI_BLOCK
            localparam integer START = i * K;
            localparam integer END   = (START + K > N) ? N : (START + K);
            localparam integer SIZE  = END - START;

            wire [SIZE-1:0] A_blk = A[END-1:START];
            wire [SIZE-1:0] B_blk = B[END-1:START];
            wire [SIZE-1:0] S_blk;
            wire Cout_blk;

            if (i == 0) begin
                // Primeiro bloco: RCA normal
                rca #(.N(SIZE)) rca_first (
                    .A(A_blk),
                    .B(B_blk),
                    .Cin(carry[i]),
                    .S(S_blk),
                    .Cout(Cout_blk)
                );

                assign S[END-1:START] = S_blk;
                assign carry[i+1] = Cout_blk;

            end else begin
                // Blocos subsequentes: RCA assume carry=0
                rca #(.N(SIZE)) rca_blk (
                    .A(A_blk),
                    .B(B_blk),
                    .Cin(1'b0),
                    .S(S_blk),
                    .Cout(Cout_blk)
                );

                // Preenche até K bits (para uso do módulo inc_cond)
                wire [K-1:0] S_blk_ext;
                assign S_blk_ext = {{(K-SIZE){1'b0}}, S_blk};

                wire [K-1:0] S_inc_ext;
                inc_cond #(.K(K)) INC_BLOCK (
                    .in(S_blk_ext),
                    .carry_in(carry[i]),
                    .out(S_inc_ext)
                );

                assign S[END-1:START] = S_inc_ext[SIZE-1:0];
                assign carry[i+1] = Cout_blk | (carry[i] & &S_blk);
            end
        end
    endgenerate

    assign Cout = carry[NUM_BLOCKS];

endmodule


// ======================================================
// Módulo Incrementador Condicional (usado internamente)
// ======================================================
module inc_cond #(
    parameter K = 4
)(
    input  wire [K-1:0] in,
    input  wire         carry_in,
    output wire [K-1:0] out
);
    wire [K:0] c;
    assign c[0] = carry_in;

    genvar j;
    generate
        for (j = 0; j < K; j = j + 1) begin : INC_BITS
            assign out[j] = in[j] ^ c[j];
            assign c[j+1] = in[j] & c[j];
        end
    endgenerate
endmodule
