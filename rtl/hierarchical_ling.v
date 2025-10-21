// =====================================================
// hierarchical_ling: Ling adder hierárquico para N bits com blocos de K
// - aceita N qualquer; último bloco pode ter largura < K
// - compatível com a interface do seu hierarchical_cla
// =====================================================

module hierarchical_ling #(
    parameter  N = 32,
    parameter  K = 4
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire         Cin,
    output wire [N-1:0] S,
    output wire         Cout
);
    // número de blocos (ceil)
    localparam  NB = (N + K - 1) / K;

    // arrays para sinais de bloco
    wire [NB-1:0] Gblk;
    wire [NB-1:0] Pblk;
    // carry-in de cada bloco (blkCin[0] = Cin; blkCin[NB] = final Cout)
    wire [NB:0] blkCin;
    assign blkCin[0] = Cin;

    genvar bi;
    generate
        for (bi = 0; bi < NB; bi = bi + 1) begin : BLK_GEN
            // base index e largura deste bloco
            localparam integer base  = bi * K;
            localparam integer WIDTH = (bi == NB-1) ? (N - base) : K;

            if (WIDTH <= 0) begin
                // proteção (não deverá acontecer)
            end else begin
                // instanciar bloco Ling com largura WIDTH
                ling_block_ripple #(.W(WIDTH)) blk (
                    .A(A[base +: WIDTH]),
                    .B(B[base +: WIDTH]),
                    .Cin(blkCin[bi]),
                    .S(S[base +: WIDTH]),
                    .Cout(),             // opcional (não usado diretamente aqui)
                    .G_block(Gblk[bi]),
                    .P_block(Pblk[bi])
                );

                // compute next block carry (block-level CLA style)
                assign blkCin[bi+1] = Gblk[bi] | (Pblk[bi] & blkCin[bi]);
            end
        end
    endgenerate

    // final Cout é carry-in do bloco NB (blkCin[NB])
    assign Cout = blkCin[NB];

endmodule


// =====================================================
// ling_block_ripple: bloco Ling de W bits
// - fornece S[W-1:0], Cout, G_block, P_block
// - implementa H-prefix internal (Ling formulation)
// =====================================================
module ling_block_ripple #(
    parameter  W = 4
)(
    input  wire [W-1:0] A,
    input  wire [W-1:0] B,
    input  wire         Cin,
    output wire [W-1:0] S,
    output wire         Cout,
    output wire         G_block, // generate do bloco (Cout quando Cin=0)
    output wire         P_block  // propaga do bloco (AND de todos P bits)
);

    // sinais locais
    wire [W-1:0] G = A & B;    // geração por bit
    wire [W-1:0] P = A | B;    // propagate para Ling: usamos OR (P = A | B)

    // -------------------------------------------------
    // Cálculo H com Cin real (H[0] = Cin; H[i+1] = G[i] | (P[i] & H[i]))
    // H[k] representa carry deslocado (Ling carry)
    // -------------------------------------------------
    wire [W:0] H;
    assign H[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < W; i = i + 1) begin : LING_H
            assign H[i+1] = G[i] | (P[i] & H[i]);
            // soma usa H[i] (carry "anterior" no sentido Ling)
            assign S[i] = A[i] ^ B[i] ^ H[i];
        end
    endgenerate

    assign Cout = H[W];

    // -------------------------------------------------
    // G_block (carry out quando Cin=0) e P_block (AND de P)
    // - G_block: calculado com Cin=0 (prefix C0)
    // -------------------------------------------------
    wire [W:0] C0;
    assign C0[0] = 1'b0;
    generate
        for (i = 0; i < W; i = i + 1) begin : LING_C0
            assign C0[i+1] = G[i] | (P[i] & C0[i]);
        end
    endgenerate
    assign G_block = C0[W];
    assign P_block = &P;

endmodule
