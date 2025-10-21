import json
import config
import compile
import report
import os

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

    # Defina as larguras que deseja testar
    bitwidths = [4, 6, 8, 16, 19, 32, 64, 128, 256]

    all_reports = []

    for module_name in dependencies.keys():
        # Copia arquivos e resolve dependências recursivas
        project_path, rtl_files, sdc_files = compile.copy_files_for_project(module_name, module_name, dependencies)

        # Gera QSF/QPF
        compile.generate_qsf(project_path, module_name, rtl_files, sdc_files)
        compile.create_qpf(project_path, module_name)

        # Verifica se o parâmetro N existe no arquivo Verilog principal
        top_file = project_path / f"{module_name}.v"
        has_N = False
        if top_file.exists():
            with open(top_file, "r") as f:
                for line in f:
                    if "parameter N" in line:
                        has_N = True
                        break

        if not has_N:
            print(f"⚙️ Módulo {module_name} não possui parâmetro N — compilação única.")
            if compile.compile_project(module_name, project_path):
                data = report.extract_data_from_reports(module_name, project_path)
                if data:
                    data["N"] = "default"
                    all_reports.append(data)
            continue  # pula o loop de bitwidths

        # Caso possua o parâmetro N, faz varredura normal
        for N in bitwidths:
            print(f"\n==============================")
            print(f"🧩 Projeto: {module_name} | N={N}")
            print(f"==============================")

            # Atualiza o parâmetro N antes da compilação
            compile.set_parameter_in_verilog(module_name, project_path, "N", N)

            if compile.compile_project(module_name, project_path):
                data = report.extract_data_from_reports(module_name, project_path)
                if data:
                    data["N"] = N
                    all_reports.append(data)

    # Salva relatório consolidado
    if all_reports:
        report.write_consolidated_report(all_reports)

    print("\n🎯 Fluxo completo: compilação + relatório consolidado concluído!")
