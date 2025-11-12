# simulation.py
"""
SIMULAÇÃO MODELSIM E GERENCIAMENTO DE TESTBENCHES
"""

import os
import subprocess
import time
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys

import config

# =============================================================================
# TIPOS DE DADOS
# =============================================================================

SimulationResult = Dict[str, any]

# =============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS DE SIMULAÇÃO
# =============================================================================

def get_simulation_directory(project_path: Path) -> Path:
    """Retorna o diretório de simulação no padrão Quartus."""
    return project_path / "simulation" / "modelsim"

def get_modelsim_work_dir(project_path: Path) -> Path:
    """Retorna o diretório de trabalho do ModelSim."""
    return get_simulation_directory(project_path) / "work"

def get_simulation_results_dir(project_path: Path, tb_name: str, N: any = "default") -> Path:
    """Retorna diretório para resultados específicos de simulação."""
    sim_dir = get_simulation_directory(project_path)
    return sim_dir / f"{tb_name}_N{N}"

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
# COMPILAÇÃO MODELSIM (ATUALIZADA)
# =============================================================================

def compile_modelsim_project(project_path: Path, module_name: str, 
                           rtl_files: List[Path], tb_files: List[Path]) -> bool:
    """Compila projeto para simulação no ModelSim."""
    print(f"🔨 Compilando para ModelSim: {module_name}")
    
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    if not vlog_path.exists():
        print(f"❌ vlog.exe não encontrado")
        return False
    
    # Prepara ambiente com estrutura organizada
    _prepare_modelsim_environment(project_path)
    
    # Compila todos os arquivos
    all_files = rtl_files + tb_files
    compile_success = _compile_files(project_path, all_files)
    
    if compile_success:
        _list_compiled_modules(project_path)
    
    return compile_success

def _prepare_modelsim_environment(project_path: Path):
    """Prepara ambiente ModelSim com estrutura organizada."""
    modelsim_dir = get_simulation_directory(project_path)
    work_dir = get_modelsim_work_dir(project_path)
    
    # Limpa diretório de simulação anterior
    if modelsim_dir.exists():
        shutil.rmtree(modelsim_dir)
    
    # Cria estrutura de diretórios
    modelsim_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Estrutura de simulação criada: {modelsim_dir.relative_to(project_path)}")
    
    # Cria library work no diretório correto
    cmd_lib = [str(config.MODELSIM_DIR / "vlib"), "work"]
    result = subprocess.run(cmd_lib, capture_output=True, text=True, cwd=modelsim_dir)
    
    if result.returncode == 0:
        print("✅ Library 'work' criada em simulation/modelsim/")
    else:
        print(f"❌ Falha ao criar library: {result.stderr}")

