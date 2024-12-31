from typing import Dict
from dapr.ext.grpc import InvokeMethodRequest
from . import current_trace_id, current_company_id, current_user_id


def extract_trace_info(request: InvokeMethodRequest) -> None:
    """
    Extracts the trace info (traceid, companyid, userid) from the request headers and sets it in the contextvar
    Use this at the beginning of every method to ensure logging is using the correct trace info
    :param request: The incoming request
    """
    trace_id_full = request.metadata.get("traceparent", [None])[0]
    correctx = request.metadata.get("correlation-context", [None])[0]
    # correctx is formatted as a string: "CompanyID=company_id, UserID=user_id"
    try:
        company_id = correctx.split(",")[0].strip().split("=")[1]
        user_id = correctx.split(",")[1].strip().split("=")[1]
    except Exception:
        company_id = None
        user_id = None

    current_trace_id.set(trace_id_full)
    current_company_id.set(company_id)
    current_user_id.set(user_id)


def inject_trace_info() -> Dict[str, str]:
    """
    Injects the trace info into the headers (traceid, companyid, userid)
    Usage: with DaprClient(headers_callback=inject_trace_info) as d:
    Every request made with the DaprClient will have the trace info injected into the headers
    """
    trace_id = current_trace_id.get()
    company_id = current_company_id.get()
    user_id = current_user_id.get()
    ret_dict = {}
    if trace_id:
        ret_dict["traceparent"] = trace_id
    if company_id and user_id:
        ret_dict["correlation-context"] = f"CompanyID={company_id}, UserID={user_id}"
    return ret_dict
