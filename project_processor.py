# project_processor.py
"""
PROCESSAMENTO DE PROJETOS
"""

import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple

import config
import compile
import simulation

CompiledProject = Tuple[str, Path, Any, Path, List[Path], List[Dict]]

def verify_simulation_environment() -> bool:
    """Verifica se o ModelSim está disponível."""
    print("🔍 Verificando ambiente de simulação...")
    
    if not config.MODELSIM_DIR.exists():
        print("❌ ModelSim não encontrado. Simulações serão puladas.")
        return False
    
    vsim_path = config.MODELSIM_DIR / "vsim.exe"
    vlog_path = config.MODELSIM_DIR / "vlog.exe"
    
    if not all([vsim_path.exists(), vlog_path.exists()]):
        print("❌ Arquivos do ModelSim não encontrados.")
        return False
    
    print("✅ ModelSim detectado")
    return True

def check_has_parameter_n(project_path: Path, module_name: str) -> bool:
    """Verifica se o módulo possui parâmetro N."""
    top_file = project_path / f"{module_name}.v"
    if not top_file.exists():
        return False
    
    with open(top_file, "r") as f:
        content = f.read()
        return "parameter N" in content or "parameter.*N" in content

def compile_single_project(project_info: Tuple, run_simulations: bool) -> CompiledProject:
    """Compila projeto único (sem parâmetro N)."""
    module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
    
    print(f"⚙️ Compilando {module_name} (sem parâmetro N)...")
    
    # Gera arquivos de projeto
    compile.generate_optimized_qsf(project_path, module_name, rtl_files, sdc_files)
    compile.create_qpf(project_path, module_name)
    
    # Executa compilação
    if compile.compile_project(module_name, project_path):
        out_dir = project_path / "output_files"
        sim_results = run_simulations_for_project(project_info, out_dir, "default", run_simulations)
        return (module_name, project_path, "default", out_dir, copied_tbs, sim_results)
    
    return None

def compile_parametrized_project(project_info: Tuple, bitwidths: List[int], 
                               run_simulations: bool) -> List[CompiledProject]:
    """Compila projeto com parâmetro N para diferentes bitwidths."""
    module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
    results = []
    
    # Cria diretório base para N se não existir
    n_base_dir = project_path / "N_variants"
    n_base_dir.mkdir(exist_ok=True)
    
    for N in bitwidths:
        print(f"\n{'='*50}")
        print(f"🧩 {module_name} | N={N}")
        print(f"{'='*50}")
        
        # Cria diretório específico para este N
        n_dir = n_base_dir / f"N{N}"
        if n_dir.exists():
            shutil.rmtree(n_dir)
        n_dir.mkdir(parents=True)
        
        # Copia todos os arquivos para o diretório N
        _copy_project_files_to_n_dir(project_path, n_dir, rtl_files, sdc_files, copied_tbs)
        
        # Define parâmetro N nos arquivos copiados
        compile.set_parameter_in_verilog(module_name, n_dir, "N", N)
        for tb_file in n_dir.glob("*_tb.v"):
            simulation.set_parameter_in_tb(tb_file, "N", N)
        
        # Compila no diretório N
        if compile.compile_project_with_n(module_name, n_dir, N):
            out_dir = n_dir / "output_files"
            sim_results = run_simulations_for_n_project(project_info, n_dir, out_dir, N, run_simulations)
            results.append((module_name, n_dir, N, out_dir, list(n_dir.glob("*_tb.v")), sim_results))
        else:
            print(f"❌ Falha na compilação para N={N}")
    
    return results

