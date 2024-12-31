from functools import wraps
import timeit
import logging

def timed(decimal_places=3, log_level="info"):
    """
    This decorator prints the execution time for the decorated function.
    :param decimal_places: The number of decimal places to round to.
    :param log_type: The type of log to use. Can be "info", "debug", "warning", or "error".
    """

    log_function = {
        "info": logging.info,
        "debug": logging.debug,
        "warning": logging.warning,
        "error": logging.error
    }.get(log_level, logging.info)  # Default to logging.info if log_level is not recognized

    def actual_timed(func):
        """This decorator prints the execution time for the decorated function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # timeit.default_timer() is the most accurate timer
            start = timeit.default_timer()
            result = func(*args, **kwargs)
            end = timeit.default_timer()
            log_function("{} ran in {}s".format(func.__name__, round(end - start, decimal_places)))
            return result
        return wrapper
    return actual_timed