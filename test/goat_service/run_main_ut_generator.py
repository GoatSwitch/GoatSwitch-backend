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
        # Create a typed message with content type and body
        response = d.invoke_method(
            "goat_service",
            "generate_unittests",
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


def validate_solutions(solutions, target_language):
    print("type of solutions:", type(solutions))
    print("type of solutions0:", type(solutions[0]))
    assert solutions != [], "Solutions should not be empty"

    for s in solutions:
        test_project = CodeProject.model_validate(s)
        assert len(test_project.files) == 1, "Test project should have one file"


if __name__ == "__main__":
    pytest.main(["-s", "-vv", __file__])
