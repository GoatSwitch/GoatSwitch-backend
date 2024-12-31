import json
from pprint import pprint
from datetime import datetime

import pytest
from dapr.clients.grpc.client import DaprGrpcClient

import gs_common.proto.ut_picker_pb2 as utg_proto
from gs_common.CodeProject import CodeProject, CodeFile
from dataset.util import load_example_project

import gs_common.proto.ut_picker_pb2 as utg_proto
from gs_common.proto.common_pb2 import CodeProject as ProtoCodeProject
from gs_common.proto.common_pb2 import CodeFile as ProtoCodeFile
from google.protobuf.json_format import ParseDict, MessageToJson, MessageToDict

# NOTE: this file is not tested atm; might have to refactor all tests


def _save_all_test_projects(test_projects):
    pprint(test_projects)
    print("len test_projects:", len(test_projects))
    assert test_projects != []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, test_project in enumerate(test_projects):
        test_project.save_to_dir(f"generated/test_ut_gen_{timestamp}_{i}")


def send_dapr(
    source_project: CodeProject = None, target_language: str = None
) -> utg_proto.UTPickerResponse:
    # NOTE: make simpler
    proto_code_files = [
        ProtoCodeFile(file_name=cf.file_name, source_code=cf.source_code)
        for cf in source_project.files
    ]
    pcp = ProtoCodeProject(
        source_language=source_project.source_language,
        files=proto_code_files,
        display_name=source_project.display_name,
    )

    req_proto = utg_proto.UTPickerRequest(
        source_project=pcp, target_language=target_language
    )

    with DaprGrpcClient() as d:
        # Create a typed message with content type and body
        response = d.invoke_method(
            "goat_service",
            "pick_unittests",
            data=req_proto,
            timeout=1000,
        )

    # Deserialize the response
    resp_proto = utg_proto.UTPickerResponse()
    response.unpack(resp_proto)
    return resp_proto


def test_ut_gen_dotnetframework_json_solutions():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    ut_gen_resp = send_dapr(source_project=source_project, target_language="dotnet8")
    solution = CodeProject.model_validate(MessageToDict(ut_gen_resp.solution))
    _save_all_test_projects([solution])

    assert ut_gen_resp.return_code == 0

    relevant_public_functions = ["CalculatePremium", "ProcessClaim"]
    # concat all source_code
    source_code = "\n".join([cf.source_code for cf in source_project.files])
    # assert that all public functions are in the source code
    assert all([f in source_code for f in relevant_public_functions])
    # assert there are at least 2*3 [Test] in the solution
    assert source_code.count("[Test]") >= len(relevant_public_functions) * 3


def test_ut_gen_dotnetframework_dotnet8_qrcoder():
    source_project = load_example_project("QRCoder", "dotnetframework")
    resp = send_dapr(source_project=source_project, target_language="dotnet8")

    solution = resp.text()
    print("solution:\n", solution)

    assert resp.status_code == 200
    assert solution != ""


if __name__ == "__main__":
    # pytest.main(["-vv", "-s", __file__])
    test_ut_gen_dotnetframework_json_solutions()
    # test_ut_gen_dotnetframework_dotnet8_qrcoder()
