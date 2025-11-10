# main.py
"""
FLUXO PRINCIPAL DE COMPILAÇÃO E SIMULAÇÃO

Este script orquestra todo o processo:
1. Carrega dependências do JSON
2. Detecta estrutura do projeto (hierárquica ou plana)
3. Compila projetos no Quartus
4. Executa simulações no ModelSim
5. Gera relatórios consolidados
"""

import json
from pathlib import Path
import config
import project_loader
import project_processor
import report_generator

# main.py (apenas a parte do loop principal)
def main():
    """Fluxo principal de execução."""
    print("🚀 Build automatizado + simulação + relatório completo")
    
    # ========================
    # CONFIGURAÇÃO INICIAL
    # ========================
    run_simulations = project_processor.verify_simulation_environment()
    dependencies = project_loader.load_dependencies()
    bitwidths = [4, 8]
    compiled_projects = []

    # ========================
    # DETECTA ESTRUTURA DO PROJETO
    # ========================
    if project_loader.is_hierarchical(dependencies):
        print("🌲 Estrutura hierárquica detectada")
        projects_info = project_loader.load_hierarchical_projects(dependencies)
    else:
        print("📜 Estrutura plana detectada") 
        projects_info = project_loader.load_flat_projects(dependencies)

    # ========================
    # LOOP PRINCIPAL - PROCESSAMENTO
    # ========================
    for project_info in projects_info:
        # Handle diferentes formatos de retorno
        if len(project_info) == 4:
            module_name, project_path, rtl_files, sdc_files = project_info
            copied_tbs = []  # Inicializa vazio
        elif len(project_info) == 5:
            module_name, project_path, rtl_files, sdc_files, copied_tbs = project_info
        else:
            print(f"❌ Formato inválido de project_info: {project_info}")
            continue
            
        print(f"\n🔧 Processando módulo: {module_name}")

        # Verifica se tem parâmetro N
        has_N = project_processor.check_has_parameter_n(project_path, module_name)
        
        if has_N:
            # Projeto com parâmetro N - múltiplas compilações com organização
            projects = project_processor.compile_parametrized_project(
                (module_name, project_path, rtl_files, sdc_files, copied_tbs), 
                bitwidths, run_simulations
            )
            compiled_projects.extend(projects)
        else:
            # Projeto único - uma compilação
            project = project_processor.compile_single_project(
                (module_name, project_path, rtl_files, sdc_files, copied_tbs), 
                run_simulations
            )
            if project:
                compiled_projects.append(project)

    # ========================
    # RELATÓRIOS FINAIS
    # ========================
    if compiled_projects:
        report_generator.generate_all_reports(compiled_projects)
        print("✅ Relatórios gerados com sucesso")
    else:
        print("❌ Nenhum projeto foi compilado")

    print("\n🎯 Fluxo completo concluído!")



if __name__ == "__main__":
    main()