import logging
import os
import time
from typing import Optional

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from . import current_trace_id, current_company_id, current_user_id


class MaxLengthLogFormatter(logging.Formatter):
    """
    truncate the message to fit into the log
    NOTE: this limit is due to dapr using go to parse STDOUT.
    Gos bufio.Scanner has a MaxScanTokenSize of 64 * 1024
    if we go over that limit it crashes something and there are no further logs
    """

    def format(self, record: logging.LogRecord):
        formatted = super().format(record)
        # len_prefix = len(f"{record.asctime} - {record.levelname} - {record.trace_id} - ")
        len_prefix = 200  # above is correct, but not worth the effort
        max_message_length = (64 * 1024) - len_prefix - 1
        if len(formatted) > max_message_length:
            formatted = (
                f"{formatted:.{max_message_length}}... [truncated by gs_common logging]"
            )
        return formatted


class TraceInfoFilter(logging.Filter):
    """
    Injects the trace info (traceid, companyid, userid) into the log message if it exists
    """

    def filter(self, record):
        trace_id_full = current_trace_id.get()
        if trace_id_full:
            # the full w3c trace id is in the format of
            # version-parentspan_id-span_id-sampled
            # we care about the parentspan_id
            trace_id = trace_id_full.split("-")[1]
        else:
            trace_id = "NA"
        user_id = current_user_id.get("NA")
        company_id = current_company_id.get("NA")
        record.__dict__["trace_id"] = trace_id
        record.__dict__["user_id"] = user_id
        record.__dict__["company_id"] = company_id
        return True


class InfoFilter(logging.Filter):
    """
    Add timestamp and level to log records.
    This should be used for the otel log handler, since it does not include these by default
    """

    default_time_format = "%Y-%m-%d %H:%M:%S"
    default_msec_format = "%s,%03d"

    def filter(self, record):
        ct = time.localtime(record.created)
        t = time.strftime(self.default_time_format, ct)
        t = self.default_msec_format % (t, record.msecs)
        record.__dict__["timestamp"] = t
        record.__dict__["level"] = record.levelname
        return True


def setup_logging(service_name: Optional[str] = None):
    """
    Setup logging for the service
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add handler to log to console
    stream_handler = logging.StreamHandler()
    formatter = MaxLengthLogFormatter(
        "%(asctime)s - %(levelname)s - %(company_id)s - %(user_id)s - %(trace_id)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)
    # Add trace id to log records
    stream_handler.addFilter(TraceInfoFilter())
    root_logger.addHandler(stream_handler)

    # Add handler to log to opentelemetry directly
    # NOTE: This is necessary for windows because otel-collector does not run on windows
    # to collect logs from stdout like it does on linux
    enable_otel_log_handler = os.getenv("ENABLE_OTEL_LOG_HANDLER")
    if os.name == "nt" and enable_otel_log_handler == "true":
        if not service_name:
            raise ValueError(
                "service_name is required for windows open telemetry logging"
            )
        add_otel_log_handler(service_name)


def add_otel_log_handler(service_name: str):
    """
    Add a handler to log to opentelemetry directly
    """
    OTLP_WIN_ENDPOINT = "otlp-win-router.dapr-monitoring.svc.cluster.local:4317"
    root_logger = logging.getLogger()
    root_logger.addFilter(InfoFilter())
    logger_provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "k8s.container.name": service_name,
                "k8s.namespace.name": "default",
                "k8s.pod.name": "N/A",
                "k8s.deployment.name": service_name,
            }
        )
    )
    set_logger_provider(logger_provider)
    exporter = OTLPLogExporter(insecure=True, endpoint=OTLP_WIN_ENDPOINT)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(exporter, max_export_batch_size=1)
    )
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger.addHandler(handler)
