// ============================================================
// Spanning Tree Adder (STA) - Puro funcional
// ============================================================
module spanning_tree_adder #(parameter N = 8)(
    input  wire CLOCK_50,
    input  [N-1:0] A,
    input  [N-1:0] B,
    input          Cin,
    output [N-1:0] Sum,
    output         Cout
);

    // --------------------------------------------
    // 1) Generate e Propagate iniciais
    // --------------------------------------------
    wire [N-1:0] G, P;
    assign G = A & B;
    assign P = A ^ B;

    // --------------------------------------------
    // 2) Número de níveis da árvore
    // --------------------------------------------
    localparam L = $clog2(N);

    // --------------------------------------------
    // 3) Prefix network (estrutura tipo árvore STA)
    // --------------------------------------------
    wire [N-1:0] G_level [0:L];
    wire [N-1:0] P_level [0:L];

    genvar i, level;
    generate
        // Nível 0
        for (i = 0; i < N; i = i + 1) begin : LEVEL0
            assign G_level[0][i] = G[i];
            assign P_level[0][i] = P[i];
        end

        // Níveis de prefixo STA
        for (level = 1; level <= L; level = level + 1) begin : PREFIX
            for (i = 0; i < N; i = i + 1) begin : CELLS
                if (i >= (1 << (level-1))) begin
                    black_cell bc (
                        .Gk(G_level[level-1][i]),
                        .Pk(P_level[level-1][i]),
                        .Gi(G_level[level-1][i - (1 << (level-1))]),
                        .Pi(P_level[level-1][i - (1 << (level-1))]),
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

    // --------------------------------------------
    // 4) Cálculo correto dos carries
    // --------------------------------------------
    wire [N:0] C;
    assign C[0] = Cin;

    generate
        for(i = 0; i < N; i = i + 1) begin : CARRY
            grey_cell gc (
                .Gk(G_level[L][i]),
                .Pk(P_level[L][i]),
                .Gi(C[i]),
                .Gout(C[i+1])
            );
        end
    endgenerate

    // --------------------------------------------
    // 5) Soma final
    // --------------------------------------------
    generate
        for(i = 0; i < N; i = i + 1) begin : SUM_BITS
            assign Sum[i] = P[i] ^ C[i];
        end
    endgenerate

    assign Cout = C[N];

endmodule

// ============================================================
// Black cell
// ============================================================
module black_cell(
    input  Gk, Pk, Gi, Pi,
    output Gout, Pout
);
    assign Gout = Gk | (Pk & Gi);
    assign Pout = Pk & Pi;
endmodule

// ============================================================
// Grey cell
// ============================================================
module grey_cell(
    input  Gk, Pk, Gi,
    output Gout
);
    assign Gout = Gk | (Pk & Gi);
endmodule
