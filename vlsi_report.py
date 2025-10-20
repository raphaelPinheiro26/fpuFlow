import subprocess
import sys
import re
import csv
from pathlib import Path
import os
import subprocess
from pathlib import Path

# ================= CONFIGURAÇÃO =================
base_dir = Path(r"C:\Users\Rafael\Desktop\3-Ripple_Carry_Adder\output_files")
project_name = "rca"
rpt_file = base_dir / f"{project_name}.sta.rpt"
summary_file = base_dir / f"{project_name}.sta.summary"
fit_file = base_dir / f"{project_name}.fit.summary"
map_file = base_dir / f"{project_name}.map.rpt"
pow_file_summary = base_dir / f"{project_name}.pow.summary"
pow_file_rpt = base_dir / f"{project_name}.pow.rpt"

base_csv = Path(r"C:\Users\Rafael\Desktop\3-Ripple_Carry_Adder\report")
csv_file = base_csv / f"{project_name}_report.csv"




# ================= EXTRAÇÃO TOPO E PARÂMETROS =================
top_level = project_name
N_param = ""

with open(map_file, "r") as f:
    text = f.read()
    m_top = re.search(r"Top-level Entity\s*:\s*\|?(\S+)\s*;", text)
    if m_top:
        top_level = m_top.group(1).strip()
    m_N = re.search(r";\s*N\s*;\s*([\d\.]+)\s*;\s*[\w\s]+;", text)
    if m_N:
        N_param = m_N.group(1)

# ================= EXTRAÇÃO FMAX =================
fmax_data = {}
with open(rpt_file, "r") as f:
    for line in f:
        m = re.search(r';\s*([\d\.]+)\s*MHz\s*;\s*([\d\.]+)\s*MHz\s*;\s*(\S+)\s*;', line)
        if m:
            fmax_val, fmax_res, clk_name = m.groups()
            fmax_data[clk_name] = {
                "Fmax": float(fmax_val),
                "Restricted_Fmax": float(fmax_res)
            }

# ================= EXTRAÇÃO SLACKS =================
setup_slack = {}
hold_slack = {}
with open(summary_file, "r") as f:
    current_type = None
    current_clock = None
    for line in f:
        m_type = re.search(r"Type\s*:.*Model (Setup|Hold)\s+'(\S+)'", line)
        if m_type:
            current_type, current_clock = m_type.groups()
        m_slack = re.search(r"Slack\s*:\s*([-\d\.]+)", line)
        if m_slack and current_clock:
            slack_val = float(m_slack.group(1))
            if current_type == "Setup":
                setup_slack[current_clock] = slack_val
            elif current_type == "Hold":
                hold_slack[current_clock] = slack_val

# ================= EXTRAÇÃO UTILIZAÇÃO DE RECURSOS =================
resource_data = {}
with open(fit_file, "r") as f:
    text = f.read()

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

for key, pattern in patterns.items():
    match = re.search(pattern, text)
    if match:
        resource_data[key] = match.group(1).strip()

# ================= EXTRAÇÃO THERMAL POWER =================
power_data = {}
with open(pow_file_summary, "r") as f:
    for line in f:
        m_total = re.search(r"Total Thermal Power Dissipation\s*:\s*([\d\.]+)\s*mW", line)
        m_dynamic = re.search(r"Core Dynamic Thermal Power Dissipation\s*:\s*([\d\.]+)\s*mW", line)
        m_static = re.search(r"Core Static Thermal Power Dissipation\s*:\s*([\d\.]+)\s*mW", line)
        m_io = re.search(r"I/O Thermal Power Dissipation\s*:\s*([\d\.]+)\s*mW", line)
        if m_total:
            power_data["Total Thermal Power Dissipation"] = float(m_total.group(1))
        if m_dynamic:
            power_data["Core Dynamic Thermal Power Dissipation"] = float(m_dynamic.group(1))
        if m_static:
            power_data["Core Static Thermal Power Dissipation"] = float(m_static.group(1))
        if m_io:
            power_data["I/O Thermal Power Dissipation"] = float(m_io.group(1))

# ================= EXTRAÇÃO CORRENTE VCC =================
vcc_data = {}
with open(pow_file_rpt, "r") as f:
    for line in f:
        if line.strip().startswith("; VCC"):
            m = re.findall(r"([\d\.]+)\s*mA", line)
            if m and len(m) >= 3:
                vcc_data["Total Current (mA)"] = float(m[0])
                vcc_data["Dynamic Current (mA)"] = float(m[1])
                vcc_data["Static Current (mA)"] = float(m[2])
            break

# ================= EXPORTAÇÃO CSV =================
base_csv.mkdir(parents=True, exist_ok=True)

with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    
    # Cabeçalhos (mantendo padrão)
    header = ["Parameter", "Project", "Clock", "Fmax(MHz)", "Restricted_Fmax(MHz)",
              "SetupSlack(ns)", "HoldSlack(ns)",
              "Logic utilization (in ALMs)", "Total registers", "Total pins",
              "Total virtual pins", "Total block memory bits", "Total RAM Blocks",
              "Total DSP Blocks", "Total PLLs", "Total DLLs",
              "Total Thermal Power (mW)", "Core Dynamic Power (mW)",
              "Core Static Power (mW)", "I/O Power (mW)",
              "VCC Total Current (mA)", "VCC Dynamic Current (mA)", "VCC Static Current (mA)"]
    writer.writerow(header)
    
    for clk in fmax_data:
        fmax_val = fmax_data[clk]["Fmax"]
        fmax_res = fmax_data[clk]["Restricted_Fmax"]
        setup_val = setup_slack.get(clk, "")
        hold_val = hold_slack.get(clk, "")
        row = [
            N_param,
            top_level,
            clk, fmax_val, fmax_res, setup_val, hold_val,
            resource_data.get("Logic utilization (in ALMs)", ""),
            resource_data.get("Total registers", ""),
            resource_data.get("Total pins", ""),
            resource_data.get("Total virtual pins", ""),
            resource_data.get("Total block memory bits", ""),
            resource_data.get("Total RAM Blocks", ""),
            resource_data.get("Total DSP Blocks", ""),
            resource_data.get("Total PLLs", ""),
            resource_data.get("Total DLLs", ""),
            power_data.get("Total Thermal Power Dissipation", ""),
            power_data.get("Core Dynamic Thermal Power Dissipation", ""),
            power_data.get("Core Static Thermal Power Dissipation", ""),
            power_data.get("I/O Thermal Power Dissipation", ""),
            vcc_data.get("Total Current (mA)", ""),
            vcc_data.get("Dynamic Current (mA)", ""),
            vcc_data.get("Static Current (mA)", "")
        ]
        writer.writerow(row)

print(f"✅ Relatório completo salvo em: {csv_file}")
