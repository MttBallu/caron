"""The proposed result keeps source witnesses and successful empty coverage."""

from dataclasses import replace

import pytest

from caron import Accepted, career_ontology_v5_0, validate_candidate
from caron.adapters.neo4j_projection import ProjectionError
from caron.adapters.neo4j_reconstruction import ReconstructedSnapshot
from caron.adapters.neo4j_results import (
    ActivityResourceMatch,
    LearningMatch,
    Request,
    assemble_result,
)
from caron.adapters.neo4j_retrieval import ActivityRow, LearningRow, RetrievalRows
from caron.realisations import RealisationCandidate
from tests.fixtures.query_algebra import validated_query_algebra_fixture


def _snapshot() -> ReconstructedSnapshot:
    source = validated_query_algebra_fixture()
    return ReconstructedSnapshot(
        candidate=RealisationCandidate(
            source.id,
            source.ontology.id,
            source.ontology.version,
            source.entities,
            source.relations,
            source.coverage,
        ),
        validated=source,
        source_state_id="source:sample",
    )


def _rows(snapshot: ReconstructedSnapshot) -> RetrievalRows:
    source = snapshot.validated
    return RetrievalRows(
        source.id,
        source.ontology.id,
        source.ontology.version,
        snapshot.source_state_id,
        source.coverage,
        (
            LearningRow("matteo", "geant4", "msc", "learns:geant4:msc"),
            LearningRow("matteo", "geant4", "geant4_refresh", "learns:geant4:refresh"),
        ),
        (
            ActivityRow(
                "matteo",
                "geant4",
                "implement_detector_simulation",
                "beta_telescope",
                "uses_technology",
                "performs:implement_detector_simulation",
                "occurs_in:implement_detector_simulation",
                "uses:geant4:detector",
            ),
        ),
    )


def test_assembly_keeps_individual_supports_and_reference_closed_view() -> None:
    snapshot = _snapshot()
    result = assemble_result(snapshot, Request("matteo", "geant4"), _rows(snapshot))
    assert result.diagnostics == ()
    assert len(result.matches) == 3
    assert isinstance(result.matches[0], LearningMatch)
    assert isinstance(result.matches[2], ActivityResourceMatch)
    assert result.matches[2].resource_relation == "uses:geant4:detector"
    assert result.view is not None
    assert {item.id for item in result.view.relations} == {
        "learns:geant4:msc",
        "learns:geant4:refresh",
        "performs:implement_detector_simulation",
        "occurs_in:implement_detector_simulation",
        "uses:geant4:detector",
    }
    assert {item.id for item in result.view.entities} == {
        "matteo",
        "geant4",
        "msc",
        "geant4_refresh",
        "implement_detector_simulation",
        "beta_telescope",
    }
    assert result.coverage == snapshot.validated.coverage
    assert result.view.results == result.matches
    assert tuple(binding.name for binding in result.view.bindings) == (
        "person",
        "target",
    )


def test_empty_and_rejected_requests_keep_request_source_and_coverage() -> None:
    snapshot = _snapshot()
    source = snapshot.validated
    empty_rows = RetrievalRows(
        source.id,
        source.ontology.id,
        source.ontology.version,
        snapshot.source_state_id,
        source.coverage,
        (),
        (),
    )
    result = assemble_result(snapshot, Request("matteo", "geant4"), empty_rows)
    assert result.matches == ()
    assert result.diagnostics == ()
    assert result.view is not None
    assert result.view.entities == ()
    assert result.view.relations == ()
    for request, code in (
        (Request("absent", "geant4"), "query.unknown_person"),
        (Request("msc", "geant4"), "query.invalid_person_kind"),
        (Request("matteo", "absent"), "query.unknown_target"),
        (Request("matteo", "msc"), "query.invalid_target_kind"),
    ):
        rejected = assemble_result(snapshot, request, None)
        assert rejected.request == request
        assert rejected.source_realisation_id == source.id
        assert rejected.coverage == source.coverage
        assert rejected.view is None and rejected.matches == ()
        assert rejected.diagnostics[0].code == code


def test_assembly_rejects_inconsistent_witnesses_or_snapshot_metadata() -> None:
    snapshot = _snapshot()
    rows = _rows(snapshot)
    with pytest.raises(ProjectionError, match="snapshot disagree"):
        assemble_result(
            snapshot,
            Request("matteo", "geant4"),
            replace(rows, source_state_id="other"),
        )
    altered = replace(
        rows, learning=(replace(rows.learning[0], context_id="beta_telescope"),)
    )
    with pytest.raises(ProjectionError, match="context disagrees"):
        assemble_result(snapshot, Request("matteo", "geant4"), altered)


def test_draft_rejects_a_validated_source_of_another_ontology_version() -> None:
    snapshot = _snapshot()
    other_ontology = replace(career_ontology_v5_0(), version="5.1")
    candidate = replace(snapshot.candidate, ontology_version="5.1")
    checked = validate_candidate(other_ontology, candidate)
    assert isinstance(checked, Accepted)
    other = ReconstructedSnapshot(candidate, checked.realisation, None)
    result = assemble_result(other, Request("matteo", "geant4"), None)
    assert result.matches == () and result.view is None
    assert tuple(item.code for item in result.diagnostics) == (
        "query.unsupported_ontology",
    )
