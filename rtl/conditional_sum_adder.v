// =====================================================
// Conditional Sum Adder (CSuA)
// - Baseado no hierarchical_cla como adder de bloco
// - Estrutura em árvore de seleção condicional
// =====================================================
module conditional_sum_adder #(
    parameter N = 32,   // largura total
    parameter K = 4     // tamanho de cada bloco CLA
)(
    input  wire CLOCK_50,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire         Cin,
    output wire [N-1:0] S,
    output wire         Cout
);
    // =====================================================
    // Número de blocos (ceil)
    // =====================================================
    localparam NB = (N + K - 1) / K;

    // Resultados condicionais por bloco
    wire [N-1:0] sum0, sum1;   // soma para Cin=0 e Cin=1
    wire [NB-1:0] cout0, cout1; // carry out de cada bloco (para Cin=0/1)
    wire [NB:0] carry_sel;      // carry selecionado real
    assign carry_sel[0] = Cin;

    genvar i;
    generate
        for (i = 0; i < NB; i = i + 1) begin : CSUM_BLOCK
            localparam START = i * K;
            localparam END   = (START + K > N) ? N : (START + K);
            localparam SIZE  = END - START;

            // Subvetores A e B do bloco
            wire [SIZE-1:0] A_blk = A[END-1:START];
            wire [SIZE-1:0] B_blk = B[END-1:START];

            // =====================================================
            // Duas versões: uma assumindo carry_in=0 e outra =1
            // =====================================================
            hierarchical_cla #(.N(SIZE), .K(K)) cla0 (
                .A(A_blk), .B(B_blk),
                .Cin(1'b0),
                .S(sum0[END-1:START]),
                .Cout(cout0[i])
            );

            hierarchical_cla #(.N(SIZE), .K(K)) cla1 (
                .A(A_blk), .B(B_blk),
                .Cin(1'b1),
                .S(sum1[END-1:START]),
                .Cout(cout1[i])
            );

            // =====================================================
            // Seleciona a soma e carry corretos
            // =====================================================
            assign S[END-1:START] = (carry_sel[i]) ? sum1[END-1:START]
                                                   : sum0[END-1:START];
            assign carry_sel[i+1] = (carry_sel[i]) ? cout1[i]
                                                   : cout0[i];
        end
    endgenerate

    // Carry final
    assign Cout = carry_sel[NB];

endmodule
