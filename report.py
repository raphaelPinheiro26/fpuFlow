import re
import csv
import config

# ========================
# PARSER DE RELATÓRIOS COMPLETO
# ========================
def extract_data_from_reports(project_name, project_path):
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

    def read(p): return p.read_text(errors="ignore") if p.exists() else ""
    data = {"Project": project_name, "Top": project_name}

    # Top-level
    map_text = read(mapr)
    m_top = re.search(r"Top-level Entity\s*:\s*\|?(\S+)\s*;", map_text)
    if m_top:
        data["Top"] = m_top.group(1).strip()

    # Parameter (N)
    m_param = re.search(r";\s*N\s*;\s*([\d\.]+)\s*;", map_text)
    data["Parameter"] = m_param.group(1) if m_param else ""

    # Fmax
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

    # Setup/Hold Slack
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

    # Recursos
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
        data[k] = m.group(1).strip() if m else "-"

    # ========================
    # POTÊNCIA E CORRENTES
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
    # CORRENTES POR FONTE (VCC, VCCIO, etc.)
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
# RELATÓRIO CONSOLIDADO
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

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)

        for data in all_data:
            power = data.get("Power", {"Total": "", "Dynamic": "", "Static": "", "IO": ""})
            
            # 🔹 pega apenas a fonte principal (VCC) ou VCCINT se não existir
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
                    data.get("Logic utilization (in ALMs)", ""),
                    data.get("Total registers", ""),
                    data.get("Total pins", ""),
                    data.get("Total virtual pins", ""),
                    data.get("Total block memory bits", ""),
                    data.get("Total RAM Blocks", ""),
                    data.get("Total DSP Blocks", ""),
                    data.get("Total PLLs", ""),
                    data.get("Total DLLs", ""),
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
