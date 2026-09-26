"""Fix representative whole-career expectations before querying Neo4j."""

from pathlib import Path

import pytest

from caron import career_ontology_v5_0
from caron.adapters.neo4j_results import ActivityResourceMatch, LearningMatch
from caron.yaml_reader import LoadAccepted, load_realisation_yaml
from tests.fixtures.neo4j_career import PROBES, CareerProbe, source_matches

CAREER = Path(__file__).parents[2] / "caron/data/career-across-contexts-v0.1.yaml"


@pytest.mark.parametrize("probe", PROBES, ids=lambda probe: probe.target_id)
def test_career_probe_fixes_independent_source_witnesses(probe: CareerProbe) -> None:
    loaded = load_realisation_yaml(CAREER, ontology=career_ontology_v5_0())
    assert isinstance(loaded, LoadAccepted), loaded
    matches = source_matches(loaded.realisation, probe.target_id)
    assert {item.learns for item in matches if isinstance(item, LearningMatch)} == (
        probe.learning_ids
    )
    assert {
        item.resource_relation
        for item in matches
        if isinstance(item, ActivityResourceMatch)
    } == probe.resource_ids
    assert len(matches) == len(probe.learning_ids) + len(probe.resource_ids)
    if probe.target_id == "technology:geant4":
        assert {
            item.context.entity_id
            for item in matches
            if isinstance(item, LearningMatch)
        } == {"context:geant4-course"}
        assert {
            item.local_context.entity_id
            for item in matches
            if isinstance(item, ActivityResourceMatch)
        } == {"context:gamma-analysis", "context:beta-spectrometer"}
