"""A broad authored career fixture exercises cross-context read semantics."""

from hashlib import sha256
from pathlib import Path

from caron import (
    CoverageStatus,
    CoveredMonthKind,
    EntityRef,
    TemporalClassification,
    before,
    career_ontology_v5_0,
    covered_months,
    select_whole_realisation,
)
from caron._bundled_realisation import load_bundled_career_realisation
from caron.yaml_reader import LoadAccepted, LoadRejected, load_realisation_yaml

FIXTURE = Path(__file__).parents[2] / "caron/data/career-across-contexts-v0.1.yaml"


def test_career_wide_fixture_retains_cross_period_witnesses() -> None:
    result = load_bundled_career_realisation()
    assert isinstance(result, LoadAccepted), result
    assert result.source_path == FIXTURE
    graph = result.realisation
    assert len(graph.entities) >= 60 and len(graph.relations) >= 80
    assert graph.coverage.status is CoverageStatus.SELECTIVE
    assert graph.id == "fixture:career-across-contexts"
    assert result.source_state_id == sha256(FIXTURE.read_bytes()).hexdigest()

    python_uses = graph.matching_relations(
        kind="uses_technology", target_id="technology:python"
    )
    assert {relation.source.entity_id for relation in python_uses} >= {
        "activity:build-open-data-poc",
        "activity:fit-galaxy-spectra",
        "activity:analyse-alice-data",
        "activity:generate-synthetic-spectra",
        "activity:implement-jax-losses",
    }
    learning = graph.relation("r:learns-geant4-msc")
    beta_use = graph.relation("r:beta-simulation-uses-geant4")
    assert learning is not None and beta_use is not None
    assert learning.qualifier("context") == EntityRef("context:geant4-course")
    assert beta_use.source == EntityRef("activity:simulate-beta-telescope")
    ordering = before(
        graph, "activity:analyse-alice-data", "activity:simulate-beta-telescope"
    )
    assert ordering.classification is TemporalClassification.ENTAILED
    assert "r:beta-spectrometer-part-of-phd" in ordering.witness.relations
    cea_months = covered_months(graph, "context:cea-internship")
    assert cea_months.kind is CoveredMonthKind.EXACT
    assert cea_months.minimum == cea_months.maximum == 7
    assert {
        "r:cea-internship-part-of-msc",
        "r:cea-internship-part-of-engineering",
    }.issubset(cea_months.witness.relations)
    assert (
        covered_months(graph, "context:jax-project").kind
        is CoveredMonthKind.EXACT_AS_OF
    )

    view = select_whole_realisation(graph)
    assert view.source_realisation_id == graph.id
    assert view.coverage == graph.coverage
    assert any(item.id == "r:learns-geant4-msc" for item in view.relations)


def test_career_wide_fixture_failure_keeps_location(tmp_path: Path) -> None:
    original = FIXTURE.read_text(encoding="utf-8")
    before = 'target: "technology:geant4"}'
    assert before in original
    changed = original.replace(before, 'target: "technology:missing"}', 1)
    file = tmp_path / "career.yaml"
    file.write_text(changed, encoding="utf-8")
    outcome = load_realisation_yaml(file, ontology=career_ontology_v5_0())
    assert isinstance(outcome, LoadRejected)
    finding = next(
        item for item in outcome.findings if item.code == "record.dangling_endpoint"
    )
    assert finding.record_id == "r:fipps-simulation-uses-geant4"
    assert finding.field == "target"
    assert finding.location is not None
    assert finding.location.path == file
    assert (
        finding.location.line
        == changed[: changed.index('target: "technology:missing"}')].count("\n") + 1
    )


def test_source_bytes_and_career_identity_are_separate(tmp_path: Path) -> None:
    original = load_realisation_yaml(FIXTURE, ontology=career_ontology_v5_0())
    assert isinstance(original, LoadAccepted)
    copied = tmp_path / "career.yaml"
    copied.write_bytes(FIXTURE.read_bytes() + b"\n# Another comment.\n")
    reloaded = load_realisation_yaml(copied, ontology=career_ontology_v5_0())
    assert isinstance(reloaded, LoadAccepted)
    assert reloaded.realisation == original.realisation
    assert reloaded.source_state_id != original.source_state_id
