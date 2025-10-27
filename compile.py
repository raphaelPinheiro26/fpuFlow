import os
import subprocess
import time
import re
import shutil
from pathlib import Path
import config
import multiprocessing

NUM_CORES = max(1, multiprocessing.cpu_count() // 2)



# ========================
# EXECUÇÃO DE COMANDOS
# ========================
def run_cmd(cmd, logfile):
    print(f"\n[EXECUTANDO] {' '.join(cmd)}")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start

    with open(logfile, "w") as f:
        f.write(result.stdout)
        f.write(result.stderr)

    if result.returncode != 0:
        print(f"❌ Erro ({elapsed:.1f}s)")
        print(result.stderr)
        return False
    else:
        print(f"✅ Sucesso ({elapsed:.1f}s)")
        return True


# ========================
# DEPENDÊNCIAS RECURSIVAS (LEGADO)
# ========================
def get_all_dependencies(module, dependencies_dict, seen=None):
    if seen is None:
        seen = set()
    if module in seen:
        return set()
    seen.add(module)
    deps = set()
    for dep in dependencies_dict.get(module, []):
        deps.add(dep)
        deps.update(get_all_dependencies(dep, dependencies_dict, seen))
    return deps


# ========================
# NOVA FUNÇÃO: CÓPIA HIERÁRQUICA
# ========================
def copy_hierarchical_projects(tree, parent_path=None):
    """
    Percorre o dicionário JSON hierárquico e replica a estrutura dentro de BUILD_DIR.
    Só copia módulos que realmente existirem em RTL_DIR.
    Retorna uma lista de (module_name, build_path, rtl_files, sdc_files).
    """
    if parent_path is None:
        parent_path = config.RTL_DIR

    built_projects = []

    for name, node in tree.items():
        rtl_path = parent_path / name
        build_path = config.BUILD_DIR / rtl_path.relative_to(config.RTL_DIR)

        # Verifica se o módulo existe
        if not rtl_path.exists():
            print(f"⚠️ Módulo '{name}' ignorado — pasta {rtl_path} não encontrada.")
            continue

        # Arquivos RTL e SDC
        rtl_files = list(rtl_path.glob("*.v"))
        sdc_files = list(rtl_path.glob("*.sdc"))

        # Só cria se houver conteúdo relevante
        if not rtl_files and not sdc_files:
            print(f"⚠️ Pasta {rtl_path} ignorada (sem arquivos .v ou .sdc).")
            continue

        # Cria diretório correspondente no build
        build_path.mkdir(parents=True, exist_ok=True)

        # Copia os arquivos
        copied_files = []
        for f in rtl_files + sdc_files:
            shutil.copy(f, build_path / f.name)
            copied_files.append(f.name)

        print(f"📂 [{name}] arquivos copiados: {copied_files}")

        built_projects.append((name, build_path, rtl_files, sdc_files))

        # Se tiver submódulos, desce um nível
        for subname, subnode in node.items():
            if isinstance(subnode, dict):
                built_projects.extend(copy_hierarchical_projects({subname: subnode}, rtl_path))

    return built_projects


# ========================
# CÓPIA PLANA (COMPATIBILIDADE LEGADA)
# ========================
def copy_files_for_project(project_name, module_name, dependencies_dict):
    project_path = config.BUILD_DIR / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    all_deps = get_all_dependencies(module_name, dependencies_dict)
    files_to_copy = [module_name] + list(all_deps)
    copied_files = []

    for f in files_to_copy:
        src_file = config.RTL_DIR / f"{f}.v"
        if not src_file.exists():
            print(f"⚠️ Arquivo {src_file} não encontrado!")
            continue
        dst_file = project_path / src_file.name
        shutil.copy(src_file, dst_file)
        copied_files.append(dst_file)

    # Copia SDCs genéricos
    sdc_files = list(config.SDC_DIR.glob("*.sdc"))
    copied_sdc_files = []
    for sdc_file in sdc_files:
        dst_sdc = project_path / sdc_file.name
        shutil.copy(sdc_file, dst_sdc)
        copied_sdc_files.append(dst_sdc)

    print(f"📂 Arquivos copiados: {[f.name for f in copied_files + copied_sdc_files]}")
    return project_path, copied_files, copied_sdc_files


# ========================
# GERAÇÃO DE QSF OTIMIZADA - COMPATÍVEL QUARTUS LITE
# ========================
def generate_optimized_qsf(project_path, top_module, rtl_files, sdc_files=[]):
    """
    Gera QSF otimizado COMPATÍVEL com Quartus Lite
    """
    qsf_path = project_path / f"{top_module}.qsf"
    
    with open(qsf_path, "w") as f:
        # =============================================================================
        # CONFIGURAÇÕES GLOBAIS (COMPROVADAS E COMPATÍVEIS)
        # =============================================================================
        f.write("# =============================================================================\n")
        f.write("# CONFIGURAÇÕES OTIMIZADAS - QUARTUS LITE COMPATIBLE\n")
        f.write("# =============================================================================\n\n")
        
        # BÁSICO (100% COMPATÍVEL)
        f.write('set_global_assignment -name FAMILY "Cyclone V"\n')
        f.write('set_global_assignment -name DEVICE 5CSEMA5F31C6\n')
        f.write(f'set_global_assignment -name TOP_LEVEL_ENTITY {top_module}\n')
        f.write('set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n')
        f.write('set_global_assignment -name BOARD "DE1-SoC Board"\n\n')
        
        # POWER SETTINGS (COMPATÍVEIS)
        f.write('# POWER SETTINGS - CONFIGURAÇÕES ESTÁVEIS\n')
        f.write('set_global_assignment -name POWER_PRESET_COOLING_SOLUTION "23 MM HEAT SINK WITH 200 LFPM AIRFLOW"\n')
        f.write('set_global_assignment -name POWER_BOARD_THERMAL_MODEL "NONE (CONSERVATIVE)"\n')
        f.write('set_global_assignment -name POWER_USE_INPUT_FILES OFF\n')
        f.write('set_global_assignment -name POWER_DEFAULT_INPUT_IO_TOGGLE_RATE "12.5%"\n')
        f.write('set_global_assignment -name POWER_HPS_ENABLE OFF\n\n')  # 🔥 CRÍTICO!
        
        # OTIMIZAÇÕES DE TIMING (COMPATÍVEIS)
        f.write('# OTIMIZAÇÕES DE PERFORMANCE\n')
        f.write('set_global_assignment -name OPTIMIZATION_MODE "AGGRESSIVE PERFORMANCE"\n')
        f.write('set_global_assignment -name PHYSICAL_SYNTHESIS_EFFORT "EXTRA"\n')
        f.write('set_global_assignment -name TIMING_ANALYZER_MULTICORNER_ANALYSIS ON\n')
        f.write('set_global_assignment -name NUM_PARALLEL_PROCESSORS ALL\n\n')
        
        # =============================================================================
        # ARQUIVOS
        # =============================================================================
        f.write('# ARQUIVOS DE DESIGN\n')
        for rtl in rtl_files:
            rel_path = os.path.relpath(rtl, project_path)
            f.write(f'set_global_assignment -name VERILOG_FILE "{rel_path}"\n')
        
        for sdc in sdc_files:
            f.write(f'set_global_assignment -name SDC_FILE "{sdc.name}"\n')
        f.write('\n')
        
        # =============================================================================
        # PIN ASSIGNMENTS BÁSICOS (APENAS O ESSENCIAL)
        # =============================================================================
        f.write('# PIN ASSIGNMENTS ESSENCIAIS\n')
        f.write('set_location_assignment PIN_AF14 -to CLOCK_50\n')
        f.write('set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50\n\n')
        
        # =============================================================================
        # CURRENT STRENGTH CONSERVADORA (COMPATÍVEL)
        # =============================================================================
        f.write('# CURRENT STRENGTH - CONFIGURAÇÃO CONSERVADORA\n')
        f.write('# LEDs\n')
        for i in range(8):
            f.write(f'set_instance_assignment -name CURRENT_STRENGTH_NEW "8MA" -to LEDR[{i}]\n')
        
        f.write('# 7-Segment Displays\n')
        for i in range(7):
            f.write(f'set_instance_assignment -name CURRENT_STRENGTH_NEW "8MA" -to HEX0[{i}]\n')
            f.write(f'set_instance_assignment -name CURRENT_STRENGTH_NEW "8MA" -to HEX1[{i}]\n')
        f.write('\n')
        
        # =============================================================================
        # CONFIGURAÇÕES ADICIONAIS COMPATÍVEIS
        # =============================================================================
        f.write('# CONFIGURAÇÕES DE COMPILAÇÃO COMPATÍVEIS\n')
        f.write('set_global_assignment -name ADV_NETLIST_OPT_SYNTH_WYSIWYG_REMAP ON\n')
        f.write('set_global_assignment -name ALLOW_POWER_UP_DONT_CARE OFF\n')
        f.write('set_global_assignment -name AUTO_PACKED_REGISTERS_STRATIXII OFF\n')
        
        # FLOW ENABLE (COMPATÍVEL)
        f.write('set_global_assignment -name FLOW_ENABLE_POWER_ANALYZER ON\n\n')
        
        f.write("# =============================================================================\n")
        f.write("# FIM DAS CONFIGURAÇÕES COMPATÍVEIS\n")
        f.write("# =============================================================================\n")

    print(f"✅ QSF COMPATÍVEL gerado: {qsf_path.name}")
    print(f"   • 100% compatível com Quartus Lite")
    print(f"   • POWER_HPS_ENABLE OFF (crítico)")
    print(f"   • Removidos comandos não suportados")
    
    return qsf_path

# ========================
# CRIAÇÃO DO QPF
# ========================
def create_qpf(project_path, project_name):
    qpf_path = project_path / f"{project_name}.qpf"
    if not qpf_path.exists():
        with open(qpf_path, "w") as f:
            f.write(f'QUARTUS_VERSION = "20.1"\n')
            f.write(f'PROJECT_REVISION = "{project_name}"\n')
        print("🆕 QPF criado.")
    else:
        print("ℹ️ QPF já existente.")


# ========================
# ALTERAR PARÂMETRO N
# ========================
def set_parameter_in_verilog(module_name, project_path, param_name, value):
    top_file = project_path / f"{module_name}.v"
    if not top_file.exists():
        print(f"❌ Arquivo {top_file} não encontrado.")
        return False

    with open(top_file, "r") as f:
        content = f.read()

    pattern = rf"(parameter\s+{param_name}\s*=\s*)(\d+)"
    replacement = r"\g<1>" + str(value)

    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        with open(top_file, "w") as f:
            f.write(new_content)
        print(f"🔧 Parâmetro {param_name} atualizado para {value} em {top_file.name}")
        return True
    else:
        print(f"⚠️ Parâmetro '{param_name}' não encontrado em {top_file.name}")
        return False


# ========================
# COMPILAÇÃO COMPLETA
# ========================
def compile_project(project_name, project_path):
    os.chdir(project_path)
    print(f"\n🚀 Compilando projeto {project_name}...")

    success = run_cmd(
        [
            f"{config.QUARTUS_BIN}\\quartus_sh",
            "--flow", "compile",
            project_name
        ],
        logfile=project_path / "quartus_compile.log"
    )
    if not success:
        return False

    print("\n⚡ Executando análise de potência (quartus_pow)...")
    run_cmd(
        [f"{config.QUARTUS_BIN}\\quartus_pow", project_name],
        logfile=project_path / "quartus_power.log"
    )
    return True
