module bit_serial_adder #(
    parameter N = 8
)(
    input  wire CLOCK_50,   // clock físico da FPGA
    input wire rst,
    input wire start,
    input wire [N-1:0] A,
    input wire [N-1:0] B,
    output reg [N-1:0] S,
    output reg Cout,
    output reg done
);

    reg [$clog2(N):0] count;
    reg carry;
    wire sum_bit, carry_out;

    full_adder FA (
        .A(A[count]),
        .B(B[count]),
        .Cin(carry),
        .S(sum_bit),
        .Cout(carry_out)
    );

    reg busy;

    always @(posedge CLOCK_50 or posedge rst) begin
        if (rst) begin
            S     <= 0;
            Cout  <= 0;
            count <= 0;
            carry <= 0;
            done  <= 0;
            busy  <= 0;
        end else begin
            if (start && !busy) begin
                // inicia nova operação
                S     <= 0;
                Cout  <= 0;
                count <= 0;
                carry <= 0;
                done  <= 0;
                busy  <= 1;
            end else if (busy) begin
                if (count < N) begin
                    S[count] <= sum_bit;
                    carry    <= carry_out;
                    count    <= count + 1;
                end else begin
                    Cout <= carry;
                    done <= 1;
                    busy <= 0;  // operação finalizada
                end
            end
        end
    end

endmodule
