import pytest
from gs_common.CodeProject import CodeProject
from gs_common.file_ops import (
    generate_save_dir,
)

from dataset.util import load_example_project, setup_trace_info_for_testing
from src.code_executor.pre_migration_assessor import PreMigrationAssessor

setup_trace_info_for_testing()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # setup code here
    global save_dir
    save_dir = generate_save_dir("unittests-assessor")
    yield
    # teardown code here


def test_analyze_csproj():
    # Arrange
    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)

    # Act
    result = pre_migration_assessor.analyze_csproj()

    print(result)

    # Assert
    assert "Library" in result
    assert "v4.6.1" in result
    # <PackageReference Include="Newtonsoft.Json">
    assert "Newtonsoft.Json" in result
    # <ProjectReference Include="..\Captura.Base\Captura.Base.csproj">
    assert "Captura.Base.csproj" in result
    # <Reference Include="NLog">
    #  <HintPath>..\packages\NLog.4.5.11\lib\net45\NLog.dll</HintPath>
    assert "NLog.4.5.11" in result
    # <Reference Include="System.Windows.Forms" />
    assert "System.Windows.Forms" in result


def test_analyze_source_code():
    # Arrange
    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)

    # Act
    result = pre_migration_assessor.analyze_source_code()

    print(result)

    # Assert
    assert "Unnecessary using directive" in result
    assert "lines of code" in result.lower()
    assert "public HotkeyModel(Captura.ServiceName ServiceName, " in result


def test_no_obsolete_methods():
    # Arrange
    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)

    # Act
    result = pre_migration_assessor.analyze_obsolete_methods()

    print(result)

    # Assert
    assert "No obsolete methods found" in result


def test_obsolete_methods():
    # Arrange
    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    # modify to include obsolete methods
    source_project.files[-1].source_code += " AppDomain.ExecuteAssembly();"
    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)

    # Act
    result = pre_migration_assessor.analyze_obsolete_methods()

    print(result)

    # Assert
    assert "AppDomain.ExecuteAssembly" in result


def test_analyze_nuget_packages():
    # Arrange
    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    for file in source_project.files:
        if file.file_name == "Captura.Hotkeys.csproj":
            # <PackageReference Include="Newtonsoft.Json">
            #  <Version>11.0.2</Version>
            # </PackageReference>
            # add new package references after Newtonsoft.Json

            # include a non existent package
            file.source_code = file.source_code.replace(
                "</PackageReference>",
                '</PackageReference>\n    <PackageReference Include="GoatLogger">\n      <Version>1.0.0</Version>\n    </PackageReference>',
            )
            # include a package with four verions numbers # NHibernate/3.3.1.4000
            file.source_code = file.source_code.replace(
                "</PackageReference>",
                '</PackageReference>\n    <PackageReference Include="NHibernate">\n      <Version>3.3.1.4000</Version>\n    </PackageReference>',
            )

    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)

    # Act
    result = pre_migration_assessor.analyze_nuget_packages()

    print("*" * 80)
    print(result)

    # Assert
    # search libs and check available target frameworks
    lines = result.splitlines()
    nhibernate_index = lines.index("NHibernate 3.3.1.4000")
    nhibernate_target_frameworks = lines[nhibernate_index + 1]
    assert "Available Target Frameworks: ['net35', " in nhibernate_target_frameworks
    newtonsoft_index = lines.index("Newtonsoft.Json 11.0.2")
    newtonsoft_target_frameworks = lines[newtonsoft_index + 1]
    assert "Available Target Frameworks: ['net20', " in newtonsoft_target_frameworks
    nlog_index = lines.index("NLog 4.5.11")
    nlog_target_frameworks = lines[nlog_index + 1]
    assert "Available Target Frameworks: ['net35', " in nlog_target_frameworks
    goatlogger_index = lines.index("GoatLogger 1.0.0")
    goatlogger_target_frameworks = lines[goatlogger_index + 1]
    assert (
        "Warning: Failed to download GoatLogger 1.0.0: 404"
        in goatlogger_target_frameworks
    )


def benchmark_analyze_nuget_packages():
    # analyze different nuget package references and stop time
    import time

    source_project = load_example_project("Captura.Hotkeys", "dotnetframework")
    nuget_packages_and_version = {
        "Newtonsoft.Json": "11.0.2",
        "NLog": "3.0.0",
        "Microsoft.Extensions.DependencyInjection": "5.0.0",
        "Microsoft.Extensions.Hosting": "5.0.0",
        "AWSSDK.Core": "3.7.303",
        "Azure.Core": "1.38.0",
        "System.Drawing.Common": "8.0.2",
        "Serilog": "2.10.0",
        "Moq": "4.16.1",
        "System.Text.Json": "5.0.2",
        "xunit": "2.4.1",
        "FluentAssertions": "5.10.3",
        "Microsoft.Extensions.Logging": "5.0.0",
        "FluentValidation": "9.3.0",
    }
    # modify to include 20 additional package references
    for file in source_project.files:
        if file.file_name == "Captura.Hotkeys.csproj":
            # <PackageReference Include="Newtonsoft.Json">
            #  <Version>11.0.2</Version>
            # </PackageReference>
            # add a new package reference after Newtonsoft.Json
            for package, version in nuget_packages_and_version.items():
                file.source_code = file.source_code.replace(
                    "</PackageReference>",
                    f'</PackageReference>\n    <PackageReference Include="{package}">\n      <Version>{version}</Version>\n    </PackageReference>',
                )
    pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)
    start = time.time()
    result = pre_migration_assessor.analyze_nuget_packages()
    end = time.time()
    print("*" * 80)
    print(result)
    print(f"Time elapsed: {end - start}")
    # ~ 0.38s per package
    print(f"Time per package: {(end - start) / len(nuget_packages_and_version)}")


if __name__ == "__main__":
    # benchmark_analyze_nuget_packages()
    # exit()

    import os

    # base_dir = "/home/mw3155/dotnet-dataset/CsvReader/code/LumenWorks.Framework.IO/"
    # base_dir = "/home/mw3155/dotnet-dataset/Captura/src/Captura/"
    # base_dir = "/home/mw3155/dotnet-dataset/Captura/src/Captura.Hotkeys/"
    base_dir = "/home/mw3155/dotnet-dataset/hashids.net/Hashids.net.test/"

    project = CodeProject.load_from_dir("assessmenttest", base_dir, "dotnetframework")
    pre_migration_assessor = PreMigrationAssessor(project)
    assessment_project: CodeProject = pre_migration_assessor.assess()

    # save
    assessment_project.save_to_dir(os.path.join("generated", "assessmenttest"))
