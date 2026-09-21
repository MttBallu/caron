"""Regression checks for the executable ontology-schema viewer."""

from pathlib import Path
from typing import Any

from caron import OntologySchema, model4_ontology, model_v0_5_ontology
from examples.ontology_schema_html import (
    ontology_schema_to_cytoscape,
    render_ontology_schema_html,
)


def _graph_edges(ontology: OntologySchema) -> list[Any]:
    edges = ontology_schema_to_cytoscape(ontology)["edges"]
    assert isinstance(edges, list)
    return edges


def test_projection_contains_every_concept_and_admissible_endpoint_pair() -> None:
    ontology = model_v0_5_ontology()
    graph = ontology_schema_to_cytoscape(ontology)
    nodes = graph["nodes"]
    edges = graph["edges"]
    metadata = graph["metadata"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert isinstance(metadata, dict)

    assert {node["data"]["id"] for node in nodes} == {
        concept.id for concept in ontology.concepts
    }
    assert {
        (
            edge["data"]["kind"],
            edge["data"]["source"],
            edge["data"]["target"],
        )
        for edge in edges
    } == {
        (relation.kind, source_kind, target_kind)
        for relation in ontology.relations
        for source_kind in relation.source_kinds
        for target_kind in relation.target_kinds
    }
    assert metadata["relation_rule_count"] == len(ontology.relations)
    assert metadata["expanded_edge_count"] == len(edges) == 26


def test_projection_preserves_properties_qualifiers_and_requirements() -> None:
    ontology = model_v0_5_ontology()
    graph = ontology_schema_to_cytoscape(ontology)
    nodes = graph["nodes"]
    assert isinstance(nodes, list)

    context = next(node for node in nodes if node["data"]["id"] == "Context")
    assert context["data"]["properties"] == [
        {
            "name": "label",
            "value_kind": "text",
            "required": True,
            "allowed_reference_kinds": [],
        },
        {
            "name": "temporal_extent",
            "value_kind": "temporal_extent",
            "required": False,
            "allowed_reference_kinds": [],
        },
    ]

    learns_technology = next(
        edge
        for edge in _graph_edges(ontology)
        if edge["data"]["kind"] == "learns" and edge["data"]["target"] == "Technology"
    )
    assert learns_technology["data"]["source_kinds"] == ["Person"]
    assert learns_technology["data"]["target_kinds"] == [
        "Method",
        "Subject",
        "Technology",
    ]
    assert learns_technology["data"]["qualifiers"] == [
        {
            "name": "context",
            "value_kind": "entity_reference",
            "required": True,
            "allowed_reference_kinds": ["Context"],
        }
    ]

    performs = next(
        edge for edge in _graph_edges(ontology) if edge["data"]["kind"] == "performs"
    )
    assert performs["data"]["has_requirement"] is True
    assert performs["data"]["requirements"] == [
        {
            "concept": "Activity",
            "relation_kind": "performs",
            "endpoint": "target",
            "minimum": 1,
            "maximum": None,
            "display": "1..*",
        }
    ]


def test_version_selection_exposes_the_context_property_difference() -> None:
    model4 = ontology_schema_to_cytoscape(model4_ontology())
    temporal = ontology_schema_to_cytoscape(model_v0_5_ontology())
    model4_nodes = model4["nodes"]
    temporal_nodes = temporal["nodes"]
    assert isinstance(model4_nodes, list)
    assert isinstance(temporal_nodes, list)

    model4_context = next(
        node for node in model4_nodes if node["data"]["id"] == "Context"
    )
    temporal_context = next(
        node for node in temporal_nodes if node["data"]["id"] == "Context"
    )

    assert [item["name"] for item in model4_context["data"]["properties"]] == [
        "label",
        "start",
        "end",
        "status",
    ]
    assert [item["name"] for item in temporal_context["data"]["properties"]] == [
        "label",
        "temporal_extent",
    ]


def test_renderer_injects_schema_data_and_escapes_script_content(
    tmp_path: Path,
) -> None:
    output = tmp_path / "ontology.html"

    render_ontology_schema_html(
        model_v0_5_ontology(),
        output,
        title="Schema </script><script>alert(1)</script>",
    )

    html = output.read_text(encoding="utf-8")
    assert "__CARON_ONTOLOGY_DATA__" not in html
    assert '"projection":"executable_ontology_schema"' in html
    assert '"ontology_version":"0.5"' in html
    assert "\\u003c/script\\u003e" in html
    assert "cytoscape({" in html
