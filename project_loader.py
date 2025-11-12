# project_loader.py
"""
CARREGAMENTO E CONFIGURAÇÃO DE PROJETOS
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import config
import compile
import simulation

# Definir o tipo ProjectInfo explicitamente
ProjectInfo = Tuple[str, Path, List[Path], List[Path], List[Path]]

def is_hierarchical(json_obj: Dict) -> bool:
    """Detecta se o JSON tem estrutura hierárquica."""
    return any(isinstance(v, dict) for v in json_obj.values())

def load_dependencies() -> Dict:
    """Carrega dependências do arquivo JSON."""
    if not config.DEPENDENCIES_FILE.exists():
        print("❌ Arquivo dependencies.json não encontrado.")
        exit(1)
    
    with open(config.DEPENDENCIES_FILE, "r") as f:
        return json.load(f)

def load_hierarchical_projects(dependencies: Dict) -> List[ProjectInfo]:
    """Carrega projetos da estrutura hierárquica."""
    print("🌲 Carregando projetos hierárquicos...")
    
    # A função copy_hierarchical_projects retorna (module_name, project_path, rtl_files, sdc_files)
    # Precisamos adaptar para (module_name, project_path, rtl_files, sdc_files, copied_tbs)
    raw_projects = compile.copy_hierarchical_projects(dependencies)
    
    # Converter para o formato ProjectInfo incluindo testbenches
    projects_info = []
    for module_name, project_path, rtl_files, sdc_files in raw_projects:
        # Encontra testbenches para este módulo
        tb_files = simulation.find_testbenches(module_name)
        copied_tbs = []
        if tb_files:
            print(f"🎯 Testbenches para {module_name}: {[tb.name for tb in tb_files]}")
            copied_tbs = simulation.copy_tb_to_project(module_name, project_path, tb_files)
        
        projects_info.append((module_name, project_path, rtl_files, sdc_files, copied_tbs))
    
    return projects_info

def load_flat_projects(dependencies: Dict) -> List[ProjectInfo]:
    """Carrega projetos da estrutura plana."""
    print("📜 Carregando projetos planos...")
    projects_info = []
    
    for module_name in dependencies.keys():
        project_info = setup_project_environment(module_name, dependencies)
        projects_info.append(project_info)
    
    return projects_info

def setup_project_environment(module_name: str, dependencies: Dict) -> ProjectInfo:
    """Prepara ambiente do projeto: copia arquivos e testbenches."""
    # Copia arquivos do projeto
    project_path, rtl_files, sdc_files = compile.copy_files_for_project(
        module_name, module_name, dependencies
    )
    
    # Encontra e copia testbenches
    tb_files = simulation.find_testbenches(module_name)
    copied_tbs = []
    if tb_files:
        print(f"🎯 Testbenches encontrados: {[tb.name for tb in tb_files]}")
        copied_tbs = simulation.copy_tb_to_project(module_name, project_path, tb_files)
    else:
        print("ℹ️ Nenhum testbench encontrado")
    
    return (module_name, project_path, rtl_files, sdc_files, copied_tbs)

