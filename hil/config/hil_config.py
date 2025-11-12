"""
CONFIGURAÇÃO PRINCIPAL HIL - FPUMASTER
"""

from pathlib import Path

# Diretórios principais
HIL_BASE = Path(__file__).parent.parent
PROJECT_ROOT = HIL_BASE.parent

# Configurações FPGA
FPGA_SERIAL_PORT = "COM3"  # Windows
# FPGA_SERIAL_PORT = "/dev/ttyUSB0"  # Linux
FPGA_BAUDRATE = 115200
FPGA_TIMEOUT = 2.0

# Configurações de Teste
DEFAULT_SAMPLES = 1000
MONTE_CARLO_SAMPLES = 10000
EDGE_CASE_COUNT = 50

# Operações suportadas
SUPPORTED_OPERATIONS = {
    'integer': ['add', 'sub', 'mult', 'div'],
    'fpu': ['fadd', 'fsub', 'fmult', 'fdiv', 'fsqrt']
}

# Métricas
METRICS_CONFIG = {
    'accuracy_threshold': 0.999,
    'max_ulp_error': 2,
    'timing_margin_ns': 1.0
}
