// ============================================================
// Module: ladner_fischer_adder
// Function: Parametrized Ladner-Fischer Prefix Adder com Grey Cells
// ============================================================
module ladner_fischer_adder #(parameter N = 8)(
    input  wire CLOCK_50,
    input  [N-1:0] A,
    input  [N-1:0] B,
    input          Cin,
    output [N-1:0] Sum,
    output         Cout,
    output         overflow
);

    // ======== Etapa 1: sinais G e P iniciais ========
    wire [N-1:0] G, P;
    assign G = A & B;
    assign P = A ^ B;

    // ======== Etapa 2: prefixos por nível ========
    localparam L = $clog2(N);
    wire [N-1:0] G_level [0:L];
    wire [N-1:0] P_level [0:L];

    assign G_level[0] = G;
    assign P_level[0] = P;

    genvar level, i;
    generate
        for(level = 1; level <= L; level = level + 1) begin : prefix_levels
            for(i = 0; i < N; i = i + 1) begin : prefix_cells
                if(i >= 2**(level-1)) begin
                    black_cell bc(
                        .Gk(G_level[level-1][i]),
                        .Pk(P_level[level-1][i]),
                        .Gi(G_level[level-1][i - 2**(level-1)]),
                        .Pi(P_level[level-1][i - 2**(level-1)]),
                        .Gout(G_level[level][i]),
                        .Pout(P_level[level][i])
                    );
                end else begin
                    assign G_level[level][i] = G_level[level-1][i];
                    assign P_level[level][i] = P_level[level-1][i];
                end
            end
        end
    endgenerate

    // ======== Etapa 3: cálculo dos carries com Grey Cells ========
    wire [N:0] C;
    assign C[0] = Cin;

    generate
        for(i = 0; i < N; i = i + 1) begin : carry_calc
            grey_cell gc(
                .Gk(G_level[L][i]),
                .Pk(P_level[L][i]),
                .Gi(C[i]),
                .Gout(C[i+1])
            );
        end
    endgenerate

    // ======== Etapa 4: soma ========
    generate
        for(i = 0; i < N; i = i + 1) begin : sum_bits
            assign Sum[i] = P[i] ^ C[i];
        end
    endgenerate

    // ======== Etapa 5: Carry-out e Overflow ========
    assign Cout     = C[N];
    assign overflow = C[N] ^ C[N-1];

endmodule

// ============================================================
// Black cell: calcula G_out e P_out
// ============================================================
module black_cell(
    input  Gk, Pk, Gi, Pi,
    output Gout, Pout
);
    assign Gout = Gk | (Pk & Gi);
    assign Pout = Pk & Pi;
endmodule

// ============================================================
// Grey cell: calcula apenas o carry (G_out)
// ============================================================
module grey_cell(
    input  Gk, Pk, Gi,
    output Gout
);
    assign Gout = Gk | (Pk & Gi);
endmodule
