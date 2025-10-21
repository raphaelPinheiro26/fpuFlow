// ============================================================
// Module: han_carlson_adder
// Function: Parametrized Han-Carlson Adder with Carry-In and Overflow
// Author: Raphael
// ============================================================
module han_carlson_adder #(
    parameter N = 8
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire         Cin,
    output wire [N-1:0] Sum,
    output wire         Cout,
    output wire         overflow
);

    // ======== Etapa 1: sinais G e P iniciais ========
    wire [N-1:0] G0, P0;
    assign G0 = A & B;
    assign P0 = A ^ B;

    // ======== Etapa 2: árvore de prefixos Han-Carlson ========
    localparam L = $clog2(N);
    wire [N-1:0] G [0:L];
    wire [N-1:0] P [0:L];

    assign G[0] = G0;
    assign P[0] = P0;

    genvar i, level;
    generate
        for(level = 1; level <= L; level = level + 1) begin : levels
            for(i = 0; i < N; i = i + 1) begin : cells
                // Han-Carlson: combina Kogge-Stone (para metade superior) + Brent-Kung (restante)
                if(i >= 2**(level-1)) begin
                    assign G[level][i] = G[level-1][i] | (P[level-1][i] & G[level-1][i - 2**(level-1)]);
                    assign P[level][i] = P[level-1][i] & P[level-1][i - 2**(level-1)];
                end else begin
                    assign G[level][i] = G[level-1][i];
                    assign P[level][i] = P[level-1][i];
                end
            end
        end
    endgenerate

    // ======== Etapa 3: cálculo dos carries ========
    wire [N:0] C;
    assign C[0] = Cin;

    generate
        for(i = 0; i < N; i = i + 1) begin : carries
            assign C[i+1] = G[L][i] | (P[L][i] & Cin);
        end
    endgenerate

    // ======== Etapa 4: soma final ========
    generate
        for(i = 0; i < N; i = i + 1) begin : sums
            assign Sum[i] = P0[i] ^ C[i];
        end
    endgenerate

    // ======== Etapa 5: Carry-out e Overflow ========
    assign Cout     = C[N];
    assign overflow = C[N] ^ C[N-1];

endmodule
