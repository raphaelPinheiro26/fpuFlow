# config.py
from pathlib import Path

# ========================
# CONFIGURAÇÕES GERAIS
# ========================
QUARTUS_BIN = r"C:\intelFPGA_lite\20.1\quartus\bin64"
MODELSIM_DIR = Path(r"C:\intelFPGA_lite\20.1\modelsim_ase\win32aloem")  # ✅ Convertendo para Path
ROOT = Path(__file__).resolve().parent
SDC_DIR = ROOT / "sdc"
RTL_DIR = ROOT / "rtl"
TB_DIR = ROOT / "tb"
BUILD_DIR = ROOT / "build"
REPORT_DIR = ROOT / "report"
DEPENDENCIES_FILE = ROOT / "dependencies.json"