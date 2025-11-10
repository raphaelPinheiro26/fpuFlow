module full_adder_tb;

    // Declaração das entradas e saídas
    reg  A, B, Cin;    // Entradas
    wire S, Cout;      // Saídas

    // Instanciação do módulo Full Adder
    full_adder uut (
        .A(A), 
        .B(B),
        .Cin(Cin), 
        .S(S),
        .Cout(Cout)
    );

    // Arquivo de log
    integer log;
    integer tests_passed, tests_failed, total_tests;

    // Geração do VCD
    initial begin
        $dumpfile("full_adder.vcd");
        $dumpvars(0, full_adder_tb);
        log = $fopen("full_adder_results.log", "w");
        tests_passed = 0;
        tests_failed = 0;
        total_tests = 0;
    end

    // Função para verificar resultados
    task check_result;
        input [3:0] test_num;
        input expected_S, expected_Cout;
        input [2:0] A_val, B_val, Cin_val;
        begin
            total_tests = total_tests + 1;
            if (S === expected_S && Cout === expected_Cout) begin
                tests_passed = tests_passed + 1;
                $display("[PASS] Caso %0d: A=%b, B=%b, Cin=%b -> S=%b, Cout=%b", 
                         test_num, A_val, B_val, Cin_val, S, Cout);
                $fdisplay(log, "PASS: Caso %0d: A=%b B=%b Cin=%b S=%b Cout=%b", 
                          test_num, A_val, B_val, Cin_val, S, Cout);
            end else begin
                tests_failed = tests_failed + 1;
                $display("[FAIL] Caso %0d: A=%b, B=%b, Cin=%b -> Esperado: S=%b, Cout=%b | Obtido: S=%b, Cout=%b", 
                         test_num, A_val, B_val, Cin_val, expected_S, expected_Cout, S, Cout);
                $fdisplay(log, "FAIL: Caso %0d: A=%b B=%b Cin=%b Esperado: S=%b Cout=%b | Obtido: S=%b Cout=%b", 
                          test_num, A_val, B_val, Cin_val, expected_S, expected_Cout, S, Cout);
            end
        end
    endtask

    // Teste das diferentes condições do Full Adder
    initial begin
        $display("=== INICIANDO TESTBENCH FULL ADDER ===");
        $display("Início dos testes");

        // Caso 1: A=0, B=0, Cin=0 → S=0, Cout=0
        A = 0; B = 0; Cin = 0; #20;
        check_result(1, 1'b0, 1'b0, 3'b000, 3'b000, 3'b000);

        // Caso 2: A=0, B=0, Cin=1 → S=1, Cout=0
        A = 0; B = 0; Cin = 1; #20;
        check_result(2, 1'b1, 1'b0, 3'b000, 3'b000, 3'b001);

        // Caso 3: A=0, B=1, Cin=0 → S=1, Cout=0
        A = 0; B = 1; Cin = 0; #20;
        check_result(3, 1'b1, 1'b0, 3'b000, 3'b001, 3'b000);

        // Caso 4: A=0, B=1, Cin=1 → S=0, Cout=1
        A = 0; B = 1; Cin = 1; #20;
        check_result(4, 1'b0, 1'b1, 3'b000, 3'b001, 3'b001);

        // Caso 5: A=1, B=0, Cin=0 → S=1, Cout=0
        A = 1; B = 0; Cin = 0; #20;
        check_result(5, 1'b1, 1'b0, 3'b001, 3'b000, 3'b000);

        // Caso 6: A=1, B=0, Cin=1 → S=0, Cout=1
        A = 1; B = 0; Cin = 1; #20;
        check_result(6, 1'b0, 1'b1, 3'b001, 3'b000, 3'b001);

        // Caso 7: A=1, B=1, Cin=0 → S=0, Cout=1
        A = 1; B = 1; Cin = 0; #20;
        check_result(7, 1'b0, 1'b1, 3'b001, 3'b001, 3'b000);

        // Caso 8: A=1, B=1, Cin=1 → S=1, Cout=1
        A = 1; B = 1; Cin = 1; #20;
        check_result(8, 1'b1, 1'b1, 3'b001, 3'b001, 3'b001);

        // Finalização
        #10;
        $display("\n=== RESUMO FULL ADDER ===");
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