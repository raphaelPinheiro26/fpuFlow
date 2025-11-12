"""
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
