# compile.py
"""
COMPILAÇÃO QUARTUS E GERENCIAMENTO DE PROJETOS

Responsável por:
- Cópia e organização de arquivos
- Geração de arquivos de projeto Quartus
- Compilação e análise de potência
- Processamento de parâmetros
"""

import os
import subprocess
import time
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Set, Dict, Any

import config

# =============================================================================
# TIPOS DE DADOS
# =============================================================================

ProjectFiles = Tuple[Path, List[Path], List[Path]]  # (project_path, rtl_files, sdc_files)

# =============================================================================
# EXECUÇÃO DE COMANDOS EXTERNOS
# =============================================================================

def run_cmd(cmd: List[str], logfile: Path) -> bool:
    """Executa comando externo e salva log."""
    print(f"\n[EXECUTANDO] {' '.join(cmd)}")
    start = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start

    # Salva log
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

# =============================================================================
# GERENCIAMENTO DE DEPENDÊNCIAS
# =============================================================================

def get_all_dependencies(module: str, dependencies_dict: Dict, seen: Set = None) -> Set[str]:
    """Obtém todas as dependências recursivas de um módulo."""
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

def get_all_modules_from_tree(tree: Dict) -> Set[str]:
    """Extrai todos os nomes de módulos da árvore JSON."""
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

def get_all_dependencies_from_tree(module: str, dependencies_tree: Dict, seen: Set = None) -> Set[str]:
    """Obtém dependências recursivas da árvore hierárquica."""
    if seen is None:
        seen = set()
    if module in seen:
        return set()
    
    seen.add(module)
    deps = set()
    
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

# =============================================================================
# BUSCA DE ARQUIVOS
# =============================================================================

def find_corresponding_tb(rtl_file: Path) -> Path:
    """Encontra testbench correspondente ao arquivo RTL."""
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

def find_corresponding_sdc(rtl_file: Path) -> List[Path]:
    """Encontra arquivos SDC correspondentes."""
    sdc_files = []
    
    # Busca TODOS os arquivos .sdc no diretório SDC
    for sdc_file in config.SDC_DIR.glob("*.sdc"):
        if sdc_file.exists():
            sdc_files.append(sdc_file)
            print(f"   ✅ SDC encontrado: {sdc_file.name}")
    
    if not sdc_files:
        print(f"   ⚠️ Nenhum arquivo .sdc encontrado em {config.SDC_DIR}")
    
    return sdc_files

# =============================================================================
# CÓPIA DE ARQUIVOS E DEPENDÊNCIAS
# =============================================================================

def copy_dependencies(module_name: str, project_path: Path, dependencies_tree: Dict) -> List[Path]:
    """Copia todas as dependências para a pasta do projeto."""
    dependencies = get_all_dependencies_from_tree(module_name, dependencies_tree)
    copied_files = []
    
    for dep in dependencies:
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

def copy_project_files(module_name: str, verilog_file: Path, dependencies_tree: Dict) -> ProjectFiles:
    """Copia todos os arquivos necessários para um projeto."""
    # Cria pasta do projeto
    project_path = config.BUILD_DIR / module_name
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Copia arquivo RTL principal
    dst_file = project_path / verilog_file.name
    shutil.copy(verilog_file, dst_file)
    
    # Copia dependências
    all_rtl_files = copy_dependencies(module_name, project_path, dependencies_tree)
    all_rtl_files.append(dst_file)
    
    # Copia SDCs
    sdc_files = find_corresponding_sdc(verilog_file)
    copied_sdc_files = []
    for sdc_file in sdc_files:
        sdc_dst = project_path / sdc_file.name
        shutil.copy(sdc_file, sdc_dst)
        copied_sdc_files.append(sdc_dst)
        print(f"   📋 SDC: {sdc_file.name}")
    
    return (project_path, all_rtl_files, copied_sdc_files)

# =============================================================================
# CARREGAMENTO DE PROJETOS HIERÁRQUICOS
# =============================================================================

def copy_hierarchical_projects(tree: Dict, parent_path: Path = None, current_depth: int = 0) -> List[ProjectFiles]:
    """Carrega projetos da estrutura hierárquica."""
    if parent_path is None:
        parent_path = config.RTL_DIR

    built_projects = []
    valid_modules = get_all_modules_from_tree(tree)
    
    print(f"🎯 Módulos válidos no JSON: {list(valid_modules)[:10]}{'...' if len(valid_modules) > 10 else ''}")

    def process_directory(current_path: Path, current_tree: Dict, depth: int):
        nonlocal built_projects
        
        if not current_path.exists():
            print(f"{'  ' * depth}⚠️ Pasta não encontrada: {current_path}")
            return

        # Processa arquivos .v nesta pasta
        for verilog_file in current_path.glob("*.v"):
            module_name = verilog_file.stem
            
            # Filtra módulos não presentes no JSON
            if module_name not in valid_modules:
                print(f"{'  ' * depth}⏭️  Ignorado (não está no JSON): {module_name}")
                continue
            
            # Copia arquivos do projeto
            project_path, rtl_files, sdc_files = copy_project_files(
                module_name, verilog_file, tree
            )
            
            print(f"{'  ' * depth}📦 {module_name}")
            print(f"{'  ' * (depth + 1)}📁 Build: {project_path.name}")
            
            built_projects.append((module_name, project_path, rtl_files, sdc_files))

        # Processa subdiretórios recursivamente
        if isinstance(current_tree, dict):
            for sub_name, sub_tree in current_tree.items():
                sub_path = current_path / sub_name
                process_directory(sub_path, sub_tree, depth + 1)

    # Inicia processamento recursivo
    for name, node in tree.items():
        rtl_path = parent_path / name
        print(f"{'  ' * current_depth}🔍 Explorando: {name}")
        process_directory(rtl_path, node, current_depth + 1)

    print(f"✅ {len(built_projects)} projetos processados do JSON")
    return built_projects

