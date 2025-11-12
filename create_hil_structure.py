# create_hil_structure.py
"""
CRIADOR DE ESTRUTURA HIL - INTEGRAÇÃO FPUMASTER
"""

import os
from pathlib import Path
import config

def create_hil_structure():
    """Cria estrutura completa HIL dentro do fpuMaster."""
    print("🚀 CRIANDO ESTRUTURA HIL NO FPUMASTER...")
    
    # Diretório base HIL
    HIL_BASE = config.ROOT / "hil"
    
    # Estrutura completa de pastas
    hil_structure = [
        # FASE 1: Prova de Conceito
        HIL_BASE / "01_proof_of_concept",
        HIL_BASE / "01_proof_of_concept" / "blink_led",
        HIL_BASE / "01_proof_of_concept" / "blink_led" / "quartus",
        HIL_BASE / "01_proof_of_concept" / "blink_led" / "src",
        HIL_BASE / "01_proof_of_concept" / "blink_led" / "tests",
        
        HIL_BASE / "01_proof_of_concept" / "serial_communication",
        HIL_BASE / "01_proof_of_concept" / "serial_communication" / "uart_cores",
        HIL_BASE / "01_proof_of_concept" / "serial_communication" / "python_scripts",
        HIL_BASE / "01_proof_of_concept" / "serial_communication" / "test_sequences",
        
        # FASE 2: Framework Genérico
        HIL_BASE / "02_framework",
        HIL_BASE / "02_framework" / "communication",
        HIL_BASE / "02_framework" / "communication" / "protocols",
        HIL_BASE / "02_framework" / "communication" / "drivers",
        
        HIL_BASE / "02_framework" / "stimulus_generation",
        HIL_BASE / "02_framework" / "stimulus_generation" / "integer",
        HIL_BASE / "02_framework" / "stimulus_generation" / "fpu",
        HIL_BASE / "02_framework" / "stimulus_generation" / "edge_cases",
        
        HIL_BASE / "02_framework" / "oracle",
        HIL_BASE / "02_framework" / "oracle" / "reference_models",
        HIL_BASE / "02_framework" / "oracle" / "validation",
        
        HIL_BASE / "02_framework" / "test_management",
        HIL_BASE / "02_framework" / "test_management" / "test_cases",
        HIL_BASE / "02_framework" / "test_management" / "results",
        
        # FASE 3: Métricas e Tradeoffs
        HIL_BASE / "03_metrics",
        HIL_BASE / "03_metrics" / "basic_metrics",
        HIL_BASE / "03_metrics" / "basic_metrics" / "integer_ops",
        HIL_BASE / "03_metrics" / "basic_metrics" / "fpu_ops",
        
        HIL_BASE / "03_metrics" / "tradeoff_analysis",
        HIL_BASE / "03_metrics" / "tradeoff_analysis" / "area_vs_performance",
        HIL_BASE / "03_metrics" / "tradeoff_analysis" / "power_vs_accuracy",
        HIL_BASE / "03_metrics" / "tradeoff_analysis" / "timing_vs_precision",
        
        HIL_BASE / "03_metrics" / "statistical_sampling",
        HIL_BASE / "03_metrics" / "statistical_sampling" / "monte_carlo",
        HIL_BASE / "03_metrics" / "statistical_sampling" / "metropolis",
        HIL_BASE / "03_metrics" / "statistical_sampling" / "random_walk",
        
        HIL_BASE / "03_metrics" / "error_analysis",
        HIL_BASE / "03_metrics" / "error_analysis" / "ulp_error",
        HIL_BASE / "03_metrics" / "error_analysis" / "relative_error",
        HIL_BASE / "03_metrics" / "error_analysis" / "absolute_error",
        
        # FASE 4: Orquestração e Integração
        HIL_BASE / "04_orchestration",
        HIL_BASE / "04_orchestration" / "pipeline",
        HIL_BASE / "04_orchestration" / "pipeline" / "rtl_to_fpga",
        HIL_BASE / "04_orchestration" / "pipeline" / "fpga_to_metrics",
        HIL_BASE / "04_orchestration" / "pipeline" / "results_to_reports",
        
        HIL_BASE / "04_orchestration" / "integration",
        HIL_BASE / "04_orchestration" / "integration" / "fpuMaster_hooks",
        HIL_BASE / "04_orchestration" / "integration" / "automation_scripts",
        
        HIL_BASE / "04_orchestration" / "reports",
        HIL_BASE / "04_orchestration" / "reports" / "hil_reports",
        HIL_BASE / "04_orchestration" / "reports" / "comparative_analysis",
        
        # Configurações e Utilitários
        HIL_BASE / "config",
        HIL_BASE / "config" / "fpga_settings",
        HIL_BASE / "config" / "test_configurations",
        
        HIL_BASE / "utils",
        HIL_BASE / "utils" / "file_handling",
        HIL_BASE / "utils" / "data_processing",
        HIL_BASE / "utils" / "visualization",
        
        # Logs e Temporários
        HIL_BASE / "logs",
        HIL_BASE / "logs" / "execution_logs",
        HIL_BASE / "logs" / "debug_logs",
        
        HIL_BASE / "temp",
        HIL_BASE / "temp" / "upload_files",
        HIL_BASE / "temp" / "results_cache",
    ]
    
    # Criar todas as pastas
    created_count = 0
    for directory in hil_structure:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory.relative_to(config.ROOT)}")
            created_count += 1
    
    # Criar arquivos de configuração essenciais
    _create_config_files(HIL_BASE)
    
    # Criar scripts principais
    _create_main_scripts(HIL_BASE)
    
    print(f"\n🎯 ESTRUTURA HIL CRIADA: {created_count} pastas")
    _show_hil_tree(HIL_BASE)

