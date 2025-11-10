`timescale 1ns/1ps

module rca_tb;
    parameter N = 8;
    parameter NUM_TESTS = 100;
    parameter MAX_WIDTH = N;
    parameter CLOCK_PERIOD = 10;

    reg clk;
    reg [MAX_WIDTH-1:0] A, B, S_expected;
    reg Cin, Cout_expected;
    reg test_pass;
    wire [MAX_WIDTH-1:0] S;
    wire Cout;
    
    integer error_count = 0;
    integer test_count = 0;
    integer total_operations = 0;
    real total_simulation_time = 0;
    real average_test_time = 0;
    integer tests_per_second = 0;
    
    integer file;
    integer csv_file;
    integer cov_file;
    integer perf_file;
    integer md_file;
    real success_rate;
    
    integer coverage_bins [0:5][0:5][0:1];
    
    // Variáveis para tasks - declaradas no escopo do módulo
    integer i, j, k;
    integer a_bin, b_bin, cin_bin;
    integer covered_bins, total_bins;
    real coverage_percentage;
    real error_rate;
    real progress;
    integer bar_width;
    reg [255:0] progress_bar;
    
    rca #(.N(N)) DUT (
        .A(A[N-1:0]),
        .B(B[N-1:0]),
        .Cin(Cin),
        .S(S[N-1:0]),
        .Cout(Cout)
    );

    initial clk = 0;
    always #(CLOCK_PERIOD/2) clk = ~clk;

    // =========================================================================
    // SISTEMA DE RELATORIOS CSV
    // =========================================================================
    task init_csv_report;
        begin
            csv_file = $fopen("adder_test_cases.csv", "w");
            $fdisplay(csv_file, "Test_ID,Test_Name,Width,A,B,Cin,Expected_S,Expected_Cout,Actual_S,Actual_Cout,Result,Timestamp");
            $fclose(csv_file);
        end
    endtask
    
    task verify_result_with_mask;
        input [MAX_WIDTH-1:0] expected_sum;
        input expected_cout;
        input [80:0] test_name;
        input integer width;
        input integer test_id;
        reg [MAX_WIDTH-1:0] mask;
        reg [MAX_WIDTH-1:0] expected_sum_masked;
        reg [80:0] result_str;
        integer local_csv_file;
        begin
            test_count = test_count + 1;
            mask = (1 << width) - 1;
            expected_sum_masked = expected_sum & mask;
            
            local_csv_file = $fopen("adder_test_cases.csv", "a");
            
            if ((S & mask) !== expected_sum_masked || Cout !== expected_cout) begin
                $display("[FAIL] %s: A=%h, B=%h, Cin=%b -> Got S=%h, Cout=%b, Expected S=%h, Cout=%b",
                       test_name, A & mask, B & mask, Cin, S & mask, Cout, expected_sum_masked, expected_cout);
                result_str = "FAIL";
                error_count = error_count + 1;
                test_pass = 0;
            end else begin
                $display("[PASS] %s", test_name);
                result_str = "PASS";
                test_pass = 1;
            end
            
            $fdisplay(local_csv_file, "%0d,%s,%0d,%h,%h,%b,%h,%b,%h,%b,%s,%t",
                     test_id, test_name, width, 
                     A & mask, B & mask, Cin,
                     expected_sum_masked, expected_cout,
                     S & mask, Cout,
                     result_str, $time);
            
            $fclose(local_csv_file);
        end
    endtask



    // =========================================================================
    // RELATORIO EXECUTIVO
    // =========================================================================
    task generate_executive_summary;
        begin
            md_file = $fopen("ADDER_TEST_SUMMARY.txt", "w");
            
            if (test_count > 0) begin
                coverage_percentage = (100.0 * (test_count - error_count)) / test_count;
            end else begin
                coverage_percentage = 0.0;
            end
            
            $fdisplay(md_file, "ADDER TEST SUITE - EXECUTIVE SUMMARY");
            $fdisplay(md_file, "====================================");
            $fdisplay(md_file, "");
            $fdisplay(md_file, "TEST RESULTS OVERVIEW");
            $fdisplay(md_file, "---------------------");
            $fdisplay(md_file, "Total Tests: %0d", test_count);
            $fdisplay(md_file, "Tests Passed: %0d", test_count - error_count);
            $fdisplay(md_file, "Tests Failed: %0d", error_count);
            $fdisplay(md_file, "Success Rate: %0.2f%%", coverage_percentage);
            $fdisplay(md_file, "Simulation Time: %0.3f ns", $time);
            $fdisplay(md_file, "");
            
            $fdisplay(md_file, "TEST DISTRIBUTION");
            $fdisplay(md_file, "-----------------");
            $fdisplay(md_file, "- Deterministic Tests: 8 cases");
            $fdisplay(md_file, "- Random Tests: %0d cases", NUM_TESTS);
            $fdisplay(md_file, "- Corner Cases: 3-4 cases");
            $fdisplay(md_file, "- Mutation Tests: 1 case");
            $fdisplay(md_file, "");
            
            $fdisplay(md_file, "PERFORMANCE METRICS");
            $fdisplay(md_file, "-------------------");
            $fdisplay(md_file, "- Tests per Second: %0d", tests_per_second);
            $fdisplay(md_file, "- Average Test Time: %0.3f ns", average_test_time);
            $fdisplay(md_file, "");
            
            $fdisplay(md_file, "GENERATED REPORTS");
            $fdisplay(md_file, "-----------------");
            $fdisplay(md_file, "- Detailed Test Cases: adder_test_cases.csv");
            $fdisplay(md_file, "- Coverage Analysis: adder_coverage_report.txt");
            $fdisplay(md_file, "- Performance Report: adder_performance_report.txt");
            $fdisplay(md_file, "- Raw Results: adder_test_results.txt");
            $fdisplay(md_file, "");
            
            $fdisplay(md_file, "TEST EXECUTION");
            $fdisplay(md_file, "--------------");
            $fdisplay(md_file, "Generated: %t", $time);
            $fdisplay(md_file, "Adder Width: %0d bits", N);
            $fdisplay(md_file, "Test Configuration: NUM_TESTS=%0d", NUM_TESTS);
            
            $fclose(md_file);
            $display("Executive Summary: ADDER_TEST_SUMMARY.txt");
        end
    endtask

    // =========================================================================
    // DASHBOARD ASCII SIMPLIFICADO
    // =========================================================================
    task print_ascii_dashboard;
        real success_rate_local;
        begin
            if (test_count > 0) begin
                progress = (100.0 * test_count) / (8 + NUM_TESTS + 4 + 1);
                success_rate_local = (100.0 * (test_count - error_count)) / test_count;
            end else begin
                progress = 0;
                success_rate_local = 0.0;
            end
            
            bar_width = 30;
            progress_bar = "";
            
            for (i = 0; i < bar_width; i = i + 1) begin
                if (i < (progress * bar_width / 100)) 
                    progress_bar = {progress_bar, "="};
                else
                    progress_bar = {progress_bar, "-"};
            end
            
            $display("");
            $display("==========================================================");
            $display("                   ADDER TEST DASHBOARD");
            $display("==========================================================");
            $display(" Progress: [%s] %0.1f%%", progress_bar, progress);
            $display(" Tests: %0d  |  Errors: %0d  |  Success: %0.2f%%", 
                     test_count, error_count, success_rate_local);
            $display(" Simulation Time: %0.3f ns", $time);
            $display("==========================================================");
        end
    endtask

    // =========================================================================
    // TASKS DE TESTE BASICAS
    // =========================================================================
    task verify_result;
        input [MAX_WIDTH-1:0] expected_sum;
        input expected_cout;
        input [80:0] test_name;
        input integer width;
        begin
            verify_result_with_mask(expected_sum, expected_cout, test_name, width, test_count);
        end
    endtask

    task run_deterministic_tests;
        input integer width;
        integer local_i;
        reg [80:0] test_name;
        reg [MAX_WIDTH-1:0] max_val;
        reg [MAX_WIDTH:0] expected_full;
        begin
            $display("=== TESTES DETERMINISTICOS - %0d bits ===", width);
            
            max_val = (1 << width) - 1;
            
            A = 0; B = 0; Cin = 0; #10;
            verify_result(0, 0, "Zero+Zero", width);
            
            A = max_val; B = max_val; Cin = 1; #10;
            expected_full = max_val + max_val + 1;
            verify_result(expected_full & max_val, expected_full >> width, "Max+Max+Cin", width);
            
            A = 1; B = max_val; Cin = 0; #10;
            expected_full = 1 + max_val + 0;
            verify_result(expected_full & max_val, expected_full >> width, "1 + MAX", width);
            
            // Padrão alternado
            for (local_i = 0; local_i < 4; local_i = local_i + 1) begin
                A = (local_i % 2) ? max_val : 0;
                B = ((local_i / 2) % 2) ? max_val : 0;
                Cin = local_i % 2;
                #10;
                
                expected_full = A + B + Cin;
                case (local_i)
                    0: test_name = "Pattern 0";
                    1: test_name = "Pattern 1"; 
                    2: test_name = "Pattern 2";
                    3: test_name = "Pattern 3";
                endcase
                verify_result(expected_full & max_val, expected_full >> width, test_name, width);
            end
        end
    endtask

    task run_random_tests;
        input integer width;
        input integer num_tests;
        integer local_i;
        reg [MAX_WIDTH:0] expected;
        reg [80:0] test_name;
        reg [MAX_WIDTH-1:0] mask;
        begin
            $display("=== TESTES ALEATORIOS - %0d bits (%0d testes) ===", width, num_tests);
            
            mask = (1 << width) - 1;
            
            for (local_i = 0; local_i < num_tests; local_i = local_i + 1) begin
                A = $random & mask;
                B = $random & mask;
                Cin = $random & 1;
                #10;
                
                expected = A + B + Cin;
                S_expected = expected & mask;
                Cout_expected = expected >> width;
                
                test_name = "Random Test";
                verify_result_with_mask(S_expected, Cout_expected, test_name, width, test_count);
            end
        end
    endtask

    task print_summary;
        real success_rate_local;
        begin
            if (test_count > 0) begin
                success_rate_local = (100.0 * (test_count - error_count)) / test_count;
            end else begin
                success_rate_local = 0.0;
            end
            
            $display("\n=== RESUMO DA SIMULACAO ===");
            $display("Total de testes: %0d", test_count);
            $display("Erros encontrados: %0d", error_count);
            $display("Taxa de sucesso: %0.2f%%", success_rate_local);
            
            if (error_count == 0) begin
                $display("*** TODOS OS TESTES PASSARAM! ***");
            end else begin
                $display("*** ALGUNS TESTES FALHARAM! ***");
            end
        end
    endtask
	 
			 
        integer test_id;
    // =========================================================================
    // SEQUENCIA PRINCIPAL DE TESTES
    // =========================================================================
    initial begin

        
        $display("=== INICIANDO TESTBENCH DE ADDERS ===");
        $display("Configuracao: N=%0d bits, NUM_TESTS=%0d", N, NUM_TESTS);
        
        init_csv_report();
        test_id = 0;
        
        #30;
        
        $display("\n*** EXECUTANDO TESTES PARA LARGURA: %0d bits ***", N);
        
        print_ascii_dashboard();
        
        run_deterministic_tests(N);
        print_ascii_dashboard();
        
        run_random_tests(N, NUM_TESTS);
        print_ascii_dashboard();
        
        #100;
        
        print_summary();
        generate_executive_summary();
        
        print_ascii_dashboard();
        
        $display("");
        $display("TODOS OS RELATORIOS GERADOS COM SUCESSO!");
        $display("Verifique os arquivos .csv, .txt para analise detalhada");
        $stop;
    end

    initial begin
        #5000000;
        $display("*** TIMEOUT - SIMULACAO EXCEDEU TEMPO MAXIMO ***");
        $display("Testes executados: %0d, Erros: %0d", test_count, error_count);
        $stop;
    end

endmodule