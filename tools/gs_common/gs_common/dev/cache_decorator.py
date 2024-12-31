from functools import wraps
import logging
from dapr.ext.grpc import InvokeMethodRequest, InvokeMethodResponse
from typing import Dict
from collections import OrderedDict
from google.protobuf.json_format import MessageToDict
from gs_common.tracing import extract_trace_info


def daprcache(maxsize: int = 3):
    """
    This decorator caches dapr grpc service calls
    """
    cache: OrderedDict[str, InvokeMethodResponse] = OrderedDict()

    def decorator(func):
        @wraps(func)
        def wrapper(req: InvokeMethodRequest) -> InvokeMethodResponse:
            try:
                req_grpc = MessageToDict(req._data)
                hash_str = str(req_grpc)
            except Exception as e:
                logging.error(f"Error hashing request: {e}")
                return func(req)
            if hash_str in cache:
                extract_trace_info(req)
                logging.info("Cache hit")
                result = cache[hash_str]
            else:
                result = func(req)
                # limit cache size to maxsize
                if len(cache) >= maxsize:
                    cache.popitem(last=False)
                cache[hash_str] = result
            return result

        return wrapper

    return decorator
