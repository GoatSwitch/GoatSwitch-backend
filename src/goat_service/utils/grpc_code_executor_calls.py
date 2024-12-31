import json

from dapr.aio.clients import DaprClient
from gs_common.tracing import inject_trace_info


async def _call_upgrade_assistant(source_project, target_language) -> dict:
    data = {
        "source_project": source_project.model_dump(),
        "target_language": target_language,
    }
    async with DaprClient(headers_callback=inject_trace_info) as d:
        task = d.invoke_method(
            "code-executor",
            "call_upgrade_assistant",
            data=json.dumps(data),
            # TODO: good to set here? or via k8s? i dont get error; probably need to catch or something and send to frontend as timeout err
            timeout=120,
        )
        response = await task
    return json.loads(response.data)


async def _call_pre_migration_assessor(source_project, target_language) -> dict:
    data = {
        "source_project": source_project.model_dump(),
        "target_language": target_language,
    }
    async with DaprClient(headers_callback=inject_trace_info) as d:
        task = d.invoke_method(
            "code-executor",
            "call_assess",
            data=json.dumps(data),
            timeout=120,
        )
        response = await task
    return json.loads(response.data)
