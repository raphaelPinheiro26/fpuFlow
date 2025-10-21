// =====================================================
// hierarchical_cla: CLA hierárquico para N bits com blocos de K
// - aceita N qualquer; último bloco pode ter largura < K
// =====================================================
module hierarchical_cla #(
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
    wire [NB-1:0] blkC;       // carry-in de cada bloco
    wire [NB-1:0] blkCout;    // carry-out de cada bloco (usado só para referência)

    // bloco 0 carry-in = Cin
    // blocC_in vector will be blkCin[0..NB-1]
    wire [NB:0] blkCin;
    assign blkCin[0] = Cin;

    genvar bi;
    generate
        for (bi = 0; bi < NB; bi = bi + 1) begin : BLK_GEN
            // base index e largura deste bloco
            localparam  base = bi * K;
            localparam  WIDTH = (bi == NB-1) ? (N - base) : K;
            // safety: if WIDTH==0 (shouldn't happen) set to K
            if (WIDTH <= 0) begin
                // nothing (edge-case protection)
            end else begin
                // instanciar bloco com largura WIDTH
                cla_block_ripple #(.W(WIDTH)) blk (
                    .A(A[base +: WIDTH]),
                    .B(B[base +: WIDTH]),
                    .Cin(blkCin[bi]),
                    .S(S[base +: WIDTH]),
                    .Cout(blkCout[bi]),
                    .G_block(Gblk[bi]),
                    .P_block(Pblk[bi])
                );

                // compute next block carry (ripple at block granularity for now)
                // we'll build blkCin[bi+1] = Gblk[bi] | (Pblk[bi] & blkCin[bi])
                assign blkCin[bi+1] = Gblk[bi] | (Pblk[bi] & blkCin[bi]);
            end
        end
    endgenerate

    // final Cout is carry out of last block
    assign Cout = blkCin[NB];

endmodule






// =====================================================
// cla_block_ripple: bloco de W bits que fornece:
//   - S[W-1:0], Cout
//   - G_block (Cout quando Cin=0), P_block (AND de P bits)
// =====================================================

module cla_block_ripple #(
    parameter  W = 4
)(
    input  wire [W-1:0] A,
    input  wire [W-1:0] B,
    input  wire         Cin,
    output wire [W-1:0] S,
    output wire         Cout,
    output wire         G_block, // generate do bloco (Cout se Cin=0)
    output wire         P_block  // propaga do bloco (AND de todos P)
);
    // sinais internos
    wire [W-1:0] G = A & B;
    wire [W-1:0] P = A ^ B;

    // Carries quando Cin = 0 (para calcular G_block)
    wire [W:0] C0;
    assign C0[0] = 1'b0;
    genvar i;
    generate
        for (i = 0; i < W; i = i+1) begin : GEN_C0
            assign C0[i+1] = G[i] | (P[i] & C0[i]);
        end
    endgenerate
    assign G_block = C0[W];

    // P_block = AND de todos P
    assign P_block = &P;

    // Carries reais com Cin (para somas)
    wire [W:0] C;
    assign C[0] = Cin;
    generate
        for (i = 0; i < W; i = i+1) begin : GEN_C
            assign C[i+1] = G[i] | (P[i] & C[i]);
            assign S[i] = P[i] ^ C[i];
        end
    endgenerate
    assign Cout = C[W];

endmodule


