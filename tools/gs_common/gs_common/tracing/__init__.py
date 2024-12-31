import contextvars

# Context variable for trace_id
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)
current_company_id = contextvars.ContextVar("current_company_id", default=None)
current_user_id = contextvars.ContextVar("current_user_id", default=None)

from .trace_logger import setup_logging
from .utils import extract_trace_info, inject_trace_info

__all__ = [
    "setup_logging",
    "extract_trace_info",
    "inject_trace_info",
]
