"""Structured diagnostics returned at explicit validation boundaries."""

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class DiagnosticLayer(StrEnum):
    ONTOLOGY = "ontology"
    LOCAL_RECORD = "local_record"
    REALISATION = "realisation"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    layer: DiagnosticLayer
    message: str
    severity: Severity = Severity.ERROR
    record_id: str | None = None
    field: str | None = None
