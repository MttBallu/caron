"""Regression checks for the renderer experiment."""

from dataclasses import replace
from pathlib import Path

from caron import (
    Accepted,
    GraphView,
    TemporalExtent,
    TemporalMatch,
    TemporalMatchMode,
    TemporalWindow,
    YearMonth,
    before,
    covered_months,
    select_activities_in_window,
    select_whole_realisation,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0
from examples.cytoscape_html import (
    _cytoscape_value,
    graph_view_to_cytoscape,
    render_cytoscape_html,
)
from examples.semantic_spine import build_candidate, validate_example
from examples.temporal_queries import build_candidate as temporal_candidate


def _whole_example_view() -> GraphView[object]:
    return select_whole_realisation(validate_example(build_candidate()))


def _temporal_view() -> GraphView[TemporalMatch]:
    validation = validate_candidate(career_ontology_v5_0(), temporal_candidate())
    assert isinstance(validation, Accepted)
    return select_activities_in_window(
        validation.realisation,
        TemporalWindow.closed("2022-01", "2022-12"),
        mode=TemporalMatchMode.POSSIBLE,
    )


def test_adapter_preserves_long_entity_content() -> None:
    graph = graph_view_to_cytoscape(_whole_example_view())
    nodes = graph["nodes"]
    assert isinstance(nodes, list)
    proposition = next(
        item for item in nodes if item["data"]["id"] == "proposition:rb90-discrepancy"
    )

    assert proposition["data"]["properties"] == [
        {
            "name": "content",
            "value": {
                "type": "text",
                "value": (
                    "The measured cascade intensity differs from evaluated data."
                ),
            },
        },
        {
            "name": "context",
            "value": {
                "type": "entity_reference",
                "entity_id": "context:phd",
                "label": "Nuclear-physics PhD",
                "kind": "Context",
            },
        },
    ]


def test_renderer_injects_data_and_removes_template_token(tmp_path: Path) -> None:
    output = tmp_path / "view.html"

    render_cytoscape_html(
        _whole_example_view(),
        output,
    )

    html = output.read_text(encoding="utf-8")
    assert "__CARON_GRAPH_DATA__" not in html
    assert "proposition:rb90-discrepancy" in html
    assert "cytoscape({" in html


def test_representative_v5_graph_renders_new_concepts_and_typed_award() -> None:
    graph = graph_view_to_cytoscape(_whole_example_view())
    metadata = graph["metadata"]
    nodes = graph["nodes"]
    assert isinstance(metadata, dict)
    assert isinstance(nodes, list)

    assert metadata["ontology_version"] == "5.0"
    new_kinds = {
        node["data"]["kind"]
        for node in nodes
        if node["data"]["kind"] in {"Collective", "Language", "Credential"}
    }
    assert new_kinds == {"Collective", "Language", "Credential"}

    credential = next(
        node for node in nodes if node["data"]["id"] == "credential:doctorate"
    )
    assert credential["data"]["properties"] == [
        {
            "name": "awarded_in",
            "value": {"type": "year_month", "value": "2025-10"},
        }
    ]


def test_reference_valued_organization_qualifier_remains_navigable() -> None:
    graph = graph_view_to_cytoscape(_whole_example_view())
    edges = graph["edges"]
    assert isinstance(edges, list)
    participation = next(
        edge for edge in edges if edge["data"]["id"] == "relation:participation"
    )

    organization = next(
        item
        for item in participation["data"]["qualifiers"]
        if item["name"] == "organization"
    )
    assert organization["value"] == {
        "type": "entity_reference",
        "entity_id": "organization:cea",
        "label": "CEA",
        "kind": "Organization",
    }


def test_contextual_relation_is_visibly_anchored_to_its_context() -> None:
    graph = graph_view_to_cytoscape(_whole_example_view())
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)

    relation_node_id = "view:contextual-relation:relation:learns-fitting"
    relation_node = next(
        item for item in nodes if item["data"]["id"] == relation_node_id
    )
    relation_legs = {
        item["data"]["view_role"]: item["data"]
        for item in edges
        if item["data"].get("semantic_relation_id") == "relation:learns-fitting"
    }

    assert relation_node["data"]["kind"] == "ContextualRelation"
    assert {item["name"] for item in relation_node["data"]["properties"]} == {
        "source",
        "target",
        "context",
    }
    assert relation_legs["source"]["source"] == "person:matteo"
    assert relation_legs["target"]["target"] == "method:peak-fitting"
    assert relation_legs["context"]["target"] == "context:phd"


