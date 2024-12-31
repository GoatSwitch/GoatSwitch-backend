import pytest

from dataset.util import load_example_project
from src.goat_service.ut_generator.utils.ut_postprocessor import (
    UnitTestPostProcessor,
)


def test_display_name():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    post_processor = UnitTestPostProcessor(source_project)
    post_processor.load_dotnet_csproj()
    post_processed_project = post_processor.post_process(test_project)
    assert (
        post_processed_project.display_name == "Hashids.net-v112"
    ), "Display name should be 'Hashids.net-v112'"


def test_csproj_added_and_named_after_source_project():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    # remove csproj
    test_project.files = [
        file for file in test_project.files if ".csproj" not in file.file_name
    ]
    post_processor = UnitTestPostProcessor(source_project)
    post_processor.load_dotnet_csproj()
    post_processed_project = post_processor.post_process(test_project)
    print([f.file_name for f in post_processed_project.files])
    # assert that csproj is added
    assert any(
        [
            f.file_name == "Hashids.net-GSTests.csproj"
            for f in post_processed_project.files
        ]
    ), "Test project should have a csproj file named after the source project"


def test_wpf_csproj_added():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    # add wpf refernces to source project
    csproj_file = [f for f in source_project.files if f.file_name.endswith(".csproj")][
        0
    ]
    csproj_file.source_code += '<Reference Include="PresentationFramework" />\n'

    post_processor = UnitTestPostProcessor(source_project)
    post_processor.load_dotnet_csproj()
    post_processed_project = post_processor.post_process(test_project)

    # check if test project has wpf references
    csproj_file = [
        f for f in post_processed_project.files if f.file_name.endswith(".csproj")
    ][0]
    assert (
        '<Reference Include="PresentationCore" />' in csproj_file.source_code
    ), "Test project should have a wpf reference"


def test_dotnet_gslite_without_hardcoded_csproj():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    post_processor = UnitTestPostProcessor(source_project)
    # rename csproj
    print([f.file_name for f in test_project.files])
    test_project.get_file(
        "Hashids.net-v112-Test.csproj"
    ).file_name = "TestWorked.csproj"

    post_processed_project = post_processor.post_process(test_project)
    # print filenames
    print([f.file_name for f in post_processed_project.files])
    # assert csproj is still there
    assert test_project.get_file("TestWorked.csproj")
