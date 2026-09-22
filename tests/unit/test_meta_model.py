"""Regression checks for the executable ontology meta-model."""

from dataclasses import replace

import pytest

from caron import (
    Accepted,
    Diagnostic,
    DiagnosticLayer,
    EntityRef,
    InvariantDefinition,
    Property,
    Rejected,
    model4_ontology,
    validate_candidate,
    validate_ontology,
)
from caron._invariants import (
    INVARIANT_VALIDATORS,
    InvariantImplementation,
    InvariantStage,
    register_invariant,
)
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


@pytest.mark.parametrize(
    "fault",
    (
        "identifier",
        "blank",
        "missing",
        "unknown",
        "duplicate",
        "version",
        "relation_identifier",
        "dangling",
        "duplicate_relation",
    ),
)
def test_record_errors_stop_all_graph_checks(
    monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    # A deliberately separate test ontology exercises the acceptance machinery;
    # it neither removes declarations from nor impersonates the 5.0 catalogue.
    ontology = replace(
        model4_ontology(),
        id="test.local-staging",
        version="test",
        invariants=tuple(
            InvariantDefinition(name)
            for name in (
                "record_identifier_lexical",
                "required_text_non_blank",
                "test.graph",
            )
        ),
    )
    candidate = replace(
        minimal_candidate(), ontology_id=ontology.id, ontology_version=ontology.version
    )
    entity = candidate.entities[0]
    if fault == "identifier":
        entity = replace(entity, id=" ")
    elif fault == "blank":
        entity = replace(entity, properties=(Property("label", " \t"),))
    elif fault == "missing":
        entity = replace(entity, properties=())
    elif fault == "unknown":
        entity = replace(entity, kind="Unknown")
    candidate = replace(candidate, entities=(entity, *candidate.entities[1:]))
    if fault == "duplicate":
        candidate = replace(candidate, entities=(*candidate.entities, entity))
    if fault == "version":
        candidate = replace(candidate, ontology_version="different")
    if fault == "relation_identifier":
        candidate = replace(
            candidate,
            relations=(
                replace(candidate.relations[0], id=" "),
                *candidate.relations[1:],
            ),
        )
    if fault == "dangling":
        candidate = replace(
            candidate,
            relations=(
                replace(candidate.relations[0], source=EntityRef("missing")),
                *candidate.relations[1:],
            ),
        )
    if fault == "duplicate_relation":
        candidate = replace(
            candidate, relations=(*candidate.relations, candidate.relations[0])
        )

    def unexpected_graph_check(*_args: object) -> tuple[Diagnostic, ...]:
        raise AssertionError("Graph-wide validation ran before local acceptance")

    monkeypatch.setitem(
        INVARIANT_VALIDATORS,
        "test.graph",
        InvariantImplementation(unexpected_graph_check, InvariantStage.REALISATION),
    )
    monkeypatch.setattr(
        "caron.validation._validate_relation_requirements", unexpected_graph_check
    )
    monkeypatch.setattr(
        "caron.validation._validate_temporal_containment", unexpected_graph_check
    )

    result = validate_candidate(ontology, candidate)

    assert isinstance(result, Rejected)
    expected = {
        "identifier": "record.invalid_identifier",
        "blank": "record.blank_required_text",
        "missing": "record.missing_required_property",
        "unknown": "record.unknown_concept",
        "duplicate": "realisation.duplicate_entity_id",
        "version": "realisation.ontology_version_mismatch",
        "relation_identifier": "record.invalid_identifier",
        "dangling": "record.dangling_endpoint",
        "duplicate_relation": "realisation.duplicate_relation_id",
    }
    assert expected[fault] in {item.code for item in result.diagnostics}


def test_local_and_graph_handlers_run_once_in_stage_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def local_check(*_args: object) -> tuple[Diagnostic, ...]:
        calls.append("local")
        return ()

    def graph_check(*_args: object) -> tuple[Diagnostic, ...]:
        calls.append("graph")
        return ()

    monkeypatch.setitem(
        INVARIANT_VALIDATORS,
        "test.local",
        InvariantImplementation(local_check, InvariantStage.LOCAL_RECORD),
    )
    monkeypatch.setitem(
        INVARIANT_VALIDATORS,
        "test.graph",
        InvariantImplementation(graph_check, InvariantStage.REALISATION),
    )
    ontology = replace(
        model4_ontology(),
        id="test.stages",
        version="test",
        invariants=(
            InvariantDefinition("test.graph"),
            InvariantDefinition("test.local"),
            InvariantDefinition("record_identifier_lexical"),
            InvariantDefinition("required_text_non_blank"),
        ),
    )
    candidate = replace(
        minimal_candidate(), ontology_id=ontology.id, ontology_version=ontology.version
    )

    result = validate_candidate(ontology, candidate)

    assert isinstance(result, Accepted)
    assert calls == ["local", "graph"]
    assert result.realisation.entities == candidate.entities
    assert result.realisation.relations == candidate.relations


def test_local_invariants_only_apply_when_declared() -> None:
    candidate = minimal_candidate()
    entity = replace(candidate.entities[0], properties=(Property("label", ""),))
    candidate = replace(candidate, entities=(entity, *candidate.entities[1:]))

    # Legacy schemas have not adopted the new required-text invariant.
    assert isinstance(validate_candidate(model4_ontology(), candidate), Accepted)
