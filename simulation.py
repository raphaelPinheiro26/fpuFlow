# simulation.py
import os
import subprocess
import time
import shutil
from pathlib import Path
import config
import re

def debug_simulation_environment():
    """Verifica o ambiente de simulação"""
    print("\n🔍 DIAGNÓSTICO DO AMBIENTE DE SIMULAÇÃO")
    
    # Verifica ModelSim
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    
    print(f"✅ ModelSim directory: {config.MODELSIM_DIR.exists()}")
    print(f"✅ vsim.exe: {vsim_path.exists()}")
    print(f"✅ vlog.exe: {vlog_path.exists()}")
    
    # Verifica se há testbenches
    tb_count = len(list(config.TB_DIR.rglob("*_tb.v"))) + len(list(config.TB_DIR.rglob("*_tb.sv")))
    print(f"✅ Testbenches encontrados: {tb_count}")
    
    return vsim_path.exists() and vlog_path.exists()

def find_testbenches(module_name):
    """Encontra todos os testbenches para um módulo específico."""
    # Busca por todas as extensões possíveis
    patterns = [
        f"{module_name}_tb.v",      # Verilog puro
        f"{module_name}_tb.sv",     # SystemVerilog  
        f"{module_name}_tb*.v",     # Verilog com sufixo
        f"{module_name}_tb*.sv",    # SystemVerilog com sufixo
    ]
    
    tb_files = []
    for pattern in patterns:
        tb_files.extend(list(config.TB_DIR.glob(pattern)))
    
    # Remove duplicatas
    tb_files = list(set(tb_files))
    
    print(f"🔍 Testbenches encontrados para {module_name}: {[f.name for f in tb_files]}")
    return tb_files

def get_file_extension_type(file_path):
    """Determina o tipo de arquivo e como compilá-lo."""
    ext = file_path.suffix.lower()
    name = file_path.name.lower()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Análise heurística do conteúdo
    is_systemverilog = any(keyword in content for keyword in [
        'logic', 'bit', 'always_ff', 'always_comb', 'assert',
        'typedef', 'struct', 'enum', 'interface'
    ])
    
    if ext == '.sv' or is_systemverilog:
        return 'systemverilog'
    elif ext == '.v':
        return 'verilog'
    else:
        # Por padrão, trata como Verilog
        return 'verilog'

def compile_modelsim_project(project_path, module_name, rtl_files, tb_files):
    """Compila projeto para simulação no ModelSim com suporte híbrido."""
    
    print(f"🔨 Compilando para ModelSim: {module_name}")
    
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    if not vlog_path.exists():
        print(f"❌ vlog.exe não encontrado em: {vlog_path}")
        return False
    
    modelsim_work = project_path / "modelsim_work"
    modelsim_work.mkdir(exist_ok=True)
    
    # Executa vlib para criar library work
    cmd_lib = [str(config.MODELSIM_DIR / "vlib"), "work"]
    result_lib = subprocess.run(cmd_lib, capture_output=True, text=True, cwd=project_path)
    
    if result_lib.returncode != 0:
        print(f"❌ Falha ao criar library work: {result_lib.stderr}")
        return False
    
    # Compila arquivos RTL (sempre como Verilog)
    print("📦 Compilando arquivos RTL:")
    for rtl_file in rtl_files:
        file_type = get_file_extension_type(rtl_file)
        if file_type == 'systemverilog':
            cmd_compile = [
                str(config.MODELSIM_DIR / "vlog"),
                "-work", "work",
                "-sv",  # Compila como SystemVerilog
                str(rtl_file)
            ]
            type_label = " (como SV)"
        else:
            cmd_compile = [
                str(config.MODELSIM_DIR / "vlog"),
                "-work", "work",
                str(rtl_file)
            ]
            type_label = " (como Verilog)"
        
        print(f"   🔄 {rtl_file.name}{type_label}")
        result = subprocess.run(cmd_compile, capture_output=True, text=True, cwd=project_path)
        
        if result.returncode == 0:
            print(f"   ✅ {rtl_file.name}")
        else:
            print(f"   ❌ {rtl_file.name}")
            if result.stderr:
                print(f"      Erro: {result.stderr}")
            return False
    
    # Compila testbenches (detecta automaticamente o tipo)
    print("📦 Compilando testbenches:")
    for tb_file in tb_files:
        file_type = get_file_extension_type(tb_file)
        
        if file_type == 'systemverilog':
            # Tenta primeiro como SystemVerilog
            cmd_compile = [
                str(config.MODELSIM_DIR / "vlog"),
                "-work", "work",
                "-sv",  # Flag para SystemVerilog
                str(tb_file)
            ]
            type_label = " (como SystemVerilog)"
        else:
            # Compila como Verilog tradicional
            cmd_compile = [
                str(config.MODELSIM_DIR / "vlog"),
                "-work", "work",
                str(tb_file)
            ]
            type_label = " (como Verilog)"
        
        print(f"   🔄 {tb_file.name}{type_label}")
        result = subprocess.run(cmd_compile, capture_output=True, text=True, cwd=project_path)
        
        if result.returncode == 0:
            print(f"   ✅ {tb_file.name}")
        else:
            # Se falhou, tenta abordagem alternativa
            print(f"   ⚠️  Primeira tentativa falhou, tentando abordagem alternativa...")
            
            if file_type == 'systemverilog':
                # Tenta como Verilog puro (pode funcionar para SV simples)
                cmd_compile_alt = [
                    str(config.MODELSIM_DIR / "vlog"),
                    "-work", "work",
                    str(tb_file)  # Sem flag -sv
                ]
                print(f"   🔄 Tentativa alternativa: {tb_file.name} (como Verilog)")
                result_alt = subprocess.run(cmd_compile_alt, capture_output=True, text=True, cwd=project_path)
                
                if result_alt.returncode == 0:
                    print(f"   ✅ {tb_file.name} (compilado como Verilog)")
                else:
                    print(f"   ❌ {tb_file.name}")
                    if result_alt.stderr:
                        print(f"      Erro: {result_alt.stderr}")
                    return False
            else:
                print(f"   ❌ {tb_file.name}")
                if result.stderr:
                    print(f"      Erro: {result.stderr}")
                return False
    
    print("✅ Todos os arquivos compilados com sucesso!")
    return True

