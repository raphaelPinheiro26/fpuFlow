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
            report_data["Module_Name"] = module_name
            report_data["N"] = N
            report_data["Simulation_Results"] = sim_results
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
    
    # Gera relatórios consolidados da raiz
    _generate_root_reports(hierarchical_data, base_report_dir)
    
    # Gera relatórios hierárquicos
    _generate_hierarchical_reports_recursive(hierarchical_data, base_report_dir)
    
    print("✅ Relatórios hierárquicos gerados!")

def _organize_by_hierarchy(all_reports_data: List[Dict]) -> Dict:
    """Organiza dados pela hierarquia do RTL."""
    hierarchical_data = {}
    
    for report_data in all_reports_data:
        module_name = report_data["Module_Name"]
        
        # Encontra caminho RTL do módulo
        rtl_path = _find_rtl_path(module_name)
        if not rtl_path:
            # Se não encontrou, coloca na raiz
            rtl_path = Path(".")
        
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

def _generate_root_reports(hierarchical_data: Dict, base_dir: Path):
    """Gera relatórios consolidados na raiz."""
    all_modules = _collect_all_modules(hierarchical_data)
    
    # Relatório de compilação geral
    compilation_file = base_dir / "00_geral_compilation_report.csv"
    _write_compilation_csv(all_modules, compilation_file)
    
    # Relatório de simulação geral
    simulation_file = base_dir / "00_geral_simulation_report.csv"
    _write_simulation_csv(all_modules, simulation_file)
    
    # Sumário geral
    summary_file = base_dir / "00_geral_simulation_summary.txt"
    _write_simulation_summary(all_modules, summary_file, "PROJETO COMPLETO")

def _generate_hierarchical_reports_recursive(hierarchical_data: Dict, current_dir: Path, level_path: Path = None):
    """Gera relatórios recursivamente para cada nível."""
    if level_path is None:
        level_path = Path(".")
    
    # Gera relatórios para este nível (se tiver módulos)
    if "modules" in hierarchical_data:
        level_name = current_dir.name
        
        # Determina o nome do relatório baseado no nível
        if level_path == Path("."):
            report_name = "geral"
        else:
            report_name = level_name
        
        compilation_file = current_dir / f"compilation_report_{report_name}.csv"
        _write_compilation_csv(hierarchical_data["modules"], compilation_file)
        
        simulation_file = current_dir / f"simulation_report_{report_name}.csv"
        _write_simulation_csv(hierarchical_data["modules"], simulation_file)
        
        summary_file = current_dir / f"simulation_summary_{report_name}.txt"
        _write_simulation_summary(hierarchical_data["modules"], summary_file, report_name.upper())
    
    # Processa subdiretórios
    for key, value in hierarchical_data.items():
        if key != "modules":
            sub_dir = current_dir / key
            sub_dir.mkdir(exist_ok=True)
            _generate_hierarchical_reports_recursive(value, sub_dir, level_path / key)

def _collect_all_modules(hierarchical_data: Dict) -> List[Dict]:
    """Coleta todos os módulos de um nível e seus subníveis."""
    all_modules = []
    
    if "modules" in hierarchical_data:
        all_modules.extend(hierarchical_data["modules"])
    
    for key, value in hierarchical_data.items():
        if key != "modules":
            all_modules.extend(_collect_all_modules(value))
    
    return all_modules

def _write_compilation_csv(modules: List[Dict], csv_file: Path):
    """Escreve CSV de compilação para um nível hierárquico."""
    if not modules:
        return
    
    header = [
        "Module", "Parameter_N", "Clock", "Fmax_MHz", "Restricted_Fmax_MHz",
        "Setup_Slack_ns", "Hold_Slack_ns", "Logic_Utilization_ALMs", 
        "Total_Registers", "Total_Pins", "Total_Power_mW", "Dynamic_Power_mW",
        "Static_Power_mW", "IO_Power_mW"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for module_data in modules:
            rows = _extract_compilation_rows(module_data)
            for row in rows:
                writer.writerow(row)
    
    print(f"   📊 Compilação: {csv_file.relative_to(config.REPORT_DIR)}")

def _extract_compilation_rows(module_data: Dict) -> List[List]:
    """Extrai linhas de dados de compilação de um módulo."""
    rows = []
    module_name = module_data["Module_Name"]
    N = module_data.get("N", "default")
    
    # Dados de timing
    clocks = module_data.get("Clocks", [])
    setup_slack = module_data.get("SetupSlack", {})
    hold_slack = module_data.get("HoldSlack", {})
    power = module_data.get("Power", {})
    
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
            power.get("Static", ""), power.get("IO", ""),
        ]
        rows.append(row)
    
    return rows

