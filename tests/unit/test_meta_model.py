"""Regression checks for the executable ontology meta-model."""

from dataclasses import replace

from caron import (
    Diagnostic,
    DiagnosticLayer,
    InvariantDefinition,
    Rejected,
    model4_ontology,
    validate_candidate,
    validate_ontology,
)
from caron._invariants import register_invariant
from tests.fixtures.minimal import minimal_candidate


@register_invariant("test.noop")
def _noop_invariant(*_args: object) -> tuple[Diagnostic, ...]:
    return ()


@register_invariant("test.reject")
def _rejecting_invariant(*_args: object) -> tuple[Diagnostic, ...]:
    return (
        Diagnostic(
            code="realisation.test_invariant",
            layer=DiagnosticLayer.REALISATION,
            message="The test invariant rejected this candidate.",
        ),
    )


def test_registered_invariant_is_structurally_valid() -> None:
    ontology = replace(
        model4_ontology(),
        invariants=(InvariantDefinition("test.noop"),),
    )

    assert validate_ontology(ontology) == ()


def test_duplicate_invariant_declaration_is_diagnosed() -> None:
    definition = InvariantDefinition("test.noop")
    ontology = replace(model4_ontology(), invariants=(definition, definition))

    diagnostics = validate_ontology(ontology)

    assert "ontology.duplicate_invariant" in {item.code for item in diagnostics}


def test_unimplemented_invariant_is_diagnosed() -> None:
    ontology = replace(
        model4_ontology(),
        invariants=(InvariantDefinition("test.not-implemented"),),
    )

    diagnostics = validate_ontology(ontology)

    assert {item.code for item in diagnostics} == {"ontology.unimplemented_invariant"}


def test_declared_invariant_runs_at_candidate_validation_boundary() -> None:
    ontology = replace(
        model4_ontology(),
        invariants=(InvariantDefinition("test.reject"),),
    )

    result = validate_candidate(ontology, minimal_candidate())

    assert isinstance(result, Rejected)
    assert {item.code for item in result.diagnostics} == {"realisation.test_invariant"}
