import os
import pytest
from gs_common.CodeProject import CodeFile, CodeProject
from gs_common.file_ops import (
    generate_save_dir,
)

from dataset.util import load_example_project, setup_trace_info_for_testing
from src.code_executor.upgrade_assistant import UpgradeAssistant

setup_trace_info_for_testing()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # setup code here
    global save_dir
    save_dir = generate_save_dir("unittests-ua")
    yield
    # teardown code here


def test_qrcoder_3files():
    source_project = load_example_project("QRCoder", "dotnetframework")

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    filenames = [file.file_name for file in upgraded_project.files]
    assert len(filenames) == 5
    assert "QRCoder.csproj" in filenames
    assert "QRCode.cs" in filenames
    assert "QRCodeGenerator.cs" in filenames
    assert "AbstractQRCode.cs" in filenames

    # check content of .csproj
    csproj = next(
        file for file in upgraded_project.files if file.file_name == "QRCoder.csproj"
    )
    assert "net8.0" in csproj.source_code
    assert '<Project Sdk="Microsoft.NET.Sdk">' in csproj.source_code
    assert "System.Drawing.Common" in csproj.source_code


def test_hashids_v112():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    filenames = [file.file_name for file in upgraded_project.files]
    assert len(filenames) == 4
    assert "Hashids.net.csproj" in filenames
    assert "Hashids.cs" in filenames
    assert "IHashids.cs" in filenames

    # check content of .csproj
    csproj = next(
        file for file in upgraded_project.files if ".csproj" in file.file_name
    )
    assert "net8.0" in csproj.source_code
    assert '<Project Sdk="Microsoft.NET.Sdk">' in csproj.source_code

    # assert UnsafeDeserialize is removed
    source_cs = next(
        file for file in source_project.files if file.file_name == "Hashids.cs"
    )
    upgraded_cs = next(
        file for file in upgraded_project.files if file.file_name == "Hashids.cs"
    )
    from pprint import pprint

    pprint(upgraded_cs.source_code)
    assert "UnsafeDeserialize" in source_cs.source_code
    assert "UnsafeDeserialize" not in upgraded_cs.source_code


def test_crc32_v100():
    source_project = load_example_project("Crc32.NET-v100", "dotnetframework")

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    filenames = [file.file_name for file in upgraded_project.files]
    assert len(filenames) == 4
    assert "Crc32.NET.csproj" in filenames
    assert "Crc32Algorithm.cs" in filenames

    # check content of .csproj
    csproj = next(
        file for file in upgraded_project.files if ".csproj" in file.file_name
    )
    assert "net8.0" in csproj.source_code
    assert '<Project Sdk="Microsoft.NET.Sdk">' in csproj.source_code

    source_cs = next(
        file for file in source_project.files if file.file_name == "Crc32Algorithm.cs"
    )
    upgraded_cs = next(
        file for file in upgraded_project.files if file.file_name == "Crc32Algorithm.cs"
    )
    from pprint import pprint

    pprint(upgraded_cs.source_code)
    # assert same
    assert source_cs.source_code == upgraded_cs.source_code


def test_not_in_new_sdk_format():
    # NOTE: this test only works on linux; on windows, winforms is installed
    if os.name == "nt":
        pytest.skip("Skipping test that only works on linux")

    source_project = load_example_project("QRCoder", "dotnetframework")
    # add     <Reference Include="System.Windows.Forms" />
    csproj = next(
        file for file in source_project.files if file.file_name == "QRCoder.csproj"
    )
    csproj.source_code = csproj.source_code.replace(
        '<Reference Include="System" />',
        '<Reference Include="System" />\n    <Reference Include="System.Windows.Forms" />',
    )

    with pytest.raises(Exception) as e:
        ua = UpgradeAssistant(source_project, save_dir)
        upgraded_project = ua.upgrade()
        print(upgraded_project)

    assert "Error: .csproj file is not in new SDK format" in str(e.value)


def test_all_files_are_returned():
    source_project = load_example_project("QRCoder", "dotnetframework")
    # add another file Assets/pink.ico
    source_project.files.append(
        CodeFile(
            file_name="Assets/pink.txt",
            source_code="binary data",
        )
    )

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    filenames = [file.file_name for file in upgraded_project.files]
    assert len(filenames) == 6
    assert "QRCoder.csproj" in filenames
    assert "QRCode.cs" in filenames
    assert "Assets/pink.txt" in filenames


def test_qrcoder_with_reference_files_success():
    source_project = load_example_project("QRCoder", "dotnetframework")
    # set files to be in a folder
    for file in source_project.files:
        file.file_name = "QRCoder/" + file.file_name
    # add a reference_file to the root project
    source_project.reference_files.append(
        CodeFile(
            file_name="Assets/pink.ico",
            source_code="binary data",
        )
    )

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    # reference files are not added to the upgraded_project
    filenames = [file.file_name for file in upgraded_project.files]
    assert len(filenames) == 5
    assert "QRCoder/QRCoder.csproj" in filenames
    assert "QRCoder/QRCode.cs" in filenames
    assert "QRCoder/Properties/AssemblyInfo.cs" in filenames

    assert len(upgraded_project.reference_files) == 0


def test_wpf_project_should_have_usewpf_added():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    # add WPF reference to csproj
    csproj = next(
        file for file in source_project.files if file.file_name == "Hashids.net.csproj"
    )
    # add PresentationFramework reference
    csproj.source_code = csproj.source_code.replace(
        '<Reference Include="System" />',
        '<Reference Include="System" />\n    <Reference Include="PresentationFramework" />',
    )

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    # check content of .csproj
    csproj = next(
        file for file in upgraded_project.files if ".csproj" in file.file_name
    )
    print("*" * 80)
    print(csproj.source_code)
    print("*" * 80)
    assert "net8.0-windows" in csproj.source_code
    assert '<Project Sdk="Microsoft.NET.Sdk">' in csproj.source_code
    assert "<UseWPF>true</UseWPF>" in csproj.source_code


def test_csproj_encoding_same_as_before():
    # UA should not introduce BOM or windows line endings
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    csproj = next(
        file for file in source_project.files if file.file_name == "Hashids.net.csproj"
    )

    ua = UpgradeAssistant(source_project, save_dir)
    upgraded_project = ua.upgrade()

    # Assert
    # check content of .csproj
    csproj = next(
        file for file in upgraded_project.files if ".csproj" in file.file_name
    )
    assert "net8.0" in csproj.source_code
    assert '<Project Sdk="Microsoft.NET.Sdk">' in csproj.source_code

    # check no BOM and no win line endings
    has_bom = csproj.source_code.startswith("\ufeff")
    has_win_line_endings = "\r\n" in csproj.source_code
    assert has_bom is False, "BOM should not be present"
    assert has_win_line_endings is False, "Windows line endings should not be present"
