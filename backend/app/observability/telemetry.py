from __future__ import annotations
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource


_tracer_provider: Optional[TracerProvider] = None
_logger: Optional[logging.Logger] = None


def setup_telemetry(service_name: str = "ensam-agent-os") -> TracerProvider:
    global _tracer_provider, _logger

    resource = Resource.create({"service.name": service_name, "service.version": "0.1.0"})
    _tracer_provider = TracerProvider(resource=resource)
    _tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_tracer_provider)

    _logger = logging.getLogger("ensam_agent_os")
    _logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    _logger.addHandler(handler)

    return _tracer_provider


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)


def get_tracer(name: str = "ensam-agent-os") -> trace.Tracer:
    return trace.get_tracer(name)


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        setup_telemetry()
    return _logger


def log_event(event_name: str, data: dict, level: str = "info"):
    logger = get_logger()
    record = logger.makeRecord(
        logger.name, getattr(logging, level.upper(), logging.INFO),
        "", 0, event_name, (), None,
    )
    record.extra_data = data
    logger.handle(record)


def create_span(name: str, attributes: Optional[dict] = None):
    tracer = get_tracer()
    span = tracer.start_span(name)
    if attributes:
        for k, v in attributes.items():
            span.set_attribute(k, str(v))
    return span
