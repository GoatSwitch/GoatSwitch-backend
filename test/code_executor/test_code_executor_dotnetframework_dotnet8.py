import pytest
from gs_common.CodeProject import CodeFile, CodeProject
from gs_common.file_ops import (
    generate_save_dir,
)

from dataset.util import (
    load_example_project,
    setup_trace_info_for_testing,
)
from src.code_executor.factories import CodeExecutorFactory

CONFIG = {
    "source_language": "dotnetframework",
    "testing_framework": "nunit",
}
CONFIG_DOTNET8 = {
    "source_language": "dotnet8",
    "testing_framework": "nunit",
}

setup_trace_info_for_testing()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # setup code here
    global save_dir
    save_dir = generate_save_dir("unittests-ce-dotnetframework-dotnet8")
    yield
    # teardown code here


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dotnetframework_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnetframework")
    test_project = load_example_project(project_name + "-GSTests", "nunit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dotnetframework_fail(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnetframework")
    test_project = load_example_project(project_name + "-GSTests", "nunit_unittests")
    # modify tests
    # print all filesnames
    print("test_project.files: ", [file.file_name for file in test_project.files])
    test_project.files[-1].source_code = test_project.files[-1].source_code.replace(
        "Assert.IsNotNull", "Assert.IsNull", 1
    )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 1


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dotnet8_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnet8")
    test_project = load_example_project(project_name + "-GSTests", "nunit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dotnet8_fail(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnet8")
    # NOTE: need to use 1File tests instead of 3Files; not working on net8.0 (drawing lib)
    test_project = load_example_project(project_name + "-GSTests", "nunit_unittests")
    # modify tests
    test_project.files[-1].source_code = test_project.files[-1].source_code.replace(
        "Assert.IsNotNull", "Assert.IsNull", 1
    )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 1


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dummy_dotnetframework_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnetframework")
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dummy_dotnetframework_code_error(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnetframework")
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")
    # code-exec should give err if source is not compilable
    # modify source
    source_project.files[0].source_code = source_project.files[0].source_code.replace(
        "System", "SYSTEM_REPLACE_TO_MAKE_TEST_FAIL", 1
    )

    # Act
    with pytest.raises(Exception) as e:
        ce = CodeExecutorFactory.create(
            CONFIG,
            source_project,
            test_project,
            save_dir=save_dir,
        )
        result = ce.execute()

    # Assert
    assert "msbuild error" in str(e.value)


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dummy_dotnet8_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnet8")
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize("project_name", ["QRCoder"])
def test_qrcoder_dummy_dotnet8_code_error(project_name):
    # Arrange
    source_project = load_example_project(project_name, "dotnet8")
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")

    # code-exec should give err if target code is not compilable
    # modify source
    source_project.files[0].source_code = source_project.files[0].source_code.replace(
        "System", "SYSTEM_REPLACE_TO_MAKE_TEST_FAIL", 1
    )

    # Act
    with pytest.raises(Exception) as e:
        ce = CodeExecutorFactory.create(
            CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
        )
        result = ce.execute()

    # Assert
    assert "dotnet error" in str(e.value)


def test_hashids_dotnet8():
    # Arrange
    source_project = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


def test_hashids_dotnet8_fail():
    # Arrange
    source_project = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    # modify tests
    test_project.files[1].source_code = test_project.files[1].source_code.replace(
        "Assert.IsNotEmpty", "Assert.IsEmpty", 1
    )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 1


def test_hashids_dotnet6():
    # Arrange
    source_project: CodeProject = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    # change net8.0 to net6.0
    # source_project.get_file("Hashids.net.csproj").source_code = source_project.get_file(
    #     "Hashids.net.csproj"
    # ).source_code.replace("net8.0", "net6.0", 1)
    csproj = source_project.get_file("Hashids.net.csproj")
    new_csproj = csproj.source_code.replace("net8.0", "net6.0", 1)
    assert new_csproj != csproj.source_code
    csproj.source_code = new_csproj

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


def test_hashids_dotnet8_specific_windows_version():
    # Arrange
    source_project = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    # set target framework to net8.0-windows10
    csproj = source_project.get_file("Hashids.net.csproj")
    new_csproj = csproj.source_code.replace(
        "<TargetFramework>net8.0</TargetFramework>",
        "<TargetFramework>net8.0-windows10</TargetFramework>",
        1,
    )
    assert new_csproj != csproj.source_code
    csproj.source_code = new_csproj

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


def test_hashids_dotnet8_multiple_versions():
    # Arrange
    source_project = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    # set multiple target frameworks
    csproj = source_project.get_file("Hashids.net.csproj")
    new_csproj = csproj.source_code.replace(
        "<TargetFramework>net8.0</TargetFramework>",
        "<TargetFrameworks>net8.0;net8.0-windows10</TargetFrameworks>",
        1,
    )
    assert new_csproj != csproj.source_code
    csproj.source_code = new_csproj

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


def test_target_framework_is_changed_to_windows():
    # Arrange
    source_project = load_example_project("Hashids.net-v112", "dotnet8")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    # Modify the target framework of the project
    for file in source_project.files:
        if file.file_name.endswith(".csproj"):
            lines = file.source_code.split("\n")
            for line_idx, line in enumerate(lines):
                if "<TargetFramework>" in line:
                    lines[line_idx] = (
                        "<TargetFramework>net8.0-windows</TargetFramework>"
                    )
            file.source_code = "\n".join(lines)
            break

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


def test_package_is_installed():
    # Arrange
    source_project = load_example_project("QRCoder", "dotnetframework")
    test_project = load_example_project("QRCoder-GSTests", "nunit_unittests")

    # add a reference to Serilog in the source project
    for file in source_project.files:
        if file.file_name.endswith("QRCoder.cs"):
            file.source_code = "using Serilog;\n" + file.source_code

    # add a packages.config file to the source project
    packages_file = CodeFile(
        file_name="packages.config",
        source_code="""<?xml version="1.0" encoding="utf-8"?>
        <packages>
        <package id="Serilog" version="2.10.0" targetFramework="net45" />
        </packages>""",
    )
    source_project.files.append(packages_file)
    # add package ref to csproj
    # also make the HintPath point to a parent dir
    # -> must be replaced by our formatter
    to_insert = """<ItemGroup>
        <Reference Include="Serilog">
            <HintPath>..\\..\\packages\\Serilog.2.10.0\\lib\\net45\\Serilog.dll</HintPath>
        </Reference>
    </ItemGroup>"""
    for file in source_project.files:
        if file.file_name.endswith(".csproj"):
            file.source_code = file.source_code.replace(
                "</Project>", to_insert + "\n</Project>"
            )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


# def test_debug():
#     # Arrange
#     path = r"\\wsl.localhost\Ubuntu-24.04\mnt\gs-vault\2024-09-14\33298df134bafffd14e0c55a024bb53b\WorkflowRetry\sourceProject\17-53-49_375487e8996b4230a03f8bf62f493e5d\files"
#     name = "nager"
#     # load from dir
#     source_project = CodeProject.load_from_dir(
#         display_name=name,
#         base_dir=path,
#         source_language="dotnet8",
#     )

#     # load dummy tests
#     test_project = load_example_project("Dummy-GSTests", "nunit_unittests")

#     # Act
#     ce = CodeExecutorFactory.create(
#         CONFIG_DOTNET8, source_project, test_project, save_dir=save_dir
#     )
#     result = ce.execute()

#     # Assert
#     assert result.failed_tests == 0
