# ============================================================
# File: de1soc.sdc
# Purpose: Clock and timing constraints for DE1-SoC board
# Author: Raphael
# ============================================================

# === CLOCK PRINCIPAL 50 MHz ===
create_clock -name CLOCK_50 -period 20.0 [get_ports {CLOCK_50}]

# === MARGEM DE INSEGURANÇA / JITTER ===
set_clock_uncertainty -to [get_clocks {CLOCK_50}] 0.2

# === PADRÕES DE ENTRADA/SAÍDA (opcional) ===
set_input_delay  1.500 -clock [get_clocks {CLOCK_50}] [all_inputs]
set_output_delay 1.500 -clock [get_clocks {CLOCK_50}] [all_outputs]