def _create_config_files(hil_base):
    """Cria arquivos de configuração essenciais."""
    
    # Configuração principal HIL
    main_config = hil_base / "config" / "hil_config.py"
    if not main_config.exists():
        main_config.write_text(_hil_config_content())
        print("   📄 hil_config.py criado")
    
    # Configuração FPGA DE1-SoC
    fpga_config = hil_base / "config" / "fpga_settings" / "de1_soc_config.py"
    if not fpga_config.exists():
        fpga_config.write_text(_fpga_config_content())
        print("   📄 de1_soc_config.py criado")
    
    # Exemplo de configuração de teste
    test_config = hil_base / "config" / "test_configurations" / "integer_add.json"
    if not test_config.exists():
        test_config.write_text(_test_config_content())
        print("   📄 integer_add.json criado")

def _create_main_scripts(hil_base):
    """Cria scripts principais."""
    
    # Script principal HIL
    main_script = hil_base / "run_hil.py"
    if not main_script.exists():
        main_script.write_text(_main_script_content())
        print("   📄 run_hil.py criado")
    
    # Communication driver
    comm_script = hil_base / "02_framework" / "communication" / "fpga_driver.py"
    if not comm_script.exists():
        comm_script.write_text(_fpga_driver_content())
        print("   📄 fpga_driver.py criado")
    
    # Stimulus generator
    stimulus_script = hil_base / "02_framework" / "stimulus_generation" / "stimulus_generator.py"
    if not stimulus_script.exists():
        stimulus_script.write_text(_stimulus_generator_content())
        print("   📄 stimulus_generator.py criado")

def _hil_config_content():
    return '''"""
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
'''

def _fpga_config_content():
    return '''"""
CONFIGURAÇÃO FPGA DE1-SoC
"""

# Pinos DE1-SoC
DE1_SOC_PINS = {
    'CLOCK_50': 'PIN_AF14',
    'UART_RXD': 'PIN_AF15', 
    'UART_TXD': 'PIN_AG16',
    'LEDG': ['PIN_W15', 'PIN_AA24', 'PIN_V16', 'PIN_V15', 
             'PIN_AF26', 'PIN_AE26', 'PIN_Y16', 'PIN_AA23'],
    'LEDR': ['PIN_AE12', 'PIN_AD12', 'PIN_AF13', 'PIN_AF12', 'PIN_AH11']
}

# Configurações Quartus
QUARTUS_SETTINGS = {
    'family': 'Cyclone V',
    'device': '5CSEMA5F31C6',
    'top_level_entity': 'hil_top'
}
'''

def _test_config_content():
    return '''{
    "test_name": "integer_add",
    "operation": "add",
    "data_type": "integer",
    "bit_width": 32,
    "test_cases": [
        {"a": 10, "b": 20, "expected": 30},
        {"a": 0, "b": 0, "expected": 0},
        {"a": 255, "b": 1, "expected": 256}
    ],
    "generator": "random",
    "samples": 100,
    "metrics": ["accuracy", "latency", "throughput"]
}
'''