def test_adapter_serializes_temporal_extents_and_query_results() -> None:
    graph = graph_view_to_cytoscape(_temporal_view())
    metadata = graph["metadata"]
    nodes = graph["nodes"]
    assert isinstance(metadata, dict)
    assert isinstance(nodes, list)

    assert metadata["query"]["name"] == "activities_in_temporal_window"
    assert {
        (item["entity_id"], item["classification"])
        for item in metadata["query"]["results"]
    } == {
        ("activity:analyse-alice-data", "possible"),
        ("activity:build-synthetic-dataset", "possible"),
    }

    alice = next(
        item for item in nodes if item["data"]["id"] == "context:alice-project"
    )
    extent = next(
        item["value"]
        for item in alice["data"]["properties"]
        if item["name"] == "temporal_extent"
    )
    assert extent == {
        "type": "temporal_extent",
        "start": "2021-11",
        "end": {"kind": "known", "month": "2022-02"},
        "display": "2021-11 — 2022-02",
    }

    activity = next(
        item for item in nodes if item["data"]["id"] == "activity:analyse-alice-data"
    )
    assert activity["data"]["query_classification"] == "possible"
    assert activity["data"]["query_results"][0]["witness"]["relations"] == [
        "relation:alice-activity-occurs-in"
    ]


def test_renderer_exposes_temporal_result_in_inspector_payload(tmp_path: Path) -> None:
    output = tmp_path / "temporal-view.html"

    render_cytoscape_html(_temporal_view(), output)

    html = output.read_text(encoding="utf-8")
    assert '"type":"temporal_extent"' in html
    assert '"classification":"possible"' in html
    assert "appendQueryResults(data.query_results || [])" in html
    assert "witnessDescription(result.witness)" in html
    assert "Witness ·" in html


def test_adapter_serializes_open_temporal_end_states() -> None:
    assert _cytoscape_value(TemporalExtent.unknown_end("2024-01"), {}) == {
        "type": "temporal_extent",
        "start": "2024-01",
        "end": {"kind": "unknown"},
        "display": "2024-01 — unknown",
    }
    assert _cytoscape_value(TemporalExtent.ongoing("2026-04", as_of="2026-09"), {}) == {
        "type": "temporal_extent",
        "start": "2026-04",
        "end": {"kind": "ongoing_as_of", "as_of": "2026-09"},
        "display": "2026-04 — ongoing (as of 2026-09)",
    }


def test_adapter_serializes_year_month_property_value() -> None:
    assert _cytoscape_value(YearMonth.parse("2025-10"), {}) == {
        "type": "year_month",
        "value": "2025-10",
    }


def test_adapter_serializes_other_temporal_result_kinds() -> None:
    validation = validate_candidate(career_ontology_v5_0(), temporal_candidate())
    assert isinstance(validation, Accepted)
    realisation = validation.realisation
    predicate = before(realisation, "context:alice-project", "context:phd")
    count = covered_months(realisation, "context:phd")
    view = replace(
        select_whole_realisation(realisation),
        query_name="temporal_result_serialization",
        results=(predicate, count),
    )

    graph = graph_view_to_cytoscape(view)
    metadata = graph["metadata"]
    assert isinstance(metadata, dict)
    results = metadata["query"]["results"]

    assert results[0]["type"] == "temporal_predicate"
    assert results[0]["predicate"] == "before"
    assert results[0]["classification"] == "entailed"
    assert results[1]["type"] == "covered_months"
    assert results[1]["kind"] == "exact"
    assert (results[1]["minimum"], results[1]["maximum"]) == (37, 37)
