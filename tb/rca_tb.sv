module rca_tb;

    parameter N = 8;

    // sinais de teste
    reg  [N-1:0] A, B;
    reg  Cin;
    reg  CLOCK_50;       // clock fictício apenas para a instância
    wire [N-1:0] S;
    wire Cout;

    // instância do RCA
    rca #(
        .N(N)
    ) uut (
        .CLOCK_50(CLOCK_50),
        .A(A),
        .B(B),
        .Cin(Cin),
        .S(S),
        .Cout(Cout)
    );
	 
	 // clock opcional (fictício, não afeta combinacional)
    initial CLOCK_50 = 0;
    always #10 CLOCK_50 = ~CLOCK_50;  // 50 MHz, só para ter transição
	 
	 

    // Arquivo de log
    integer log;
    initial log = $fopen("rca_results.log", "w");

    // Geração do VCD
    initial begin
        $dumpfile("rca.vcd");
        $dumpvars(0, rca_tb);
    end

    // Testes automáticos
    initial begin
        $display("Início dos testes do RCA 8 bits");

        // Caso 1: 0 + 0
        A = 8'b00000000; B = 8'b00000000; Cin = 0; #20;
        assert (S == 8'b00000000 && Cout == 0)
            else begin
                $error("Erro Caso 1: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro Caso 1: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 2: 1 + 1 sem carry
        A = 8'b00000001; B = 8'b00000001; Cin = 0; #20;
        assert (S == 8'b00000010 && Cout == 0)
            else begin
                $error("Erro Caso 2: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro Caso 2: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 3: 255 + 1 → overflow
        A = 8'b11111111; B = 8'b00000001; Cin = 0; #20;
        assert (S == 8'b00000000 && Cout == 1)
            else begin
                $error("Erro Caso 3: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro Caso 3: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 4: 170 + 85 = 255
        A = 8'b10101010; B = 8'b01010101; Cin = 0; #20;
        assert (S == 8'b11111111 && Cout == 0)
            else begin
                $error("Erro Caso 4: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro Caso 4: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        $display("Testes concluídos.");
        $fclose(log);
        $stop;
    end

endmodule
