// ============================================================
// Module: adaptive_adder_wrapper
// Function: Seleciona automaticamente K baseado em N
// ============================================================

module adaptive_adder_wrapper #(
    parameter N = 16
)(
    input  wire CLOCK_50,
    input  wire rst,
    input  wire start,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire Cin,
    output wire [N-1:0] S,
    output wire Cout,
    output wire done
);

    // ============================================================
    // FÓRMULA DE OURO - CORRIGIDA
    // ============================================================
    localparam K_OPTIMAL = (N * 3 + 7) / 8;  // 37.5% de N
    
    // Debug automático - AGORA FUNCIONAL
    initial begin 
        $display("=== Adaptive Adder Configuration ===");
        $display("N=%0d, K_OPTIMAL=%0d", N, K_OPTIMAL);
        $display("Expected cycles: %0d", (N + K_OPTIMAL - 1) / K_OPTIMAL + 1);
    end

    carry_shifting_adder_optimized #(
        .N(N),
        .K(K_OPTIMAL)  // CORRIGIDO: era K_OPTIMAL, não K
    ) adder_instance (
        .CLOCK_50(CLOCK_50),
        .rst(rst),
        .start(start),
        .A(A),
        .B(B),
        .Cin(Cin),
        .S(S),
        .Cout(Cout),
        .done(done)
    );

endmodule

// ============================================================
// Module: carry_shifting_adder_optimized
// Function: Digit-serial adder com K bits por ciclo
// ============================================================

module carry_shifting_adder_optimized #(
    parameter N = 32,               // Tamanho total dos operandos
    parameter K = 4                 // Bits processados por ciclo (DIGIT_SIZE)
)(
    input  wire CLOCK_50,
    input  wire rst,
    input  wire start,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire Cin,
    output reg  [N-1:0] S,
    output reg  Cout,
    output reg  done
);

    // Cálculo de parâmetros derivados
    localparam NUM_ITERATIONS = (N + K - 1) / K;  // Arredonda para cima
    localparam COUNT_WIDTH = $clog2(NUM_ITERATIONS) + 1;
    
    // Debug interno
    initial begin
        $display("Carry Shifting Adder: N=%0d, K=%0d, Iterations=%0d", 
                 N, K, NUM_ITERATIONS);
    end
    
    // Registradores internos
    reg [N-1:0] A_reg, B_reg, S_reg;
    reg carry;
    reg [COUNT_WIDTH-1:0] count;
    reg active;

    // Wires para o adder de K bits
    wire [K:0] K_adder_result;      // [K] = carry_out, [K-1:0] = soma
    wire [K-1:0] current_A_bits;
    wire [K-1:0] current_B_bits;

    // Seleciona os K bits atuais
    assign current_A_bits = A_reg[K-1:0];
    assign current_B_bits = B_reg[K-1:0];

    // Instância do adder de K bits
    k_bit_adder #(.K(K)) K_ADDER (
        .A(current_A_bits),
        .B(current_B_bits),
        .Cin(carry),
        .S(K_adder_result[K-1:0]),
        .Cout(K_adder_result[K])
    );

    always @(posedge CLOCK_50 or posedge rst) begin
        if (rst) begin
            A_reg  <= 0;
            B_reg  <= 0;
            S_reg  <= 0;
            S      <= 0;
            carry  <= 0;
            Cout   <= 0;
            count  <= 0;
            done   <= 0;
            active <= 0;
        end else begin
            done <= 0;  // Done dura apenas 1 ciclo
            
            if (start && !active) begin
                A_reg  <= A;
                B_reg  <= B;
                S_reg  <= 0;
                carry  <= Cin;
                count  <= 0;
                active <= 1;
            end 
            else if (active) begin
                // Processa K bits de uma vez
                S_reg <= {K_adder_result[K-1:0], S_reg[N-1:K]};
                A_reg <= {{K{1'b0}}, A_reg[N-1:K]};
                B_reg <= {{K{1'b0}}, B_reg[N-1:K]};
                carry <= K_adder_result[K];  // Carry para próxima iteração
                count <= count + 1'b1;

                // Finalização - detecta uma iteração antes
                if (count == NUM_ITERATIONS - 1) begin
                    active <= 0;
                    // Registra saída no próximo ciclo
                    S <= {K_adder_result[K-1:0], S_reg[N-1:K]};
                    Cout <= K_adder_result[K];
                    done <= 1'b1;
                end
            end
        end
    end

endmodule

// ============================================================
// Module: k_bit_adder
// Function: Adder de K bits (Ripple Carry otimizado)
// ============================================================

module k_bit_adder #(
    parameter K = 4
)(
    input  wire [K-1:0] A,
    input  wire [K-1:0] B,
    input  wire Cin,
    output wire [K-1:0] S,
    output wire Cout
);

    wire [K:0] carry_chain;
    
    assign carry_chain[0] = Cin;
    
    genvar i;
    generate
        for (i = 0; i < K; i = i + 1) begin : bit_slice
            full_adder_corrected FA (
                .A(A[i]),
                .B(B[i]),
                .Cin(carry_chain[i]),
                .S(S[i]),
                .Cout(carry_chain[i+1])
            );
        end
    endgenerate
    
    assign Cout = carry_chain[K];

endmodule

// ============================================================
// Module: full_adder_corrected
// ============================================================

module full_adder_corrected (
    input  wire A,
    input  wire B,
    input  wire Cin,
    output wire S,
    output wire Cout
);
    assign S = A ^ B ^ Cin;
    assign Cout = (A & B) | (A & Cin) | (B & Cin);
endmodule