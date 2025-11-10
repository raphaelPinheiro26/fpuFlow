# simulation.py
"""
SIMULAÇÃO MODELSIM E GERENCIAMENTO DE TESTBENCHES

Responsável por:
- Compilação e execução de simulações ModelSim
- Gerenciamento de testbenches
- Extração e análise de resultados
- Organização de arquivos de simulação
"""

import os
import subprocess
import time
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import config

# =============================================================================
# TIPOS DE DADOS
# =============================================================================

SimulationResult = Dict[str, any]

# =============================================================================
# VERIFICAÇÃO DE AMBIENTE
# =============================================================================

def verify_simulation_environment() -> bool:
    """Verifica se o ModelSim está instalado e acessível."""
    print("🔍 Verificando ambiente de simulação...")
    
    if not config.MODELSIM_DIR.exists():
        print("❌ ModelSim não encontrado.")
        return False
    
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    
    if not all([vsim_path.exists(), vlog_path.exists()]):
        print("❌ Arquivos do ModelSim não encontrados.")
        return False
    
    print("✅ ModelSim detectado e pronto")
    return True

# =============================================================================
# GERENCIAMENTO DE TESTBENCHES
# =============================================================================

def find_testbenches(module_name: str) -> List[Path]:
    """Encontra todos os testbenches para um módulo específico."""
    patterns = [
        f"*{module_name}*_tb.v",
        f"*{module_name}*_tb.sv", 
        f"*{module_name}*tb.v",
        f"*{module_name}*tb.sv",
        f"*tb_{module_name}*.v",
        f"*tb_{module_name}*.sv",
    ]
    
    tb_files = []
    for pattern in patterns:
        tb_files.extend(list(config.TB_DIR.rglob(pattern)))
    
    # Remove duplicatas e filtra apenas arquivos
    tb_files = list(set([f for f in tb_files if f.is_file()]))
    
    print(f"🔍 Testbenches para {module_name}: {[f.name for f in tb_files]}")
    return tb_files

def copy_tb_to_project(module_name: str, project_path: Path, tb_files: List[Path]) -> List[Path]:
    """Copia testbenches para a pasta do projeto."""
    copied_tbs = []
    for tb_file in tb_files:
        dst_file = project_path / tb_file.name
        shutil.copy(tb_file, dst_file)
        copied_tbs.append(dst_file)
        print(f"📄 Testbench copiado: {tb_file.name}")
    
    return copied_tbs

def set_parameter_in_tb(tb_file: Path, param_name: str, value: int) -> bool:
    """Define parâmetro em testbench."""
    if not tb_file.exists():
        print(f"❌ Testbench {tb_file} não encontrado.")
        return False

    with open(tb_file, "r") as f:
        content = f.read()

    # Padrões para encontrar parâmetros
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
            print(f"🔧 Parâmetro {param_name} = {value} em {tb_file.name}")
            return True

    print(f"⚠️ Parâmetro '{param_name}' não encontrado")
    return False

# =============================================================================
# DETECÇÃO DE TIPO DE ARQUIVO
# =============================================================================

def get_file_extension_type(file_path: Path) -> str:
    """Determina se arquivo é Verilog ou SystemVerilog."""
    ext = file_path.suffix.lower()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Análise heurística do conteúdo
    sv_keywords = ['logic', 'bit', 'always_ff', 'always_comb', 'assert',
                   'typedef', 'struct', 'enum', 'interface']
    
    is_systemverilog = any(keyword in content for keyword in sv_keywords)
    
    if ext == '.sv' or is_systemverilog:
        return 'systemverilog'
    else:
        return 'verilog'

# =============================================================================
# COMPILAÇÃO MODELSIM
# =============================================================================

def compile_modelsim_project(project_path: Path, module_name: str, 
                           rtl_files: List[Path], tb_files: List[Path]) -> bool:
    """Compila projeto para simulação no ModelSim."""
    print(f"🔨 Compilando para ModelSim: {module_name}")
    
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    if not vlog_path.exists():
        print(f"❌ vlog.exe não encontrado")
        return False
    
    # Prepara ambiente
    _prepare_modelsim_environment(project_path)
    
    # Compila todos os arquivos
    all_files = rtl_files + tb_files
    compile_success = _compile_files(project_path, all_files)
    
    if compile_success:
        _list_compiled_modules(project_path)
    
    return compile_success

def _prepare_modelsim_environment(project_path: Path):
    """Prepara ambiente ModelSim (library work)."""
    modelsim_work = project_path / "modelsim_work"
    
    # Limpa trabalho anterior
    if modelsim_work.exists():
        shutil.rmtree(modelsim_work)
    modelsim_work.mkdir(exist_ok=True)
    
    # Cria library work
    cmd_lib = [str(config.MODELSIM_DIR / "vlib"), "work"]
    result = subprocess.run(cmd_lib, capture_output=True, text=True, cwd=project_path)
    
    if result.returncode == 0:
        print("✅ Library 'work' criada")
    else:
        print(f"❌ Falha ao criar library: {result.stderr}")

