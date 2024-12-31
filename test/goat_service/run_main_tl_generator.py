import json

import pytest
from dapr.clients import DaprClient

from dataset.util import load_example_project
from gs_common.CodeProject import CodeProject, CodeFile


def send_dapr(source_project=None, target_language=None):
    req_data = {}
    if source_project != None:
        req_data["source_project"] = source_project.model_dump()
    if target_language != None:
        req_data["target_language"] = target_language

    with DaprClient() as d:
        response = d.invoke_method(
            "goat_service",
            "generate_translations",
            data=json.dumps(req_data),
            timeout=1000,
        )
    """
    if response.status_code == 200:
        pprint(response.json())
    else:
        print(response.status_code)
        print(response.text)
    """
    return response


def _check_single_file_solutions(solutions):
    assert solutions != []
    # check that solutions is a CodeProject
    for solution in solutions:
        code_project = CodeProject.model_validate(solution)
        print("len of files:", len(code_project.files))
        assert len(code_project.files) == 1


def test_dotnetframework_dotnet8_json_success():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    resp = send_dapr(source_project=source_project, target_language="dotnet8")
    assert resp.status_code == 200
    _check_single_file_solutions(resp.json()["solutions"])


if __name__ == "__main__":
    pytest.main(["-vv", "-s", "-k", "t", __file__])