def _main_script_content():
    return '''"""
SCRIPT PRINCIPAL HIL - FPUMASTER
"""

import sys
from pathlib import Path

# Adiciona diretório HIL ao path
HIL_BASE = Path(__file__).parent
sys.path.append(str(HIL_BASE))

from config.hil_config import *
from utils.logger import setup_logger
from orchestration.pipeline.hil_orchestrator import HILOrchestrator

def main():
    """Executa pipeline HIL completo."""
    print("🚀 INICIANDO HIL FPUMASTER")
    
    # Setup
    logger = setup_logger()
    orchestrator = HILOrchestrator()
    
    try:
        # 1. Carrega configuração
        config = orchestrator.load_config()
        
        # 2. Conecta com FPGA
        if not orchestrator.connect_fpga():
            logger.error("Falha na conexão FPGA")
            return
        
        # 3. Executa testes baseado no módulo
        results = orchestrator.run_test_pipeline(config)
        
        # 4. Gera relatórios
        orchestrator.generate_reports(results)
        
        print("✅ HIL EXECUTADO COM SUCESSO!")
        
    except Exception as e:
        logger.error(f"Erro no HIL: {e}")
        raise

if __name__ == "__main__":
    main()
'''

def _fpga_driver_content():
    return '''"""
DRIVER DE COMUNICAÇÃO FPGA
"""

import serial
import time
from config.hil_config import *

class FPGADriver:
    def __init__(self):
        self.serial = None
        self.connected = False
    
    def connect(self):
        """Conecta com FPGA via serial."""
        try:
            self.serial = serial.Serial(
                port=FPGA_SERIAL_PORT,
                baudrate=FPGA_BAUDRATE,
                timeout=FPGA_TIMEOUT
            )
            self.connected = True
            print("✅ Conectado à FPGA")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def send_operation(self, operation, operands):
        """Envia operação para FPGA."""
        if not self.connected:
            raise Exception("FPGA não conectada")
        
        # Formata comando (protocolo simples)
        command = f"{operation}:{','.join(map(str, operands))}\\n"
        self.serial.write(command.encode())
        
        # Aguarda resposta
        response = self.serial.readline().decode().strip()
        return response
    
    def close(self):
        """Fecha conexão."""
        if self.serial:
            self.serial.close()
            self.connected = False
'''

def _stimulus_generator_content():
    return '''"""
GERADOR DE ESTÍMULOS
"""

import random
import numpy as np
from config.hil_config import *

class StimulusGenerator:
    def generate_integer_stimuli(self, operation, samples=1000, bit_width=32):
        """Gera estímulos para operações inteiras."""
        max_val = 2**(bit_width-1) - 1
        min_val = -2**(bit_width-1)
        
        stimuli = []
        for _ in range(samples):
            a = random.randint(min_val, max_val)
            b = random.randint(min_val, max_val)
            stimuli.append((a, b))
        
        return stimuli
    
    def generate_fpu_stimuli(self, operation, samples=1000, method='monte_carlo'):
        """Gera estímulos para operações FPU."""
        if method == 'monte_carlo':
            return self._monte_carlo_sampling(samples)
        elif method == 'edge_cases':
            return self._edge_case_sampling()
        else:
            return self._random_sampling(samples)
    
    def _monte_carlo_sampling(self, samples):
        """Amostragem Monte Carlo para FPU."""
        stimuli = []
        for _ in range(samples):
            # Gera números de ponto flutuante aleatórios
            a = random.uniform(-1000.0, 1000.0)
            b = random.uniform(-1000.0, 1000.0)
            stimuli.append((a, b))
        return stimuli
    
    def _edge_case_sampling(self):
        """Casos de borda importantes para FPU."""
        edge_cases = [
            (0.0, 0.0), (1.0, 0.0), (-1.0, 0.0),
            (float('inf'), 1.0), (-float('inf'), 1.0),
            (float('nan'), 1.0), (1.0, float('nan')),
            (1.0e-10, 1.0e10), (1.0e10, 1.0e-10)
        ]
        return edge_cases
'''

def _show_hil_tree(hil_base):
    """Mostra árvore da estrutura HIL criada."""
    print("\n🌳 ESTRUTURA HIL CRIADA:")
    print("hil/")
    _print_tree(hil_base, "    ")

def _print_tree(directory, prefix):
    """Imprime árvore de diretórios."""
    items = list(directory.iterdir())
    items.sort()
    
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        
        if item.is_dir():
            print(f"{prefix}{connector}{item.name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            _print_tree(item, new_prefix)
        else:
            print(f"{prefix}{connector}{item.name}")

if __name__ == "__main__":
    create_hil_structure()
    print("\n🎉 ESTRUTURA HIL PRONTA! Agora execute:")
    print("   python hil/run_hil.py")