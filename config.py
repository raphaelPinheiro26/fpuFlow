# config.py - Atualizado com estrutura numerada
from pathlib import Path

# ========================
# CONFIGURAÇÕES GERAIS
# ========================
QUARTUS_BIN = r"C:\intelFPGA_lite\20.1\quartus\bin64"
MODELSIM_DIR = Path(r"C:\intelFPGA_lite\20.1\modelsim_ase\win32aloem")
ROOT = Path(__file__).resolve().parent

# ========================
# ESTRUTURA NUMERADA src/
# ========================
SRC_DIR = ROOT / "src"
RTL_DIR = SRC_DIR / "rtl"
TB_DIR = SRC_DIR / "tb"
SDC_DIR = SRC_DIR / "sdc"
TCL_DIR = SRC_DIR / "tcl"

# ========================
# CATEGORIAS NUMERADAS
# ========================
# 1. Integer Arithmetic
RTL_INTEGER_DIR = RTL_DIR / "01_integer_arithmetic"
RTL_ADDERS_DIR = RTL_INTEGER_DIR / "01_adders"
RTL_MULTIPLIERS_DIR = RTL_INTEGER_DIR / "02_multipliers"
RTL_DIVIDERS_DIR = RTL_INTEGER_DIR / "03_dividers"

# 2. Primitive Units  
RTL_PRIMITIVE_DIR = RTL_DIR / "02_primitive_units"
RTL_LZC_DIR = RTL_PRIMITIVE_DIR / "01_lzc"
RTL_SHIFTERS_DIR = RTL_PRIMITIVE_DIR / "02_barrel_shifters"
RTL_PRIORITY_DIR = RTL_PRIMITIVE_DIR / "03_priority_encoders"
RTL_COMPRESSORS_DIR = RTL_PRIMITIVE_DIR / "04_compressors"

# 3. Common Modules
RTL_COMMON_DIR = RTL_DIR / "03_common_modules"
RTL_UNPACK_DIR = RTL_COMMON_DIR / "01_unpack"
RTL_NORMALIZE_DIR = RTL_COMMON_DIR / "02_normalize"
RTL_ROUND_DIR = RTL_COMMON_DIR / "03_round"

# 4. Specific Operations
RTL_SPECIFIC_DIR = RTL_DIR / "04_specific_operations"
RTL_MANTISSA_ALIGN_DIR = RTL_SPECIFIC_DIR / "01_mantissa_align"
RTL_MANTISSA_ADD_SUB_DIR = RTL_SPECIFIC_DIR / "02_mantissa_add_sub"

# 5. FPU Operations
RTL_FPU_OPS_DIR = RTL_DIR / "05_fpu_operations"
RTL_FPU_ADD_SUB_DIR = RTL_FPU_OPS_DIR / "01_fpu_add_sub"
RTL_FPU_MULT_DIR = RTL_FPU_OPS_DIR / "02_fpu_mult"
RTL_FPU_DIV_DIR = RTL_FPU_OPS_DIR / "03_fpu_div"

# 6. FPU Core
RTL_FPU_CORE_DIR = RTL_DIR / "06_fpu_core"
RTL_FPU_PIPELINE_DIR = RTL_FPU_CORE_DIR / "01_fpu_pipeline"
RTL_FPU_CONTROLLER_DIR = RTL_FPU_CORE_DIR / "02_fpu_controller"
RTL_FPU_UNIT_DIR = RTL_FPU_CORE_DIR / "03_fpu_unit"

# ========================
# DIRETÓRIOS DE SAÍDA
# ========================
BUILD_DIR = ROOT / "build"
REPORT_DIR = ROOT / "report"
ASIC_DIR = ROOT / "asic"

# ========================
# ARQUIVOS DE CONFIGURAÇÃO
# ========================
DEPENDENCIES_FILE = ROOT / "dependencies.json"

# ========================
# MAPEAMENTO INTELIGENTE
# ========================
CATEGORY_MAPPING = {
    "adder": RTL_ADDERS_DIR,
    "mult": RTL_MULTIPLIERS_DIR,
    "div": RTL_DIVIDERS_DIR,
    "lzc": RTL_LZC_DIR,
    "shifter": RTL_SHIFTERS_DIR,
    "priority": RTL_PRIORITY_DIR,
    "unpack": RTL_UNPACK_DIR,
    "normalize": RTL_NORMALIZE_DIR,
    "round": RTL_ROUND_DIR,
    "fpu_add": RTL_FPU_ADD_SUB_DIR,
    "fpu_mult": RTL_FPU_MULT_DIR,
    "fpu_div": RTL_FPU_DIV_DIR,
}