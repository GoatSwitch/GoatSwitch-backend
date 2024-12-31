import logging
import os

import pytest
from gs_client import GSClient, GSClientResult
from gs_common.CodeProject import CodeProject

from dataset.util import load_example_project
from test.utils import MAX_WAIT_TIME, SERVER_URL, get_dataset

# setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def send_gen_plan(
    source_project: CodeProject,
    instruction: str,
):
    gs_client = GSClient(
        server_url=SERVER_URL,
        max_wait_time=MAX_WAIT_TIME,
        project_name=source_project.display_name,
        run_id=os.getenv("RUN_ID", ""),
    )
    gs_client.connect()
    gs_client.send_workflow_gen_plan(source_project, instruction)
    gs_client.disconnect()
    res: GSClientResult = gs_client.get_result()
    logging.info(f"res: {res}")
    if res.translate_error:
        raise Exception(f"translate_error: {res.translate_error}")
    return res, gs_client.plan


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_gen_plan_upgrade_dotnet8(project_name: str):
    source_language = "dotnetframework"
    source_project = load_example_project(project_name, source_language)
    # instruction = "upgrade to dotnet8"
    # instruction = "upgrade to dotnet8 and add one docstring"
    instruction = "upgrade to dotnet8 and add serilog and add 3 logging statements"
    res, plan = send_gen_plan(source_project, instruction)
    print(f"test_gen_plan: plan: {plan}")
    assert "upgrade dotnet project" in plan
