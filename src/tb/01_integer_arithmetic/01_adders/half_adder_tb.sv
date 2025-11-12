module half_adder_tb;

    // Declaração das entradas e saídas
    reg  CLOCK_50;     // Clock de 50MHz
    reg  A, B;         // Entradas 'A' e 'B'
    wire S, Co;        // Saídas

    // Instanciação do módulo Half Adder
    half_adder uut (
        .CLOCK_50(CLOCK_50),
        .A(A), 
        .B(B), 
        .S(S),
        .Co(Co)
    );

    // Geração do clock (50 MHz = 20ns period)
    always #10 CLOCK_50 = ~CLOCK_50;

    // Arquivo de log
    integer log;
    initial log = $fopen("half_adder_results.log", "w");

    // Geração do VCD para análise de power
    initial begin
        $dumpfile("half_adder.vcd");        // nome do arquivo VCD
        $dumpvars(0, half_adder_tb);        // gera VCD para todos sinais do testbench
    end

    // Inicialização
    initial begin
        CLOCK_50 = 0;
        A = 0;
        B = 0;
    end

    // Teste das diferentes condições de comparação
    initial begin
        $display("Início dos testes");

        // Espera um pouco para estabilizar
        #100;

        // Caso 1: A=0, B=0 → S=0, Co=0
        A = 0; B = 0; #100;
        assert (S == 0 && Co == 0)
            else begin
                $error("Falha no Caso 1: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 1: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 2: A=0, B=1 → S=1, Co=0
        A = 0; B = 1; #100;
        assert (S == 1 && Co == 0)
            else begin
                $error("Falha no Caso 2: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 2: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 3: A=1, B=0 → S=1, Co=0
        A = 1; B = 0; #100;
        assert (S == 1 && Co == 0)
            else begin
                $error("Falha no Caso 3: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 3: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        // Caso 4: A=1, B=1 → S=0, Co=1
        A = 1; B = 1; #100;
        assert (S == 0 && Co == 1)
            else begin
                $error("Falha no Caso 4: S=%b, Co=%b", S, Co);
                $fdisplay(log, "Erro no Caso 4: A=%b B=%b S=%b Co=%b", A, B, S, Co);
            end

        $display("Testes concluídos com sucesso!");
        $fdisplay(log, "Todos os testes passaram!");
        $fclose(log);
        $display("Simulação finalizada em %t", $time);
        $finish;
    end

endmodule