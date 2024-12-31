import base64
import os
import tempfile

from dataset.util import load_example_project
from gs_common.CodeProject import CodeFile, CodeProject, REFERENCE_FILE_DIRS


def test_is_binary_file():
    assert CodeProject._is_binary_file("file.txt") is False
    assert CodeProject._is_binary_file("file") is True
    assert CodeProject._is_binary_file("file.c") is False
    assert CodeProject._is_binary_file("file.png") is True
    assert CodeProject._is_binary_file("file.py") is False
    assert CodeProject._is_binary_file("file.java") is False
    assert CodeProject._is_binary_file("file.dll") is True
    assert CodeProject._is_binary_file("file.so") is True
    assert CodeProject._is_binary_file("file.o") is True
    assert CodeProject._is_binary_file("file.exe") is True
    assert CodeProject._is_binary_file("file.bin") is True


def test_load_from_dir():
    source_project = load_example_project("QRCoder", "dotnetframework")
    assert source_project.display_name == "QRCoder"
    assert source_project.source_language == "dotnetframework"
    assert len(source_project.files) == 5
    filenames = [file.file_name for file in source_project.files]
    assert "QRCoder.csproj" in filenames
    assert "QRCode.cs" in filenames
    assert "Properties/AssemblyInfo.cs" in filenames


def test_save_and_load_project():
    source_project = load_example_project("QRCoder", "dotnetframework")
    with tempfile.TemporaryDirectory() as temp_dir:
        source_project.save_to_dir(temp_dir)
        loaded_project = CodeProject.load_from_dir(
            "QRCoder", temp_dir, "dotnetframework"
        )
        assert loaded_project.display_name == "QRCoder"
        assert loaded_project.source_language == "dotnetframework"
        assert len(loaded_project.files) == 5
        loaded_filenames = sorted([file.file_name for file in loaded_project.files])
        source_filenames = sorted([file.file_name for file in source_project.files])
        assert loaded_filenames == source_filenames


def test_save_load_binary_file():
    """
    create project with a binary file
    save to dir
    load from dir
    check that the binary file is same and in reference files
    """
    # create a binary file base64 encoded
    binary_content = base64.b64encode(b"binary content").decode()
    # load the binary file
    code_file = CodeFile(file_name="test.bin", source_code=binary_content)
    project = CodeProject(
        display_name="test", source_language="dotnet8", files=[code_file]
    )
    # save the project to a directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project.save_to_dir(temp_dir)
        # load the project from the directory
        loaded_project = CodeProject.load_from_dir("test", temp_dir, "dotnet8")
        # check that the binary file is same
        assert len(loaded_project.reference_files) == 1
        assert loaded_project.reference_files[0].file_name == "test.bin"
        assert loaded_project.reference_files[0].source_code == binary_content


def test_split_reference_files():
    # Arrange
    source_project = load_example_project("QRCoder", "dotnetframework")
    # add some reference files
    # to do this we need to modify the paths
    # move csproj into Properties dir
    # -> Properties dir is new main dir
    # -> other files should be marked as reference files then
    for file in source_project.files:
        if file.file_name == "QRCoder.csproj":
            file.file_name = "Properties/QRCoder.csproj"

    # Act
    source_project.split_reference_files(
        relative_path_to_main_csproj="Properties/QRCoder.csproj"
    )

    # Assert
    # check that the files are split correctly
    gt_main_file_names = [
        "Properties/AssemblyInfo.cs",
        "Properties/QRCoder.csproj",
    ]
    gt_reference_file_names = ["QRCode.cs", "QRCodeGenerator.cs", "AbstractQRCode.cs"]
    new_main_file_names = [file.file_name for file in source_project.files]
    new_reference_file_names = [
        file.file_name for file in source_project.reference_files
    ]
    assert new_main_file_names == gt_main_file_names
    assert sorted(new_reference_file_names) == sorted(gt_reference_file_names)


def test_receiving_file_from_linux():
    # test linux line endings \n
    # Arrange
    content = '<?xml version="1.0" encoding="utf-8"?>\n<Project ToolsVersion="12.0" DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n'
    file = CodeFile(file_name="HashidsNet.csproj", source_code=content)
    project = CodeProject(
        display_name="HashidsNet", source_language="dotnet8", files=[file]
    )

    # Act
    save_dir = "generated"
    os.makedirs(save_dir, exist_ok=True)
    project.save_to_dir(save_dir)

    # Assert
    newcp = CodeProject.load_from_dir("HashidsNet", save_dir, "dotnet8")
    assert newcp.files[0].source_code == content


def test_receiving_file_from_windows():
    # test windows line endings \r\n
    # Arrange
    content = '<?xml version="1.0" encoding="utf-8"?>\r\n<Project ToolsVersion="12.0" DefaultTargets="Build"\r\n'
    file = CodeFile(file_name="HashidsNet.csproj", source_code=content)
    project = CodeProject(
        display_name="HashidsNet", source_language="dotnet8", files=[file]
    )

    # Act
    save_dir = "generated"
    os.makedirs(save_dir, exist_ok=True)
    project.save_to_dir(save_dir)

    # Assert
    newcp = CodeProject.load_from_dir("HashidsNet", save_dir, "dotnet8")
    assert newcp.files[0].source_code == content


def test_reference_file_dirs():
    """
    load some project
    add a file that should go to reference files
    save, load again
    -> file should be in reference files
    """
    # Arrange
    source_project = load_example_project("QRCoder", "dotnetframework")
    # add a file that should go to reference files
    ref_file_name = REFERENCE_FILE_DIRS[0] + "/ReferenceFile.cs"
    file = CodeFile(file_name=ref_file_name, source_code="class ReferenceFile {}")
    source_project.files.append(file)

    # Act
    with tempfile.TemporaryDirectory() as temp_dir:
        source_project.save_to_dir(temp_dir)
        loaded_project = CodeProject.load_from_dir(
            "QRCoder", temp_dir, "dotnetframework"
        )

        # Assert
        assert len(loaded_project.reference_files) == 1
        assert loaded_project.reference_files[0].file_name == ref_file_name
        assert loaded_project.reference_files[0].source_code == "class ReferenceFile {}"
