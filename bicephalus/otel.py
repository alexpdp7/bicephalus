import logging

from opentelemetry import _logs
from opentelemetry.sdk import _logs as sdk_logs
from opentelemetry.sdk._logs import export as logs_export

from opentelemetry import trace
from opentelemetry.sdk import trace as sdk_trace
from opentelemetry.sdk.trace import export as trace_export

from opentelemetry.sdk import resources


def configure(log_level=logging.WARNING):
    resource = resources.Resource({"service.name": "bicephalus"})

    # configure OpenTelemetry tracing
    tracer_provider = sdk_trace.TracerProvider(resource=resource)
    trace_exporter = trace_export.ConsoleSpanExporter()
    trace_processor = trace_export.BatchSpanProcessor(trace_exporter)
    tracer_provider.add_span_processor(trace_processor)
    trace.set_tracer_provider(tracer_provider)

    # configure OpenTelemetry logging
    logger_provider = sdk_logs.LoggerProvider(resource=resource)
    log_exporter = logs_export.ConsoleLogExporter()
    logger_provider.add_log_record_processor(logs_export.SimpleLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(logger_provider)

    # configure Python logging to send logs to OpenTelemetry logging
    logging_handler = sdk_logs.LoggingHandler(logger_provider=logger_provider)
    logging.basicConfig(handlers=[logging_handler], level=log_level)
    logging.getLogger("aiohttp").propagate = False  # aiohttp is not OpenTelemetry-compliant and causes warnings
