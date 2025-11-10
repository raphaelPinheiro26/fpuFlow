# project_processor.py
"""
PROCESSAMENTO DE PROJETOS

Responsável por:
- Compilação Quartus
- Simulações ModelSim
- Processamento de parâmetros
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
        return "parameter N" in content

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
    
    for N in bitwidths:
        print(f"\n{'='*40}")
        print(f"🧩 {module_name} | N={N}")
        print(f"{'='*40}")
        
        # Define parâmetro N
        compile.set_parameter_in_verilog(module_name, project_path, "N", N)
        for tb_file in copied_tbs:
            simulation.set_parameter_in_tb(tb_file, "N", N)
        
        # Compila
        if not compile.compile_project(module_name, project_path):
            print(f"❌ Falha na compilação para N={N}")
            continue
        
        # Organiza saída
        out_dir = organize_compilation_output(project_path, N)
        if not out_dir:
            continue
        
        # Executa simulações
        sim_results = run_simulations_for_project(project_info, out_dir, N, run_simulations)
        results.append((module_name, project_path, N, out_dir, copied_tbs, sim_results))
    
    return results

def organize_compilation_output(project_path: Path, N: int) -> Path:
    """Move e organiza arquivos de saída da compilação."""
    src_out = project_path / "output_files"
    dst_out = project_path / f"output_files_N{N}"
    
    if not src_out.exists():
        print(f"⚠️ Pasta de saída não encontrada: {src_out}")
        return None
    
    if dst_out.exists():
        shutil.rmtree(dst_out)
    
    shutil.move(str(src_out), str(dst_out))
    return dst_out

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