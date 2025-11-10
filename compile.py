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
# DEPENDÊNCIAS RECURSIVAS
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
# CÓPIA HIERÁRQUICA CORRIGIDA PARA ESTRUTURA NUMERADA
# ========================
# compile.py - Função copy_hierarchical_projects corrigida

# compile.py - Função copy_hierarchical_projects corrigida

def copy_hierarchical_projects(tree, parent_path=None, current_depth=0):
    """
    Versão CORRIGIDA - processa apenas módulos que estão no JSON
    """
    if parent_path is None:
        parent_path = config.RTL_DIR

    built_projects = []
    
    # Coleta todos os módulos válidos do JSON
    valid_modules = get_all_modules_from_tree(tree)
    print(f"🎯 Módulos válidos no JSON: {', '.join(valid_modules)}")

    for name, node in tree.items():
        rtl_path = parent_path / name
        print(f"{'  ' * current_depth}🔍 Explorando: {name}")

        if not rtl_path.exists():
            print(f"{'  ' * current_depth}⚠️ Pasta {rtl_path} não encontrada.")
            continue

        # Para categorias principais, navega nas subpastas numeradas
        if name.startswith(('01_', '02_', '03_', '04_', '05_', '06_')):
            for subdir in rtl_path.iterdir():
                if subdir.is_dir() and any(subdir.name.startswith(f"{i:02d}_") for i in range(1, 7)):
                    print(f"{'  ' * (current_depth + 1)}📁 Subpasta: {subdir.name}")
                    
                    # Processa arquivos .v nesta subpasta APENAS se estiverem no JSON
                    for verilog_file in subdir.glob("*.v"):
                        module_name = verilog_file.stem
                        
                        # 🔥 FILTRO: Só processa se o módulo está no JSON
                        if module_name not in valid_modules:
                            print(f"{'  ' * (current_depth + 2)}⏭️  Ignorado (não está no JSON): {module_name}")
                            continue
                        
                        # Cria pasta única para cada projeto no build
                        project_path = config.BUILD_DIR / module_name
                        project_path.mkdir(parents=True, exist_ok=True)
                        
                        # Copia RTL para pasta do projeto
                        dst_file = project_path / verilog_file.name
                        shutil.copy(verilog_file, dst_file)
                        
                        # Encontra e copia testbench
                        tb_file = find_corresponding_tb(verilog_file)
                        tb_files = []
                        if tb_file and tb_file.exists():
                            tb_dst = project_path / tb_file.name
                            shutil.copy(tb_file, tb_dst)
                            tb_files = [tb_dst]
                        
                        # Encontra e copia SDC
                        sdc_files = find_corresponding_sdc(verilog_file)
                        copied_sdc_files = []
                        for sdc_file in sdc_files:
                            sdc_dst = project_path / sdc_file.name
                            shutil.copy(sdc_file, sdc_dst)
                            copied_sdc_files.append(sdc_dst)
                        
                        # Copia dependências
                        all_rtl_files = copy_dependencies(module_name, project_path, tree)
                        all_rtl_files.append(dst_file)
                        
                        print(f"{'  ' * (current_depth + 2)}📦 {module_name}")
                        print(f"{'  ' * (current_depth + 3)}📁 Build: {project_path.name}")
                        
                        built_projects.append((module_name, project_path, all_rtl_files, copied_sdc_files))

        # Processa recursivamente os nós filhos
        if isinstance(node, dict):
            for subname, subnode in node.items():
                if isinstance(subnode, dict):
                    sub_rtl_path = rtl_path / subname
                    if sub_rtl_path.exists():
                        built_projects.extend(
                            copy_hierarchical_projects(
                                {subname: subnode}, 
                                rtl_path, 
                                current_depth + 1
                            )
                        )

    print(f"✅ {len(built_projects)} projetos processados do JSON")
    return built_projects

