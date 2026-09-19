"""Minimal OpenTelemetry wiring shared by every service in this repo.

Uses the OTel API against an in-process console/no-op exporter by default so
the showcase runs and tests pass with zero external collector — swap the
exporter for OTLP (pointed at Grafana/Tempo/Jaeger, or ServiceNow's own
observability stack) via the OTEL_EXPORTER_OTLP_ENDPOINT env var with no
code changes, per the OpenTelemetry SDK's standard env-based config.
"""

from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

_configured = False


def configure_tracing(service_name: str) -> None:
    global _configured
    if _configured:
        return
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        # Imported lazily: the OTLP exporter package is an optional extra so
        # `pip install .` without it still works in fully offline/CI runs.
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _configured = True


def get_tracer(service_name: str):
    configure_tracing(service_name)
    return trace.get_tracer(service_name)
