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
    integer tests_passed, tests_failed, total_tests;

    // Geração do VCD para análise de power
    initial begin
        $dumpfile("half_adder.vcd");
        $dumpvars(0, half_adder_tb);
        log = $fopen("half_adder_results.log", "w");
        tests_passed = 0;
        tests_failed = 0;
        total_tests = 0;
    end

    // Função para verificar resultados
    task check_result;
        input [3:0] test_num;
        input expected_S, expected_Co;
        input [1:0] A_val, B_val;
        begin
            total_tests = total_tests + 1;
            if (S === expected_S && Co === expected_Co) begin
                tests_passed = tests_passed + 1;
                $display("[PASS] Caso %0d: A=%b, B=%b -> S=%b, Co=%b", 
                         test_num, A_val, B_val, S, Co);
                $fdisplay(log, "PASS: Caso %0d: A=%b B=%b S=%b Co=%b", 
                          test_num, A_val, B_val, S, Co);
            end else begin
                tests_failed = tests_failed + 1;
                $display("[FAIL] Caso %0d: A=%b, B=%b -> Esperado: S=%b, Co=%b | Obtido: S=%b, Co=%b", 
                         test_num, A_val, B_val, expected_S, expected_Co, S, Co);
                $fdisplay(log, "FAIL: Caso %0d: A=%b B=%b Esperado: S=%b Co=%b | Obtido: S=%b Co=%b", 
                          test_num, A_val, B_val, expected_S, expected_Co, S, Co);
            end
        end
    endtask

    // Teste das diferentes condições
    initial begin
        $display("=== INICIANDO TESTBENCH HALF ADDER ===");
        $display("Início dos testes");

        // Caso 1: A=0, B=0 → S=0, Co=0
        A = 0; B = 0; #20;
        check_result(1, 1'b0, 1'b0, 2'b00, 2'b00);

        // Caso 2: A=0, B=1 → S=1, Co=0
        A = 0; B = 1; #20;
        check_result(2, 1'b1, 1'b0, 2'b00, 2'b01);

        // Caso 3: A=1, B=0 → S=1, Co=0
        A = 1; B = 0; #20;
        check_result(3, 1'b1, 1'b0, 2'b01, 2'b00);

        // Caso 4: A=1, B=1 → S=0, Co=1
        A = 1; B = 1; #20;
        check_result(4, 1'b0, 1'b1, 2'b01, 2'b01);

        // Finalização
        #10;
        $display("\n=== RESUMO HALF ADDER ===");
        $display("Total de testes: %0d", total_tests);
        $display("Testes passados: %0d", tests_passed);
        $display("Testes falhados: %0d", tests_failed);
        $display("Taxa de sucesso: %.2f%%", (tests_passed * 100.0) / total_tests);
        
        $fdisplay(log, "\n=== RESUMO ===");
        $fdisplay(log, "Total: %0d | Passaram: %0d | Falharam: %0d | Sucesso: %.2f%%",
                  total_tests, tests_passed, tests_failed, (tests_passed * 100.0) / total_tests);
        
        if (tests_failed == 0) begin
            $display("*** TODOS OS TESTES PASSARAM! ***");
            $fdisplay(log, "RESULTADO: TODOS OS TESTES PASSARAM");
        end else begin
            $display("*** ALGUNS TESTES FALHARAM! ***");
            $fdisplay(log, "RESULTADO: ALGUNS TESTES FALHARAM");
        end
        
        $fclose(log);
        $finish;
    end

endmodule