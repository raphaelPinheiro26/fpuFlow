from pathlib import Path


# ========================
# CONFIGURAÇÕES GERAIS
# ========================
QUARTUS_BIN = r"C:\intelFPGA_lite\20.1\quartus\bin64"
ROOT = Path(__file__).resolve().parent
SDC_DIR = ROOT / "sdc"
RTL_DIR = ROOT / "rtl"
BUILD_DIR = ROOT / "build"
REPORT_DIR = ROOT / "report"
DEPENDENCIES_FILE = ROOT / "dependencies.json"