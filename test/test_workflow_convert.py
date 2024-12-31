import logging
import os
import time

import pytest
from gs_client import GSClient, GSClientResult
from gs_common.CodeProject import CodeProject

from dataset.util import load_example_project
from test.utils import MAX_WAIT_TIME, SERVER_URL

# setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def send_convert(
    source_project: CodeProject,
    target_language,
):
    gs_client = GSClient(
        server_url=SERVER_URL,
        max_wait_time=MAX_WAIT_TIME,
        project_name=source_project.display_name,
        run_id=os.getenv("RUN_ID", ""),
    )

    gs_client.connect()
    gs_client.send_workflow_basic(source_project, target_language)
    gs_client.disconnect()

    res: GSClientResult = gs_client.get_result()
    logging.info(f"res: {res}")

    # parse ut solution
    if gs_client.ut_result is None or len(gs_client.ut_result) == 0:
        raise Exception(f"ut_result is None: {source_project.display_name}")
    if gs_client.ut_result[0]["solution"] is None:
        raise Exception(
            f"ut_result[0]['solution'] is None: {source_project.display_name}"
        )
    test_output = gs_client.ut_result[0]["test_output"]
    if test_output is not None and test_output != "":
        logging.info(f"test_output: {test_output.splitlines()[0]}")
    ut_solution = CodeProject.model_validate(gs_client.ut_result[0]["solution"])
    if ut_solution is None:
        raise Exception(f"ut_solution is None: {source_project.display_name}")

    # parse tl solution
    if gs_client.tl_result is None or len(gs_client.tl_result) == 0:
        raise Exception(f"tl_result is None: {source_project.display_name}")
    if gs_client.tl_result[0]["solution"] is None:
        raise Exception(
            f"tl_result[0]['solution'] is None: {source_project.display_name}"
        )
    tl_solution = CodeProject.model_validate(gs_client.tl_result[0]["solution"])
    if tl_solution is None:
        raise Exception(f"tl_solution is None: {source_project.display_name}")

    return res, ut_solution, tl_solution


@pytest.mark.parametrize(
    "program",
    [
        "Hashids.net-v112",
    ],
)
def test_dotnetframework_dotnet8(program):
    source_project = load_example_project(program, "dotnetframework")
    send_convert(
        source_project,
        target_language="dotnet8",
    )


@pytest.mark.parametrize(
    "program",
    [
        "spring-boot-payroll-example",
    ],
)
def test_java8_java21(program):
    source_project = load_example_project(program, "java8")
    send_convert(
        source_project,
        target_language="java21",
    )


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "--workers", "1"])
    # exit()

    for i in range(20):
        time.sleep(1)
        print("iter: ------------- ", i)

        ### dotnetframework - dotnet8
        # test_dotnetframework_dotnet8("Hashids.net-v112")
        # test_dotnetframework_dotnet8("QRCoder")
        # test_dotnetframework_dotnet8("Crc32.NET-v100")
        # test_dotnetframework_dotnet8("CsvReader")
        # test_dotnetframework_dotnet8("CommonMark")
        # test_dotnetframework_dotnet8("GeoAPI")
        # test_dotnetframework_dotnet8("NLipsum.Core")
        # test_dotnetframework_dotnet8("Numbers")
        test_dotnetframework_dotnet8("Hashids.net-v112")

        ### java
        # test_java8_java21("spring-boot-payroll-example", False)

        exit()
