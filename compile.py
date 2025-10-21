import os
import subprocess
import time
import re
import shutil
import config

# ========================
# FUNÇÕES AUXILIARES
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
# CRIAÇÃO DO PROJETO
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

def copy_files_for_project(project_name, module_name, dependencies_dict):
    project_path = config.BUILD_DIR / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # pega todas as dependências recursivamente
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

    # Copiar arquivos SDC da pasta config.SDC_DIR
    sdc_files = list(config.SDC_DIR.glob("*.sdc"))
    copied_sdc_files = []
    for sdc_file in sdc_files:
        dst_sdc = project_path / sdc_file.name
        shutil.copy(sdc_file, dst_sdc)
        copied_sdc_files.append(dst_sdc)

    print(f"📂 Arquivos copiados: {[f.name for f in copied_files + copied_sdc_files]}")
    return project_path, copied_files, copied_sdc_files



def generate_qsf(project_path, top_module, rtl_files, sdc_files=[]):
    qsf_path = project_path / f"{top_module}.qsf"
    with open(qsf_path, "w") as f:
        # --------------------------------------
        # Informações gerais do projeto
        # --------------------------------------
        f.write(f'set_global_assignment -name FAMILY "Cyclone V"\n')
        f.write(f'set_global_assignment -name DEVICE 5CSEMA5F31C6\n')
        f.write(f'set_global_assignment -name TOP_LEVEL_ENTITY {top_module}\n')
        f.write(f'set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n')
        f.write(f'set_global_assignment -name NUM_PARALLEL_PROCESSORS ALL\n')
        f.write(f'set_global_assignment -name ORIGINAL_QUARTUS_VERSION 20.1.1\n')
        f.write(f'set_global_assignment -name LAST_QUARTUS_VERSION "20.1.1 Lite Edition"\n')
        f.write(f'set_global_assignment -name BOARD "DE1-SoC Board"\n')
        f.write(f'set_global_assignment -name EDA_SIMULATION_TOOL "ModelSim-Altera (SystemVerilog)"\n')
        f.write(f'set_global_assignment -name EDA_TIME_SCALE "1 ps" -section_id eda_simulation\n')
        f.write(f'set_global_assignment -name EDA_OUTPUT_DATA_FORMAT "SYSTEMVERILOG HDL" -section_id eda_simulation\n\n')

        # --------------------------------------
        # Arquivos RTL
        # --------------------------------------
        for rtl in rtl_files:
            rel_path = os.path.relpath(rtl, project_path)
            f.write(f'set_global_assignment -name VERILOG_FILE "{rel_path}"\n')

        # --------------------------------------
        # Arquivos SDC
        # --------------------------------------
        for sdc in sdc_files:
            f.write(f'set_global_assignment -name SDC_FILE "{sdc.name}"\n')

        # --------------------------------------
        # Placeholder para testbench
        # --------------------------------------
        f.write('\n# Para simulação, se houver testbench, você pode adicionar:')
        f.write('\n# set_global_assignment -name SYSTEMVERILOG_FILE <tb_file.sv>\n')

    print(f"📝 QSF gerado: {qsf_path.name}")


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
    """Atualiza o valor de um parâmetro no arquivo Verilog sem quebrar a sintaxe."""
    top_file = project_path / f"{module_name}.v"
    if not top_file.exists():
        print(f"❌ Arquivo {top_file} não encontrado.")
        return False

    with open(top_file, "r") as f:
        content = f.read()

    # Regex para capturar algo como: parameter N = 8 ou parameter N=16
    pattern = rf"(parameter\s+{param_name}\s*=\s*)(\d+)"
    replacement = r"\g<1>" + str(value)  # substitui apenas o número

    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        with open(top_file, "w") as f:
            f.write(new_content)
        print(f"🔧 Parâmetro {param_name} atualizado para {value} em {top_file.name}")
        return True
    else:
        print(f"⚠️ Parâmetro '{param_name}' não encontrado em {top_file.name} (nenhuma modificação feita)")
        return False




# ========================
# COMPILAÇÃO COMPLETA
# ========================
def compile_project(project_name, project_path):
    os.chdir(project_path)
    print(f"\n🚀 Compilando projeto {project_name} com todos os núcleos disponíveis...")

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
