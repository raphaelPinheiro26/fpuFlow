# hierarchical_reports.py
"""
RELATÓRIOS HIERÁRQUICOS - Estrutura que espelha o RTL
"""

import csv
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

import config
import report

def generate_hierarchical_reports(compiled_projects: List, dependencies: Dict):
    """Gera relatórios organizados pela hierarquia do RTL."""
    print("\n🌲 Gerando relatórios hierárquicos...")
    
    # Coleta todos os dados primeiro
    all_reports_data = []
    for project in compiled_projects:
        module_name, project_path, N, out_dir, copied_tbs, sim_results = project
        
        report_data = report.extract_data_from_reports(module_name, project_path, out_dir, N)
        if report_data:
            report_data["N"] = N
            report_data["Simulation_Results"] = sim_results
            report_data["Module_Name"] = module_name
            all_reports_data.append(report_data)
    
    if not all_reports_data:
        print("❌ Nenhum dado para gerar relatórios hierárquicos")
        return
    
    # Cria estrutura base
    base_report_dir = config.REPORT_DIR / "hierarchical"
    if base_report_dir.exists():
        shutil.rmtree(base_report_dir)
    base_report_dir.mkdir(parents=True)
    
    # Organiza por hierarquia
    hierarchical_data = _organize_by_hierarchy(all_reports_data)
    
    # Gera relatórios
    _generate_hierarchical_csv(hierarchical_data, base_report_dir)
    _generate_hierarchical_summary(hierarchical_data, base_report_dir)
    
    print("✅ Relatórios hierárquicos gerados!")

def _organize_by_hierarchy(all_reports_data: List[Dict]) -> Dict:
    """Organiza dados pela hierarquia do RTL."""
    hierarchical_data = {}
    
    for report_data in all_reports_data:
        module_name = report_data["Module_Name"]
        
        # Encontra caminho RTL do módulo
        rtl_path = _find_rtl_path(module_name)
        if not rtl_path:
            continue
        
        # Adiciona à estrutura hierárquica
        current_level = hierarchical_data
        for part in rtl_path.parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        # Adiciona módulo
        if "modules" not in current_level:
            current_level["modules"] = []
        current_level["modules"].append(report_data)
    
    return hierarchical_data

def _find_rtl_path(module_name: str) -> Optional[Path]:
    """Encontra o caminho RTL de um módulo."""
    for rtl_file in config.RTL_DIR.rglob(f"{module_name}.v"):
        return rtl_file.relative_to(config.RTL_DIR).parent
    return None

def _generate_hierarchical_csv(hierarchical_data: Dict, base_dir: Path, current_path: Path = None):
    """Gera CSVs recursivamente para cada nível."""
    if current_path is None:
        current_path = base_dir
    
    # Coleta todos os módulos deste nível e subníveis
    all_modules = _collect_all_modules(hierarchical_data)
    
    if all_modules:
        # Gera CSV para este nível
        csv_file = current_path / "level_report.csv"
        _write_hierarchical_csv(all_modules, csv_file)
    
    # Processa subdiretórios
    for key, value in hierarchical_data.items():
        if key != "modules":
            sub_dir = current_path / key
            sub_dir.mkdir(exist_ok=True)
            _generate_hierarchical_csv(value, base_dir, sub_dir)

def _collect_all_modules(hierarchical_data: Dict) -> List[Dict]:
    """Coleta todos os módulos de um nível e seus subníveis."""
    all_modules = []
    
    if "modules" in hierarchical_data:
        all_modules.extend(hierarchical_data["modules"])
    
    for key, value in hierarchical_data.items():
        if key != "modules":
            all_modules.extend(_collect_all_modules(value))
    
    return all_modules