def auto_convert_if_needed(file_path):
    """Converte automaticamente SystemVerilog para Verilog se necessário."""
    if get_file_extension_type(file_path) == 'systemverilog':
        print(f"🔄 Detectado SystemVerilog: {file_path.name}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Conversões básicas (expandível conforme necessidade)
        conversions = [
            (r'\blogic\b', 'reg'),
            (r'\bbit\b', 'reg'),
            (r'\balways_ff\b', 'always'),
            (r'\balways_comb\b', 'always'),
            (r'\balways_latch\b', 'always'),
            (r'\bassert\s*\(([^)]+)\)\s*', 'if (!(\\1)) begin $display("ASSERT FAILED"); $stop; end'),
        ]
        
        new_content = content
        for pattern, replacement in conversions:
            new_content = re.sub(pattern, replacement, new_content)
        
        # Cria arquivo convertido
        converted_path = file_path.parent / f"{file_path.stem}_converted.v"
        with open(converted_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Convertido: {file_path.name} -> {converted_path.name}")
        return converted_path
    
    return file_path

# simulation.py - atualize a função run_modelsim_simulation

def run_modelsim_simulation(project_path, tb_name, simulation_time="100ns"):
    """Executa simulação no ModelSim com correções."""
    
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    if not vsim_path.exists():
        print(f"❌ vsim.exe não encontrado em: {vsim_path}")
        return None
    
    # Cria script de simulação mais simples e confiável
    do_file = project_path / "simulate.do"
    
    with open(do_file, "w") as f:
        f.write("# Script de simulação automática ModelSim\n")
        f.write("onbreak {resume}\n")
        f.write("onerror {exit -code 1}\n")
        f.write("set NumericStdNoWarnings 1\n")
        f.write("set StdArithNoWarnings 1\n")
        f.write(f"vsim -voptargs=+acc -t 1ns {tb_name}\n")
        f.write("run -all\n")
        f.write("quit -sim\n")
        f.write("exit\n")
    
    print(f"🎯 Iniciando simulação: {tb_name}")
    
    cmd = [
        str(vsim_path),
        "-c",  # Modo console
        "-do", "simulate.do"
    ]
    
    try:
        # Aumenta timeout para 60 segundos
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=project_path,
            timeout=60
        )
        
        # Salva log
        log_file = project_path / f"simulation_{tb_name}.log"
        with open(log_file, "w", encoding='utf-8') as f:
            f.write("STDOUT:\n" + result.stdout)
            if result.stderr:
                f.write("\nSTDERR:\n" + result.stderr)
        
        print(f"📄 Log salvo: {log_file.name}")
        
        # Analisa resultado
        if result.returncode == 0:
            print(f"✅ Simulação {tb_name} concluída")
            return extract_simulation_results(log_file, tb_name)
        else:
            print(f"❌ Erro na simulação (code: {result.returncode})")
            return {
                "TB_Name": tb_name,
                "Simulation_Status": "FAILED",
                "Warnings": 0,
                "Errors": 1
            }
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: Simulação excedeu 60 segundos")
        return {
            "TB_Name": tb_name,
            "Simulation_Status": "TIMEOUT",
            "Warnings": 0,
            "Errors": 1
        }

def extract_simulation_results(log_file, tb_name):
    """Extrai resultados da simulação do arquivo de log."""
    if not log_file.exists():
        return None
    
    with open(log_file, "r") as f:
        content = f.read()
    
    results = {
        "TB_Name": tb_name,
        "Simulation_Time": "",
        "Warnings": 0,
        "Errors": 0,
        "Total_Tests": 0,
        "Tests_Passed": 0,
        "Tests_Failed": 0,
        "Success_Rate": 0.0,
        "Simulation_Status": "Unknown"
    }
    
    # Conta warnings e errors do ModelSim
    results["Warnings"] = content.count("# ** Warning: ")
    results["Errors"] = content.count("# ** Error: ")
    
    # Procura totais de testes (padrão do seu RCA)
    total_match = re.search(r"Total de testes:\s*(\d+)", content)
    if total_match:
        results["Total_Tests"] = int(total_match.group(1))
    
    errors_match = re.search(r"Erros encontrados:\s*(\d+)", content)
    if errors_match:
        results["Tests_Failed"] = int(errors_match.group(1))
        results["Tests_Passed"] = results["Total_Tests"] - results["Tests_Failed"]
    
    # Procura taxa de sucesso
    success_match = re.search(r"Taxa de sucesso:\s*([\d\.]+)%", content)
    if success_match:
        results["Success_Rate"] = float(success_match.group(1))
    
    # Status baseado no resultado
    if "TODOS OS TESTES PASSARAM" in content:
        results["Simulation_Status"] = "ALL_PASSED"
    elif results["Tests_Failed"] > 0:
        results["Simulation_Status"] = "SOME_FAILED"
    elif results["Total_Tests"] > 0:
        results["Simulation_Status"] = "ALL_PASSED"
    
    return results
def copy_tb_to_project(module_name, project_path, tb_files):
    """Copia testbenches para a pasta do projeto."""
    copied_tbs = []
    for tb_file in tb_files:
        dst_file = project_path / tb_file.name
        shutil.copy(tb_file, dst_file)
        copied_tbs.append(dst_file)
        print(f"📄 Testbench copiado: {tb_file.name}")
    
    return copied_tbs

def set_parameter_in_tb(tb_file, param_name, value):
    """Define parâmetro N no testbench (similar à função do compile.py)."""
    if not tb_file.exists():
        print(f"❌ Testbench {tb_file} não encontrado.")
        return False

    with open(tb_file, "r") as f:
        content = f.read()

    # Padrões para encontrar parâmetros em testbenches
    patterns = [
        rf"(parameter\s+{param_name}\s*=\s*)(\d+)",
        rf"(localparam\s+{param_name}\s*=\s*)(\d+)",
        rf"({param_name}\s*=\s*)(\d+)"
    ]

    for pattern in patterns:
        new_content, count = re.subn(pattern, r"\g<1>" + str(value), content)
        if count > 0:
            with open(tb_file, "w") as f:
                f.write(new_content)
            print(f"🔧 Parâmetro {param_name} atualizado para {value} em {tb_file.name}")
            return True

    print(f"⚠️ Parâmetro '{param_name}' não encontrado em {tb_file.name}")
    return False

# simulation.py - adicione estas funções de debug

def debug_simulation_issue(project_path, tb_name):
    """Faz debug detalhado de problemas na simulação."""
    print(f"\n🔍 DEBUG Simulação: {tb_name}")
    
    # Verifica se o executável foi compilado
    work_dir = project_path / "modelsim_work"
    if not work_dir.exists():
        print("❌ Diretório 'modelsim_work' não encontrado")
        return
    
    # Lista arquivos compilados
    print("📁 Arquivos no modelsim_work:")
    for file in work_dir.rglob("*"):
        print(f"   {file.relative_to(work_dir)}")
    
    # Verifica se o módulo existe na library
    cmd_check = [
        str(config.MODELSIM_DIR / "vdir"),
        "-lib", "work"
    ]
    
    result = subprocess.run(cmd_check, capture_output=True, text=True, cwd=project_path)
    print(f"📋 Módulos na library 'work':")
    print(result.stdout if result.stdout else "   (vazia)")
    
    # Testa simulação simplificada
    print("🧪 Testando simulação simplificada...")
    do_simple = project_path / "debug_simple.do"
    
    with open(do_simple, "w") as f:
        f.write(f"vsim -c {tb_name}\n")
        f.write("run 10ns\n")
        f.write("quit -sim\n")
    
    cmd_simple = [str(config.MODELSIM_DIR / "vsim"), "-do", "debug_simple.do"]
    
    try:
        result_simple = subprocess.run(
            cmd_simple, 
            capture_output=True, 
            text=True, 
            cwd=project_path,
            timeout=10
        )
        print("✅ Simulação simplificada executada")
        if result_simple.stdout:
            print("   Saída:", result_simple.stdout[-200:])  # Últimos 200 chars
    except subprocess.TimeoutExpired:
        print("❌ Simulação simplificada também travou")

def create_enhanced_simulation_script(project_path, tb_name):
    """Cria script de simulação mais robusto."""
    do_file = project_path / "simulate_enhanced.do"
    
    with open(do_file, "w") as f:
        f.write("# Script de simulação robusto\n")
        f.write("echo \"Iniciando simulação...\"\n")
        f.write("onbreak {resume}\n")
        f.write("onerror {exit -code 1}\n")
        f.write("set NumericStdNoWarnings 1\n")
        f.write("set StdArithNoWarnings 1\n")
        f.write(f"vsim -voptargs=\"+acc\" -t 1ns {tb_name}\n")
        f.write("echo \"Módulo carregado, executando...\"\n")
        f.write("run -all\n")
        f.write("echo \"Simulação concluída\"\n")
        f.write("quit -sim\n")
        f.write("echo \"Finalizado\"\n")
        f.write("exit\n")
    
    return do_file

# simulation.py - adicione estas funções

def organize_simulation_files(project_path, out_dir, tb_name, N="default"):
    """Organiza arquivos de simulação dentro da pasta output_files correspondente."""
    
    # Cria diretório para simulação dentro do output_files
    sim_dir = out_dir / "simulation"
    sim_dir.mkdir(exist_ok=True)
    
    # Arquivos a serem movidos
    simulation_files = [
        f"simulation_{tb_name}.log",
        f"{tb_name}.vcd",  # Waveform
        f"{tb_name}_results.log",  # Log do testbench
        "simulate.do",
        "compile.do",
        "modelsim_work"  # Diretório de trabalho
    ]
    
    # Arquivos de relatório gerados pelo testbench (como no seu RCA)
    report_patterns = [
        "*_SUMMARY.txt",
        "*_report.csv", 
        "*_results.csv",
        "*_dashboard.txt"
    ]
    
    moved_files = []
    
    for file_pattern in simulation_files + report_patterns:
        for file_path in project_path.glob(file_pattern):
            if file_path.exists():
                # Para diretórios, usa copytree
                if file_path.is_dir():
                    dst_path = sim_dir / f"{file_path.name}_N{N}"
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(file_path, dst_path)
                else:
                    # Para arquivos, copia com sufixo N
                    new_name = f"{file_path.stem}_N{N}{file_path.suffix}"
                    dst_path = sim_dir / new_name
                    shutil.copy2(file_path, dst_path)
                
                moved_files.append(dst_path.name)
    
    if moved_files:
        print(f"📁 Arquivos de simulação organizados em: {sim_dir.name}")
        print(f"   📄 {', '.join(moved_files[:5])}{'...' if len(moved_files) > 5 else ''}")
    
    return sim_dir

def run_modelsim_simulation_with_organization(project_path, tb_name, out_dir, N="default"):
    """Executa simulação e organiza os arquivos no output_dir correspondente."""
    
    # Executa a simulação normal
    sim_results = run_modelsim_simulation(project_path, tb_name)
    
    # Organiza os arquivos de simulação
    sim_dir = organize_simulation_files(project_path, out_dir, tb_name, N)
    
    # Adiciona informação do diretório aos resultados
    if sim_results:
        sim_results["Simulation_Directory"] = str(sim_dir.relative_to(project_path))
    
    return sim_results