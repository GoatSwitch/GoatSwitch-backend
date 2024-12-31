from src.goat_service.tl_generator.utils.tl_postprocessor import (
    TLPostProcessor,
)
from gs_common.CodeProject import CodeProject, CodeFile

p1 = CodeProject(
    display_name="test",
    files=[
        CodeFile(file_name="test1.py", source_code="testtesttest"),
        CodeFile(file_name="test2.py", source_code="test2"),
    ],
)
p2 = CodeProject(
    display_name="testGPTADDEDSTH",
    files=[
        CodeFile(file_name="toast1.py", source_code="testtesttest"),
        CodeFile(file_name="test2.py", source_code="GoatSwitch"),
    ],
)


def test_postprocessing_identity():
    tpp = TLPostProcessor(p1)
    p1_processed = tpp.post_process(p1)
    assert p1_processed.display_name == p1.display_name
    assert p1_processed == p1


def test_postprocessing_rename():
    tpp = TLPostProcessor(p1)
    p2_processed = tpp.post_process(p2)
    # Make sure display_name is always same as source project
    assert p2_processed.display_name == p1.display_name
    # Make sure file names are renamed to match the source project
    assert p2_processed.files[0].file_name == "test1.py"
    assert p2_processed.files[1].file_name == "test2.py"
    # Make sure file contents are not changed
    assert p2_processed.files[1].source_code == p2.files[1].source_code
    assert p2_processed.files[0].source_code == p2.files[0].source_code


def test_postprocessing_rename_all():
    tpp = TLPostProcessor(p1)
    p2_processed = tpp.post_process_all([p2])
    assert len(p2_processed) == 1
    p2_processed = p2_processed[0]
    # Make sure display_name is always same as source project
    assert p2_processed.display_name == p1.display_name
    # Make sure file names are renamed to match the source project
    assert p2_processed.files[0].file_name == "test1.py"
    assert p2_processed.files[1].file_name == "test2.py"
    # Make sure file contents are not changed
    assert p2_processed.files[1].source_code == p2.files[1].source_code
    assert p2_processed.files[0].source_code == p2.files[0].source_code