def _copy_project_files_to_n_dir(project_path: Path, n_dir: Path, 
                               rtl_files: List[Path], sdc_files: List[Path], 
                               tb_files: List[Path]):
    """Copia todos os arquivos do projeto para diretório N específico."""
    # Copia arquivos RTL
    for rtl_file in rtl_files:
        if rtl_file.exists():
            shutil.copy2(rtl_file, n_dir / rtl_file.name)
    
    # Copia arquivos SDC
    for sdc_file in sdc_files:
        if sdc_file.exists():
            shutil.copy2(sdc_file, n_dir / sdc_file.name)
    
    # Copia testbenches
    for tb_file in tb_files:
        if tb_file.exists():
            shutil.copy2(tb_file, n_dir / tb_file.name)
    
    print(f"   📁 Arquivos copiados para: {n_dir.name}")

def compile_project_with_n(project_info: Tuple, N: int, run_simulations: bool) -> CompiledProject:
    """Compila uma variante específica de N para projeto parametrizado."""
    module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
    
    # Cria diretório para este N
    n_dir = project_path / f"N{N}"
    if n_dir.exists():
        shutil.rmtree(n_dir)
    n_dir.mkdir()
    
    # Copia arquivos
    _copy_project_files_to_n_dir(project_path, n_dir, rtl_files, sdc_files, copied_tbs)
    
    # Define parâmetro
    compile.set_parameter_in_verilog(module_name, n_dir, "N", N)
    for tb_file in n_dir.glob("*_tb.v"):
        simulation.set_parameter_in_tb(tb_file, "N", N)
    
    # Compila
    if compile.compile_project_with_n(module_name, n_dir, N):
        out_dir = n_dir / "output_files"
        sim_results = run_simulations_for_n_project(project_info, n_dir, out_dir, N, run_simulations)
        return (module_name, n_dir, N, out_dir, list(n_dir.glob("*_tb.v")), sim_results)
    
    return None

def run_simulations_for_project(project_info: Tuple, out_dir: Path, 
                              N: Any, run_simulations: bool) -> List[Dict]:
    """Executa simulações ModelSim para um projeto."""
    module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
    
    if not (copied_tbs and run_simulations):
        return []
    
    print(f"🎯 Iniciando simulações ModelSim...")
    
    # Compila para ModelSim
    if not simulation.compile_modelsim_project(project_path, module_name, rtl_files, copied_tbs):
        print(f"❌ Falha na compilação ModelSim")
        return []
    
    # Executa simulações
    sim_results = []
    for tb_file in copied_tbs:
        tb_name = tb_file.stem
        print(f"   🚀 Simulando: {tb_name}")
        
        result = simulation.run_modelsim_simulation_with_organization(
            project_path, tb_name, out_dir, N
        )
        
        if result:
            result["N"] = N
            sim_results.append(result)
            status = result.get('Simulation_Status', 'UNKNOWN')
            print(f"   📊 {tb_name}: {status}")
    
    return sim_results

def run_simulations_for_n_project(project_info: Tuple, n_dir: Path, out_dir: Path,
                                N: int, run_simulations: bool) -> List[Dict]:
    """Executa simulações para projeto com parâmetro N."""
    module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
    
    if not run_simulations:
        return []
    
    print(f"🎯 Iniciando simulações ModelSim para N={N}...")
    
    # Usa arquivos do diretório N
    n_rtl_files = list(n_dir.glob("*.v"))
    n_tb_files = list(n_dir.glob("*_tb.v"))
    
    # Compila para ModelSim
    if not simulation.compile_modelsim_project(n_dir, module_name, n_rtl_files, n_tb_files):
        print(f"❌ Falha na compilação ModelSim para N={N}")
        return []
    
    # Executa simulações
    sim_results = []
    for tb_file in n_tb_files:
        tb_name = tb_file.stem
        print(f"   🚀 Simulando: {tb_name} (N={N})")
        
        result = simulation.run_modelsim_simulation_with_organization(
            n_dir, tb_name, out_dir, N
        )
        
        if result:
            result["N"] = N
            sim_results.append(result)
            status = result.get('Simulation_Status', 'UNKNOWN')
            print(f"   📊 {tb_name}: {status}")
    
    return sim_results