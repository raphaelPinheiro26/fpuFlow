import json
import config
import compile
import report
import time

if __name__ == "__main__":
    print("🚀 Build automatizado + relatório completo")

    if not config.DEPENDENCIES_FILE.exists():
        print("❌ Arquivo dependencies.json não encontrado.")
        exit(1)

    with open(config.DEPENDENCIES_FILE, "r") as f:
        dependencies = json.load(f)

    bitwidths = [4, 6, 8, 16, 32, 64]
    compiled_projects = []  # 🔹 lista para pós-processamento

    for module_name in dependencies.keys():
        project_path, rtl_files, sdc_files = compile.copy_files_for_project(
            module_name, module_name, dependencies
        )

        compile.generate_qsf(project_path, module_name, rtl_files, sdc_files)
        compile.create_qpf(project_path, module_name)

        top_file = project_path / f"{module_name}.v"
        has_N = any("parameter N" in line for line in open(top_file, "r")) if top_file.exists() else False

        if not has_N:
            print(f"⚙️ Módulo {module_name} não possui parâmetro N — compilação única.")
            if compile.compile_project(module_name, project_path):
                compiled_projects.append((module_name, project_path, "default"))
            continue

        for N in bitwidths:
            print(f"\n==============================")
            print(f"🧩 Projeto: {module_name} | N={N}")
            print(f"==============================")

            compile.set_parameter_in_verilog(module_name, project_path, "N", N)

            if compile.compile_project(module_name, project_path):
                compiled_projects.append((module_name, project_path, N))

    # ==================================================
    # ETAPA FINAL: coleta de todos os relatórios
    # ==================================================
    all_reports = []
    print("\n📊 Coletando dados de todos os projetos...")

    for module_name, project_path, N in compiled_projects:
        pow_report = project_path / "output_files" / f"{module_name}.pow.rpt"

        # 🔹 Aguarda até o relatório de potência existir (máx. 120s)
        wait_time = 0
        while not pow_report.exists() and wait_time < 120:
            print(f"⏳ Aguardando relatório de potência de {module_name} ({wait_time}s)...", end="\r")
            time.sleep(2)
            wait_time += 2

        if not pow_report.exists():
            print(f"\n⚠️ Relatório de potência não encontrado após {wait_time}s — pulando {module_name}")
            continue

        data = report.extract_data_from_reports(module_name, project_path)
        if data:
            data["N"] = N
            all_reports.append(data)

    # ==================================================
    # RELATÓRIO FINAL
    # ==================================================
    if all_reports:
        report.write_consolidated_report(all_reports)

    print("\n🎯 Fluxo completo: compilação + relatório consolidado concluído!")