def get_all_modules_from_tree(tree):
    """Extrai todos os nomes de módulos da árvore JSON"""
    modules = set()
    
    def extract_modules(node):
        if isinstance(node, dict):
            for key, value in node.items():
                modules.add(key)
                if isinstance(value, dict):
                    extract_modules(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            modules.add(item)
    
    extract_modules(tree)
    return modules

def copy_dependencies(module_name, project_path, dependencies_tree):
    """Copia todas as dependências de um módulo para a pasta do projeto"""
    dependencies = get_all_dependencies_from_tree(module_name, dependencies_tree)
    copied_files = []
    
    for dep in dependencies:
        # Busca o arquivo de dependência em toda a estrutura RTL
        found = False
        for rtl_file in config.RTL_DIR.rglob(f"{dep}.v"):
            dst_file = project_path / rtl_file.name
            if not dst_file.exists():  # Evita duplicatas
                shutil.copy(rtl_file, dst_file)
                copied_files.append(dst_file)
                print(f"{'  ' * 4}📄 Dep: {dep}.v")
            found = True
            break
        
        if not found:
            print(f"{'  ' * 4}⚠️ Dep não encontrada: {dep}.v")
    
    return copied_files

def get_all_dependencies_from_tree(module, dependencies_tree, seen=None):
    """Obtém todas as dependências recursivamente da árvore hierárquica"""
    if seen is None:
        seen = set()
    if module in seen:
        return set()
    seen.add(module)
    
    deps = set()
    
    # Função auxiliar para buscar em toda a árvore
    def find_dependencies_in_node(node, current_module):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == current_module:
                    if isinstance(value, list):
                        return set(value)
                    elif isinstance(value, dict):
                        return set(value.keys())
                elif isinstance(value, dict):
                    result = find_dependencies_in_node(value, current_module)
                    if result:
                        return result
        return set()
    
    # Encontra dependências diretas
    direct_deps = find_dependencies_in_node(dependencies_tree, module)
    deps.update(direct_deps)
    
    # Encontra dependências recursivas
    for dep in direct_deps:
        deps.update(get_all_dependencies_from_tree(dep, dependencies_tree, seen))
    
    return deps

def find_corresponding_tb(rtl_file):
    """Encontra o testbench correspondente a um arquivo RTL"""
    # Caminho correspondente em TB
    rtl_relative = rtl_file.relative_to(config.RTL_DIR)
    tb_candidate = config.TB_DIR / rtl_relative.parent / f"{rtl_file.stem}_tb.v"
    
    if tb_candidate.exists():
        return tb_candidate
    
    # Tenta com .sv
    tb_candidate = config.TB_DIR / rtl_relative.parent / f"{rtl_file.stem}_tb.sv"
    if tb_candidate.exists():
        return tb_candidate
    
    # Busca recursiva como fallback
    for tb_file in config.TB_DIR.rglob(f"{rtl_file.stem}_tb.v"):
        return tb_file
    for tb_file in config.TB_DIR.rglob(f"{rtl_file.stem}_tb.sv"):
        return tb_file
    
    return None



def find_corresponding_sdc(rtl_file):
    """Copia QUALQUER arquivo .sdc da pasta SDC_DIR para o projeto"""
    sdc_files = []
    
    # Busca TODOS os arquivos .sdc no diretório SDC
    for sdc_file in config.SDC_DIR.glob("*.sdc"):
        if sdc_file.exists():
            sdc_files.append(sdc_file)
            print(f"   ✅ SDC encontrado: {sdc_file.name}")
    
    if not sdc_files:
        print(f"   ⚠️ Nenhum arquivo .sdc encontrado em {config.SDC_DIR}")
        print(f"   📁 Será usado clock padrão no relatório")
    
    return sdc_files

# ========================
# CÓPIA PLANA (COMPATIBILIDADE)
# ========================
def copy_files_for_project(project_name, module_name, dependencies_dict):
    """Modo de compatibilidade - busca em toda a estrutura"""
    project_path = config.BUILD_DIR / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    all_deps = get_all_dependencies(module_name, dependencies_dict)
    files_to_copy = [module_name] + list(all_deps)
    copied_files = []

    for module in files_to_copy:
        # Busca recursiva pelo arquivo .v
        found = False
        for rtl_file in config.RTL_DIR.rglob(f"{module}.v"):
            dst_file = project_path / rtl_file.name
            shutil.copy(rtl_file, dst_file)
            copied_files.append(dst_file)
            found = True
            break
        
        if not found:
            print(f"⚠️ Arquivo {module}.v não encontrado em {config.RTL_DIR}!")

    # Copia SDCs
    sdc_files = list(config.SDC_DIR.glob("*.sdc"))
    copied_sdc_files = []
    for sdc_file in sdc_files:
        dst_sdc = project_path / sdc_file.name
        shutil.copy(sdc_file, dst_sdc)
        copied_sdc_files.append(dst_sdc)

    print(f"📂 Arquivos copiados: {[f.name for f in copied_files + copied_sdc_files]}")
    return project_path, copied_files, copied_sdc_files

# ========================
# GERAÇÃO DE QSF OTIMIZADA
# ========================
def generate_optimized_qsf(project_path, top_module, rtl_files, sdc_files=[]):
    qsf_path = project_path / f"{top_module}.qsf"
    
    with open(qsf_path, "w") as f:
        f.write("# =============================================================================\n")
        f.write("# CONFIGURAÇÕES OTIMIZADAS - QUARTUS LITE COMPATIBLE\n")
        f.write("# =============================================================================\n\n")
        
        # Configurações básicas
        f.write('set_global_assignment -name FAMILY "Cyclone V"\n')
        f.write('set_global_assignment -name DEVICE 5CSEMA5F31C6\n')
        f.write(f'set_global_assignment -name TOP_LEVEL_ENTITY {top_module}\n')
        f.write('set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n')
        f.write('set_global_assignment -name BOARD "DE1-SoC Board"\n\n')
        
        # Power settings
        f.write('# POWER SETTINGS\n')
        f.write('set_global_assignment -name POWER_PRESET_COOLING_SOLUTION "23 MM HEAT SINK WITH 200 LFPM AIRFLOW"\n')
        f.write('set_global_assignment -name POWER_BOARD_THERMAL_MODEL "NONE (CONSERVATIVE)"\n')
        f.write('set_global_assignment -name POWER_USE_INPUT_FILES OFF\n')
        f.write('set_global_assignment -name POWER_DEFAULT_INPUT_IO_TOGGLE_RATE "12.5%"\n')
        f.write('set_global_assignment -name POWER_HPS_ENABLE OFF\n\n')
        
        # Otimizações
        f.write('# OTIMIZAÇÕES DE PERFORMANCE\n')
        f.write('set_global_assignment -name OPTIMIZATION_MODE "AGGRESSIVE PERFORMANCE"\n')
        f.write('set_global_assignment -name PHYSICAL_SYNTHESIS_EFFORT "EXTRA"\n')
        f.write('set_global_assignment -name TIMING_ANALYZER_MULTICORNER_ANALYSIS ON\n')
        f.write('set_global_assignment -name NUM_PARALLEL_PROCESSORS ALL\n\n')
        
        # Arquivos
        f.write('# ARQUIVOS DE DESIGN\n')
        for rtl in rtl_files:
            rel_path = os.path.relpath(rtl, project_path)
            f.write(f'set_global_assignment -name VERILOG_FILE "{rel_path}"\n')
        
        for sdc in sdc_files:
            f.write(f'set_global_assignment -name SDC_FILE "{sdc.name}"\n')
        f.write('\n')
        
        # Pin assignments
        f.write('# PIN ASSIGNMENTS ESSENCIAIS\n')
        f.write('set_location_assignment PIN_AF14 -to CLOCK_50\n')
        f.write('set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50\n\n')
        
        f.write("# =============================================================================\n")
        f.write("# FIM DAS CONFIGURAÇÕES\n")
        f.write("# =============================================================================\n")

    print(f"✅ QSF gerado: {qsf_path.name}")
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