"""Internal registry for declared ontology-invariant implementations."""

from collections.abc import Callable

from caron.diagnostics import Diagnostic
from caron.ontology import OntologySchema
from caron.realisations import RealisationCandidate

type InvariantValidator = Callable[
    [OntologySchema, RealisationCandidate], tuple[Diagnostic, ...]
]


INVARIANT_VALIDATORS: dict[str, InvariantValidator] = {}


def register_invariant(
    invariant_id: str,
) -> Callable[[InvariantValidator], InvariantValidator]:
    """Register one internal implementation for an inspectable invariant id."""

    def decorator(validator: InvariantValidator) -> InvariantValidator:
        if invariant_id in INVARIANT_VALIDATORS:
            raise ValueError(f"Invariant {invariant_id!r} is already registered")
        INVARIANT_VALIDATORS[invariant_id] = validator
        return validator

    return decorator
