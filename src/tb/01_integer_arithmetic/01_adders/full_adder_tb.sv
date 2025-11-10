module full_adder_tb;

    // Declaração das entradas e saídas
    reg  A, B, Cin;         // Entradas 'A' e 'B'
    wire S, Cout;        // Saídas

    // Instanciação do módulo Half Adder
    full_adder uut (
        .A(A), 
        .B(B),
		  .Cin(Cin), 
        .S(S),
        .Cout(Cout)
    );

    // Arquivo de log
    integer log;
    initial log = $fopen("full_adder_results.log", "w");

    // Geração do VCD para análise de power
    initial begin
        $dumpfile("full_adder.vcd");        // nome do arquivo VCD
        $dumpvars(0, full_adder_tb);        // gera VCD para todos sinais do testbench
    end

    // Teste das diferentes condições do Full Adder
    initial begin
        $display("Início dos testes");

        // Caso 1: A=0, B=0, Cin=0 → S=0, Cout=0
        A = 0; B = 0; Cin = 0; #20;
        assert (S == 0 && Cout == 0)
            else begin
                $error("Falha no Caso 1: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 1: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 2: A=0, B=0, Cin=1 → S=1, Cout=0
        A = 0; B = 0; Cin = 1; #20;
        assert (S == 1 && Cout == 0)
            else begin
                $error("Falha no Caso 2: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 2: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 3: A=0, B=1, Cin=0 → S=1, Cout=0
        A = 0; B = 1; Cin = 0; #20;
        assert (S == 1 && Cout == 0)
            else begin
                $error("Falha no Caso 3: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 3: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 4: A=0, B=1, Cin=1 → S=0, Cout=1
        A = 0; B = 1; Cin = 1; #20;
        assert (S == 0 && Cout == 1)
            else begin
                $error("Falha no Caso 4: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 4: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 5: A=1, B=0, Cin=0 → S=1, Cout=0
        A = 1; B = 0; Cin = 0; #20;
        assert (S == 1 && Cout == 0)
            else begin
                $error("Falha no Caso 5: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 5: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 6: A=1, B=0, Cin=1 → S=0, Cout=1
        A = 1; B = 0; Cin = 1; #20;
        assert (S == 0 && Cout == 1)
            else begin
                $error("Falha no Caso 6: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 6: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 7: A=1, B=1, Cin=0 → S=0, Cout=1
        A = 1; B = 1; Cin = 0; #20;
        assert (S == 0 && Cout == 1)
            else begin
                $error("Falha no Caso 7: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 7: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        // Caso 8: A=1, B=1, Cin=1 → S=1, Cout=1
        A = 1; B = 1; Cin = 1; #20;
        assert (S == 1 && Cout == 1)
            else begin
                $error("Falha no Caso 8: S=%b, Cout=%b", S, Cout);
                $fdisplay(log, "Erro no Caso 8: A=%b B=%b Cin=%b S=%b Cout=%b", A, B, Cin, S, Cout);
            end

        $display("Testes concluídos.");
        $fclose(log);
        $stop;
    end


endmodule