def _write_simulation_csv(modules: List[Dict], csv_file: Path):
    """Escreve CSV de simulação para um nível hierárquico."""
    if not modules:
        return
    
    header = [
        "Module", "Parameter_N", "Testbench", "Total_Tests", "Tests_Passed",
        "Tests_Failed", "Success_Rate_%", "Status", "Warnings", "Errors",
        "Simulation_Time", "Simulation_Directory"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for module_data in modules:
            rows = _extract_simulation_rows(module_data)
            for row in rows:
                writer.writerow(row)
    
    print(f"   🧪 Simulação: {csv_file.relative_to(config.REPORT_DIR)}")

def _extract_simulation_rows(module_data: Dict) -> List[List]:
    """Extrai linhas de dados de simulação de um módulo."""
    rows = []
    module_name = module_data["Module_Name"]
    N = module_data.get("N", "default")
    sim_results = module_data.get("Simulation_Results", [])
    
    for sim_result in sim_results:
        row = [
            module_name,
            N,
            sim_result.get("TB_Name", ""),
            sim_result.get("Total_Tests", 0),
            sim_result.get("Tests_Passed", 0),
            sim_result.get("Tests_Failed", 0),
            f"{sim_result.get('Success_Rate', 0):.2f}",
            sim_result.get("Simulation_Status", "UNKNOWN"),
            sim_result.get("Warnings", 0),
            sim_result.get("Errors", 0),
            sim_result.get("Simulation_Time", ""),
            sim_result.get("Simulation_Directory", ""),
        ]
        rows.append(row)
    
    # Se não tem simulações, cria uma linha indicando isso
    if not rows and "modules" in module_data:  # Só para nível de módulo, não para diretório
        row = [
            module_name, N, "NO_SIMULATION", 0, 0, 0, "0.00", 
            "NO_SIM", 0, 0, "", ""
        ]
        rows.append(row)
    
    return rows

def _write_simulation_summary(modules: List[Dict], summary_file: Path, level_name: str):
    """Escreve resumo de simulação para um nível hierárquico."""
    simulation_data = []
    
    for module_data in modules:
        sim_results = module_data.get("Simulation_Results", [])
        for sim_result in sim_results:
            simulation_data.append({
                "module": module_data["Module_Name"],
                "N": module_data.get("N", "default"),
                **sim_result
            })
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"RELATÓRIO DE SIMULAÇÃO - {level_name}\n")
        f.write("=" * 60 + "\n\n")
        
        if not simulation_data:
            f.write("Nenhum dado de simulação disponível para este nível.\n")
            return
        
        # Estatísticas
        total_simulations = len(simulation_data)
        passed_simulations = sum(1 for s in simulation_data if s.get("Simulation_Status") == "ALL_PASSED")
        failed_simulations = sum(1 for s in simulation_data if s.get("Simulation_Status") in ["SOME_FAILED", "FAILED"])
        unknown_simulations = total_simulations - passed_simulations - failed_simulations
        
        success_rate = (passed_simulations / total_simulations * 100) if total_simulations > 0 else 0
        
        f.write("📈 ESTATÍSTICAS:\n")
        f.write(f"   • Total de simulações: {total_simulations}\n")
        f.write(f"   • Simulações com sucesso: {passed_simulations}\n")
        f.write(f"   • Simulações com falhas: {failed_simulations}\n")
        f.write(f"   • Simulações desconhecidas: {unknown_simulations}\n")
        f.write(f"   • Taxa de sucesso: {success_rate:.1f}%\n\n")
        
        if simulation_data:
            f.write("🧪 DETALHES POR MÓDULO:\n")
            f.write("-" * 40 + "\n")
            
            # Agrupa por módulo
            modules_summary = {}
            for sim_data in simulation_data:
                module = sim_data["module"]
                if module not in modules_summary:
                    modules_summary[module] = []
                modules_summary[module].append(sim_data)
            
            for module, sims in modules_summary.items():
                f.write(f"\n📦 {module}:\n")
                for sim in sims:
                    status_icon = "✅" if sim.get("Simulation_Status") == "ALL_PASSED" else "❌"
                    f.write(f"   {status_icon} {sim.get('TB_Name', 'N/A')} (N={sim['N']}): ")
                    f.write(f"{sim.get('Tests_Passed', 0)}/{sim.get('Total_Tests', 0)} ")
                    f.write(f"({sim.get('Success_Rate', 0):.1f}%)\n")