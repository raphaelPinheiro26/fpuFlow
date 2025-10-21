module sparse_kogge_stone_adder #(parameter N = 8, parameter K = 4)(
    input  wire CLOCK_50,
    input  [N-1:0] A,
    input  [N-1:0] B,
    input  Cin,
    output [N-1:0] Sum,
    output Cout
);

    localparam L = $clog2(N);

    // ===== 1) Generate e Propagate iniciais =====
    wire [N-1:0] G, P;
    assign G = A & B;
    assign P = A ^ B;

    // ===== 2) Prefixos por nível (checkpoints a cada K bits) =====
    wire [N-1:0] G_level [0:L];
    wire [N-1:0] P_level [0:L];
    assign G_level[0] = G;
    assign P_level[0] = P;

    genvar level, i;
    generate
        for(level = 1; level <= L; level = level + 1) begin : PREFIX_LEVEL
            for(i = 0; i < N; i = i + 1) begin : CELLS
                if((i >= 2**(level-1)) && (i % K == 0)) begin
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

    // ===== 3) Cálculo dos carries =====
    wire [N:0] C;
    assign C[0] = Cin;

    generate
        for(i = 0; i < N; i = i + 1) begin : CARRY_CALC
            if(i % K == 0)
                grey_cell gc (
                    .Gk(G_level[L][i]),
                    .Pk(P_level[L][i]),
                    .Gi(C[i]),
                    .Gout(C[i+1])
                );
            else
                assign C[i+1] = G[i] | (P[i] & C[i]); // ripple carry local
        end
    endgenerate

    // ===== 4) Soma final =====
    generate
        for(i = 0; i < N; i = i + 1) begin : SUM_BITS
            assign Sum[i] = P[i] ^ C[i];
        end
    endgenerate

    assign Cout = C[N];

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
