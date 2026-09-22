"""Internal staged implementations of declared ontology invariants."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from caron.diagnostics import Diagnostic, DiagnosticLayer
from caron.ontology import OntologySchema, ValueKind
from caron.realisations import RealisationCandidate

type InvariantValidator = Callable[
    [OntologySchema, RealisationCandidate], tuple[Diagnostic, ...]
]


class InvariantStage(Enum):
    LOCAL_RECORD = "local_record"
    REALISATION = "realisation"


@dataclass(frozen=True, slots=True)
class InvariantImplementation:
    validator: InvariantValidator
    stage: InvariantStage


INVARIANT_VALIDATORS: dict[str, InvariantImplementation] = {}


def register_invariant(
    invariant_id: str,
    *,
    stage: InvariantStage = InvariantStage.REALISATION,
) -> Callable[[InvariantValidator], InvariantValidator]:
    """Register one internal implementation for an inspectable invariant id."""

    def decorator(validator: InvariantValidator) -> InvariantValidator:
        if invariant_id in INVARIANT_VALIDATORS:
            raise ValueError(f"Invariant {invariant_id!r} is already registered")
        INVARIANT_VALIDATORS[invariant_id] = InvariantImplementation(validator, stage)
        return validator

    return decorator


@register_invariant("record_identifier_lexical", stage=InvariantStage.LOCAL_RECORD)
def _record_identifier_lexical(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    """Check opaque record identifiers without normalizing or parsing them."""

    diagnostics: list[Diagnostic] = []
    identifiers = (
        *(entity.id for entity in candidate.entities),
        *(relation.id for relation in candidate.relations),
    )
    for record_id in identifiers:
        if not record_id.strip() or record_id != record_id.strip():
            diagnostics.append(
                Diagnostic(
                    code="record.invalid_identifier",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        "Record identifiers must contain a non-whitespace character "
                        "and must not begin or end with whitespace."
                    ),
                    record_id=record_id,
                    field="id",
                )
            )
    return tuple(diagnostics)


@register_invariant("required_text_non_blank", stage=InvariantStage.LOCAL_RECORD)
def _required_text_non_blank(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    """Check present, well-typed required text; shape checks handle other errors."""

    diagnostics: list[Diagnostic] = []
    for entity in candidate.entities:
        concept = ontology.concept(entity.kind)
        if concept is None:
            continue
        for item in entity.properties:
            definition = concept.property_definition(item.name)
            if (
                definition is not None
                and definition.required
                and definition.value_kind is ValueKind.TEXT
                and isinstance(item.value, str)
                and not item.value.strip()
            ):
                diagnostics.append(_blank_text_diagnostic(entity.id, item.name))

    for relation in candidate.relations:
        relation_definition = ontology.relation(relation.kind)
        if relation_definition is None:
            continue
        for qualifier in relation.qualifiers:
            qualifier_definition = relation_definition.qualifier_definition(
                qualifier.name
            )
            if (
                qualifier_definition is not None
                and qualifier_definition.required
                and qualifier_definition.value_kind is ValueKind.TEXT
                and isinstance(qualifier.value, str)
                and not qualifier.value.strip()
            ):
                diagnostics.append(_blank_text_diagnostic(relation.id, qualifier.name))
    return tuple(diagnostics)


def _blank_text_diagnostic(record_id: str, field_name: str) -> Diagnostic:
    return Diagnostic(
        code="record.blank_required_text",
        layer=DiagnosticLayer.LOCAL_RECORD,
        message=f"Required text field {field_name!r} must not be blank.",
        record_id=record_id,
        field=field_name,
    )