def _compile_files(project_path: Path, files: List[Path]) -> bool:
    """Compila lista de arquivos no ModelSim."""
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    
    for file_path in files:
        if not file_path.exists():
            print(f"   ⚠️ Arquivo não encontrado: {file_path}")
            continue
            
        # Determina comando de compilação
        file_type = get_file_extension_type(file_path)
        if file_type == 'systemverilog':
            cmd = [str(vlog_path), "-work", "work", "-sv", str(file_path)]
            type_label = " (SystemVerilog)"
        else:
            cmd = [str(vlog_path), "-work", "work", str(file_path)]
            type_label = " (Verilog)"
        
        print(f"   🔄 Compilando: {file_path.name}{type_label}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)
        
        if result.returncode == 0:
            print(f"   ✅ {file_path.name}")
        else:
            print(f"   ❌ Falha: {file_path.name}")
            # Mostra primeiros erros
            errors = result.stderr.split('\n')[:3]
            for err in errors:
                if err.strip():
                    print(f"      {err}")
            return False
    
    print("✅ Todos os arquivos compilados")
    return True

def _list_compiled_modules(project_path: Path):
    """Lista módulos compilados na library work."""
    cmd_list = [str(config.MODELSIM_DIR / "vdir"), "-lib", "work"]
    result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=project_path)
    
    if result.returncode == 0 and result.stdout.strip():
        print("📋 Módulos compilados:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"   📄 {line.strip()}")

# =============================================================================
# EXECUÇÃO DE SIMULAÇÕES
# =============================================================================

def run_modelsim_simulation(project_path: Path, tb_name: str, 
                          timeout: int = 60) -> Optional[SimulationResult]:
    """Executa simulação no ModelSim."""
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    if not vsim_path.exists():
        print(f"❌ vsim.exe não encontrado")
        return None
    
    print(f"🎯 Iniciando simulação: {tb_name}")
    
    # Cria script de simulação
    do_file = _create_simulation_script(project_path, tb_name)
    
    # Executa simulação
    cmd = [str(vsim_path), "-c", "-do", "simulate.do"]
    result = _execute_simulation_command(cmd, project_path, tb_name, timeout)
    
    return result

def run_modelsim_simulation_with_organization(project_path: Path, tb_name: str, 
                                            out_dir: Path, N: any = "default") -> Optional[SimulationResult]:
    """Executa simulação e organiza arquivos de resultado."""
    # Executa simulação
    sim_results = run_modelsim_simulation(project_path, tb_name)
    
    # Organiza arquivos
    sim_dir = organize_simulation_files(project_path, out_dir, tb_name, N)
    
    # Adiciona informação do diretório
    if sim_results:
        sim_results["Simulation_Directory"] = str(sim_dir.relative_to(project_path))
    
    return sim_results

def _create_simulation_script(project_path: Path, tb_name: str) -> Path:
    """Cria script DO para simulação ModelSim."""
    do_file = project_path / "simulate.do"
    
    with open(do_file, "w") as f:
        f.write("# Script de simulação ModelSim\n")
        f.write("onbreak {resume}\n")
        f.write("onerror {exit -code 1}\n")
        f.write(f"vsim -voptargs=+acc {tb_name}\n")
        f.write("run -all\n")
        f.write("quit -sim\n")
    
    return do_file

def _execute_simulation_command(cmd: List[str], project_path: Path, 
                              tb_name: str, timeout: int) -> Optional[SimulationResult]:
    """Executa comando de simulação e processa resultados."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=project_path,
            timeout=timeout
        )
        
        # Salva log
        log_file = _save_simulation_log(project_path, tb_name, result)
        
        # Processa resultado
        return _process_simulation_result(log_file, tb_name, result.returncode)
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: Simulação excedeu {timeout}s")
        return {
            "TB_Name": tb_name,
            "Simulation_Status": "TIMEOUT",
            "Warnings": 0,
            "Errors": 1
        }
    except Exception as e:
        print(f"💥 ERRO inesperado: {e}")
        return {
            "TB_Name": tb_name,
            "Simulation_Status": "ERROR", 
            "Warnings": 0,
            "Errors": 1
        }

def _save_simulation_log(project_path: Path, tb_name: str, 
                        result: subprocess.CompletedProcess) -> Path:
    """Salva log detalhado da simulação."""
    log_file = project_path / f"simulation_{tb_name}.log"
    
    with open(log_file, "w", encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
        f.write(f"\n=== RETURN CODE: {result.returncode} ===\n")
    
    print(f"📄 Log salvo: {log_file.name}")
    return log_file

def _process_simulation_result(log_file: Path, tb_name: str, 
                             return_code: int) -> Optional[SimulationResult]:
    """Processa resultado da simulação."""
    if return_code == 0:
        print(f"✅ Simulação {tb_name} concluída")
        results = extract_simulation_results(log_file, tb_name)
        return results
    else:
        print(f"❌ Erro na simulação (code: {return_code})")
        
        # Tenta extrair resultados mesmo com erro
        results = extract_simulation_results(log_file, tb_name)
        if results:
            results["Simulation_Status"] = "FAILED"
            return results
        else:
            return {
                "TB_Name": tb_name,
                "Simulation_Status": "FAILED",
                "Warnings": 0,
                "Errors": 1
            }

# =============================================================================
# EXTRAÇÃO DE RESULTADOS
# =============================================================================

def extract_simulation_results(log_file: Path, tb_name: str) -> Optional[SimulationResult]:
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
    
    # Conta warnings e errors
    results["Warnings"] = content.count("# ** Warning: ")
    results["Errors"] = content.count("# ** Error: ")
    
    # Extrai resultados de teste
    _extract_test_results(content, results)
    
    # Determina status
    _determine_simulation_status(content, results)
    
    return results

def _extract_test_results(content: str, results: SimulationResult):
    """Extrai resultados de testes do log."""
    # Total de testes
    total_match = re.search(r"Total de testes:\s*(\d+)", content)
    if total_match:
        results["Total_Tests"] = int(total_match.group(1))
    
    # Erros encontrados
    errors_match = re.search(r"Erros encontrados:\s*(\d+)", content)
    if errors_match:
        results["Tests_Failed"] = int(errors_match.group(1))
        results["Tests_Passed"] = results["Total_Tests"] - results["Tests_Failed"]
    
    # Taxa de sucesso
    success_match = re.search(r"Taxa de sucesso:\s*([\d\.]+)%", content)
    if success_match:
        results["Success_Rate"] = float(success_match.group(1))

def _determine_simulation_status(content: str, results: SimulationResult):
    """Determina status final da simulação."""
    if "TODOS OS TESTES PASSARAM" in content:
        results["Simulation_Status"] = "ALL_PASSED"
    elif results["Tests_Failed"] > 0:
        results["Simulation_Status"] = "SOME_FAILED"
    elif results["Total_Tests"] > 0:
        results["Simulation_Status"] = "ALL_PASSED"

# =============================================================================
# ORGANIZAÇÃO DE ARQUIVOS
# =============================================================================

def organize_simulation_files(project_path: Path, out_dir: Path, 
                            tb_name: str, N: any = "default") -> Path:
    """Organiza arquivos de simulação em diretório específico."""
    sim_dir = out_dir / "simulation"
    sim_dir.mkdir(exist_ok=True)
    
    # Padrões de arquivos a serem movidos
    simulation_files = [
        f"simulation_{tb_name}.log",
        f"{tb_name}.vcd",
        f"{tb_name}_results.log", 
        "simulate.do",
        "modelsim_work"
    ]
    
    report_patterns = [
        "*_SUMMARY.txt",
        "*_report.csv",
        "*_results.csv", 
        "*_dashboard.txt"
    ]
    
    moved_files = _move_simulation_files(project_path, sim_dir, 
                                       simulation_files + report_patterns, N)
    
    if moved_files:
        print(f"📁 Arquivos organizados em: {sim_dir.name}")
    
    return sim_dir

def _move_simulation_files(project_path: Path, sim_dir: Path, 
                          patterns: List[str], N: any) -> List[str]:
    """Move arquivos de simulação para diretório organizado."""
    moved_files = []
    
    for pattern in patterns:
        for file_path in project_path.glob(pattern):
            if file_path.exists():
                dst_path = _get_destination_path(file_path, sim_dir, N)
                
                if file_path.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(file_path, dst_path)
                else:
                    shutil.copy2(file_path, dst_path)
                
                moved_files.append(dst_path.name)
    
    return moved_files

def _get_destination_path(file_path: Path, sim_dir: Path, N: any) -> Path:
    """Gera caminho de destino para arquivo de simulação."""
    if file_path.is_dir():
        return sim_dir / f"{file_path.name}_N{N}"
    else:
        new_name = f"{file_path.stem}_N{N}{file_path.suffix}"
        return sim_dir / new_name

# =============================================================================
# FUNÇÕES DE DEBUG (OPCIONAIS)
# =============================================================================

def debug_simulation_issue(project_path: Path, tb_name: str):
    """Faz debug detalhado de problemas na simulação."""
    print(f"\n🔍 DEBUG Simulação: {tb_name}")
    
    work_dir = project_path / "modelsim_work"
    if not work_dir.exists():
        print("❌ Diretório 'modelsim_work' não encontrado")
        return
    
    # Lista arquivos compilados
    print("📁 Arquivos no modelsim_work:")
    for file in work_dir.rglob("*"):
        print(f"   {file.relative_to(work_dir)}")
    
    # Lista módulos na library
    cmd_list = [str(config.MODELSIM_DIR / "vdir"), "-lib", "work"]
    result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=project_path)
    
    print("📋 Módulos na library 'work':")
    print(result.stdout if result.stdout else "   (vazia)")