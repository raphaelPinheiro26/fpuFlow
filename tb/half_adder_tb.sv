module half_adder_tb;

    // Declaração das entradas e saídas
    reg  A, B;         // Entradas 'A' e 'B'
    wire S, Co;        // Saídas

    // Instanciação do módulo Half Adder
    half_adder uut (
        .A(A), 
        .B(B), 
        .S(S),
        .Co(Co)
    );

    // Arquivo de log
    integer log;
    initial log = $fopen("half_adder_results.log", "w");

    // Geração do VCD para análise de power
    initial begin
        $dumpfile("half_adder.vcd");        // nome do arquivo VCD
        $dumpvars(0, half_adder_tb);        // gera VCD para todos sinais do testbench
    end

    // Teste das diferentes condições de comparação
    initial begin
        $display("Início dos testes");

        // Caso 1: A=0, B=0 → S=0, Co=0
        A = 0; B = 0; #20;
        assert (S == 0 && Co == 0)
            else begin
                $error("Falha no Caso 1: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 1: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 2: A=0, B=1 → S=1, Co=0
        A = 0; B = 1; #20;
        assert (S == 1 && Co == 0)
            else begin
                $error("Falha no Caso 2: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 2: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 3: A=1, B=0 → S=1, Co=0
        A = 1; B = 0; #20;
        assert (S == 1 && Co == 0)
            else begin
                $error("Falha no Caso 3: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 3: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 4: A=1, B=1 → S=0, Co=1
        A = 1; B = 1; #20;
        assert (S == 0 && Co == 1)
            else begin
                $error("Falha no Caso 4: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 4: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        $display("Testes concluídos.");
        $fclose(log);
        $stop;
    end

endmodule
