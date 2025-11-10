# report.py
import re
import csv
import config

# ========================
# FUNÇÕES AUXILIARES
# ========================
def clean_resource_value(value):
    """Remove conteúdo após '/' e limpa valores de recursos."""
    if value == "-" or not value:
        return value
    
    # Remove conteúdo após '/' e espaços extras
    cleaned = value.split('/')[0].strip()
    
    # Remove parênteses e conteúdo dentro
    cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()
    
    # Remove porcentagens e outros suffixes
    cleaned = re.sub(r'[\s%]+$', '', cleaned)
    
    return cleaned

# ========================
# PARSER DE RELATÓRIOS COMPLETO
# ========================
def extract_data_from_reports(project_name, project_path, out_dir=None):
    """
    Extrai dados de relatórios Quartus (STA, FIT, MAP, POW) de uma pasta de saída específica.
    Agora aceita `out_dir` para suportar múltiplas larguras de bits (output_files_N{N}).
    """
    if out_dir is None:
        out_dir = project_path / "output_files"

    if not out_dir.exists():
        print(f"⚠️ Diretório de relatórios não encontrado para {project_name}")
        return None

    rpt = out_dir / f"{project_name}.sta.rpt"
    sta_sum = out_dir / f"{project_name}.sta.summary"
    fit = out_dir / f"{project_name}.fit.summary"
    mapr = out_dir / f"{project_name}.map.rpt"
    pow_sum = out_dir / f"{project_name}.pow.summary"
    pow_rpt = out_dir / f"{project_name}.pow.rpt"

    def read(p): 
        return p.read_text(errors="ignore") if p.exists() else ""

    data = {"Project": project_name, "Top": project_name}

    # ========================
    # Top-level entity
    # ========================
    map_text = read(mapr)
    m_top = re.search(r"Top-level Entity\s*:\s*\|?(\S+)\s*;", map_text)
    if m_top:
        data["Top"] = m_top.group(1).strip()

    # ========================
    # Parâmetro N (tolerante a variações)
    # ========================
    m_param = re.search(r"\bN\b\s*[:=]?\s*([\d]+)", map_text)
    if not m_param:
        m_param = re.search(r";\s*N\s*;\s*([\d\.]+)\s*;", map_text)
    data["Parameter"] = m_param.group(1) if m_param else ""

    # ========================
    # Fmax (MHz)
    # ========================
    data["Clocks"] = []
    rpt_text = read(rpt)
    for line in rpt_text.splitlines():
        m = re.search(r';\s*([\d\.]+)\s*MHz\s*;\s*([\d\.]+)\s*MHz\s*;\s*(\S+)\s*;', line)
        if m:
            fmax_val, fmax_res, clk_name = m.groups()
            data["Clocks"].append({
                "Clock": clk_name,
                "Fmax": fmax_val,
                "Restricted_Fmax": fmax_res
            })

    # ========================
    # Setup / Hold Slack
    # ========================
    setup, hold = {}, {}
    sta_text = read(sta_sum)
    ctype, clk = None, None
    for line in sta_text.splitlines():
        m_type = re.search(r"Type\s*:.*Model (Setup|Hold)\s+'(\S+)'", line)
        if m_type:
            ctype, clk = m_type.groups()
        m_slack = re.search(r"Slack\s*:\s*([-\d\.]+)", line)
        if m_slack and clk:
            val = m_slack.group(1)
            if ctype == "Setup":
                setup[clk] = val
            else:
                hold[clk] = val

    data["SetupSlack"] = setup
    data["HoldSlack"] = hold

    # ========================
    # Utilização de recursos (LIMPO)
    # ========================
    fit_text = read(fit)
    patterns = {
        "Logic utilization (in ALMs)": r"Logic utilization \(in ALMs\)\s*:\s*([^\n]+)",
        "Total registers": r"Total registers\s*:\s*([^\n]+)",
        "Total pins": r"Total pins\s*:\s*([^\n]+)",
        "Total virtual pins": r"Total virtual pins\s*:\s*([^\n]+)",
        "Total block memory bits": r"Total block memory bits\s*:\s*([^\n]+)",
        "Total RAM Blocks": r"Total RAM Blocks\s*:\s*([^\n]+)",
        "Total DSP Blocks": r"Total DSP Blocks\s*:\s*([^\n]+)",
        "Total PLLs": r"Total PLLs\s*:\s*([^\n]+)",
        "Total DLLs": r"Total DLLs\s*:\s*([^\n]+)"
    }
    for k, ptn in patterns.items():
        m = re.search(ptn, fit_text)
        if m:
            data[k] = clean_resource_value(m.group(1).strip())
        else:
            data[k] = "-"

    # ========================
    # Potência total e parciais (mW)
    # ========================
    power = {"Total": "", "Dynamic": "", "Static": "", "IO": ""}
    pow_sum_text = read(pow_sum)
    for line in pow_sum_text.splitlines():
        if re.search(r"Total\s+Thermal\s+Power", line, re.I):
            m = re.search(r"([\d\.]+)\s*mW", line)
            if m: power["Total"] = m.group(1)
        elif re.search(r"Core\s+Dynamic", line, re.I):
            m = re.search(r"([\d\.]+)\s*mW", line)
            if m: power["Dynamic"] = m.group(1)
        elif re.search(r"Core\s+Static", line, re.I):
            m = re.search(r"([\d\.]+)\s*mW", line)
            if m: power["Static"] = m.group(1)
        elif re.search(r"I/?O\s+Thermal\s+Power", line, re.I):
            m = re.search(r"([\d\.]+)\s*mW", line)
            if m: power["IO"] = m.group(1)

    # ========================
    # Correntes por fonte (VCC, VCCIO, etc.)
    # ========================
    vcc_data = {}
    pow_rpt_text = read(pow_rpt)
    for line in pow_rpt_text.splitlines():
        m_header = re.match(r"^\s*;\s*(VCC\S*)", line, re.I)
        if m_header:
            name = m_header.group(1).strip()
            m_vals = re.findall(r"([\d\.]+)\s*mA", line)
            if len(m_vals) >= 3:
                vcc_data[name] = {
                    "Total": m_vals[0],
                    "Dynamic": m_vals[1],
                    "Static": m_vals[2]
                }

    data["Power"] = power
    data["VCCs"] = vcc_data

    return data

