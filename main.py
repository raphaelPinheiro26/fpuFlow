import json 
import config
import compile
import report

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    print("🚀 Build automatizado + relatório completo")

    if not config.DEPENDENCIES_FILE.exists():
        print("❌ Arquivo dependencies.json não encontrado.")
        exit(1)

    with open(config.DEPENDENCIES_FILE, "r") as f:
        dependencies = json.load(f)

    all_reports = []

    for module_name, deps in dependencies.items():
        print("\n==============================")
        print(f"🧩 Projeto: {module_name}")
        print("==============================")

        project_path, rtl_files, sdc_files = compile.copy_files_for_project(module_name, module_name, deps)
        compile.generate_qsf(project_path, module_name, rtl_files, sdc_files)
        compile.create_qpf(project_path, module_name)

        if compile.compile_project(module_name, project_path):
            data = report.extract_data_from_reports(module_name, project_path)
            if data:
                all_reports.append(data)

    if all_reports:
        report.write_consolidated_report(all_reports)

    print("\n🎯 Fluxo completo: compilação + relatório consolidado concluído!")
