import json
import time
import shutil
from pathlib import Path

import config
import compile
import report


if __name__ == "__main__":
    print("🚀 Build automatizado + relatório completo")

    if not config.DEPENDENCIES_FILE.exists():
        print("❌ Arquivo dependencies.json não encontrado.")
        exit(1)

    # ========================
    # CARREGA DEPENDÊNCIAS
    # ========================
    with open(config.DEPENDENCIES_FILE, "r") as f:
        dependencies = json.load(f)

    bitwidths = [4, 6, 8, 16, 32, 64]
    compiled_projects = []

    # ==================================================
    # LOOP PRINCIPAL DE COMPILAÇÃO
    # ==================================================
    for module_name in dependencies.keys():
        print(f"\n🔧 Preparando módulo: {module_name}")

        project_path, rtl_files, sdc_files = compile.copy_files_for_project(
            module_name, module_name, dependencies
        )

        compile.generate_qsf(project_path, module_name, rtl_files, sdc_files)
        compile.create_qpf(project_path, module_name)

        top_file = project_path / f"{module_name}.v"
        has_N = any("parameter N" in line for line in open(top_file, "r")) if top_file.exists() else False

        # ==================================================
        # CASO SEM PARÂMETRO N
        # ==================================================
        if not has_N:
            print(f"⚙️ Módulo {module_name} não possui parâmetro N — compilação única.")
            if compile.compile_project(module_name, project_path):
                compiled_projects.append((module_name, project_path, "default", project_path / "output_files"))
            continue

        # ==================================================
        # CASO COM PARÂMETRO N
        # ==================================================
        for N in bitwidths:
            print(f"\n==============================")
            print(f"🧩 Projeto: {module_name} | N={N}")
            print(f"==============================")

            # Define o parâmetro N dentro do Verilog
            compile.set_parameter_in_verilog(module_name, project_path, "N", N)

            # Compila o projeto
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

            compiled_projects.append((module_name, project_path, N, dst_out))

    # ==================================================
    # ETAPA FINAL: COLETA DE RELATÓRIOS
    # ==================================================
    all_reports = []
    print("\n📊 Coletando dados de todos os projetos...")

    for module_name, project_path, N, out_dir in compiled_projects:
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
            all_reports.append(data)

    # ==================================================
    # RELATÓRIO FINAL CONSOLIDADO
    # ==================================================
    if all_reports:
        report.write_consolidated_report(all_reports)

    print("\n🎯 Fluxo completo: compilação + relatório consolidado concluído!")
