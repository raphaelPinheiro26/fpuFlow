// ============================================================
// Module: carry_shifting_adder
// Function: Bit-serial adder com deslocamento e suporte a Cin
// ============================================================

module carry_shifting_adder #(
    parameter N = 8
)(
    input  wire CLOCK_50,
    input  wire rst,
    input  wire start,
    input  wire [N-1:0] A,
    input  wire [N-1:0] B,
    input  wire Cin,              // Novo: entrada de carry inicial
    output reg  [N-1:0] S,
    output reg  Cout,
    output reg  done
);

    // Registradores internos
    reg [N-1:0] A_reg, B_reg, S_reg;
    reg carry;
    reg [$clog2(N):0] count;
    reg active;

    // Fios do somador de 1 bit
    wire sum_bit;
    wire carry_out;

    // Instância do somador de 1 bit
    full_adder FA (
        .A   (A_reg[0]),
        .B   (B_reg[0]),
        .Cin (carry),
        .S   (sum_bit),
        .Cout(carry_out)
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
            if (start && !active) begin
                A_reg  <= A;
                B_reg  <= B;
                S_reg  <= 0;
                carry  <= Cin;        // Usa carry inicial
                count  <= 0;
                done   <= 0;
                active <= 1;
            end 
            else if (active) begin
                // Soma bit a bit com deslocamento
                S_reg <= {sum_bit, S_reg[N-1:1]};
                A_reg <= {1'b0, A_reg[N-1:1]};
                B_reg <= {1'b0, B_reg[N-1:1]};
                carry <= carry_out;
                count <= count + 1'b1;

                // Quando terminar todos os bits
                if (count == N-1) begin
                    S     <= {sum_bit, S_reg[N-1:1]};
                    Cout  <= carry_out;
                    done  <= 1;
                    active <= 0;
                end
            end
        end
    end

endmodule