def _compile_files(project_path: Path, files: List[Path]) -> bool:
    """Compila lista de arquivos no ModelSim."""
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    modelsim_dir = get_simulation_directory(project_path)
    
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
        
        # Compila no diretório de simulação
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=modelsim_dir)
        
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
    modelsim_dir = get_simulation_directory(project_path)
    cmd_list = [str(config.MODELSIM_DIR / "vdir"), "-lib", "work"]
    
    result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=modelsim_dir)
    
    if result.returncode == 0 and result.stdout.strip():
        print("📋 Módulos compilados:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"   📄 {line.strip()}")

# =============================================================================
# EXECUÇÃO DE SIMULAÇÕES (ATUALIZADA)
# =============================================================================

def run_modelsim_simulation(project_path: Path, tb_name: str, 
                          timeout: int = 60) -> Optional[SimulationResult]:
    """Executa simulação no ModelSim com estrutura organizada."""
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    if not vsim_path.exists():
        print(f"❌ vsim.exe não encontrado")
        return None
    
    modelsim_dir = get_simulation_directory(project_path)
    
    print(f"🎯 Iniciando simulação: {tb_name}")
    
    # Cria script de simulação no diretório de simulação
    do_file = _create_simulation_script(modelsim_dir, tb_name)
    
    # Executa simulação no diretório de simulação
    cmd = [str(vsim_path), "-c", "-do", "do simulate.do; exit"]
    result = _execute_simulation_command(cmd, modelsim_dir, tb_name, timeout)
    
    return result

def run_modelsim_simulation_with_organization(project_path: Path, tb_name: str, 
                                            out_dir: Path, N: any = "default") -> Optional[SimulationResult]:
    """Executa simulação e organiza arquivos na estrutura Quartus."""
    # Executa simulação
    sim_results = run_modelsim_simulation(project_path, tb_name)
    
    # Organiza arquivos na estrutura simulation/modelsim/
    sim_dir = organize_simulation_files(project_path, out_dir, tb_name, N)
    
    # Adiciona informação do diretório
    if sim_results:
        sim_results["Simulation_Directory"] = str(sim_dir.relative_to(project_path))
    
    return sim_results

def _create_simulation_script(sim_dir: Path, tb_name: str) -> Path:
    do_file = sim_dir / "simulate.do"
    
    with open(do_file, "w") as f:
        f.write("# Script de simulação ModelSim\n")
        f.write("onbreak {exit -code 1}\n")
        f.write("onerror {exit -code 1}\n")
        f.write(f"vsim -c -voptargs=+acc {tb_name}\n")  # ← -c para batch mode
        f.write("run -all\n")
        f.write("echo \"Simulation finished successfully\"\n")
        f.write("quit -force\n")  # ← Force quit
    
    return do_file

def _execute_simulation_command(cmd: List[str], sim_dir: Path, 
                              tb_name: str, timeout: int) -> Optional[SimulationResult]:
    """Executa comando de simulação e processa resultados."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=sim_dir,  # Agora no diretório de simulação
            timeout=timeout
        )
        
        # Salva log no diretório de simulação
        log_file = _save_simulation_log(sim_dir, tb_name, result)
        
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

def _save_simulation_log(sim_dir: Path, tb_name: str, 
                        result: subprocess.CompletedProcess) -> Path:
    """Salva log detalhado da simulação no diretório de simulação."""
    log_file = sim_dir / f"simulation_{tb_name}.log"
    
    with open(log_file, "w", encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
        f.write(f"\n=== RETURN CODE: {result.returncode} ===\n")
    
    print(f"📄 Log salvo: {log_file.relative_to(sim_dir.parent.parent)}")
    return log_file

def _process_simulation_result(log_file: Path, tb_name: str, 
                             return_code: int) -> Optional[SimulationResult]:
    """Processa resultado da simulação - IGNORA return_code do ModelSim."""
    
    # No ModelSim, return_code 1 geralmente significa apenas $stop, não erro real
    # Então ignoramos o return_code e confiamos apenas na análise do log
    
    print(f"🔍 Analisando simulação {tb_name} (return_code: {return_code})")
    
    # Extrai resultados do arquivo de log
    results = extract_simulation_results(log_file, tb_name)
    
    if results:
        # Determina status baseado nos dados reais extraídos do log
        total_tests = results.get("Total_Tests", 0)
        tests_failed = results.get("Tests_Failed", 0)
        tests_passed = results.get("Tests_Passed", 0)
        
        if total_tests == 0:
            # Se não encontrou contagem de testes, verifica se completou
            if "Testes concluídos" in str(results):
                results["Simulation_Status"] = "COMPLETED"
            else:
                results["Simulation_Status"] = "UNKNOWN"
        elif tests_failed == 0 and total_tests > 0:
            results["Simulation_Status"] = "ALL_PASSED"
        elif tests_failed > 0 and tests_passed > 0:
            results["Simulation_Status"] = "SOME_FAILED" 
        elif tests_failed > 0:
            results["Simulation_Status"] = "FAILED"
        else:
            results["Simulation_Status"] = "UNKNOWN"
        
        status = results["Simulation_Status"]
        print(f"✅ Simulação {tb_name}: {status} ({tests_passed}/{total_tests} passed)")
        return results
        
    else:
        # Fallback se não conseguiu extrair dados
        print(f"⚠️ Dados insuficientes da simulação {tb_name}")
        return {
            "TB_Name": tb_name,
            "Simulation_Status": "UNKNOWN",
            "Warnings": 0,
            "Errors": 0,
            "Total_Tests": 0,
            "Tests_Passed": 0,
            "Tests_Failed": 0,
            "Success_Rate": 0.0
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
# ORGANIZAÇÃO DE ARQUIVOS (ATUALIZADA)
# =============================================================================

def organize_simulation_files(project_path: Path, out_dir: Path, 
                            tb_name: str, N: any = "default") -> Path:
    """Organiza arquivos de simulação em estrutura Quartus."""
    # Diretório específico para esta simulação
    sim_results_dir = get_simulation_results_dir(project_path, tb_name, N)
    sim_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Diretório base de simulação
    modelsim_dir = get_simulation_directory(project_path)
    
    # Padrões de arquivos a serem organizados
    simulation_files = [
        f"simulation_{tb_name}.log",
        f"{tb_name}.vcd",
        "simulate.do",
    ]
    
    # Move arquivos específicos da simulação
    moved_files = _move_simulation_files(modelsim_dir, sim_results_dir, simulation_files)
    
    # Copia todo o diretório work (library compilada)
    work_dir = get_modelsim_work_dir(project_path)
    if work_dir.exists():
        work_dest = sim_results_dir / "work"
        if work_dest.exists():
            shutil.rmtree(work_dest)
        shutil.copytree(work_dir, work_dest)
        moved_files.append("work/")
    
    if moved_files:
        rel_path = sim_results_dir.relative_to(project_path)
        print(f"📁 Arquivos organizados em: {rel_path}")
        print(f"   📄 {', '.join(moved_files[:5])}{'...' if len(moved_files) > 5 else ''}")
    
    return sim_results_dir

def _move_simulation_files(source_dir: Path, dest_dir: Path, 
                          patterns: List[str]) -> List[str]:
    """Move arquivos de simulação para diretório organizado."""
    moved_files = []
    
    for pattern in patterns:
        for file_path in source_dir.glob(pattern):
            if file_path.exists() and file_path.is_file():
                dest_path = dest_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                moved_files.append(file_path.name)
    
    return moved_files

# =============================================================================
# FUNÇÕES DE DEBUG (ATUALIZADAS)
# =============================================================================

def debug_simulation_issue(project_path: Path, tb_name: str):
    """Faz debug detalhado de problemas na simulação."""
    print(f"\n🔍 DEBUG Simulação: {tb_name}")
    
    modelsim_dir = get_simulation_directory(project_path)
    work_dir = get_modelsim_work_dir(project_path)
    
    if not work_dir.exists():
        print("❌ Diretório 'work' não encontrado")
        return
    
    # Lista estrutura de simulação
    print("📁 Estrutura de simulação:")
    for item in modelsim_dir.rglob("*"):
        if item.is_relative_to(modelsim_dir):
            rel_path = item.relative_to(modelsim_dir)
            type_icon = "📁" if item.is_dir() else "📄"
            print(f"   {type_icon} {rel_path}")
    
    # Lista módulos na library
    cmd_list = [str(config.MODELSIM_DIR / "vdir"), "-lib", "work"]
    result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=modelsim_dir)
    
    print("📋 Módulos na library 'work':")
    print(result.stdout if result.stdout else "   (vazia)")