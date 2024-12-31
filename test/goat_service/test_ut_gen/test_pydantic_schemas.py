import pytest

from dataset.util import load_example_project
from src.goat_service.ut_generator.prompts.nunit_ut_prompter import NUnitFile


def test_nunit_format():
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    # remove csproj
    test_project.files = [
        file for file in test_project.files if "csproj" not in file.file_name
    ]
    for file in test_project.files:
        NUnitFile(file_name=file.file_name, source_code=file.source_code)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
