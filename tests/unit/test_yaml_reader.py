"""The authored YAML path must converge on the public in-memory validator."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from caron import (
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    TemporalExtent,
    YearMonth,
    career_ontology_v5_0,
    validate_candidate,
)
from caron.temporal import OngoingAsOf, UnknownEnd
from caron.yaml_reader import LoadAccepted, LoadRejected, load_realisation_yaml

FIXTURE = Path(__file__).parents[1] / "fixtures/geant4-learning-and-activity-v0.1.yaml"
ONTOLOGY = career_ontology_v5_0()


def load_text(tmp_path: Path, content: str) -> LoadAccepted | LoadRejected:
    path = tmp_path / "career.yaml"
    path.write_text(content, encoding="utf-8")
    return load_realisation_yaml(path, ontology=ONTOLOGY)


def assert_finding(
    result: LoadAccepted | LoadRejected,
    code: str,
    *,
    record_id: str | None = None,
    field: str | None = None,
) -> None:
    assert isinstance(result, LoadRejected)
    matching = [item for item in result.findings if item.code == code]
    assert matching, result.findings
    finding = matching[0]
    if record_id is not None:
        assert finding.record_id == record_id
    if field is not None:
        assert finding.field == field
    if result.source_state_id is not None:
        assert finding.location is not None
        assert finding.location.line >= 1
        assert finding.location.column >= 1


def test_fixture_matches_independently_constructed_candidate() -> None:
    result = load_realisation_yaml(FIXTURE, ontology=ONTOLOGY)
    assert isinstance(result, LoadAccepted)
    candidate = RealisationCandidate(
        "fixture:geant4-learning-and-activity",
        ONTOLOGY.id,
        ONTOLOGY.version,
        (
            Entity("person:matteo", "Person", (Property("label", "Mattéo"),)),
            Entity("technology:geant4", "Technology", (Property("label", "GEANT4"),)),
            Entity("context:msc", "Context", (Property("label", "MSc"),)),
            Entity(
                "context:phd",
                "Context",
                (
                    Property("label", "PhD"),
                    Property(
                        "temporal_extent", TemporalExtent.closed("2022-10", "2025-10")
                    ),
                ),
            ),
            Entity(
                "activity:simulate-detector",
                "Activity",
                (Property("label", "Simulate a detector"),),
            ),
        ),
        (
            RelationAssertion(
                "relation:learns-geant4",
                "learns",
                EntityRef("person:matteo"),
                EntityRef("technology:geant4"),
                (Qualifier("context", EntityRef("context:msc")),),
            ),
            RelationAssertion(
                "relation:performs-simulation",
                "performs",
                EntityRef("person:matteo"),
                EntityRef("activity:simulate-detector"),
            ),
            RelationAssertion(
                "relation:simulation-context",
                "occurs_in",
                EntityRef("activity:simulate-detector"),
                EntityRef("context:phd"),
            ),
            RelationAssertion(
                "relation:simulation-uses-geant4",
                "uses_technology",
                EntityRef("activity:simulate-detector"),
                EntityRef("technology:geant4"),
            ),
        ),
        Coverage(
            CoverageStatus.SELECTIVE, "Selected GEANT4 learning and activity facts"
        ),
    )
    directly_validated = validate_candidate(ONTOLOGY, candidate)
    assert isinstance(directly_validated, Accepted)
    assert result.realisation == directly_validated.realisation
    assert result.source_state_id == sha256(FIXTURE.read_bytes()).hexdigest()
    learning = result.realisation.relation("relation:learns-geant4")
    assert learning is not None
    assert learning.qualifier("context") == EntityRef("context:msc")
    assert {item.id for item in result.realisation.relations} == {
        "relation:learns-geant4",
        "relation:performs-simulation",
        "relation:simulation-context",
        "relation:simulation-uses-geant4",
    }


def test_full_tagged_values_bind_without_ontology_field_lookup(tmp_path: Path) -> None:
    source = FIXTURE.read_text(encoding="utf-8")
    extra_entities = """  - id: "context:unknown"
    kind: "Context"
    properties:
      label: "Unknown end"
      temporal_extent: {type: "temporal_extent", start: "2023-01", end: {unknown: true}}
  - id: "context:ongoing"
    kind: "Context"
    properties:
      label: "Continuing"
      temporal_extent:
        type: "temporal_extent"
        start: "2023-01"
        end: {ongoing_as_of: "2026-09"}
  - id: "organization:university"
    kind: "Organization"
    properties: {label: "University"}
  - id: "credential:degree"
    kind: "Credential"
    properties:
      label: "Degree"
      awarded_in: {type: "year_month", value: "2025-10"}
  - id: "proposition:example"
    kind: "Proposition"
    properties:
      label: "Example"
      content: "One result"
      context: {type: "entity_ref", id: "context:phd"}