# ========================
# RELATÓRIOS DE SIMULAÇÃO
# ========================
def extract_simulation_summary(all_data):
    """Extrai resumo das simulações para relatório separado."""
    simulation_data = []
    
    for data in all_data:
        project = data.get("Project", "")
        N = data.get("N", "")
        sim_results = data.get("Simulation_Results", [])
        
        for sim_result in sim_results:
            tb_name = sim_result.get("TB_Name", "")
            
            sim_row = {
                "Project": project,
                "N": N,
                "Testbench": tb_name,
                "Total_Tests": sim_result.get("Total_Tests", 0),
                "Tests_Passed": sim_result.get("Tests_Passed", 0),
                "Tests_Failed": sim_result.get("Tests_Failed", 0),
                "Success_Rate": sim_result.get("Success_Rate", 0),
                "Simulation_Status": sim_result.get("Simulation_Status", "Unknown"),
                "Warnings": sim_result.get("Warnings", 0),
                "Errors": sim_result.get("Errors", 0),
                "Simulation_Time": sim_result.get("Simulation_Time", ""),
                "Simulation_Directory": sim_result.get("Simulation_Directory", "")
            }
            simulation_data.append(sim_row)
    
    return simulation_data

def write_simulation_report(all_data):
    """Gera relatório consolidado apenas com dados de simulação."""
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = config.REPORT_DIR / "simulation_report.csv"
    print(f"\n🎯 Gerando relatório de simulação: {csv_file}")
    
    simulation_data = extract_simulation_summary(all_data)
    
    if not simulation_data:
        print("ℹ️ Nenhum dado de simulação encontrado para gerar relatório")
        return
    
    header = [
        "Project", "N", "Testbench", "Total_Tests", "Tests_Passed", 
        "Tests_Failed", "Success_Rate_%", "Status", "Warnings", 
        "Errors", "Simulation_Time", "Simulation_Directory"
    ]
    
    # 🔥 CORREÇÃO: Usar encoding UTF-8
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for sim_row in simulation_data:
            row = [
                sim_row["Project"],
                sim_row["N"],
                sim_row["Testbench"],
                sim_row["Total_Tests"],
                sim_row["Tests_Passed"],
                sim_row["Tests_Failed"],
                f"{sim_row['Success_Rate']:.2f}" if sim_row['Success_Rate'] else "0.00",
                sim_row["Simulation_Status"],
                sim_row["Warnings"],
                sim_row["Errors"],
                sim_row["Simulation_Time"],
                sim_row["Simulation_Directory"]
            ]
            writer.writerow(row)
    
    print(f"✅ Relatório de simulação salvo em: {csv_file}")
    
    # Gera também um resumo executivo
    write_simulation_executive_summary(simulation_data)
    
    # Gera relatório de falhas se houver
    write_detailed_simulation_failures(simulation_data)

