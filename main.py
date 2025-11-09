# main.py
import json
import time
import shutil
from pathlib import Path

import config
import compile
import report
import simulation

def is_hierarchical(json_obj):
    """Detecta se o arquivo JSON contém estrutura hierárquica."""
    return any(isinstance(v, dict) for v in json_obj.values())

if __name__ == "__main__":
    print("🚀 Build automatizado + simulação + relatório completo")

    if not config.DEPENDENCIES_FILE.exists():
        print("❌ Arquivo dependencies.json não encontrado.")
        exit(1)

    # ========================
    # CARREGA DEPENDÊNCIAS
    # ========================
    with open(config.DEPENDENCIES_FILE, "r") as f:
        dependencies = json.load(f)

    bitwidths = [4, 8, 16, 32, 64]
    compiled_projects = []

    # ==================================================
    # DETECTA TIPO DE JSON (HIERÁRQUICO OU PLANO)
    # ==================================================
    if is_hierarchical(dependencies):
        print("🌲 Estrutura hierárquica detectada — copiando árvore completa...")
        projects_info = compile.copy_hierarchical_projects(dependencies)
    else:
        print("📜 Estrutura plana detectada — modo compatibilidade.")
        projects_info = []
        for module_name in dependencies.keys():
            project_path, rtl_files, sdc_files = compile.copy_files_for_project(
                module_name, module_name, dependencies
            )
            projects_info.append((module_name, project_path, rtl_files, sdc_files))

    # ==================================================
    # LOOP PRINCIPAL DE COMPILAÇÃO E SIMULAÇÃO
    # ==================================================
    for module_name, project_path, rtl_files, sdc_files in projects_info:
        print(f"\n🔧 Preparando módulo: {module_name}")

        # ========================
        # ENCONTRA TESTBENCHES
        # ========================
        tb_files = simulation.find_testbenches(module_name)
        if tb_files:
            print(f"🎯 Testbenches encontrados: {[tb.name for tb in tb_files]}")
            copied_tbs = simulation.copy_tb_to_project(module_name, project_path, tb_files)
        else:
            print("ℹ️ Nenhum testbench encontrado para este módulo")
            copied_tbs = []

        compile.generate_optimized_qsf(project_path, module_name, rtl_files, sdc_files)
        compile.create_qpf(project_path, module_name)

        top_file = project_path / f"{module_name}.v"
        has_N = any("parameter N" in line for line in open(top_file, "r")) if top_file.exists() else False

        # ==================================================
        # CASO SEM PARÂMETRO N - COMPILAÇÃO ÚNICA
        # ==================================================
        if not has_N:
            print(f"⚙️ Módulo {module_name} não possui parâmetro N — compilação única.")
            
            # COMPILAÇÃO QUARTUS
            if compile.compile_project(module_name, project_path):
                out_dir_default = project_path / "output_files"
                compiled_projects.append((module_name, project_path, "default", out_dir_default, copied_tbs, []))
            
            # SIMULAÇÃO MODELSIM
            sim_results = []
            if copied_tbs and config.MODELSIM_DIR.exists():
                print(f"🎯 Iniciando simulações ModelSim...")
                
                compile_success = simulation.compile_modelsim_project(project_path, module_name, rtl_files, copied_tbs)
                
                if compile_success:
                    for tb_file in copied_tbs:
                        tb_name = tb_file.stem
                        # USA A NOVA FUNÇÃO COM ORGANIZAÇÃO
                        result = simulation.run_modelsim_simulation_with_organization(
                            project_path, tb_name, out_dir_default, "default"
                        )
                        if result:
                            sim_results.append(result)
                            print(f"   📊 {tb_name}: {result}")
            
            # Atualiza resultados
            if compiled_projects and sim_results:
                for i, (proj_name, proj_path, n_val, out_dir, tbs, old_sim) in enumerate(compiled_projects):
                    if proj_name == module_name and n_val == "default":
                        compiled_projects[i] = (proj_name, proj_path, n_val, out_dir, tbs, sim_results)
                        break
            
            continue

        # ==================================================
        # CASO COM PARÂMETRO N - LOOP POR BITWIDTHS  
        # ==================================================
        for N in bitwidths:
            print(f"\n==============================")
            print(f"🧩 Projeto: {module_name} | N={N}")
            print(f"==============================")

            # Define o parâmetro N no RTL
            compile.set_parameter_in_verilog(module_name, project_path, "N", N)
            
            # Define o parâmetro N nos testbenches
            for tb_file in copied_tbs:
                simulation.set_parameter_in_tb(tb_file, "N", N)

            # COMPILAÇÃO QUARTUS
            success = compile.compile_project(module_name, project_path)
            if not success:
                print(f"❌ Falha na compilação para N={N}")
                continue

            # Caminhos de saída
            src_out = project_path / "output_files"
            dst_out = project_path / f"output_files_N{N}"

            # Move ou substitui a pasta de saída para preservar resultados
            if src_out.exists():
                if dst_out.exists():
                    shutil.rmtree(dst_out)
                shutil.move(str(src_out), str(dst_out))
            else:
                print(f"⚠️ Aviso: {src_out} não encontrado após compilação para N={N}")
                continue

            # SIMULAÇÃO MODELSIM COM ORGANIZAÇÃO
            sim_results = []
            if copied_tbs and config.MODELSIM_DIR.exists():
                print(f"🎯 Iniciando simulações ModelSim para N={N}...")
                compile_success = simulation.compile_modelsim_project(project_path, module_name, rtl_files, copied_tbs)
                
                if compile_success:
                    for tb_file in copied_tbs:
                        tb_name = tb_file.stem
                        # USA A NOVA FUNÇÃO COM ORGANIZAÇÃO E N
                        result = simulation.run_modelsim_simulation_with_organization(
                            project_path, tb_name, dst_out, N
                        )
                        if result:
                            result["N"] = N
                            sim_results.append(result)
                            print(f"   📊 {tb_name}: {result}")

            compiled_projects.append((module_name, project_path, N, dst_out, copied_tbs, sim_results))

    # ==================================================  # 🔥 ESTA PARTE DEVE ESTAR FORA DO LOOP!
    # ETAPA FINAL: COLETA DE RELATÓRIOS
    # ==================================================
    all_reports = []
    print("\n📊 Coletando dados de todos os projetos...")

    for module_name, project_path, N, out_dir, copied_tbs, sim_results in compiled_projects:
        pow_report = out_dir / f"{module_name}.pow.rpt"

        # Aguarda até o relatório de potência existir (máx. 120s)
        wait_time = 0
        while not pow_report.exists() and wait_time < 120:
            print(f"⏳ Aguardando relatório de potência de {module_name} (N={N}) ({wait_time}s)...", end="\r")
            time.sleep(2)
            wait_time += 2

        if not pow_report.exists():
            print(f"\n⚠️ Relatório de potência não encontrado após {wait_time}s — pulando {module_name} N={N}")
            continue

        data = report.extract_data_from_reports(module_name, project_path, out_dir)
        if data:
            data["N"] = N
            # Adiciona resultados de simulação se disponíveis
            if sim_results:
                data["Simulation_Results"] = sim_results
            all_reports.append(data)

    # ==================================================
    # RELATÓRIO FINAL CONSOLIDADO
    # ==================================================
    if all_reports:
        report.write_consolidated_report(all_reports)

    print("\n🎯 Fluxo completo: compilação + simulação + relatório consolidado concluído!")