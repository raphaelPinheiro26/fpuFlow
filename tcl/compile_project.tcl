# ============================================================
# Script: compile_project_lite.tcl
# Function: Full Quartus Lite compilation flow with multicore and power analysis
# Author: Raphael (adapted for Lite)
# ============================================================

# === [CONFIGURATION] =======================================
set project_name "rca"
set revision_name $project_name

# Caminho do Quartus (ajuste se necessário)
set quartus_bin "C:/intelFPGA_lite/20.1/quartus/bin64"

if {[file exists $quartus_bin]} {
    set env(PATH) "$quartus_bin;$env(PATH)"
    puts ">>> Quartus adicionado ao PATH: $quartus_bin"
} else {
    puts "⚠️ Caminho do Quartus não encontrado: $quartus_bin"
}

# === [OPEN OR CREATE PROJECT] ==============================
if {[file exists "$project_name.qpf"]} {
    project_open "$project_name.qpf"
    puts ">>> Projeto existente aberto: $project_name.qpf"
} else {
    project_new $project_name .
    puts ">>> Novo projeto criado: $project_name"
}

# === [MULTICORE SETUP] =====================================
if {[info exists ::env(NUMBER_OF_PROCESSORS)]} {
    set num_cores $::env(NUMBER_OF_PROCESSORS)
} elseif {[info exists ::env(NPROC)]} {
    set num_cores $::env(NPROC)
} else {
    set num_cores 4
}
puts ">>> Detectado $num_cores núcleos de CPU."
set_global_assignment -name NUM_PARALLEL_PROCESSORS $num_cores

# === [LOG FILES] ==========================================
set base_log "${project_name}_compile"
set compile_log "${base_log}.log"
set pow_log "${base_log}_pow.log"

# === [START TIMER] ========================================
set start_time [clock seconds]
puts "====================================="
puts "   Iniciando compilação do projeto (Quartus Lite)"
puts "   Projeto: $project_name"
puts "====================================="

# === [COMPILATION FLOW] ===================================
# Quartus Lite: compile flow único
if {[catch {
    exec quartus_sh --flow compile $project_name >> $compile_log 2>@1
} err]} {
    puts "❌ Erro durante a compilação do projeto!"
    puts "Mensagem: $err"
    exit 1
} else {
    puts "✅ Compilação concluída com sucesso."
}

# === [POWER ANALYSIS] ======================================
if {[file exists "power_settings.tcl"]} {
    puts ">>> Etapa: Power Analysis (com script TCL customizado)..."
    if {[catch {exec quartus_pow --read_settings_files=on --write_settings_files=off --tcl_script=power_settings.tcl $project_name >> $pow_log 2>@1} err]} {
        puts "❌ Erro na análise de potência!"
        puts "Mensagem: $err"
    } else {
        puts "✅ Análise de potência concluída."
    }
} else {
    puts ">>> Etapa: Power Analysis (modo padrão)..."
    if {[catch {exec quartus_pow --read_settings_files=on --write_settings_files=off $project_name >> $pow_log 2>@1} err]} {
        puts "❌ Erro na análise de potência!"
        puts "Mensagem: $err"
    } else {
        puts "✅ Análise de potência concluída."
    }
}

# === [FINALIZATION] ========================================
set end_time [clock seconds]
set total_time [expr {$end_time - $start_time}]
set minutes [expr {$total_time / 60}]
set seconds [expr {$total_time % 60}]

puts "====================================="
puts "   Tempo total: ${minutes}m ${seconds}s"
puts "   Logs gerados:"
puts "     - $compile_log"
puts "     - $pow_log"
puts "====================================="