"""
    extra_relations = """  - id: "relation:award-to"
    kind: "awarded_to"
    source: "credential:degree"
    target: "person:matteo"
  - id: "relation:award-by"
    kind: "awarded_by"
    source: "credential:degree"
    target: "organization:university"
  - id: "relation:award-through"
    kind: "obtained_through"
    source: "credential:degree"
    target: "context:phd"
  - id: "relation:participation"
    kind: "participates_in"
    source: "person:matteo"
    target: "context:phd"
    qualifiers:
      role: "student"
      organization: {type: "entity_ref", id: "organization:university"}
"""
    source = source.replace("\nrelations:\n", f"\n{extra_entities}\nrelations:\n")
    result = load_text(tmp_path, source + extra_relations)
    assert isinstance(result, LoadAccepted), result
    graph = result.realisation
    credential = graph.entity("credential:degree")
    proposition = graph.entity("proposition:example")
    participation = graph.relation("relation:participation")
    assert credential is not None and proposition is not None
    assert participation is not None
    assert credential.property("awarded_in") == YearMonth.parse("2025-10")
    assert proposition.property("context") == EntityRef("context:phd")
    assert participation.qualifier("organization") == EntityRef(
        "organization:university"
    )
    unknown = graph.entity("context:unknown")
    ongoing = graph.entity("context:ongoing")
    assert unknown is not None and ongoing is not None
    unknown_extent = unknown.property("temporal_extent")
    ongoing_extent = ongoing.property("temporal_extent")
    assert isinstance(unknown_extent, TemporalExtent)
    assert isinstance(ongoing_extent, TemporalExtent)
    assert isinstance(unknown_extent.end, UnknownEnd)
    assert isinstance(ongoing_extent.end, OngoingAsOf)


@pytest.mark.parametrize(
    ("before", "after", "code", "record_id", "field"),
    [
        (
            'label: "Mattéo"',
            'label: {type: "year_month", value: "2025-13"}',
            "binding.invalid_year_month",
            "person:matteo",
            "properties.label",
        ),
        (
            'label: "Mattéo"',
            'label: {type: "year_month", value: "2025-10"}',
            "record.invalid_value_kind",
            "person:matteo",
            "label",
        ),
        (
            'label: "Mattéo"',
            "label: true",
            "binding.invalid_value_form",
            "person:matteo",
            "properties.label",
        ),
        (
            'label: "Mattéo"',
            'label: {type: "entity_ref", id: "context:msc"}',
            "record.invalid_value_kind",
            "person:matteo",
            "label",
        ),
        (
            'end:\n          known: "2025-10"',
            'end: {known: "2025-10", unknown: true}',
            "binding.invalid_temporal_extent",
            "context:phd",
            "properties.temporal_extent",
        ),
        (
            'context: {type: "entity_ref", id: "context:msc"}',
            'context: {type: "entity_ref", id: "context:missing"}',
            "record.dangling_reference",
            "relation:learns-geant4",
            "context",
        ),
        (
            '    qualifiers:\n      context: {type: "entity_ref", id: "context:msc"}\n',
            "",
            "record.missing_required_qualifier",
            "relation:learns-geant4",
            "context",
        ),
    ],
)
def test_binding_vs_semantic_failures(
    tmp_path: Path, before: str, after: str, code: str, record_id: str, field: str
) -> None:
    content = FIXTURE.read_text(encoding="utf-8")
    assert before in content
    result = load_text(tmp_path, content.replace(before, after, 1))
    assert_finding(result, code, record_id=record_id, field=field)
    assert isinstance(result, LoadRejected)
    if code.startswith("binding."):
        assert result.findings[0].layer == "typed_binding"
    else:
        assert any(item.layer == "local_record" for item in result.findings)


def test_semantic_errors_remain_available_in_memory(tmp_path: Path) -> None:
    valid = load_realisation_yaml(FIXTURE, ontology=ONTOLOGY)
    assert isinstance(valid, LoadAccepted)
    graph = valid.realisation
    learning = graph.relation("relation:learns-geant4")
    assert learning is not None
    broken = replace(
        learning,
        qualifiers=(Qualifier("context", EntityRef("context:missing")),),
    )
    candidate = RealisationCandidate(
        graph.id,
        ONTOLOGY.id,
        ONTOLOGY.version,
        graph.entities,
        (broken, *graph.relations[1:]),
        graph.coverage,
    )
    direct = validate_candidate(ONTOLOGY, candidate)
    assert not isinstance(direct, Accepted)
    result = load_text(
        tmp_path,
        FIXTURE.read_text(encoding="utf-8").replace(
            'id: "context:msc"}', 'id: "context:missing"}'
        ),
    )
    assert isinstance(result, LoadRejected)
    assert {item.code for item in result.findings} == {
        item.code for item in direct.diagnostics
    }


def test_codec_checks_every_record_before_ontology_selection(tmp_path: Path) -> None:
    content = FIXTURE.read_text(encoding="utf-8")
    content = content.replace('version: "5.0"', 'version: "5.1"')
    content = content.replace(
        'kind: "Technology"', 'kind: "Technology"\n    extra: true'
    )
    result = load_text(tmp_path, content)
    assert_finding(result, "codec.invalid_record_layout")
    assert isinstance(result, LoadRejected)
    assert result.findings[0].layer == "codec"


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda text: text.replace('version: "5.0"', 'version: "5.1"'),
            "load.unsupported_ontology",
        ),
        (
            lambda text: text.replace('format_version: "0.1"', 'format_version: "0.2"'),
            "codec.unsupported_format_version",
        ),
        (
            lambda text: text.replace('kind: "Person"', 'kind: "Unknown"'),
            "record.unknown_concept",
        ),
        (
            lambda text: text.replace(
                'kind: "Person"', 'kind: "Person"\n    kind: "Person"'
            ),
            "codec.duplicate_mapping_key",
        ),
        (
            lambda text: text.replace(
                'id: "context:msc"\n    kind:', 'id: "context:phd"\n    kind:'
            ),
            "realisation.duplicate_entity_id",
        ),
        (
            lambda text: text.replace(
                'id: "relation:simulation-uses-geant4"',
                'id: "relation:performs-simulation"',
            ),
            "realisation.duplicate_relation_id",
        ),
        (
            lambda text: (
                text
                + """  - id: "relation:repeat-learning"
    kind: "learns"
    source: "person:matteo"
    target: "technology:geant4"
    qualifiers:
      context: {type: "entity_ref", id: "context:msc"}
