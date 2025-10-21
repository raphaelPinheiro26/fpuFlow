module sklansky_adder #(parameter N = 8)(
    input  wire CLOCK_50,
    input  [N-1:0] A,
    input  [N-1:0] B,
    input           Cin,
    output [N-1:0] Sum,
    output          Cout,
    output          overflow
);

    function integer log2;
        input integer value;
        integer i;
        begin
            log2 = 0;
            for(i=value-1; i>0; i=i>>1)
                log2 = log2 + 1;
        end
    endfunction

    localparam STAGES = log2(N);

    wire [N-1:0] G [0:STAGES];
    wire [N-1:0] P [0:STAGES];

    genvar i, stage;

    // Nível 0: bits individuais
    generate
        for (i=0; i<N; i=i+1) begin : gp0
            assign G[0][i] = A[i] & B[i];
            assign P[0][i] = A[i] ^ B[i];
        end
    endgenerate

    // Níveis seguintes: Sklansky tree
    generate
        for(stage=1; stage<=STAGES; stage=stage+1) begin : level_block
            for(i=0; i<N; i=i+1) begin : node_block
                if(i >= (1<<(stage-1))) begin
                    assign G[stage][i] = G[stage-1][i] | (P[stage-1][i] & G[stage-1][i-(1<<(stage-1))]);
                    assign P[stage][i] = P[stage-1][i] & P[stage-1][i-(1<<(stage-1))];
                end else begin
                    assign G[stage][i] = G[stage-1][i];
                    assign P[stage][i] = P[stage-1][i];
                end
            end
        end
    endgenerate

    // Carries
    wire [N:0] C;
    assign C[0] = Cin;
    generate
        for(i=0; i<N; i=i+1) begin : carry_gen
            assign C[i+1] = G[STAGES][i] | (P[STAGES][i] & Cin);
        end
    endgenerate

    assign Sum   = (A ^ B) ^ C[N-1:0];
    assign Cout  = C[N];
    assign overflow = C[N] ^ C[N-1]; // ✅ overflow correto

endmodule
