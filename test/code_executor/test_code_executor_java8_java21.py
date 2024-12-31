import pytest
from gs_common.file_ops import (
    generate_save_dir,
)

from dataset.util import (
    extract_maven_test_project,
    load_example_project,
    setup_trace_info_for_testing,
)
from src.code_executor.factories import CodeExecutorFactory

CONFIG = {
    "source_language": "java8",
    "testing_framework": "junit",
}
CONFIG_TL = {
    "source_language": "java21",
    "testing_framework": "junit",
}

setup_trace_info_for_testing()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # setup code here
    global save_dir
    save_dir = generate_save_dir("unittests-ce-java8-java21")
    yield
    # teardown code here


@pytest.mark.parametrize("project_name", ["spring-boot-payroll-example"])
def test_gradle_java8_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java8")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize("project_name", ["spring-boot-payroll-example"])
def test_gradle_java8_fail(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java8")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # modify tests
    for file in test_project.files:
        if file.file_name.endswith(".java"):
            file.source_code = file.source_code.replace(
                "assertEquals", "assertNotEquals", 1
            )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 1


@pytest.mark.parametrize("project_name", ["spring-boot-payroll-example"])
def test_gradle_java8_compile_error(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java8")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # modify
    file_name = "src/main/java/payroll/Employee.java"
    source_project.get_file(file_name).source_code = source_project.get_file(
        file_name
    ).source_code.replace("import", "importt", 1)

    # Act
    with pytest.raises(Exception) as e:
        ce = CodeExecutorFactory.create(
            CONFIG, source_project, test_project, save_dir=save_dir
        )
        ce.execute()

    # Assert
    assert "Build failed" in str(e.value)
    assert "compileJava FAILED" in str(e.value)


@pytest.mark.parametrize(
    "project_name",
    ["hql-criteria"],
)
def test_gradle_java21_success(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java21")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 0


@pytest.mark.parametrize(
    "project_name",
    ["hql-criteria"],
)
def test_gradle_java21_fail(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java21")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # modify tests
    for file in test_project.files:
        if file.file_name.endswith(".java"):
            file.source_code = file.source_code.replace(
                "assertEquals", "assertNotEquals", 1
            )

    # Act
    ce = CodeExecutorFactory.create(
        CONFIG, source_project, test_project, save_dir=save_dir
    )
    result = ce.execute()

    # Assert
    assert result.failed_tests == 1


@pytest.mark.parametrize("project_name", ["hql-criteria"])
def test_gradle_java21_compile_error(project_name):
    # Arrange
    source_project = load_example_project(project_name, "java21")
    test_project = load_example_project(project_name + "-GSTests", "junit_unittests")

    # modify
    file_name = "src/main/java/com/example/demo/controller/ZooGroupController.java"
    source_project.get_file(file_name).source_code = source_project.get_file(
        file_name
    ).source_code.replace("import", "importt", 1)

    # Act
    with pytest.raises(Exception) as e:
        ce = CodeExecutorFactory.create(
            CONFIG, source_project, test_project, save_dir=save_dir
        )
        ce.execute()

    # Assert
    assert "Build failed" in str(e.value)
    assert "compileJava FAILED" in str(e.value)
