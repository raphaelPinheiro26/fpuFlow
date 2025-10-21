// Kogge-Stone Adder parametrizável
module kogge_stone_adder #(parameter N = 8)(
    input  wire CLOCK_50,
    input  [N-1:0] A,
    input  [N-1:0] B,
    input  Cin,
    output [N-1:0] Sum,
    output Cout
);

    localparam L = $clog2(N);   // Número de níveis da árvore

    // 1) Generate e Propagate iniciais
    wire [N-1:0] G, P;
    assign G = A & B;
    assign P = A ^ B;

    // 2) Prefixos por nível (compatível com síntese)
    wire [N-1:0] G_level [0:L];
    wire [N-1:0] P_level [0:L];

    // 3) Nível 0 da árvore
    genvar i;
    generate
        for(i = 0; i < N; i = i + 1) begin : LEVEL0
            assign G_level[0][i] = G[i];
            assign P_level[0][i] = P[i];
        end
    endgenerate

    // 4) Construindo a árvore de prefixo
    genvar level;
    generate
        for(level = 1; level <= L; level = level + 1) begin : PREFIX_LEVEL
            for(i = 0; i < N; i = i + 1) begin : CELLS
                if(i >= 2**(level-1)) begin
                    black_cell bc (
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

    // 5) Calculando os carries usando Grey Cells
    wire [N-1:0] C;
    assign C[0] = G_level[L][0] | (P_level[L][0] & Cin);

    generate
        for(i = 1; i < N; i = i + 1) begin : FINAL_CARRY
            grey_cell gc (
                .Gk(G_level[L][i]),
                .Pk(P_level[L][i]),
                .Gi(C[i-1]),
                .Gout(C[i])
            );
        end
    endgenerate

    // 6) Soma final
    generate
        for(i = 0; i < N; i = i + 1) begin : SUM_BITS
            assign Sum[i] = P[i] ^ ((i==0) ? Cin : C[i-1]);
        end
    endgenerate

    assign Cout = C[N-1];

endmodule

// Black cell: calcula G_out e P_out
module black_cell(
    input  Gk, Pk, Gi, Pi,
    output Gout, Pout
);
    assign Gout = Gk | (Pk & Gi);
    assign Pout = Pk & Pi;
endmodule

// Grey cell: calcula apenas carry
module grey_cell(
    input  Gk, Pk, Gi,
    output Gout
);
    assign Gout = Gk | (Pk & Gi);
endmodule
