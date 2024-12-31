from src.goat_service.tl_generator.tl_gen_service import TLGenService
from gs_common.CodeProject import CodeProject


def test_simple():
    s = TLGenService()
    assert s is not None


def test_rename_variable_in_one_file():
    source_project = CodeProject(
        display_name="p1",
        source_language="doesnotmatter",
        files=[],
    )
    source_project.add_file(file_name="f1", source_code="a = 1")
    source_project.add_file(file_name="f2", source_code="a = 1")
    target_language = "doesnotmatter"
    instruction = """
    # AI Plan
    ## Step 1: RENAME_VARIABLE
    Use <rename_variable old_name="a" new_name="b" file_path="f1" />
    ## Step 2: RENAME_VARIABLE
    Use <rename_variable old_name="a" new_name="b" file_path="f2" />

    # Current task: RENAME_VARIABLE
    Use <rename_variable old_name="a" new_name="b" file_path="f1" />
    """

    s = TLGenService()
    new_project = s._call_rename_variable(
        source_project=source_project,
        target_language=target_language,
        instruction=instruction,
    )

    assert new_project.files[0].source_code == "b = 1"
    assert new_project.display_name == "p1"
    assert new_project.files[0].file_name == "f1"
    assert new_project.files[1].source_code == "a = 1"
    assert new_project.files[1].file_name == "f2"


def test_rename_variable_global():
    source_project = CodeProject(
        display_name="p1",
        source_language="doesnotmatter",
        files=[],
    )
    source_project.add_file(file_name="f1", source_code="a = 1")
    source_project.add_file(file_name="f2", source_code="a = 1")
    target_language = "doesnotmatter"
    instruction = """
    # AI Plan
    ## Step 1: RENAME_VARIABLE_GLOBAL
    Use <rename_variable_global old_name="a" new_name="b"/>
    ## Step 2: RENAME_VARIABLE_GLOBAL
    Use <rename_variable_global old_name="1" new_name="2"/>

    # Current task: RENAME_VARIABLE_GLOBAL
    Use <rename_variable_global old_name="a" new_name="b"/>
    """

    s = TLGenService()
    new_project = s._call_rename_variable_global(
        source_project=source_project,
        target_language=target_language,
        instruction=instruction,
    )

    assert new_project.files[0].source_code == "b = 1"
    assert new_project.display_name == "p1"
    assert new_project.files[0].file_name == "f1"
    assert new_project.files[1].source_code == "b = 1"
    assert new_project.files[1].file_name == "f2"