def _write_hierarchical_csv(modules: List[Dict], csv_file: Path):
    """Escreve CSV para um nível hierárquico."""
    if not modules:
        return
    
    header = [
        "Module", "Parameter_N", "Clock", "Fmax_MHz", "Restricted_Fmax_MHz",
        "Setup_Slack_ns", "Hold_Slack_ns", "Logic_Utilization_ALMs", 
        "Total_Registers", "Total_Pins", "Total_Power_mW", "Dynamic_Power_mW",
        "Static_Power_mW", "IO_Power_mW", "Simulation_Status"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for module_data in modules:
            rows = _extract_module_rows(module_data)
            for row in rows:
                writer.writerow(row)
    
    print(f"   ✅ {csv_file.relative_to(config.REPORT_DIR)}")

def _extract_module_rows(module_data: Dict) -> List[List]:
    """Extrai linhas de dados de um módulo."""
    rows = []
    module_name = module_data["Module_Name"]
    N = module_data.get("N", "default")
    
    # Dados de timing
    clocks = module_data.get("Clocks", [])
    setup_slack = module_data.get("SetupSlack", {})
    hold_slack = module_data.get("HoldSlack", {})
    power = module_data.get("Power", {})
    
    # Status de simulação
    sim_results = module_data.get("Simulation_Results", [])
    sim_status = "NO_SIM"
    if sim_results:
        if all(r.get("Simulation_Status") == "ALL_PASSED" for r in sim_results):
            sim_status = "ALL_PASSED"
        elif any(r.get("Simulation_Status") == "ALL_PASSED" for r in sim_results):
            sim_status = "SOME_PASSED"
        else:
            sim_status = "FAILED"
    
    for clock in clocks:
        clock_name = clock["Clock"]
        row = [
            module_name,
            N,
            clock_name,
            clock.get("Fmax", ""),
            clock.get("Restricted_Fmax", ""),
            setup_slack.get(clock_name, ""),
            hold_slack.get(clock_name, ""),
            module_data.get("Logic utilization (in ALMs)", ""),
            module_data.get("Total registers", ""),
            module_data.get("Total pins", ""),
            power.get("Total", ""),
            power.get("Dynamic", ""),
            power.get("Static", ""),
            power.get("IO", ""),
            sim_status
        ]
        rows.append(row)
    
    # Se não tem clocks, cria uma linha básica
    if not rows:
        row = [
            module_name, N, "N/A", "", "", "", "",
            module_data.get("Logic utilization (in ALMs)", ""),
            module_data.get("Total registers", ""),
            module_data.get("Total pins", ""),
            power.get("Total", ""), power.get("Dynamic", ""),
            power.get("Static", ""), power.get("IO", ""), sim_status
        ]
        rows.append(row)
    
    return rows

def _generate_hierarchical_summary(hierarchical_data: Dict, base_dir: Path):
    """Gera resumo geral da hierarquia."""
    summary_file = base_dir / "hierarchical_summary.txt"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("           RESUMO GERAL DA HIERARQUIA DE PROJETOS\n")
        f.write("=" * 70 + "\n\n")
        
        stats = _calculate_hierarchy_stats(hierarchical_data)
        
        f.write("📈 ESTATÍSTICAS GERAIS:\n")
        f.write(f"   • Total de módulos: {stats['total_modules']}\n")
        f.write(f"   • Módulos com parâmetro N: {stats['parametrized_modules']}\n")
        f.write(f"   • Módulos simulados: {stats['simulated_modules']}\n")
        f.write(f"   • Taxa de sucesso simulação: {stats['success_rate']:.1f}%\n\n")
        
        f.write("🌳 ESTRUTURA:\n")
        _write_hierarchy_tree(f, hierarchical_data)

def _calculate_hierarchy_stats(hierarchy: Dict) -> Dict:
    """Calcula estatísticas da hierarquia."""
    all_modules = _collect_all_modules(hierarchy)
    
    total_modules = len(all_modules)
    parametrized_modules = sum(1 for m in all_modules if m.get("N") != "default")
    
    simulated_modules = 0
    successful_sims = 0
    
    for module_data in all_modules:
        sim_results = module_data.get("Simulation_Results", [])
        if sim_results:
            simulated_modules += 1
            if all(r.get("Simulation_Status") == "ALL_PASSED" for r in sim_results):
                successful_sims += 1
    
    success_rate = (successful_sims / simulated_modules * 100) if simulated_modules > 0 else 0
    
    return {
        'total_modules': total_modules,
        'parametrized_modules': parametrized_modules,
        'simulated_modules': simulated_modules,
        'success_rate': success_rate
    }

def _write_hierarchy_tree(f, hierarchy: Dict, indent: int = 0, prefix: str = ""):
    """Escreve árvore da hierarquia."""
    for key, value in hierarchy.items():
        if key == "modules":
            for module_data in value:
                module_name = module_data["Module_Name"]
                N = module_data.get("N", "default")
                sim_status = "🧪" if module_data.get("Simulation_Results") else "📄"
                param_info = f" (N={N})" if N != "default" else ""
                f.write(f"{prefix}{sim_status} {module_name}{param_info}\n")
        else:
            f.write(f"{prefix}📁 {key}/\n")
            new_prefix = prefix + "  "
            _write_hierarchy_tree(f, value, indent + 1, new_prefix)