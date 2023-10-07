import logging

from opentelemetry import _logs
from opentelemetry.sdk import _logs as sdk_logs
from opentelemetry.sdk._logs import export


def _formatter(lr):
    r = f"{lr.severity_text}: {lr.body}\n"
    if lr.attributes.get("exception.type"):
        r += f"{lr.attributes['exception.type']}: {lr.attributes['exception.message']}\n"
        r += lr.attributes['exception.stacktrace']
    return r


def configure_logging(level=logging.WARNING):
    logger_provider = sdk_logs.LoggerProvider()
    _logs.set_logger_provider(logger_provider)
    exporter = export.ConsoleLogExporter(formatter=_formatter)
    logger_provider.add_log_record_processor(export.SimpleLogRecordProcessor(exporter))
    handler = sdk_logs.LoggingHandler(logger_provider=logger_provider)

    logging.basicConfig(handlers=[handler], level=level)
