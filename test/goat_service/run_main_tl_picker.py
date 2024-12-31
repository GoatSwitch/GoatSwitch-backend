import json
import pytest
from dapr.clients import DaprClient
from pprint import pprint

from gs_common.CodeProject import CodeProject, CodeFile
from dataset.util import load_example_project


def send_dapr(
    translated_projects=None,
    source_project=None,
    test_project=None,
    target_language=None,
):
    req_data = {}
    if translated_projects != None:
        req_data["translated_projects"] = [
            tp.model_dump() for tp in translated_projects
        ]
    if source_project != None:
        req_data["source_project"] = source_project.model_dump()
    if test_project != None:
        req_data["test_project"] = test_project.model_dump()
    if target_language != None:
        req_data["target_language"] = target_language

    with DaprClient() as d:
        # Create a typed message with content type and body
        response = d.invoke_method(
            "goat_service",
            "pick_translation",
            data=json.dumps(req_data),
        )
    if response.status_code == 200:
        pprint(response.json())
    else:
        print(response.status_code)
        print(response.text)
    return response


def test_fn_picker_dotnetframework_dotnet8_solutions_good():
    translated_projects = [
        CodeProject(
            files=[
                CodeFile(
                    file_name="unknown",
                    source_code="public class Fib {}",
                )
            ]
        ),
        load_example_project("Hashids.net-v112", "dotnet8"),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    test_project = load_example_project("Hashids.net-v112-GSTests", "nunit_unittests")
    target_language = "dotnet8"

    resp = send_dapr(
        translated_projects=translated_projects,
        source_project=source_project,
        test_project=test_project,
        target_language=target_language,
    )

    assert resp.status_code == 200
    assert resp.json()["solution"] == translated_projects[1].model_dump()


if __name__ == "__main__":
    pytest.main(["-s", "-vv", "-k", "dotnetfr", __file__])
    # test_fn_picker_dotnetframework_dotnet8_solutions_good()
    # test_fn_picker_dotnetframework_dotnet8_solutions_bad()
