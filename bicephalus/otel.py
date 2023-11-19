import logging
import os

from opentelemetry import _logs
from opentelemetry.sdk import _logs as sdk_logs
from opentelemetry.sdk._logs import export as logs_export

from opentelemetry import trace
from opentelemetry.sdk import trace as sdk_trace
from opentelemetry.sdk.trace import export as trace_export

from opentelemetry.sdk import resources

from opentelemetry.exporter.otlp.proto.grpc import _log_exporter, trace_exporter


def configure(log_level=logging.WARNING, force_localhost_export=False):
    resource = resources.Resource({"service.name": "bicephalus"})

    # configure OpenTelemetry tracing
    tracer_provider = sdk_trace.TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    console_trace_exporter = trace_export.ConsoleSpanExporter()
    console_trace_processor = trace_export.SimpleSpanProcessor(console_trace_exporter)
    tracer_provider.add_span_processor(console_trace_processor)

    if force_localhost_export or "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ or "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT" in os.environ:
        otlp_trace_exporter = trace_exporter.OTLPSpanExporter()
        otlp_trace_batch_processor = trace_export.BatchSpanProcessor(otlp_trace_exporter)
        tracer_provider.add_span_processor(otlp_trace_batch_processor)

    # configure OpenTelemetry logging
    logger_provider = sdk_logs.LoggerProvider(resource=resource)
    _logs.set_logger_provider(logger_provider)

    console_log_exporter = logs_export.ConsoleLogExporter()
    console_log_processor = logs_export.SimpleLogRecordProcessor(console_log_exporter)
    logger_provider.add_log_record_processor(console_log_processor)

    if force_localhost_export or "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ or "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT" in os.environ:
        otlp_log_exporter = _log_exporter.OTLPLogExporter()
        otlp_log_batch_processor = logs_export.BatchLogRecordProcessor(otlp_log_exporter)
        logger_provider.add_log_record_processor(otlp_log_batch_processor)

    # configure Python logging to send logs to OpenTelemetry logging
    logging_handler = sdk_logs.LoggingHandler(logger_provider=logger_provider)
    logging.basicConfig(handlers=[logging_handler], level=log_level)
    logging.getLogger("aiohttp").propagate = False  # aiohttp is not OpenTelemetry-compliant and causes warnings