"""
            ),
            "realisation.duplicate_relation_fact",
        ),
        (
            lambda text: text.replace('id: "context:msc"}', 'id: "person:matteo"}'),
            "record.invalid_reference_kind",
        ),
        (
            lambda text: text.replace('known: "2025-10"', 'known: "2020-01"'),
            "record.invalid_temporal_extent",
        ),
        (
            lambda text: text.replace('label: "Mattéo"', 'label: &name "Mattéo"'),
            "codec.invalid_yaml",
        ),
        (
            lambda text: text.replace('label: "Mattéo"', 'label: !custom "Mattéo"'),
            "codec.invalid_yaml",
        ),
        (
            lambda text: text.replace('label: "Mattéo"', "label: 2024-01-01T00:00:00Z"),
            "codec.invalid_yaml",
        ),
        (lambda text: text + "---\nextra: document\n", "codec.invalid_yaml"),
    ],
)
def test_failures_keep_stage_and_code(
    tmp_path: Path, mutation: object, code: str
) -> None:
    assert callable(mutation)
    result = load_text(tmp_path, mutation(FIXTURE.read_text(encoding="utf-8")))
    assert_finding(result, code)


def test_missing_file_and_invalid_encoding(tmp_path: Path) -> None:
    missing = load_realisation_yaml(tmp_path / "missing.yaml", ontology=ONTOLOGY)
    assert isinstance(missing, LoadRejected)
    assert missing.source_state_id is None
    assert missing.findings[0].code == "reader.not_found"
    invalid = tmp_path / "bad.yaml"
    invalid.write_bytes(b"\xff")
    result = load_realisation_yaml(invalid, ontology=ONTOLOGY)
    assert_finding(result, "codec.invalid_encoding")