def write_simulation_executive_summary(simulation_data):
    """Gera um resumo executivo das simulações."""
    summary_file = config.REPORT_DIR / "simulation_executive_summary.txt"
    
    total_simulations = len(simulation_data)
    passed_simulations = sum(1 for s in simulation_data if s["Simulation_Status"] in ["ALL_PASSED", "Success"])
    failed_simulations = sum(1 for s in simulation_data if s["Simulation_Status"] in ["SOME_FAILED", "Failed", "TIMEOUT"])
    warning_simulations = sum(1 for s in simulation_data if s["Warnings"] > 0)
    
    # 🔥 CORREÇÃO: Usar encoding UTF-8 explicitamente
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("           RELATÓRIO EXECUTIVO DE SIMULAÇÃO\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total de simulações executadas: {total_simulations}\n")
        f.write(f"Simulações com sucesso total: {passed_simulations}\n")
        f.write(f"Simulações com falhas: {failed_simulations}\n")
        f.write(f"Simulações com warnings: {warning_simulations}\n")
        f.write(f"Taxa de sucesso geral: {(passed_simulations/total_simulations*100 if total_simulations > 0 else 0):.1f}%\n\n")
        
        f.write("-" * 60 + "\n")
        f.write("DETALHES POR PROJETO:\n")
        f.write("-" * 60 + "\n")
        
        # Agrupa por projeto
        projects = {}
        for sim in simulation_data:
            project = sim["Project"]
            if project not in projects:
                projects[project] = []
            projects[project].append(sim)
        
        for project, sims in projects.items():
            # 🔥 CORREÇÃO: Substituir emojis por texto simples
            f.write(f"\n[PROJETO] {project}:\n")
            for sim in sims:
                status_icon = "[PASS]" if sim["Simulation_Status"] in ["ALL_PASSED", "Success"] else "[FAIL]"
                f.write(f"   {status_icon} {sim['Testbench']} (N={sim['N']}): ")
                f.write(f"{sim['Tests_Passed']}/{sim['Total_Tests']} passed ")
                f.write(f"({sim['Success_Rate']:.2f}%)\n")
    
    print(f"📊 Resumo executivo salvo em: {summary_file}")

def write_detailed_simulation_failures(simulation_data):
    """Gera relatório detalhado das falhas de simulação."""
    failed_simulations = [s for s in simulation_data if s["Tests_Failed"] > 0]
    
    if not failed_simulations:
        return
    
    failure_file = config.REPORT_DIR / "simulation_failures_detailed.csv"
    
    header = [
        "Project", "N", "Testbench", "Failed_Tests", 
        "Total_Tests", "Failure_Rate_%", "Error_Count"
    ]
    
    with open(failure_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for sim in failed_simulations:
            row = [
                sim["Project"],
                sim["N"],
                sim["Testbench"],
                sim["Tests_Failed"],
                sim["Total_Tests"],
                f"{(sim['Tests_Failed']/sim['Total_Tests']*100):.2f}",
                sim["Errors"]
            ]
            writer.writerow(row)
    
    print(f"🔍 Relatório de falhas detalhado salvo em: {failure_file}")

# ========================
# RELATÓRIO CONSOLIDADO (CSV)
# ========================
def write_consolidated_report(all_data):
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = config.REPORT_DIR / "consolidated_report.csv"
    print(f"\n🧾 Gerando relatório consolidado: {csv_file}")

    header = [
        "Parameter", "Project", "Clock", "Fmax(MHz)", "Restricted_Fmax(MHz)",
        "SetupSlack(ns)", "HoldSlack(ns)",
        "Logic utilization (in ALMs)", "Total registers", "Total pins",
        "Total virtual pins", "Total block memory bits", "Total RAM Blocks",
        "Total DSP Blocks", "Total PLLs", "Total DLLs",
        "Total Thermal Power (mW)", "Core Dynamic Power (mW)",
        "Core Static Power (mW)", "I/O Power (mW)",
        "VCC Total Current (mA)", "VCC Dynamic Current (mA)", "VCC Static Current (mA)"
    ]

    # 🔥 CORREÇÃO: Usar encoding UTF-8
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for data in all_data:
            power = data.get("Power", {"Total": "", "Dynamic": "", "Static": "", "IO": ""})
            vcc_data = data.get("VCCs", {})
            vcc = vcc_data.get("VCC", vcc_data.get("VCCINT", {"Total": "", "Dynamic": "", "Static": ""}))

            for clk in data.get("Clocks", []):
                clk_name = clk["Clock"]
                row = [
                    data.get("Parameter", ""),
                    data.get("Project", ""),
                    clk_name,
                    clk.get("Fmax", ""),
                    clk.get("Restricted_Fmax", ""),
                    data.get("SetupSlack", {}).get(clk_name, ""),
                    data.get("HoldSlack", {}).get(clk_name, ""),
                    clean_resource_value(data.get("Logic utilization (in ALMs)", "")),
                    clean_resource_value(data.get("Total registers", "")),
                    clean_resource_value(data.get("Total pins", "")),
                    clean_resource_value(data.get("Total virtual pins", "")),
                    clean_resource_value(data.get("Total block memory bits", "")),
                    clean_resource_value(data.get("Total RAM Blocks", "")),
                    clean_resource_value(data.get("Total DSP Blocks", "")),
                    clean_resource_value(data.get("Total PLLs", "")),
                    clean_resource_value(data.get("Total DLLs", "")),
                    power.get("Total", ""),
                    power.get("Dynamic", ""),
                    power.get("Static", ""),
                    power.get("IO", ""),
                    vcc.get("Total", ""),
                    vcc.get("Dynamic", ""),
                    vcc.get("Static", "")
                ]
                writer.writerow(row)

    print(f"✅ Relatório consolidado salvo em: {csv_file}")
    
    # GERA OS RELATÓRIOS DE SIMULAÇÃO TAMBÉM
    write_simulation_report(all_data)