# =============================================================================
# CARREGAMENTO DE PROJETOS PLANOS (COMPATIBILIDADE)
# =============================================================================

def copy_files_for_project(project_name: str, module_name: str, dependencies_dict: Dict) -> ProjectFiles:
    """Carrega projetos da estrutura plana."""
    project_path = config.BUILD_DIR / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Obtém dependências
    all_deps = get_all_dependencies(module_name, dependencies_dict)
    files_to_copy = [module_name] + list(all_deps)
    copied_files = []

    # Copia arquivos RTL
    for module in files_to_copy:
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

# =============================================================================
# GERENCIAMENTO DE PROJETOS QUARTUS
# =============================================================================

def generate_optimized_qsf(project_path: Path, top_module: str, 
                          rtl_files: List[Path], sdc_files: List[Path] = []) -> Path:
    """Gera arquivo QSF otimizado para Quartus."""
    qsf_path = project_path / f"{top_module}.qsf"
    
    with open(qsf_path, "w") as f:
        f.write("# =============================================================================\n")
        f.write("# CONFIGURAÇÕES OTIMIZADAS - QUARTUS\n")
        f.write("# =============================================================================\n\n")
        
        # Configurações básicas
        f.write('# PROJECT SETTINGS\n')
        f.write('set_global_assignment -name FAMILY "Cyclone V"\n')
        f.write('set_global_assignment -name DEVICE 5CSEMA5F31C6\n')
        f.write(f'set_global_assignment -name TOP_LEVEL_ENTITY {top_module}\n')
        f.write('set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files\n')
        f.write('set_global_assignment -name BOARD "DE1-SoC Board"\n\n')
        
        # Power settings
        f.write('# POWER SETTINGS\n')
        f.write('set_global_assignment -name POWER_PRESET_COOLING_SOLUTION "23 MM HEAT SINK WITH 200 LFPM AIRFLOW"\n')
        f.write('set_global_assignment -name POWER_BOARD_THERMAL_MODEL "NONE (CONSERVATIVE)"\n')
        f.write('set_global_assignment -name POWER_DEFAULT_INPUT_IO_TOGGLE_RATE "12.5%"\n')
        f.write('set_global_assignment -name POWER_HPS_ENABLE OFF\n\n')
        
        # Otimizações
        f.write('# OTIMIZAÇÕES\n')
        f.write('set_global_assignment -name OPTIMIZATION_MODE "AGGRESSIVE PERFORMANCE"\n')
        f.write('set_global_assignment -name PHYSICAL_SYNTHESIS_EFFORT "EXTRA"\n')
        f.write('set_global_assignment -name TIMING_ANALYZER_MULTICORNER_ANALYSIS ON\n')
        f.write('set_global_assignment -name NUM_PARALLEL_PROCESSORS ALL\n\n')
        
        # Arquivos
        f.write('# DESIGN FILES\n')
        for rtl in rtl_files:
            rel_path = os.path.relpath(rtl, project_path)
            f.write(f'set_global_assignment -name VERILOG_FILE "{rel_path}"\n')
        
        # SDC Files
        if sdc_files:
            f.write('\n# TIMING CONSTRAINTS\n')
            for sdc in sdc_files:
                f.write(f'set_global_assignment -name SDC_FILE "{sdc.name}"\n')
        
        f.write('\n# PIN ASSIGNMENTS\n')
        f.write('set_location_assignment PIN_AF14 -to CLOCK_50\n')
        f.write('set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50\n\n')
        
        f.write("# =============================================================================\n")
        f.write("# END\n")
        f.write("# =============================================================================\n")

    print(f"✅ QSF gerado: {qsf_path.name}")
    return qsf_path

def create_qpf(project_path: Path, project_name: str):
    """Cria arquivo QPF do projeto."""
    qpf_path = project_path / f"{project_name}.qpf"
    
    if not qpf_path.exists():
        with open(qpf_path, "w") as f:
            f.write(f'QUARTUS_VERSION = "20.1"\n')
            f.write(f'PROJECT_REVISION = "{project_name}"\n')
        print("🆕 QPF criado.")
    else:
        print("ℹ️ QPF já existente.")

# =============================================================================
# MODIFICAÇÃO DE PARÂMETROS
# =============================================================================

def set_parameter_in_verilog(module_name: str, project_path: Path, 
                           param_name: str, value: int) -> bool:
    """Define valor de parâmetro em arquivo Verilog."""
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
        print(f"🔧 Parâmetro {param_name} atualizado para {value}")
        return True
    else:
        print(f"⚠️ Parâmetro '{param_name}' não encontrado")
        return False

# =============================================================================
# COMPILAÇÃO QUARTUS
# =============================================================================

def compile_project(project_name: str, project_path: Path) -> bool:
    """Executa compilação completa no Quartus."""
    os.chdir(project_path)
    print(f"\n🚀 Compilando projeto {project_name}...")

    # Compilação principal
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

    # Análise de potência
    print("\n⚡ Executando análise de potência...")
    run_cmd(
        [f"{config.QUARTUS_BIN}\\quartus_pow", project_name],
        logfile=project_path / "quartus_power.log"
    )
    
    return True