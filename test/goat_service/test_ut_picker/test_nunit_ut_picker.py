import pytest
from gs_common.CodeProject import CodeFile, CodeProject

from dataset.util import load_example_project
from src.goat_service.ut_picker.nunit_ut_picker import NUnitUTPicker


def test_nunit_hashids_get_metric_perc_classes_tested():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_classes_tested(test_project) == 100.0


def test_hashids_get_metric_perc_classes_tested_0():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_classes_tested(test_project) == 0.0


def test_hashids_get_metric_perc_useful_asserts():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")

    picker = NUnitUTPicker(source_project)
    # Hashids tests are pretty bad, should be changed
    assert picker.get_metric_perc_useful_asserts(test_project) > 10


def test_hashids_get_metric_perc_useful_asserts_0():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    useless_asserts_file = CodeFile(
        file_name="Dummy.cs",
        source_code="Assert.IsEmpty();\nAssert.IsNotEmpty();\nAssert.IsNull();\nAssert.IsNotNull();\n",
    )
    test_project = CodeProject(
        files=[useless_asserts_file], source_language="dotnet8", display_name="Dummy"
    )

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_useful_asserts(test_project) == 0


def test_qrcoder_percent_classes_tested():
    source_project = load_example_project("QRCoder", "dotnetframework")
    test_project = load_example_project("QRCoder-GSTests", "nunit_unittests")

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_classes_tested(test_project) == 50


def test_qrcoder_percent_useful_asserts():
    source_project = load_example_project("QRCoder", "dotnetframework")
    test_project = load_example_project("QRCoder-GSTests", "nunit_unittests")

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_useful_asserts(test_project) > 50


def test_many_files_percent_classes_tested_and_useful_asserts():
    project_names = [
        "QRCoder",
        "Hashids.net-v112",
    ]
    source_project = load_example_project(project_names[0], "dotnetframework")
    test_project = load_example_project(
        project_names[0] + "-GSTests", "nunit_unittests"
    )
    for project_name in project_names[1:]:
        source_project.files.extend(
            load_example_project(project_name, "dotnetframework").files
        )
        test_project.files.extend(
            load_example_project(project_name + "-GSTests", "nunit_unittests").files
        )

    picker = NUnitUTPicker(source_project)
    assert picker.get_metric_perc_classes_tested(test_project) > 40
    assert picker.get_metric_perc_useful_asserts(test_project) > 30


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
