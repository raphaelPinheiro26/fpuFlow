# report_generator.py
"""
GERAÇÃO DE RELATÓRIOS

Responsável por:
- Coleta de dados de relatórios
- Geração de relatórios consolidados
- Relatórios de simulação
"""

import time
from pathlib import Path
from typing import List, Dict, Tuple

import config
import report

CompiledProject = Tuple[str, Path, any, Path, List[Path], List[Dict]]

def generate_all_reports(compiled_projects: List[CompiledProject]):
    """Gera todos os relatórios finais."""
    print("\n📊 Gerando relatórios...")
    
    all_reports = collect_reports_from_projects(compiled_projects)
    
    if all_reports:
        report.write_consolidated_report(all_reports)
    else:
        print("❌ Nenhum dado para gerar relatórios")

def collect_reports_from_projects(compiled_projects: List[CompiledProject]) -> List[Dict]:
    """Coleta dados de relatórios de todos os projetos."""
    all_reports = []
    
    for project in compiled_projects:
        module_name, project_path, N, out_dir, copied_tbs, sim_results = project
        
        # Aguarda relatório de potência
        if not wait_for_power_report(module_name, out_dir, N):
            continue
        
        # Extrai dados - agora a função sabe buscar na estrutura correta
        data = report.extract_data_from_reports(module_name, project_path, out_dir, N)
        if data:
            data["N"] = N
            if sim_results:
                data["Simulation_Results"] = sim_results
            all_reports.append(data)
    
    return all_reports

def wait_for_power_report(module_name: str, out_dir: Path, N: any, 
                         max_wait: int = 120) -> bool:
    """Aguarda até o relatório de potência estar disponível."""
    pow_report = out_dir / f"{module_name}.pow.rpt"
    
    wait_time = 0
    while not pow_report.exists() and wait_time < max_wait:
        print(f"⏳ Aguardando relatório {module_name} (N={N})...", end="\r")
        time.sleep(2)
        wait_time += 2
    
    if not pow_report.exists():
        print(f"\n⚠️ Relatório não encontrado após {wait_time}s")
        return False
    
    return True